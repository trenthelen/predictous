"""
Predictor module for orchestrating prediction generation.

Combines AgentCollector (fetching agents) and SandboxManager (running agents)
to produce predictions in three modes: champion, council, and selected.

Usage:
    from predictor import Predictor, PredictionRequest
    from agent_collector import AgentCollector
    from sandbox import SandboxManager

    collector = AgentCollector()
    with SandboxManager(gateway_url="http://localhost:8000") as manager:
        predictor = Predictor(collector, manager)

        # Champion mode (top agent)
        result = predictor.predict_champion(PredictionRequest(
            question="Will X happen?",
            resolution_criteria="X is true if...",
        ))

        # Council mode (top 3 agents, averaged)
        result = predictor.predict_council(request)

        # Selected mode (specific miner)
        result = predictor.predict_selected(request, miner_uid=123)
"""

from .logger import PredictionLogger
from .models import AgentFailure, AgentPrediction, PredictionRequest, PredictionResult
from .predictor import Predictor

__all__ = [
    "Predictor",
    "PredictionLogger",
    "PredictionRequest",
    "PredictionResult",
    "AgentPrediction",
    "AgentFailure",
]
