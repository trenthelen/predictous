from pydantic import BaseModel
from datetime import datetime
from uuid import UUID


class LeaderboardEntry(BaseModel):
    miner_uid: int
    miner_hotkey: str
    weight: float
    events_scored: int
    avg_brier: float
    accuracy: float
    prediction_bias: float
    log_loss: float


class MinerAgentEntry(BaseModel):
    version_id: UUID
    agent_name: str
    version_number: int
    created_at: datetime
    activated_at: datetime | None
