import logging
import time
from uuid import UUID

import requests

from .models import LeaderboardEntry, MinerAgentEntry


logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]
LEADERBOARD_LIMIT = 250


class NuminousAPIError(Exception):
    """Raised when API request fails after retries."""
    pass


class NuminousClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """Make HTTP request with retry logic for network errors and 5XX."""
        url = f"{self.base_url}{path}"

        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"API request: {method} {url} (attempt {attempt + 1})")
                response = self.session.request(method, url, **kwargs)

                if response.status_code >= 500:
                    logger.debug(f"Server error {response.status_code}, will retry")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(BACKOFF_SECONDS[attempt])
                        continue
                    raise NuminousAPIError(f"Server error {response.status_code} after {MAX_RETRIES} retries")

                return response

            except requests.RequestException as e:
                logger.debug(f"Request failed: {e}, will retry")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(BACKOFF_SECONDS[attempt])
                    continue
                raise NuminousAPIError(f"Request failed after {MAX_RETRIES} retries: {e}") from e

        raise NuminousAPIError("Unexpected retry loop exit")

    def get_leaderboard(self) -> list[LeaderboardEntry]:
        """Fetch the full leaderboard (max 250 miners)."""
        response = self._request("GET", "/v1/leaderboard", params={"limit": LEADERBOARD_LIMIT})
        response.raise_for_status()
        data = response.json()
        return [LeaderboardEntry(**entry) for entry in data["results"]]

    def get_miner_agents(self, miner_uid: int, miner_hotkey: str) -> list[MinerAgentEntry]:
        """Fetch all agent versions for a miner."""
        response = self._request(
            "GET",
            f"/v1/miners/{miner_uid}/{miner_hotkey}/agents",
            params={"limit": 500},
        )
        response.raise_for_status()
        data = response.json()
        return [MinerAgentEntry(**entry) for entry in data["results"]]

    def get_agent_code(self, miner_uid: int, miner_hotkey: str, version_id: UUID) -> str | None:
        """Fetch agent code. Returns None on 4XX (code not available)."""
        response = self._request(
            "GET",
            f"/v1/miners/{miner_uid}/{miner_hotkey}/agents/{version_id}/code",
        )

        if 400 <= response.status_code < 500:
            logger.debug(f"Agent code not available: {response.status_code}")
            return None

        response.raise_for_status()
        return response.text
