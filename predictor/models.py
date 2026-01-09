"""Predictor data models."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from sandbox.models import SandboxErrorType


class PredictionRequest(BaseModel):
    """Input for a prediction request."""

    question: str = Field(..., description="The binary question to predict")
    resolution_criteria: str = Field(..., description="How the outcome will be determined")
    resolution_date: Optional[str] = Field(
        default=None, description="Optional deadline for resolution"
    )
    categories: list[str] = Field(default_factory=list, description="Category tags (0-N)")


class AgentPrediction(BaseModel):
    """A single agent's prediction result."""

    miner_uid: int = Field(..., description="Miner UID that owns this agent")
    rank: int = Field(..., description="Leaderboard position (0-indexed)")
    version_id: UUID = Field(..., description="Agent version that was run")
    prediction: float = Field(..., ge=0, le=1, description="Probability prediction (0.0 to 1.0)")
    reasoning: Optional[str] = Field(default=None, description="Agent's explanation")
    cost: float = Field(..., description="Cost of this run in USD")


class AgentFailure(BaseModel):
    """Record of a failed agent execution."""

    miner_uid: int = Field(..., description="Miner UID of the failed agent")
    rank: int = Field(..., description="Leaderboard position (0-indexed)")
    error: str = Field(..., description="Error message")
    error_type: Optional[SandboxErrorType] = Field(
        default=None, description="Category of error"
    )


class PredictionResult(BaseModel):
    """Result of a prediction request."""

    status: str = Field(..., description="'success' or 'error'")
    prediction: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
        description="Aggregated prediction (average for council mode)",
    )
    agent_predictions: list[AgentPrediction] = Field(
        default_factory=list, description="Individual agent predictions"
    )
    failures: list[AgentFailure] = Field(
        default_factory=list, description="Failed agent executions"
    )
    total_cost: float = Field(default=0.0, description="Total cost in USD")
    error: Optional[str] = Field(default=None, description="Error message if status='error'")
