"""Tests for SandboxManager."""

import pytest

from sandbox import SandboxManager, SandboxErrorType


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
