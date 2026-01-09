"""Tests for AgentStore."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from db import Database
from agent_collector import AgentStore, MinerAgentEntry


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
def store(db):
    """Create an AgentStore for testing."""
    return AgentStore(db)


@pytest.fixture
def sample_agent():
    """Sample agent entry."""
    return MinerAgentEntry(
        version_id=uuid4(),
        agent_name="TestAgent",
        version_number=3,
        created_at=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        activated_at=datetime(2026, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
    )


class TestAgentStore:
    def test_record_agent(self, db, store, sample_agent):
        store.record(sample_agent, miner_uid=123, miner_hotkey="hotkey123")

        cursor = db._conn.cursor()
        cursor.execute(
            "SELECT * FROM agents WHERE version_id = ?", (str(sample_agent.version_id),)
        )
        row = cursor.fetchone()

        assert row is not None
        assert row["version_id"] == str(sample_agent.version_id)
        assert row["agent_name"] == "TestAgent"
        assert row["version_number"] == 3
        assert row["miner_uid"] == 123
        assert row["miner_hotkey"] == "hotkey123"
        assert row["fetched_at"] is not None

    def test_record_duplicate_agent_ignored(self, db, store, sample_agent):
        """Recording same agent twice should not create duplicate."""
        store.record(sample_agent, miner_uid=123, miner_hotkey="hotkey123")
        store.record(sample_agent, miner_uid=123, miner_hotkey="hotkey123")

        cursor = db._conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM agents WHERE version_id = ?",
            (str(sample_agent.version_id),),
        )
        count = cursor.fetchone()[0]
        assert count == 1

    def test_record_multiple_agents(self, db, store):
        """Record multiple different agents."""
        for i in range(3):
            agent = MinerAgentEntry(
                version_id=uuid4(),
                agent_name=f"Agent{i}",
                version_number=i,
                created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
                activated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
            store.record(agent, miner_uid=100 + i, miner_hotkey=f"hotkey{i}")

        cursor = db._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agents")
        count = cursor.fetchone()[0]
        assert count == 3

    def test_record_agents_same_miner(self, db, store):
        """Record multiple agent versions from same miner."""
        miner_uid = 123
        miner_hotkey = "hotkey123"

        for i in range(3):
            agent = MinerAgentEntry(
                version_id=uuid4(),
                agent_name="MyAgent",
                version_number=i + 1,
                created_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
                activated_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
            )
            store.record(agent, miner_uid=miner_uid, miner_hotkey=miner_hotkey)

        cursor = db._conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM agents WHERE miner_uid = ?", (miner_uid,))
        count = cursor.fetchone()[0]
        assert count == 3
