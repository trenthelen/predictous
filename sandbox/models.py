"""Sandbox data models."""

from enum import Enum
from typing import Any, Callable, Optional

from pydantic import BaseModel, Field


class SandboxErrorType(str, Enum):
    """Types of sandbox execution errors."""

    TIMEOUT = "timeout"
    CONTAINER_ERROR = "container_error"
    INVALID_OUTPUT = "invalid_output"
    AGENT_ERROR = "agent_error"
    BUDGET_EXCEEDED = "budget_exceeded"
    QUEUE_FULL = "queue_full"


class SandboxResult(BaseModel):
    """Result of a sandbox execution."""

    status: str = Field(..., description="'success' or 'error'")
    output: Optional[dict[str, Any]] = Field(
        default=None, description="Agent output if successful"
    )
    logs: str = Field(default="", description="Container stdout logs")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    traceback: Optional[str] = Field(
        default=None, description="Python traceback if failed"
    )
    error_type: Optional[SandboxErrorType] = Field(
        default=None, description="Error category"
    )
    cost: float = Field(default=0.0, description="Total cost of this run in USD")


class AgentOutput(BaseModel):
    """Expected output from an agent."""

    event_id: str = Field(..., description="Event ID this prediction is for")
    prediction: float = Field(
        ..., description="Probability prediction (0.0 to 1.0)", ge=0, le=1
    )
    reasoning: Optional[str] = Field(None, description="Explanation of prediction")
