"""Tests for SandboxManager."""

import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from sandbox import SandboxManager, SandboxErrorType
from sandbox.models import SandboxResult


# Simple agent that returns a fixed prediction
SIMPLE_AGENT = """
def agent_main(event_data):
    return {
        "event_id": event_data["event_id"],
        "prediction": 0.75,
        "reasoning": "Test prediction"
    }
"""

# Agent that uses the gateway URL env var
GATEWAY_AWARE_AGENT = """
import os

def agent_main(event_data):
    gateway_url = os.environ.get("GATEWAY_URL", "not set")
    return {
        "event_id": event_data["event_id"],
        "prediction": 0.5,
        "reasoning": f"Gateway URL: {gateway_url}"
    }
"""

# Agent that raises an error
ERROR_AGENT = """
def agent_main(event_data):
    raise ValueError("Intentional test error")
"""

# Agent that returns invalid output
INVALID_OUTPUT_AGENT = """
def agent_main(event_data):
    return {"wrong": "format"}
"""

# Agent that takes too long
SLOW_AGENT = """
import time

def agent_main(event_data):
    time.sleep(300)  # 5 minutes
    return {"event_id": event_data["event_id"], "prediction": 0.5}
"""


@pytest.fixture
def manager():
    """Create a SandboxManager for testing."""
    with SandboxManager(gateway_url="http://host.docker.internal:8000") as mgr:
        yield mgr


class TestSandboxManager:
    def test_simple_agent(self, manager):
        """Test running a simple agent that returns a valid prediction."""
        result = manager.run_agent(
            agent_code=SIMPLE_AGENT,
            event_data={"event_id": "test-123", "title": "Test event"},
        )

        assert result.status == "success"
        assert result.output is not None
        assert result.output["event_id"] == "test-123"
        assert result.output["prediction"] == 0.75
        assert result.error is None

    def test_gateway_url_points_to_proxy(self, manager):
        """Test that GATEWAY_URL env var points to the cost-tracking proxy."""
        result = manager.run_agent(
            agent_code=GATEWAY_AWARE_AGENT,
            event_data={"event_id": "test-456", "title": "Test event"},
        )

        assert result.status == "success"
        # Agents should see the proxy URL (port 8888), not the direct gateway
        assert "host.docker.internal:8888" in result.output["reasoning"]

    def test_agent_error(self, manager):
        """Test handling of agent that raises an exception."""
        result = manager.run_agent(
            agent_code=ERROR_AGENT,
            event_data={"event_id": "test-789", "title": "Test event"},
        )

        assert result.status == "error"
        assert result.error_type == SandboxErrorType.AGENT_ERROR
        assert "Intentional test error" in result.error

    def test_invalid_output(self, manager):
        """Test handling of agent that returns invalid output."""
        result = manager.run_agent(
            agent_code=INVALID_OUTPUT_AGENT,
            event_data={"event_id": "test-000", "title": "Test event"},
        )

        assert result.status == "error"
        assert result.error_type == SandboxErrorType.AGENT_ERROR
        # The agent_runner catches this as a missing field error

    def test_timeout(self, manager):
        """Test that slow agents are killed after timeout."""
        result = manager.run_agent(
            agent_code=SLOW_AGENT,
            event_data={"event_id": "test-slow", "title": "Test event"},
            timeout=3,  # 3 second timeout
        )

        assert result.status == "error"
        assert result.error_type == SandboxErrorType.TIMEOUT
        assert "Timeout" in result.error

    def test_empty_agent_code(self, manager):
        """Test handling of empty agent code."""
        result = manager.run_agent(
            agent_code="",
            event_data={"event_id": "test", "title": "Test"},
        )

        assert result.status == "error"
        assert "empty" in result.error.lower()

    def test_custom_env_vars(self, manager):
        """Test that custom env vars are passed to the agent."""
        agent_code = """
import os

def agent_main(event_data):
    custom_var = os.environ.get("MY_CUSTOM_VAR", "not set")
    return {
        "event_id": event_data["event_id"],
        "prediction": 0.5,
        "reasoning": f"Custom var: {custom_var}"
    }
"""
        result = manager.run_agent(
            agent_code=agent_code,
            event_data={"event_id": "test", "title": "Test"},
            env_vars={"MY_CUSTOM_VAR": "hello"},
        )

        assert result.status == "success"
        assert "hello" in result.output["reasoning"]

    def test_result_has_cost_field(self, manager):
        """Test that SandboxResult includes cost tracking."""
        result = manager.run_agent(
            agent_code=SIMPLE_AGENT,
            event_data={"event_id": "test-cost", "title": "Test"},
        )

        assert result.status == "success"
        # Cost should be 0 since the agent didn't make any gateway calls
        assert result.cost == 0.0
        assert isinstance(result.cost, float)


