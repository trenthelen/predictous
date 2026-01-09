from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import UUID
import tempfile

import pytest

from agent_collector.collector import AgentCollector
from agent_collector.models import LeaderboardEntry, MinerAgentEntry


def make_leaderboard_entry(uid: int, hotkey: str) -> LeaderboardEntry:
    return LeaderboardEntry(
        miner_uid=uid,
        miner_hotkey=hotkey,
        weight=0.9,
        events_scored=100,
        avg_brier=0.1,
        accuracy=0.8,
        prediction_bias=0.01,
        log_loss=0.2,
    )


def make_agent_entry(
    version_id: str, version_number: int, activated: bool = True
) -> MinerAgentEntry:
    return MinerAgentEntry(
        version_id=UUID(version_id),
        agent_name="test_agent",
        version_number=version_number,
        created_at=datetime.now(timezone.utc),
        activated_at=datetime.now(timezone.utc) if activated else None,
    )


class TestCacheTTL:
    def test_cache_expiry_before_11pm(self):
        """Cache created at 9 AM expires at 11 PM same day."""
        mock_client = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            cached_at = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
            expiry = collector._cache_expiry_for(cached_at)

            assert expiry.day == 15
            assert expiry.hour == 23

    def test_cache_expiry_after_11pm(self):
        """Cache created at 11:30 PM expires at 11 PM next day."""
        mock_client = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            cached_at = datetime(2024, 1, 15, 23, 30, 0, tzinfo=timezone.utc)
            expiry = collector._cache_expiry_for(cached_at)

            assert expiry.day == 16
            assert expiry.hour == 23

    def test_cache_valid_before_expiry(self):
        """Cache is valid when now is before expiry."""
        mock_client = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            with patch("agent_collector.collector.datetime") as mock_dt:
                # Now is 10 AM on Jan 15, cache was at 9 AM on Jan 15
                # Expiry is 11 PM on Jan 15, so cache is valid
                mock_dt.now.return_value = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
                mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

                cached_at = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
                assert collector._is_cache_valid(cached_at) is True

    def test_cache_invalid_after_expiry(self):
        """Cache is invalid when now is after the 11 PM boundary."""
        mock_client = Mock()

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            with patch("agent_collector.collector.datetime") as mock_dt:
                # Now is 10 AM on Jan 16, cache was at 9 AM on Jan 15
                # Expiry was 11 PM on Jan 15, so cache is invalid
                mock_dt.now.return_value = datetime(2024, 1, 16, 10, 0, 0, tzinfo=timezone.utc)
                mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

                cached_at = datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc)
                assert collector._is_cache_valid(cached_at) is False


class TestLeaderboardCache:
    def test_fetches_from_api_on_cache_miss(self):
        mock_client = Mock()
        mock_client.get_leaderboard.return_value = [
            make_leaderboard_entry(1, "key1"),
            make_leaderboard_entry(2, "key2"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))
            result = collector.get_leaderboard()

            assert len(result) == 2
            mock_client.get_leaderboard.assert_called_once()

    def test_uses_cache_on_hit(self):
        mock_client = Mock()
        mock_client.get_leaderboard.return_value = [make_leaderboard_entry(1, "key1")]

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            collector.get_leaderboard()
            collector.get_leaderboard()

            mock_client.get_leaderboard.assert_called_once()


