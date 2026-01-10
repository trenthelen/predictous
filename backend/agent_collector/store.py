"""Agent storage to database."""

import logging
from datetime import datetime
from uuid import UUID

from db import Database

from .models import MinerAgentEntry

logger = logging.getLogger(__name__)


class AgentStore:
    """Stores agent metadata to database."""

    def __init__(self, db: Database):
        self._db = db
        self._create_table()

    def _create_table(self) -> None:
        """Create agents table if it doesn't exist."""
        with self._db._lock:
            cursor = self._db._conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    version_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    miner_uid INTEGER NOT NULL,
                    miner_hotkey TEXT NOT NULL,
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self._db._conn.commit()
        logger.info("Agents table initialized")

    def record(
        self,
        agent: MinerAgentEntry,
        miner_uid: int,
        miner_hotkey: str,
    ) -> None:
        """Record an agent. Skips if already exists."""
        with self._db._lock:
            cursor = self._db._conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO agents
                (version_id, agent_name, version_number, created_at, miner_uid, miner_hotkey)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(agent.version_id),
                    agent.agent_name,
                    agent.version_number,
                    agent.created_at.isoformat(),
                    miner_uid,
                    miner_hotkey,
                ),
            )
            self._db._conn.commit()
        logger.debug(f"Recorded agent {agent.version_id}")
