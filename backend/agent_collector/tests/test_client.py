from unittest.mock import Mock, patch
from uuid import UUID

import pytest
import requests

from agent_collector.client import NuminousClient, NuminousAPIError


class TestNuminousClientRetries:
    def test_retries_on_network_error(self):
        client = NuminousClient("https://api.example.com")

        with patch.object(client.session, "request") as mock_request:
            mock_request.side_effect = requests.RequestException("Connection failed")

            with pytest.raises(NuminousAPIError) as exc_info:
                client.get_leaderboard()

            assert "after 3 retries" in str(exc_info.value)
            assert mock_request.call_count == 3

    def test_retries_on_500_error(self):
        client = NuminousClient("https://api.example.com")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_request.return_value = mock_response

            with pytest.raises(NuminousAPIError) as exc_info:
                client.get_leaderboard()

            assert "Server error 500" in str(exc_info.value)
            assert mock_request.call_count == 3

    def test_no_retry_on_success(self):
        client = NuminousClient("https://api.example.com")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"results": []}
            mock_request.return_value = mock_response

            result = client.get_leaderboard()

            assert result == []
            assert mock_request.call_count == 1


class TestGetLeaderboard:
    def test_parses_response(self):
        client = NuminousClient("https://api.example.com")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "miner_uid": 1,
                        "miner_hotkey": "key1",
                        "weight": 0.9,
                        "events_scored": 50,
                        "avg_brier": 0.1,
                        "accuracy": 0.8,
                        "prediction_bias": 0.01,
                        "log_loss": 0.2,
                    }
                ],
                "limit": 250,
                "offset": 0,
            }
            mock_request.return_value = mock_response

            result = client.get_leaderboard()

            assert len(result) == 1
            assert result[0].miner_uid == 1
            assert result[0].miner_hotkey == "key1"


class TestGetMinerAgents:
    def test_parses_response(self):
        client = NuminousClient("https://api.example.com")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "results": [
                    {
                        "version_id": "550e8400-e29b-41d4-a716-446655440000",
                        "agent_name": "agent1",
                        "version_number": 1,
                        "created_at": "2024-01-15T10:00:00Z",
                        "activated_at": "2024-01-16T10:00:00Z",
                    }
                ],
                "limit": 500,
                "offset": 0,
            }
            mock_request.return_value = mock_response

            result = client.get_miner_agents(42, "hotkey123")

            assert len(result) == 1
            assert result[0].version_id == UUID("550e8400-e29b-41d4-a716-446655440000")
            assert result[0].agent_name == "agent1"


class TestGetAgentCode:
    def test_returns_code_on_success(self):
        client = NuminousClient("https://api.example.com")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "def agent_main(event): pass"
            mock_request.return_value = mock_response

            result = client.get_agent_code(
                42, "hotkey", UUID("550e8400-e29b-41d4-a716-446655440000")
            )

            assert result == "def agent_main(event): pass"

    def test_returns_none_on_400(self):
        client = NuminousClient("https://api.example.com")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_request.return_value = mock_response

            result = client.get_agent_code(
                42, "hotkey", UUID("550e8400-e29b-41d4-a716-446655440000")
            )

            assert result is None

    def test_returns_none_on_404(self):
        client = NuminousClient("https://api.example.com")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response

            result = client.get_agent_code(
                42, "hotkey", UUID("550e8400-e29b-41d4-a716-446655440000")
            )

            assert result is None

    def test_no_retry_on_4xx(self):
        client = NuminousClient("https://api.example.com")

        with patch.object(client.session, "request") as mock_request:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_request.return_value = mock_response

            client.get_agent_code(
                42, "hotkey", UUID("550e8400-e29b-41d4-a716-446655440000")
            )

            assert mock_request.call_count == 1
