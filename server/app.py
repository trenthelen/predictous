"""FastAPI server for Predictous API."""

import logging
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from agent_collector import AgentCollector, AgentStore
from db import Database
from predictor import Predictor, PredictionLogger
from predictor.models import PredictionRequest, PredictionResult
from sandbox import SandboxManager

load_dotenv()

# Configure logging for all modules
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

# Config from environment
RATE_LIMIT_REQUESTS_PER_DAY = int(os.environ.get("RATE_LIMIT_REQUESTS_PER_DAY", "20"))
DAILY_BUDGET_USD = float(os.environ.get("DAILY_BUDGET_USD", "5.0"))
GATEWAY_URL = os.environ.get("GATEWAY_URL", "")
DATABASE_PATH = os.environ.get("DATABASE_PATH", "./predictous.db")

# Global instances (initialized on startup)
db: Database | None = None
predictor: Predictor | None = None
sandbox_manager: SandboxManager | None = None


def validate_config() -> None:
    """Validate required configuration. Exits if invalid."""
    errors = []

    if not GATEWAY_URL:
        errors.append("GATEWAY_URL is required")

    if RATE_LIMIT_REQUESTS_PER_DAY <= 0:
        errors.append("RATE_LIMIT_REQUESTS_PER_DAY must be positive")

    if DAILY_BUDGET_USD <= 0:
        errors.append("DAILY_BUDGET_USD must be positive")

    if errors:
        for error in errors:
            logger.error(f"Config error: {error}")
        sys.exit(1)


def check_gateway_health() -> None:
    """Check that gateway is reachable. Exits if not."""
    health_url = f"{GATEWAY_URL}/health"
    try:
        response = httpx.get(health_url, timeout=10)
        response.raise_for_status()
        logger.info(f"Gateway health check passed: {GATEWAY_URL}")
    except httpx.RequestError as e:
        logger.error(f"Gateway unreachable at {health_url}: {e}")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        logger.error(f"Gateway health check failed: {e.response.status_code}")
        sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown."""
    global db, predictor, sandbox_manager

    logger.info("Starting up Predictous API")

    validate_config()
    check_gateway_health()

    db = Database(DATABASE_PATH)
    agent_store = AgentStore(db)
    collector = AgentCollector(store=agent_store)
    sandbox_manager = SandboxManager(gateway_url=GATEWAY_URL)
    prediction_logger = PredictionLogger(db)
    predictor = Predictor(collector, sandbox_manager, prediction_logger=prediction_logger)

    yield

    logger.info("Shutting down Predictous API")
    if sandbox_manager:
        sandbox_manager.close()
    if db:
        db.close()


app = FastAPI(title="Predictous API", lifespan=lifespan)


# Response models


class AgentInfo(BaseModel):
    """Agent information from leaderboard."""

    miner_uid: int = Field(..., description="Miner UID")
    rank: int = Field(..., description="Leaderboard rank (0-indexed)")
    weight: float = Field(..., description="Network weight")
    avg_brier: float = Field(..., description="Average Brier score")
    accuracy: float = Field(..., description="Prediction accuracy")


class AgentsResponse(BaseModel):
    """Response for /agents endpoint."""

    agents: list[AgentInfo]


class HealthResponse(BaseModel):
    """Response for /health endpoint."""

    status: str
    requests_used: int
    requests_limit: int
    requests_remaining: int


class PredictResponse(BaseModel):
    """Response for prediction endpoints."""

    request_id: str
    status: str
    prediction: Optional[float] = None
    agent_predictions: list = Field(default_factory=list)
    failures: list = Field(default_factory=list)
    total_cost: float
    error: Optional[str] = None


# Helpers


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(ip: str, units: int = 1) -> None:
    """Check if IP has enough quota for the request. Raises HTTPException if not."""
    since = datetime.now() - timedelta(days=1)
    used = db.count_requests_since(ip, since)
    if used + units > RATE_LIMIT_REQUESTS_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. This request needs {units} units but you only have {RATE_LIMIT_REQUESTS_PER_DAY - used} remaining.",
        )


def check_budget() -> None:
    """Check if daily budget is exceeded. Raises HTTPException if so."""
    since = datetime.now() - timedelta(days=1)
    used = db.get_total_cost_since(since)
    if used >= DAILY_BUDGET_USD:
        raise HTTPException(
            status_code=503,
            detail="Daily budget exceeded. Service temporarily unavailable.",
        )


MODE_UNITS = {"champion": 1, "council": 3, "selected": 1}


def run_prediction(
    request: Request,
    prediction_request: PredictionRequest,
    mode: str,
    miner_uid: int | None = None,
) -> PredictResponse:
    """Common logic for all prediction endpoints."""
    request_id = str(uuid4())
    ip = get_client_ip(request)
    units = MODE_UNITS[mode]

    # Check limits
    check_rate_limit(ip, units)
    check_budget()

    # Record request
    db.record_request(request_id, ip, units)

    # Run prediction
    if mode == "champion":
        result = predictor.predict_champion(prediction_request, request_id)
    elif mode == "council":
        result = predictor.predict_council(prediction_request, request_id)
    elif mode == "selected":
        result = predictor.predict_selected(prediction_request, miner_uid, request_id)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    # Record cost
    if result.total_cost > 0:
        db.record_cost(request_id, result.total_cost)

    return PredictResponse(
        request_id=request_id,
        status=result.status,
        prediction=result.prediction,
        agent_predictions=[p.model_dump() for p in result.agent_predictions],
        failures=[f.model_dump() for f in result.failures],
        total_cost=result.total_cost,
        error=result.error,
    )


# Endpoints


@app.get("/health", response_model=HealthResponse)
async def health(request: Request):
    """Health check with user's rate limit quota."""
    ip = get_client_ip(request)
    since = datetime.now() - timedelta(days=1)
    used = db.count_requests_since(ip, since)
    return HealthResponse(
        status="healthy",
        requests_used=used,
        requests_limit=RATE_LIMIT_REQUESTS_PER_DAY,
        requests_remaining=max(0, RATE_LIMIT_REQUESTS_PER_DAY - used),
    )


@app.get("/agents", response_model=AgentsResponse)
async def list_agents():
    """List available agents from leaderboard."""
    leaderboard = predictor._collector.get_leaderboard()
    agents = [
        AgentInfo(
            miner_uid=entry.miner_uid,
            rank=rank,
            weight=entry.weight,
            avg_brier=entry.avg_brier,
            accuracy=entry.accuracy,
        )
        for rank, entry in enumerate(leaderboard)
    ]
    return AgentsResponse(agents=agents)


@app.post("/predict/champion", response_model=PredictResponse)
async def predict_champion(request: Request, prediction_request: PredictionRequest):
    """Get prediction from top-ranked agent."""
    return run_prediction(request, prediction_request, "champion")


@app.post("/predict/council", response_model=PredictResponse)
async def predict_council(request: Request, prediction_request: PredictionRequest):
    """Get averaged prediction from top 3 agents."""
    return run_prediction(request, prediction_request, "council")


@app.post("/predict/selected/{miner_uid}", response_model=PredictResponse)
async def predict_selected(
    request: Request, miner_uid: int, prediction_request: PredictionRequest
):
    """Get prediction from a specific agent."""
    return run_prediction(request, prediction_request, "selected", miner_uid)


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("SERVER_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
