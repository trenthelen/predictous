"""Tests for Predictor class."""

from unittest.mock import Mock
from uuid import UUID

import pytest

from predictor import Predictor, PredictionRequest
from sandbox import SandboxErrorType, SandboxResult


@pytest.fixture
def mock_collector():
    return Mock()


@pytest.fixture
def mock_manager():
    return Mock()


@pytest.fixture
def predictor(mock_collector, mock_manager):
    return Predictor(mock_collector, mock_manager)


@pytest.fixture
def sample_request():
    return PredictionRequest(
        question="Will Bitcoin exceed $150,000 by end of January 2026?",
        resolution_criteria="Resolves YES if BTC price exceeds $150,000 USD.",
        resolution_date="2026-01-31",
        categories=["crypto", "bitcoin"],
    )


def make_success_result(prediction: float = 0.75, cost: float = 0.02) -> SandboxResult:
    return SandboxResult(
        status="success",
        output={
            "event_id": "test-event-id",
            "prediction": prediction,
            "reasoning": "Test reasoning",
        },
        cost=cost,
    )


def make_error_result(error: str = "Test error", error_type=None) -> SandboxResult:
    return SandboxResult(
        status="error",
        error=error,
        error_type=error_type,
        cost=0.0,
    )


class TestPredictChampion:
    def test_success(self, mock_collector, mock_manager, predictor, sample_request):
        mock_collector.get_miner_by_rank.return_value = (123, "hotkey123")
        mock_collector.get_agent.return_value = (
            UUID("550e8400-e29b-41d4-a716-446655440000"),
            "def agent_main(e): pass",
        )
        mock_manager.run_agent.return_value = make_success_result(0.75, 0.019)

        result = predictor.predict_champion(sample_request)

        assert result.status == "success"
        assert result.prediction == 0.75
        assert len(result.agent_predictions) == 1
        assert result.agent_predictions[0].miner_uid == 123
        assert result.agent_predictions[0].rank == 0
        assert result.agent_predictions[0].prediction == 0.75
        assert result.total_cost == 0.019

    def test_no_miners_available(self, mock_collector, predictor, sample_request):
        mock_collector.get_miner_by_rank.side_effect = IndexError("Rank 0 out of bounds")

        result = predictor.predict_champion(sample_request)

        assert result.status == "error"
        assert "No miners available" in result.error

    def test_agent_code_unavailable(
        self, mock_collector, mock_manager, predictor, sample_request
    ):
        mock_collector.get_miner_by_rank.return_value = (123, "hotkey123")
        mock_collector.get_agent.return_value = None

        result = predictor.predict_champion(sample_request)

        assert result.status == "error"
        assert len(result.failures) == 1
        assert result.failures[0].miner_uid == 123
        assert "No agent code available" in result.error

    def test_agent_execution_fails(
        self, mock_collector, mock_manager, predictor, sample_request
    ):
        mock_collector.get_miner_by_rank.return_value = (123, "hotkey123")
        mock_collector.get_agent.return_value = (
            UUID("550e8400-e29b-41d4-a716-446655440000"),
            "def agent_main(e): pass",
        )
        mock_manager.run_agent.return_value = make_error_result(
            "Timeout exceeded", SandboxErrorType.TIMEOUT
        )

        result = predictor.predict_champion(sample_request)

        assert result.status == "error"
        assert len(result.failures) == 1
        assert result.failures[0].error_type == SandboxErrorType.TIMEOUT


