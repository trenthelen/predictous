"""Predictor - orchestrates agent fetching and execution for predictions."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from agent_collector import AgentCollector
from sandbox import SandboxManager, SandboxResult

from .models import AgentFailure, AgentPrediction, PredictionRequest, PredictionResult

if TYPE_CHECKING:
    from .logger import PredictionLogger

logger = logging.getLogger(__name__)


DEFAULT_TIMEOUT = 150+30  # seconds


class Predictor:
    """
    Orchestrates prediction generation using Numinous agents.

    Coordinates between AgentCollector (fetching agent code) and
    SandboxManager (running agents safely) to produce predictions.
    """

    def __init__(
        self,
        collector: AgentCollector,
        sandbox_manager: SandboxManager,
        timeout: int = DEFAULT_TIMEOUT,
        prediction_logger: "PredictionLogger | None" = None,
    ):
        """
        Initialize the predictor.

        Args:
            collector: AgentCollector for fetching agent code
            sandbox_manager: SandboxManager for running agents
            timeout: Maximum execution time per agent in seconds (default 150)
            prediction_logger: Optional logger for storing predictions
        """
        self._collector = collector
        self._manager = sandbox_manager
        self._timeout = timeout
        self._logger = prediction_logger

    def _build_event_data(self, request: PredictionRequest) -> dict:
        """Convert PredictionRequest to the event format agents expect."""
        return {
            "event_id": str(uuid4()),
            "title": request.question,
            "description": request.resolution_criteria,
            "cutoff": request.resolution_date,
            "event_metadata": {"topics": request.categories},
        }

    def _run_single_agent(
        self,
        uid: int,
        hotkey: str,
        rank: int,
        event_data: dict,
        request: PredictionRequest,
        request_id: str | None,
    ) -> tuple[AgentPrediction | None, AgentFailure | None]:
        """
        Run a single agent and return either a prediction or failure.

        Returns:
            Tuple of (AgentPrediction or None, AgentFailure or None)
        """
        # Fetch agent code
        agent_result = self._collector.get_agent(uid, hotkey)
        if agent_result is None:
            logger.warning(f"No agent code available for miner {uid}")
            return None, AgentFailure(
                miner_uid=uid,
                rank=rank,
                error=f"No agent code available for miner {uid}",
                error_type=None,
            )

        version_id, agent_code = agent_result

        # Run agent
        sandbox_result = self._manager.run_agent(
            agent_code, event_data, timeout=self._timeout
        )

        if sandbox_result.status == "success" and sandbox_result.output:
            prediction_value = sandbox_result.output["prediction"]
            reasoning = sandbox_result.output.get("reasoning")

            # Log successful prediction
            if self._logger and request_id:
                self._logger.log(
                    request_id=request_id,
                    version_id=version_id,
                    request=request,
                    prediction=prediction_value,
                    reasoning=reasoning,
                    cost=sandbox_result.cost,
                    status="success",
                )

            return AgentPrediction(
                miner_uid=uid,
                rank=rank,
                version_id=version_id,
                prediction=prediction_value,
                reasoning=reasoning,
                cost=sandbox_result.cost,
            ), None
        else:
            error_msg = sandbox_result.error or "Unknown error"

            # Log failed prediction
            if self._logger and request_id:
                self._logger.log(
                    request_id=request_id,
                    version_id=version_id,
                    request=request,
                    prediction=None,
                    reasoning=None,
                    cost=sandbox_result.cost,
                    status="error",
                    error=error_msg,
                )

            return None, AgentFailure(
                miner_uid=uid,
                rank=rank,
                error=error_msg,
                error_type=sandbox_result.error_type,
            )

    def predict_champion(
        self, request: PredictionRequest, request_id: str | None = None
    ) -> PredictionResult:
        """
        Get prediction from the top-ranked agent.

        Args:
            request: The prediction request
            request_id: Optional request ID for correlation

        Returns:
            PredictionResult with single agent's prediction
        """
        logger.info(f"Running champion prediction (request_id={request_id})")

        try:
            uid, hotkey = self._collector.get_miner_by_rank(0)
        except IndexError:
            return PredictionResult(
                status="error",
                error="No miners available in leaderboard",
                total_cost=0.0,
            )

        event_data = self._build_event_data(request)
        prediction, failure = self._run_single_agent(
            uid, hotkey, 0, event_data, request, request_id
        )

        if prediction:
            return PredictionResult(
                status="success",
                prediction=prediction.prediction,
                agent_predictions=[prediction],
                total_cost=prediction.cost,
            )
        else:
            return PredictionResult(
                status="error",
                failures=[failure] if failure else [],
                error=failure.error if failure else "Unknown error",
                total_cost=0.0,
            )

    def predict_council(
        self, request: PredictionRequest, request_id: str | None = None
    ) -> PredictionResult:
        """
        Get predictions from top 3 agents and average them.

        Runs agents in parallel. Requires at least 2 successful predictions.

        Args:
            request: The prediction request
            request_id: Optional request ID for correlation

        Returns:
            PredictionResult with averaged prediction from successful agents
        """
        logger.info(f"Running council prediction (top 3 agents, request_id={request_id})")

        # Fetch agent info for top 3 (sequential, fast)
        agents: list[tuple[int, int, str]] = []  # (rank, uid, hotkey)
        for rank in range(3):
            try:
                uid, hotkey = self._collector.get_miner_by_rank(rank)
                agents.append((rank, uid, hotkey))
            except IndexError:
                logger.warning(f"Not enough miners for rank {rank}")
                break

        if len(agents) < 2:
            return PredictionResult(
                status="error",
                error=f"Not enough miners available (found {len(agents)}, need at least 2)",
                total_cost=0.0,
            )

        event_data = self._build_event_data(request)
        predictions: list[AgentPrediction] = []
        failures: list[AgentFailure] = []

        # Run agents in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    self._run_single_agent, uid, hotkey, rank, event_data, request, request_id
                ): (rank, uid)
                for rank, uid, hotkey in agents
            }

            for future in as_completed(futures):
                rank, uid = futures[future]
                try:
                    prediction, failure = future.result()
                    if prediction:
                        predictions.append(prediction)
                    if failure:
                        failures.append(failure)
                except Exception as e:
                    logger.error(f"Agent {uid} raised exception: {e}")
                    failures.append(AgentFailure(
                        miner_uid=uid,
                        rank=rank,
                        error=str(e),
                        error_type=None,
                    ))

        total_cost = sum(p.cost for p in predictions)

        # Require at least 2 successes
        if len(predictions) < 2:
            return PredictionResult(
                status="error",
                agent_predictions=predictions,
                failures=failures,
                error=f"Not enough successful predictions ({len(predictions)}/3, need at least 2)",
                total_cost=total_cost,
            )

        # Average the predictions
        avg_prediction = sum(p.prediction for p in predictions) / len(predictions)

        return PredictionResult(
            status="success",
            prediction=avg_prediction,
            agent_predictions=predictions,
            failures=failures,
            total_cost=total_cost,
        )

    def predict_selected(
        self, request: PredictionRequest, miner_uid: int, request_id: str | None = None
    ) -> PredictionResult:
        """
        Get prediction from a specific agent by miner UID.

        Args:
            request: The prediction request
            miner_uid: The UID of the miner whose agent to run
            request_id: Optional request ID for correlation

        Returns:
            PredictionResult with the selected agent's prediction
        """
        logger.info(f"Running selected prediction for miner {miner_uid} (request_id={request_id})")

        # Look up miner by UID
        miner_result = self._collector.get_miner_by_uid(miner_uid)
        if miner_result is None:
            return PredictionResult(
                status="error",
                error=f"Miner with UID {miner_uid} not found in leaderboard",
                total_cost=0.0,
            )

        uid, hotkey = miner_result
        rank = self._collector.get_rank_by_uid(uid)
        if rank is None:
            rank = -1  # Should not happen, but handle gracefully

        event_data = self._build_event_data(request)
        prediction, failure = self._run_single_agent(
            uid, hotkey, rank, event_data, request, request_id
        )

        if prediction:
            return PredictionResult(
                status="success",
                prediction=prediction.prediction,
                agent_predictions=[prediction],
                total_cost=prediction.cost,
            )
        else:
            return PredictionResult(
                status="error",
                failures=[failure] if failure else [],
                error=failure.error if failure else "Unknown error",
                total_cost=0.0,
            )
