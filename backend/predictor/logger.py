"""Prediction logging to database."""

import json
import logging
from uuid import UUID

from db import Database

from .models import PredictionRequest

logger = logging.getLogger(__name__)


class PredictionLogger:
    """Logs individual agent predictions to database."""

    def __init__(self, db: Database):
        self._db = db
        self._create_table()

    def _create_table(self) -> None:
        """Create predictions table if it doesn't exist."""
        with self._db._lock:
            cursor = self._db._conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id INTEGER PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    version_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    resolution_criteria TEXT NOT NULL,
                    resolution_date TEXT,
                    categories TEXT,
                    prediction REAL,
                    reasoning TEXT,
                    cost REAL NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._db._conn.commit()
        logger.info("Predictions table initialized")

    def log(
        self,
        request_id: str,
        version_id: UUID,
        request: PredictionRequest,
        prediction: float | None,
        reasoning: str | None,
        cost: float,
        status: str,
        error: str | None = None,
    ) -> None:
        """Log a single agent prediction."""
        with self._db._lock:
            cursor = self._db._conn.cursor()
            cursor.execute(
                """
                INSERT INTO predictions
                (request_id, version_id, question, resolution_criteria,
                 resolution_date, categories, prediction, reasoning, cost, status, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    str(version_id),
                    request.question,
                    request.resolution_criteria,
                    request.resolution_date,
                    json.dumps(request.categories) if request.categories else None,
                    prediction,
                    reasoning,
                    cost,
                    status,
                    error,
                ),
            )
            self._db._conn.commit()
        logger.debug(f"Logged prediction for request {request_id}")
