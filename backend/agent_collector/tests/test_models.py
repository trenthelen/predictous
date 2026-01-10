from datetime import datetime
from uuid import UUID

import pytest

from agent_collector.models import LeaderboardEntry, MinerAgentEntry


class TestLeaderboardEntry:
    def test_parse_valid_entry(self):
        data = {
            "miner_uid": 42,
            "miner_hotkey": "abc123",
            "weight": 0.95,
            "events_scored": 100,
            "avg_brier": 0.15,
            "accuracy": 0.85,
            "prediction_bias": 0.02,
            "log_loss": 0.3,
        }
        entry = LeaderboardEntry(**data)

        assert entry.miner_uid == 42
        assert entry.miner_hotkey == "abc123"
        assert entry.weight == 0.95
        assert entry.events_scored == 100

    def test_parse_float_values(self):
        data = {
            "miner_uid": 1,
            "miner_hotkey": "key",
            "weight": 0.0,
            "events_scored": 0,
            "avg_brier": 0.0,
            "accuracy": 1.0,
            "prediction_bias": -0.5,
            "log_loss": 0.0,
        }
        entry = LeaderboardEntry(**data)
        assert entry.accuracy == 1.0
        assert entry.prediction_bias == -0.5


class TestMinerAgentEntry:
    def test_parse_with_activated_at(self):
        data = {
            "version_id": "550e8400-e29b-41d4-a716-446655440000",
            "agent_name": "my_agent",
            "version_number": 3,
            "created_at": "2024-01-15T10:30:00Z",
            "activated_at": "2024-01-16T12:00:00Z",
        }
        entry = MinerAgentEntry(**data)

        assert entry.version_id == UUID("550e8400-e29b-41d4-a716-446655440000")
        assert entry.agent_name == "my_agent"
        assert entry.version_number == 3
        assert entry.activated_at is not None

    def test_parse_with_null_activated_at(self):
        data = {
            "version_id": "550e8400-e29b-41d4-a716-446655440000",
            "agent_name": "my_agent",
            "version_number": 1,
            "created_at": "2024-01-15T10:30:00Z",
            "activated_at": None,
        }
        entry = MinerAgentEntry(**data)

        assert entry.activated_at is None

    def test_parse_without_activated_at_field(self):
        data = {
            "version_id": "550e8400-e29b-41d4-a716-446655440000",
            "agent_name": "my_agent",
            "version_number": 1,
            "created_at": "2024-01-15T10:30:00Z",
        }
        # Should fail since activated_at is required (even if nullable)
        with pytest.raises(Exception):
            MinerAgentEntry(**data)
