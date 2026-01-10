"""Tests for sandbox models."""

import pytest
from pydantic import ValidationError

from sandbox.models import AgentOutput, SandboxErrorType, SandboxResult


class TestSandboxResult:
    def test_success_result(self):
        result = SandboxResult(
            status="success",
            output={"event_id": "123", "prediction": 0.75},
            logs="some logs",
        )
        assert result.status == "success"
        assert result.output["prediction"] == 0.75
        assert result.error is None

    def test_error_result(self):
        result = SandboxResult(
            status="error",
            error="Something went wrong",
            error_type=SandboxErrorType.AGENT_ERROR,
        )
        assert result.status == "error"
        assert result.error == "Something went wrong"
        assert result.error_type == SandboxErrorType.AGENT_ERROR


class TestAgentOutput:
    def test_valid_output(self):
        output = AgentOutput(
            event_id="123",
            prediction=0.75,
            reasoning="Based on analysis...",
        )
        assert output.event_id == "123"
        assert output.prediction == 0.75
        assert output.reasoning == "Based on analysis..."

    def test_prediction_bounds(self):
        # Valid at boundaries
        AgentOutput(event_id="1", prediction=0.0)
        AgentOutput(event_id="1", prediction=1.0)

        # Invalid below 0
        with pytest.raises(ValidationError):
            AgentOutput(event_id="1", prediction=-0.1)

        # Invalid above 1
        with pytest.raises(ValidationError):
            AgentOutput(event_id="1", prediction=1.1)

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            AgentOutput(prediction=0.5)  # Missing event_id

        with pytest.raises(ValidationError):
            AgentOutput(event_id="1")  # Missing prediction
