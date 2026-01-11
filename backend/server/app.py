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
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent_collector import AgentCollector, AgentStore
from db import Database
from predictor import Predictor, PredictionLogger
from predictor.models import PredictionRequest, PredictionResult
from sandbox import SandboxManager
from sandbox.models import SandboxErrorType
from server.jobs import jobs, JobStatus

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
MAX_CONCURRENT_REQUESTS_PER_IP = 2
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
    health_url = f"{GATEWAY_URL}/api/health"
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

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


class ErrorResponse(BaseModel):
    """Error response returned by API."""

    message: str
    error_code: str


class JobResponse(BaseModel):
    """Response for async prediction submission."""

    job_id: str


class JobStatusResponse(BaseModel):
    """Response for job status check."""

    job_id: str
    status: str
    result: Optional[PredictResponse] = None
    error: Optional[str] = None


class HistoryItem(BaseModel):
    """Single item in prediction history."""

    request_id: str
    question: str
    prediction: Optional[float] = None
    timestamp: str


class HistoryResponse(BaseModel):
    """Response for /history endpoint."""

    items: list[HistoryItem]


class AgentPredictionDetail(BaseModel):
    """Agent prediction in detail view."""

    prediction: Optional[float] = None
    reasoning: Optional[str] = None
    cost: float
    status: str
    error: Optional[str] = None


class PredictionDetailResponse(BaseModel):
    """Response for prediction detail endpoint."""

    request_id: str
    question: str
    resolution_criteria: str
    resolution_date: Optional[str] = None
    categories: Optional[str] = None
    prediction: Optional[float] = None
    agent_predictions: list[AgentPredictionDetail]
    timestamp: str


# Common error responses for predict endpoints
PREDICT_ERROR_RESPONSES = {
    429: {
        "model": ErrorResponse,
        "description": "Rate limit exceeded (per-IP daily quota)",
    },
    503: {
        "model": ErrorResponse,
        "description": "Service unavailable (daily budget exceeded or queue full)",
    },
}


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
            detail={
                "message": f"Rate limit exceeded. This request needs {units} units but you only have {RATE_LIMIT_REQUESTS_PER_DAY - used} remaining.",
                "error_code": "rate_limit_exceeded",
            },
        )


def check_budget() -> None:
    """Check if daily budget is exceeded. Raises HTTPException if so."""
    since = datetime.now() - timedelta(days=1)
    used = db.get_total_cost_since(since)
    if used >= DAILY_BUDGET_USD:
        raise HTTPException(
            status_code=503,
            detail={
                "message": "Daily budget exceeded. Service temporarily unavailable.",
                "error_code": "budget_exceeded",
            },
        )


def check_concurrent_limit(ip: str) -> None:
    """Check if IP has too many active requests. Raises HTTPException if so."""
    active = jobs.count_active_for_ip(ip)
    if active >= MAX_CONCURRENT_REQUESTS_PER_IP:
        raise HTTPException(
            status_code=429,
            detail={
                "message": "You already have a prediction in progress. Please wait for it to complete.",
                "error_code": "request_in_progress",
            },
        )


MODE_UNITS = {"champion": 1, "council": 3, "selected": 1}


def _execute_prediction(
    request_id: str,
    prediction_request: PredictionRequest,
    mode: str,
    miner_uid: int | None = None,
) -> PredictResponse:
    """Execute prediction synchronously (runs in background thread)."""
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


def start_prediction_job(
    request: Request,
    prediction_request: PredictionRequest,
    mode: str,
    miner_uid: int | None = None,
) -> JobResponse:
    """Start prediction as background job, return job_id immediately."""
    request_id = str(uuid4())
    ip = get_client_ip(request)
    user_id = request.headers.get("X-User-Id")
    units = MODE_UNITS[mode]

    # Check limits before starting job
    check_concurrent_limit(ip)
    check_rate_limit(ip, units)
    check_budget()

    # Record request
    db.record_request(request_id, ip, units, user_id)

    # Create job and run in background
    job = jobs.create(ip=ip)
    jobs.run_in_background(
        job,
        _execute_prediction,
        request_id,
        prediction_request,
        mode,
        miner_uid,
        ip=ip,
    )

    return JobResponse(job_id=job.id)


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


@app.post("/predict/champion", response_model=JobResponse, responses=PREDICT_ERROR_RESPONSES)
async def predict_champion(request: Request, prediction_request: PredictionRequest):
    """Start prediction from top-ranked agent. Returns job_id to poll for result."""
    return start_prediction_job(request, prediction_request, "champion")


@app.post("/predict/council", response_model=JobResponse, responses=PREDICT_ERROR_RESPONSES)
async def predict_council(request: Request, prediction_request: PredictionRequest):
    """Start averaged prediction from top 3 agents. Returns job_id to poll for result."""
    return start_prediction_job(request, prediction_request, "council")


@app.post("/predict/selected/{miner_uid}", response_model=JobResponse, responses=PREDICT_ERROR_RESPONSES)
async def predict_selected(
    request: Request, miner_uid: int, prediction_request: PredictionRequest
):
    """Start prediction from a specific agent. Returns job_id to poll for result."""
    return start_prediction_job(request, prediction_request, "selected", miner_uid)


@app.get("/predict/status/{job_id}", response_model=JobStatusResponse)
async def predict_status(job_id: str):
    """Check status of a prediction job."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        result=job.result if job.status == JobStatus.COMPLETED else None,
        error=job.error if job.status == JobStatus.FAILED else None,
    )


@app.get("/history", response_model=HistoryResponse)
async def get_history(request: Request, limit: int = 50, offset: int = 0):
    """Get prediction history for the current user."""
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return HistoryResponse(items=[])
    items = db.get_history(user_id, limit, offset)
    return HistoryResponse(items=[HistoryItem(**item) for item in items])


@app.get("/predictions/{request_id}", response_model=PredictionDetailResponse)
async def get_prediction_detail(request_id: str):
    """Get full prediction details by request_id. Public endpoint for sharing."""
    detail = db.get_prediction_detail(request_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return PredictionDetailResponse(
        request_id=detail["request_id"],
        question=detail["question"],
        resolution_criteria=detail["resolution_criteria"],
        resolution_date=detail["resolution_date"],
        categories=detail["categories"],
        prediction=detail["prediction"],
        agent_predictions=[
            AgentPredictionDetail(**p) for p in detail["agent_predictions"]
        ],
        timestamp=detail["timestamp"],
    )


if __name__ == "__main__":
    import uvicorn

    host = os.environ.get("SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("SERVER_PORT", "8080"))
    uvicorn.run(app, host=host, port=port)