class TestGetMinerByRank:
    def test_returns_correct_miner(self):
        mock_client = Mock()
        mock_client.get_leaderboard.return_value = [
            make_leaderboard_entry(10, "key10"),
            make_leaderboard_entry(20, "key20"),
            make_leaderboard_entry(30, "key30"),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            uid, hotkey = collector.get_miner_by_rank(1)

            assert uid == 20
            assert hotkey == "key20"

    def test_raises_on_invalid_rank(self):
        mock_client = Mock()
        mock_client.get_leaderboard.return_value = [make_leaderboard_entry(1, "key1")]

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            with pytest.raises(IndexError):
                collector.get_miner_by_rank(5)


class TestGetMinerAgents:
    def test_filters_non_activated(self):
        mock_client = Mock()
        mock_client.get_miner_agents.return_value = [
            make_agent_entry("550e8400-e29b-41d4-a716-446655440001", 1, activated=True),
            make_agent_entry("550e8400-e29b-41d4-a716-446655440002", 2, activated=False),
            make_agent_entry("550e8400-e29b-41d4-a716-446655440003", 3, activated=True),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            result = collector.get_miner_agents(1, "key1")

            assert len(result) == 2
            assert all(a.activated_at is not None for a in result)

    def test_sorted_newest_first(self):
        mock_client = Mock()
        mock_client.get_miner_agents.return_value = [
            make_agent_entry("550e8400-e29b-41d4-a716-446655440001", 1),
            make_agent_entry("550e8400-e29b-41d4-a716-446655440003", 3),
            make_agent_entry("550e8400-e29b-41d4-a716-446655440002", 2),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            result = collector.get_miner_agents(1, "key1")

            assert result[0].version_number == 3
            assert result[1].version_number == 2
            assert result[2].version_number == 1


class TestGetAgentCode:
    def test_returns_from_filesystem_cache(self):
        mock_client = Mock()
        version_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            code_file = agents_dir / f"{version_id}.py"
            code_file.write_text("cached code")

            collector = AgentCollector(mock_client, agents_dir)

            result = collector.get_agent_code(1, "key1", version_id)

            assert result == "cached code"
            mock_client.get_agent_code.assert_not_called()

    def test_fetches_from_api_on_miss(self):
        mock_client = Mock()
        mock_client.get_agent_code.return_value = "api code"
        version_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            result = collector.get_agent_code(1, "key1", version_id)

            assert result == "api code"
            mock_client.get_agent_code.assert_called_once()

    def test_saves_to_filesystem_on_success(self):
        mock_client = Mock()
        mock_client.get_agent_code.return_value = "new code"
        version_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        with tempfile.TemporaryDirectory() as tmpdir:
            agents_dir = Path(tmpdir)
            collector = AgentCollector(mock_client, agents_dir)

            collector.get_agent_code(1, "key1", version_id)

            saved_file = agents_dir / f"{version_id}.py"
            assert saved_file.exists()
            assert saved_file.read_text() == "new code"

    def test_returns_none_on_4xx(self):
        mock_client = Mock()
        mock_client.get_agent_code.return_value = None
        version_id = UUID("550e8400-e29b-41d4-a716-446655440000")

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            result = collector.get_agent_code(1, "key1", version_id)

            assert result is None


class TestGetBestAgent:
    def test_returns_first_available(self):
        mock_client = Mock()
        mock_client.get_miner_agents.return_value = [
            make_agent_entry("550e8400-e29b-41d4-a716-446655440003", 3),
            make_agent_entry("550e8400-e29b-41d4-a716-446655440002", 2),
            make_agent_entry("550e8400-e29b-41d4-a716-446655440001", 1),
        ]
        mock_client.get_agent_code.return_value = "code"

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            result = collector.get_best_agent(1, "key1")

            assert result is not None
            version_id, code = result
            assert version_id == UUID("550e8400-e29b-41d4-a716-446655440003")
            assert code == "code"

    def test_falls_back_to_older_on_4xx(self):
        mock_client = Mock()
        mock_client.get_miner_agents.return_value = [
            make_agent_entry("550e8400-e29b-41d4-a716-446655440003", 3),
            make_agent_entry("550e8400-e29b-41d4-a716-446655440002", 2),
        ]
        mock_client.get_agent_code.side_effect = [None, "older code"]

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            result = collector.get_best_agent(1, "key1")

            assert result is not None
            version_id, code = result
            assert version_id == UUID("550e8400-e29b-41d4-a716-446655440002")
            assert code == "older code"

    def test_returns_none_when_no_agents(self):
        mock_client = Mock()
        mock_client.get_miner_agents.return_value = []

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            result = collector.get_best_agent(1, "key1")

            assert result is None

    def test_returns_none_when_all_unavailable(self):
        mock_client = Mock()
        mock_client.get_miner_agents.return_value = [
            make_agent_entry("550e8400-e29b-41d4-a716-446655440001", 1),
        ]
        mock_client.get_agent_code.return_value = None

        with tempfile.TemporaryDirectory() as tmpdir:
            collector = AgentCollector(mock_client, Path(tmpdir))

            result = collector.get_best_agent(1, "key1")

            assert result is None
