"""Tests for FastAPI server."""

import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from predictor.models import AgentFailure, AgentPrediction, PredictionResult
from sandbox.models import SandboxErrorType


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)
    # Clean up WAL files if they exist
    Path(db_path + "-wal").unlink(missing_ok=True)
    Path(db_path + "-shm").unlink(missing_ok=True)


@pytest.fixture
def mock_predictor():
    """Create a mock predictor."""
    mock = MagicMock()

    # Mock leaderboard for /agents
    mock._collector.get_leaderboard.return_value = [
        MagicMock(miner_uid=1, weight=0.5, avg_brier=0.2, accuracy=0.8),
        MagicMock(miner_uid=2, weight=0.3, avg_brier=0.25, accuracy=0.75),
    ]

    # Mock successful prediction
    mock.predict_champion.return_value = PredictionResult(
        status="success",
        prediction=0.72,
        agent_predictions=[
            AgentPrediction(
                miner_uid=1,
                rank=0,
                version_id="12345678-1234-1234-1234-123456789012",
                prediction=0.72,
                reasoning="Test reasoning",
                cost=0.02,
            )
        ],
        total_cost=0.02,
    )

    mock.predict_council.return_value = PredictionResult(
        status="success",
        prediction=0.70,
        agent_predictions=[
            AgentPrediction(
                miner_uid=1,
                rank=0,
                version_id="12345678-1234-1234-1234-123456789012",
                prediction=0.72,
                cost=0.02,
            ),
            AgentPrediction(
                miner_uid=2,
                rank=1,
                version_id="12345678-1234-1234-1234-123456789013",
                prediction=0.68,
                cost=0.02,
            ),
        ],
        total_cost=0.04,
    )

    mock.predict_selected.return_value = PredictionResult(
        status="success",
        prediction=0.65,
        agent_predictions=[
            AgentPrediction(
                miner_uid=5,
                rank=4,
                version_id="12345678-1234-1234-1234-123456789014",
                prediction=0.65,
                cost=0.02,
            )
        ],
        total_cost=0.02,
    )

    return mock


@pytest.fixture
def client(temp_db_path, mock_predictor, monkeypatch):
    """Create test client with mocked dependencies."""
    import sys

    # Set env vars before importing
    monkeypatch.setenv("DATABASE_PATH", temp_db_path)
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_DAY", "5")
    monkeypatch.setenv("DAILY_BUDGET_USD", "1.0")
    monkeypatch.setenv("GATEWAY_URL", "http://localhost:8000")

    # Remove cached server modules
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("server"):
            del sys.modules[mod_name]

    # Mock the heavy dependencies before import
    mock_collector = MagicMock()
    mock_manager = MagicMock()

    with patch("server.app.check_gateway_health"):  # Skip gateway check in tests
        with patch("server.app.AgentCollector", return_value=mock_collector):
            with patch("server.app.SandboxManager", return_value=mock_manager):
                with patch("server.app.Predictor", return_value=mock_predictor):
                    import server.app as app_module

                    with TestClient(app_module.app) as client:
                        yield client


class TestHealthEndpoint:
    def test_health_returns_status_and_quota(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["requests_used"] == 0
        assert data["requests_limit"] == 5
        assert data["requests_remaining"] == 5

    def test_health_quota_updates_after_champion(self, client):
        # Champion uses 1 unit
        client.post(
            "/predict/champion",
            json={"question": "Test?", "resolution_criteria": "Test"},
        )
        response = client.get("/health")
        data = response.json()
        assert data["requests_used"] == 1
        assert data["requests_remaining"] == 4

    def test_health_quota_updates_after_council(self, client):
        # Council uses 3 units
        client.post(
            "/predict/council",
            json={"question": "Test?", "resolution_criteria": "Test"},
        )
        response = client.get("/health")
        data = response.json()
        assert data["requests_used"] == 3
        assert data["requests_remaining"] == 2


class TestAgentsEndpoint:
    def test_list_agents(self, client):
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) == 2
        assert data["agents"][0]["miner_uid"] == 1
        assert data["agents"][0]["rank"] == 0


