import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from config import NUMINOUS_API_BASE_URL
from .client import NuminousClient
from .models import LeaderboardEntry, MinerAgentEntry

if TYPE_CHECKING:
    from .store import AgentStore

logger = logging.getLogger(__name__)


class AgentCollector:
    def __init__(
        self,
        agents_dir: Path = Path("./agents"),
        store: "AgentStore | None" = None,
    ):
        self.client = NuminousClient(NUMINOUS_API_BASE_URL)
        self.agents_dir = agents_dir
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        self._store = store

        self._leaderboard_cache: tuple[list[LeaderboardEntry], datetime] | None = None
        self._agents_cache: dict[tuple[int, str], tuple[list[MinerAgentEntry], datetime]] = {}
        self._unavailable_codes: dict[UUID, datetime] = {}

    def _cache_expiry_for(self, cached_at: datetime) -> datetime:
        """Calculate when a cache entry expires (first 11 PM UTC after cached_at)."""
        if cached_at.tzinfo is None:
            cached_at = cached_at.replace(tzinfo=timezone.utc)

        same_day_11pm = cached_at.replace(hour=23, minute=0, second=0, microsecond=0)

        if cached_at >= same_day_11pm:
            return same_day_11pm + timedelta(days=1)
        return same_day_11pm

    def _is_cache_valid(self, cached_at: datetime) -> bool:
        """Check if cache is still valid (hasn't crossed 11 PM UTC boundary)."""
        now = datetime.now(timezone.utc)
        expiry = self._cache_expiry_for(cached_at)
        return now < expiry

    def _agent_file_path(self, version_id: UUID) -> Path:
        return self.agents_dir / f"{version_id}.py"

    def get_leaderboard(self) -> list[LeaderboardEntry]:
        """Get leaderboard, using cache if valid."""
        if self._leaderboard_cache:
            entries, cached_at = self._leaderboard_cache
            if self._is_cache_valid(cached_at):
                logger.info("Leaderboard cache hit")
                return entries

        logger.info("Fetching leaderboard from API")
        entries = self.client.get_leaderboard()
        self._leaderboard_cache = (entries, datetime.now(timezone.utc))
        return entries

    def get_miner_by_rank(self, rank: int) -> tuple[int, str]:
        """Get miner (uid, hotkey) by rank (0-indexed)."""
        leaderboard = self.get_leaderboard()
        if rank < 0 or rank >= len(leaderboard):
            raise IndexError(f"Rank {rank} out of bounds (0-{len(leaderboard) - 1})")
        entry = leaderboard[rank]
        return entry.miner_uid, entry.miner_hotkey

    def get_miner_by_uid(self, uid: int) -> tuple[int, str] | None:
        """Get miner (uid, hotkey) by UID. Returns None if not found."""
        leaderboard = self.get_leaderboard()
        for entry in leaderboard:
            if entry.miner_uid == uid:
                return entry.miner_uid, entry.miner_hotkey
        return None

    def get_rank_by_uid(self, uid: int) -> int | None:
        """Get leaderboard rank (0-indexed) for a miner UID. Returns None if not found."""
        leaderboard = self.get_leaderboard()
        for rank, entry in enumerate(leaderboard):
            if entry.miner_uid == uid:
                return rank
        return None

    def get_miner_agents(self, miner_uid: int, miner_hotkey: str) -> list[MinerAgentEntry]:
        """Get visible agents for a miner, sorted newest first. Uses cache if valid."""
        cache_key = (miner_uid, miner_hotkey)

        if cache_key in self._agents_cache:
            agents, cached_at = self._agents_cache[cache_key]
            if self._is_cache_valid(cached_at):
                logger.info(f"Agents cache hit for miner {miner_uid}")
                return agents

        logger.info(f"Fetching agents for miner {miner_uid} from API")
        all_agents = self.client.get_miner_agents(miner_uid, miner_hotkey)

        visible = [a for a in all_agents if a.activated_at is not None]
        visible.sort(key=lambda a: a.version_number, reverse=True)

        self._agents_cache[cache_key] = (visible, datetime.now(timezone.utc))
        return visible

    def get_agent_code(self, miner_uid: int, miner_hotkey: str, version_id: UUID) -> str | None:
        """Get agent code by version_id. Checks filesystem cache first."""
        file_path = self._agent_file_path(version_id)
        if file_path.exists():
            logger.info(f"Agent code cache hit (filesystem): {version_id}")
            return file_path.read_text()

        if version_id in self._unavailable_codes:
            cached_at = self._unavailable_codes[version_id]
            if self._is_cache_valid(cached_at):
                logger.debug(f"Agent code known unavailable (cached): {version_id}")
                return None

        logger.info(f"Fetching agent code from API: {version_id}")
        code = self.client.get_agent_code(miner_uid, miner_hotkey, version_id)

        if code is None:
            self._unavailable_codes[version_id] = datetime.now(timezone.utc)
            return None

        if code.strip():
            file_path.write_text(code)
            logger.info(f"Agent code saved to {file_path}")

        return code

    def get_agent(self, miner_uid: int, miner_hotkey: str) -> tuple[UUID, str] | None:
        """Get agent code for a miner.

        Tries agents from newest to oldest, returns first one with available code.
        """
        agents = self.get_miner_agents(miner_uid, miner_hotkey)

        if not agents:
            logger.error(f"Miner {miner_uid} has no visible agents")
            return None

        for agent in agents:
            code = self.get_agent_code(miner_uid, miner_hotkey, agent.version_id)
            if code is not None and code.strip():
                # Record agent metadata to database
                if self._store:
                    self._store.record(agent, miner_uid, miner_hotkey)
                return agent.version_id, code

        logger.error(f"No available agent code for miner {miner_uid}")
        return None
