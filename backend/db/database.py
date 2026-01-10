"""SQLite database for rate limiting and cost tracking."""

import logging
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class Database:
    """Thread-safe SQLite database wrapper."""

    def __init__(self, db_path: str):
        """
        Initialize database connection and create tables.

        Args:
            db_path: Path to SQLite database file
        """
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._lock = threading.Lock()
        self._create_tables()
        logger.info(f"Database initialized at {db_path}")

    def _create_tables(self) -> None:
        """Create tables if they don't exist."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.executescript("""
                -- Track requests per IP for rate limiting
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    units INTEGER NOT NULL DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_requests_ip_timestamp
                    ON requests(ip, timestamp);

                -- Track costs per request for budget
                CREATE TABLE IF NOT EXISTS costs (
                    id INTEGER PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    cost REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_costs_timestamp
                    ON costs(timestamp);
            """)
            self._conn.commit()

    def close(self) -> None:
        """Close database connection."""
        with self._lock:
            self._conn.close()
        logger.info("Database connection closed")

    # Rate limiting

    def count_requests_since(self, ip: str, since: datetime) -> int:
        """Count request units from an IP since a given time."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(units), 0) FROM requests WHERE ip = ? AND timestamp >= ?",
                (ip, since.strftime("%Y-%m-%d %H:%M:%S")),
            )
            return cursor.fetchone()[0]

    def record_request(self, request_id: str, ip: str, units: int = 1) -> None:
        """Record a request from an IP with specified units."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO requests (request_id, ip, units) VALUES (?, ?, ?)",
                (request_id, ip, units),
            )
            self._conn.commit()

    # Budget tracking

    def get_total_cost_since(self, since: datetime) -> float:
        """Get total cost since a given time."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "SELECT COALESCE(SUM(cost), 0) FROM costs WHERE timestamp >= ?",
                (since.strftime("%Y-%m-%d %H:%M:%S"),),
            )
            return cursor.fetchone()[0]

    def record_cost(self, request_id: str, cost: float) -> None:
        """Record cost for a request."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute(
                "INSERT INTO costs (request_id, cost) VALUES (?, ?)",
                (request_id, cost),
            )
            self._conn.commit()
