"""Tests for PredictionLogger."""

import json
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from db import Database
from predictor import PredictionLogger, PredictionRequest


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    database = Database(db_path)
    yield database
    database.close()
    Path(db_path).unlink(missing_ok=True)
    Path(db_path + "-wal").unlink(missing_ok=True)
    Path(db_path + "-shm").unlink(missing_ok=True)


@pytest.fixture
def logger(db):
    """Create a PredictionLogger for testing."""
    return PredictionLogger(db)


@pytest.fixture
def sample_request():
    """Sample prediction request."""
    return PredictionRequest(
        question="Will BTC reach 100k?",
        resolution_criteria="BTC price on Coinbase",
        resolution_date="2026-12-31",
        categories=["crypto", "price"],
    )


class TestPredictionLogger:
    def test_log_successful_prediction(self, db, logger, sample_request):
        request_id = str(uuid4())
        version_id = uuid4()

        logger.log(
            request_id=request_id,
            version_id=version_id,
            request=sample_request,
            prediction=0.75,
            reasoning="BTC is trending up",
            cost=0.02,
            status="success",
        )

        # Verify in database
        cursor = db._conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE request_id = ?", (request_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["request_id"] == request_id
        assert row["version_id"] == str(version_id)
        assert row["question"] == "Will BTC reach 100k?"
        assert row["resolution_criteria"] == "BTC price on Coinbase"
        assert row["resolution_date"] == "2026-12-31"
        assert json.loads(row["categories"]) == ["crypto", "price"]
        assert row["prediction"] == 0.75
        assert row["reasoning"] == "BTC is trending up"
        assert row["cost"] == 0.02
        assert row["status"] == "success"
        assert row["error"] is None

    def test_log_failed_prediction(self, db, logger, sample_request):
        request_id = str(uuid4())
        version_id = uuid4()

        logger.log(
            request_id=request_id,
            version_id=version_id,
            request=sample_request,
            prediction=None,
            reasoning=None,
            cost=0.01,
            status="error",
            error="Agent timed out",
        )

        cursor = db._conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE request_id = ?", (request_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["prediction"] is None
        assert row["reasoning"] is None
        assert row["status"] == "error"
        assert row["error"] == "Agent timed out"

    def test_log_multiple_predictions_same_request(self, db, logger, sample_request):
        """Council mode logs 3 predictions with same request_id."""
        request_id = str(uuid4())

        for i in range(3):
            logger.log(
                request_id=request_id,
                version_id=uuid4(),
                request=sample_request,
                prediction=0.70 + i * 0.05,
                reasoning=f"Agent {i} reasoning",
                cost=0.02,
                status="success",
            )

        cursor = db._conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM predictions WHERE request_id = ?", (request_id,)
        )
        count = cursor.fetchone()[0]
        assert count == 3

    def test_log_with_minimal_request(self, db, logger):
        """Test logging with only required fields."""
        minimal_request = PredictionRequest(
            question="Will it rain?",
            resolution_criteria="Weather report",
        )
        request_id = str(uuid4())
        version_id = uuid4()

        logger.log(
            request_id=request_id,
            version_id=version_id,
            request=minimal_request,
            prediction=0.5,
            reasoning=None,
            cost=0.01,
            status="success",
        )

        cursor = db._conn.cursor()
        cursor.execute("SELECT * FROM predictions WHERE request_id = ?", (request_id,))
        row = cursor.fetchone()

        assert row is not None
        assert row["resolution_date"] is None
        assert row["categories"] is None
        assert row["reasoning"] is None