def wait_for_job(client, job_id: str, max_attempts: int = 10):
    """Poll for job completion and return result."""
    for _ in range(max_attempts):
        response = client.get(f"/predict/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        if data["status"] == "completed":
            return data["result"]
        if data["status"] == "failed":
            raise AssertionError(f"Job failed: {data['error']}")
        time.sleep(0.1)
    raise AssertionError("Job did not complete in time")


class TestPredictEndpoints:
    def test_predict_champion(self, client):
        response = client.post(
            "/predict/champion",
            json={
                "question": "Will BTC reach 100k?",
                "resolution_criteria": "BTC price on Coinbase",
            },
        )
        assert response.status_code == 200
        job_data = response.json()
        assert "job_id" in job_data

        result = wait_for_job(client, job_data["job_id"])
        assert result["status"] == "success"
        assert result["prediction"] == 0.72
        assert "request_id" in result

    def test_predict_council(self, client):
        response = client.post(
            "/predict/council",
            json={
                "question": "Will ETH reach 10k?",
                "resolution_criteria": "ETH price on Coinbase",
            },
        )
        assert response.status_code == 200
        job_data = response.json()
        assert "job_id" in job_data

        result = wait_for_job(client, job_data["job_id"])
        assert result["status"] == "success"
        assert result["prediction"] == 0.70
        assert len(result["agent_predictions"]) == 2

    def test_predict_selected(self, client):
        response = client.post(
            "/predict/selected/5",
            json={
                "question": "Will SOL reach 500?",
                "resolution_criteria": "SOL price on Coinbase",
            },
        )
        assert response.status_code == 200
        job_data = response.json()
        assert "job_id" in job_data

        result = wait_for_job(client, job_data["job_id"])
        assert result["status"] == "success"
        assert result["prediction"] == 0.65


class TestRateLimiting:
    def test_rate_limit_enforced_champion(self, client):
        """Test that rate limit is enforced for champion mode (1 unit each)."""
        # Make 5 champion requests (5 units total, at limit)
        for _ in range(5):
            response = client.post(
                "/predict/champion",
                json={"question": "Test?", "resolution_criteria": "Test"},
            )
            assert response.status_code == 200

        # Next request should be rate limited
        response = client.post(
            "/predict/champion",
            json={"question": "Test?", "resolution_criteria": "Test"},
        )
        assert response.status_code == 429
        error = response.json()["detail"]
        assert "Rate limit exceeded" in error["message"]
        assert error["error_code"] == "rate_limit_exceeded"

    def test_rate_limit_enforced_council(self, client):
        """Test that rate limit accounts for council mode (3 units each)."""
        # Make 1 council request (3 units, 2 remaining)
        response = client.post(
            "/predict/council",
            json={"question": "Test?", "resolution_criteria": "Test"},
        )
        assert response.status_code == 200

        # Another council would need 3 units but only 2 remaining
        response = client.post(
            "/predict/council",
            json={"question": "Test?", "resolution_criteria": "Test"},
        )
        assert response.status_code == 429
        error = response.json()["detail"]
        assert "needs 3 units but you only have 2" in error["message"]
        assert error["error_code"] == "rate_limit_exceeded"


class TestBudgetLimit:
    def test_budget_limit_enforced(self, client, mock_predictor):
        """Test that budget limit is enforced after exceeding daily budget."""
        # Set predictor to return high-cost results
        mock_predictor.predict_champion.return_value = PredictionResult(
            status="success",
            prediction=0.72,
            agent_predictions=[
                AgentPrediction(
                    miner_uid=1,
                    rank=0,
                    version_id="12345678-1234-1234-1234-123456789012",
                    prediction=0.72,
                    cost=0.50,
                )
            ],
            total_cost=0.50,
        )

        # Make requests until budget is exceeded (budget is 1.0, each costs 0.50)
        for _ in range(2):
            response = client.post(
                "/predict/champion",
                json={
                    "question": "Test?",
                    "resolution_criteria": "Test",
                },
            )
            assert response.status_code == 200

        # Next request should be blocked due to budget
        response = client.post(
            "/predict/champion",
            json={
                "question": "Test?",
                "resolution_criteria": "Test",
            },
        )
        assert response.status_code == 503
        error = response.json()["detail"]
        assert "budget exceeded" in error["message"]
        assert error["error_code"] == "budget_exceeded"


class TestQueueFull:
    def test_queue_full_returns_error_in_result(self, client, mock_predictor):
        """Test that queue full error is returned in job result."""
        # Mock predictor to return a queue full failure
        mock_predictor.predict_champion.return_value = PredictionResult(
            status="error",
            error="Server busy",
            failures=[
                AgentFailure(
                    miner_uid=1,
                    rank=0,
                    error="Server busy. Max 6 agents running, 6 queued.",
                    error_type=SandboxErrorType.QUEUE_FULL,
                )
            ],
            total_cost=0.0,
        )

        response = client.post(
            "/predict/champion",
            json={"question": "Test?", "resolution_criteria": "Test"},
        )

        assert response.status_code == 200
        job_data = response.json()
        assert "job_id" in job_data

        result = wait_for_job(client, job_data["job_id"])
        assert result["status"] == "error"
        assert result["error"] == "Server busy"
        assert len(result["failures"]) == 1
        assert result["failures"][0]["error_type"] == "queue_full"