class TestPredictCouncil:
    def test_all_three_succeed(
        self, mock_collector, mock_manager, predictor, sample_request
    ):
        # Setup 3 miners
        mock_collector.get_miner_by_rank.side_effect = [
            (100, "key100"),
            (200, "key200"),
            (300, "key300"),
        ]
        mock_collector.get_agent.side_effect = [
            (UUID("550e8400-e29b-41d4-a716-446655440001"), "code1"),
            (UUID("550e8400-e29b-41d4-a716-446655440002"), "code2"),
            (UUID("550e8400-e29b-41d4-a716-446655440003"), "code3"),
        ]
        mock_manager.run_agent.side_effect = [
            make_success_result(0.60, 0.01),
            make_success_result(0.70, 0.02),
            make_success_result(0.80, 0.03),
        ]

        result = predictor.predict_council(sample_request)

        assert result.status == "success"
        assert result.prediction == pytest.approx(0.70)  # (0.6 + 0.7 + 0.8) / 3
        assert len(result.agent_predictions) == 3
        assert len(result.failures) == 0
        assert result.total_cost == pytest.approx(0.06)

    def test_two_succeed_one_fails(
        self, mock_collector, mock_manager, predictor, sample_request
    ):
        mock_collector.get_miner_by_rank.side_effect = [
            (100, "key100"),
            (200, "key200"),
            (300, "key300"),
        ]
        mock_collector.get_agent.side_effect = [
            (UUID("550e8400-e29b-41d4-a716-446655440001"), "code1"),
            (UUID("550e8400-e29b-41d4-a716-446655440002"), "code2"),
            (UUID("550e8400-e29b-41d4-a716-446655440003"), "code3"),
        ]
        mock_manager.run_agent.side_effect = [
            make_success_result(0.60, 0.01),
            make_error_result("Agent crashed", SandboxErrorType.AGENT_ERROR),
            make_success_result(0.80, 0.02),
        ]

        result = predictor.predict_council(sample_request)

        assert result.status == "success"
        # With parallel execution, we can't guarantee which agent fails
        # but we know 2 succeed and 1 fails
        assert len(result.agent_predictions) == 2
        assert len(result.failures) == 1
        # Prediction is average of the two that succeeded
        predictions = [p.prediction for p in result.agent_predictions]
        assert result.prediction == pytest.approx(sum(predictions) / len(predictions))
        assert result.total_cost == pytest.approx(0.03)

    def test_only_one_succeeds_fails(
        self, mock_collector, mock_manager, predictor, sample_request
    ):
        mock_collector.get_miner_by_rank.side_effect = [
            (100, "key100"),
            (200, "key200"),
            (300, "key300"),
        ]
        mock_collector.get_agent.side_effect = [
            (UUID("550e8400-e29b-41d4-a716-446655440001"), "code1"),
            None,  # No agent code
            (UUID("550e8400-e29b-41d4-a716-446655440003"), "code3"),
        ]
        mock_manager.run_agent.side_effect = [
            make_success_result(0.60, 0.01),
            make_error_result("Timeout", SandboxErrorType.TIMEOUT),
        ]

        result = predictor.predict_council(sample_request)

        assert result.status == "error"
        assert "Not enough successful predictions" in result.error
        assert len(result.agent_predictions) == 1
        assert len(result.failures) == 2

    def test_all_fail(self, mock_collector, mock_manager, predictor, sample_request):
        mock_collector.get_miner_by_rank.side_effect = [
            (100, "key100"),
            (200, "key200"),
            (300, "key300"),
        ]
        mock_collector.get_agent.side_effect = [None, None, None]

        result = predictor.predict_council(sample_request)

        assert result.status == "error"
        assert len(result.failures) == 3
        assert len(result.agent_predictions) == 0

    def test_not_enough_miners(self, mock_collector, predictor, sample_request):
        mock_collector.get_miner_by_rank.side_effect = [
            (100, "key100"),
            IndexError("Rank 1 out of bounds"),
        ]

        result = predictor.predict_council(sample_request)

        assert result.status == "error"
        assert "Not enough miners available" in result.error


class TestPredictSelected:
    def test_success(self, mock_collector, mock_manager, predictor, sample_request):
        mock_collector.get_miner_by_uid.return_value = (456, "hotkey456")
        mock_collector.get_rank_by_uid.return_value = 5
        mock_collector.get_agent.return_value = (
            UUID("550e8400-e29b-41d4-a716-446655440000"),
            "def agent_main(e): pass",
        )
        mock_manager.run_agent.return_value = make_success_result(0.65, 0.025)

        result = predictor.predict_selected(sample_request, miner_uid=456)

        assert result.status == "success"
        assert result.prediction == 0.65
        assert len(result.agent_predictions) == 1
        assert result.agent_predictions[0].miner_uid == 456
        assert result.agent_predictions[0].rank == 5
        assert result.total_cost == 0.025

    def test_invalid_uid(self, mock_collector, predictor, sample_request):
        mock_collector.get_miner_by_uid.return_value = None

        result = predictor.predict_selected(sample_request, miner_uid=999)

        assert result.status == "error"
        assert "not found in leaderboard" in result.error

    def test_agent_execution_fails(
        self, mock_collector, mock_manager, predictor, sample_request
    ):
        mock_collector.get_miner_by_uid.return_value = (456, "hotkey456")
        mock_collector.get_rank_by_uid.return_value = 5
        mock_collector.get_agent.return_value = (
            UUID("550e8400-e29b-41d4-a716-446655440000"),
            "def agent_main(e): pass",
        )
        mock_manager.run_agent.return_value = make_error_result(
            "Budget exceeded", SandboxErrorType.BUDGET_EXCEEDED
        )

        result = predictor.predict_selected(sample_request, miner_uid=456)

        assert result.status == "error"
        assert len(result.failures) == 1
        assert result.failures[0].error_type == SandboxErrorType.BUDGET_EXCEEDED


class TestBuildEventData:
    def test_includes_all_fields(self, predictor, sample_request):
        event_data = predictor._build_event_data(sample_request)

        assert "event_id" in event_data
        assert event_data["title"] == sample_request.question
        assert event_data["description"] == sample_request.resolution_criteria
        assert event_data["cutoff"] == sample_request.resolution_date
        assert event_data["event_metadata"]["topics"] == sample_request.categories

    def test_handles_optional_fields(self, predictor):
        request = PredictionRequest(
            question="Test question?",
            resolution_criteria="Test criteria",
        )

        event_data = predictor._build_event_data(request)

        assert event_data["cutoff"] is None
        assert event_data["event_metadata"]["topics"] == []