class TestConcurrencyControl:
    """Tests for concurrency limiting (mocked, no Docker required)."""

    @pytest.fixture
    def mock_manager(self, monkeypatch):
        """Create a SandboxManager with mocked Docker and proxy."""
        # Set low limits for testing
        monkeypatch.setenv("MAX_CONCURRENT_AGENTS", "2")
        monkeypatch.setenv("MAX_QUEUED_AGENTS", "2")

        # Reload module to pick up new env vars
        import sandbox.manager
        import importlib
        importlib.reload(sandbox.manager)

        with patch("sandbox.manager.CostTrackingProxy"):
            with patch("sandbox.manager.docker.from_env"):
                with patch.object(sandbox.manager.SandboxManager, "_cleanup_old_containers"):
                    with patch.object(sandbox.manager.SandboxManager, "_build_image"):
                        with patch.object(sandbox.manager.SandboxManager, "_create_network"):
                            mgr = sandbox.manager.SandboxManager(gateway_url="http://localhost:8000")
                            yield mgr

    def test_queue_full_rejected(self, mock_manager):
        """Test that requests are rejected when queue is full."""
        results = []
        started = threading.Event()

        def slow_internal(*args, **kwargs):
            started.set()
            time.sleep(0.5)
            return SandboxResult(status="success", output={"event_id": "test", "prediction": 0.5})

        mock_manager._run_agent_internal = slow_internal

        def run_agent():
            result = mock_manager.run_agent(
                agent_code="test",
                event_data={"event_id": "test"},
            )
            results.append(result)

        # Start 4 threads (2 running + 2 queued = at capacity)
        threads = [threading.Thread(target=run_agent) for _ in range(4)]
        for t in threads:
            t.start()

        # Wait for first agent to start running
        started.wait(timeout=2)
        time.sleep(0.1)  # Give time for other threads to queue

        # 5th request should be rejected immediately
        result = mock_manager.run_agent(
            agent_code="test",
            event_data={"event_id": "test"},
        )

        assert result.status == "error"
        assert result.error_type == SandboxErrorType.QUEUE_FULL
        assert "Server busy" in result.error

        # Clean up threads
        for t in threads:
            t.join(timeout=2)

    def test_concurrent_limit_respected(self, mock_manager):
        """Test that max concurrent agents is respected."""
        concurrent_count = []
        max_concurrent = 0
        lock = threading.Lock()

        def tracking_internal(*args, **kwargs):
            nonlocal max_concurrent
            with lock:
                concurrent_count.append(1)
                current = sum(concurrent_count)
                if current > max_concurrent:
                    max_concurrent = current

            time.sleep(0.2)

            with lock:
                concurrent_count.pop()

            return SandboxResult(status="success", output={"event_id": "test", "prediction": 0.5})

        mock_manager._run_agent_internal = tracking_internal

        # Run 4 agents (should be limited to 2 concurrent)
        threads = []
        for _ in range(4):
            t = threading.Thread(
                target=mock_manager.run_agent,
                kwargs={"agent_code": "test", "event_data": {"event_id": "test"}},
            )
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=5)

        # Max concurrent should be 2 (the limit)
        assert max_concurrent == 2

    def test_semaphore_released_on_error(self, mock_manager):
        """Test that semaphore is released even when internal method raises."""
        call_count = 0

        def failing_internal(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated failure")
            return SandboxResult(status="success", output={"event_id": "test", "prediction": 0.5})

        mock_manager._run_agent_internal = failing_internal

        # First call will fail
        result1 = mock_manager.run_agent(
            agent_code="test",
            event_data={"event_id": "test"},
        )

        # Semaphore should be released, allowing second call
        result2 = mock_manager.run_agent(
            agent_code="test",
            event_data={"event_id": "test"},
        )

        # First call failed but semaphore was released
        # Second call should succeed
        assert result2.status == "success"
