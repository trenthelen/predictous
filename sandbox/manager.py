"""
SandboxManager - runs Python agents in isolated Docker containers.

This is a simplified version of the numinous validator sandbox,
without bittensor wallet signing. Agents access the gateway through
a cost-tracking proxy that enforces budget limits.
"""

import json
import logging
import shutil
import time
import uuid
from pathlib import Path
from typing import Optional

import docker
import docker.errors
import requests.exceptions

from sandbox.cost_proxy import CostTrackingProxy
from sandbox.models import AgentOutput, SandboxErrorType, SandboxResult
from sandbox.utils.docker import build_image, image_exists
from sandbox.utils.temp import cleanup_temp_dir, create_temp_dir

logger = logging.getLogger(__name__)

# Constants
SANDBOX_IMAGE_NAME = "predictous-sandbox"
SANDBOX_NETWORK_NAME = "predictous-sandbox-network"

# Resource limits (same as numinous)
MEMORY_LIMIT = "768m"
CPU_QUOTA = 50000  # 0.5 CPU
CPU_PERIOD = 100000
DEFAULT_TIMEOUT = 120
DEFAULT_CHUTES_BUDGET = 0.02  # $0.02 for LLM calls
DEFAULT_DESEARCH_BUDGET = 0.10  # $0.10 for search/crawl
DEFAULT_PROXY_PORT = 8888


class SandboxManager:
    """
    Manages Docker sandbox execution for agents.

    Usage:
        with SandboxManager(gateway_url="http://localhost:8000") as manager:
            result = manager.run_agent(
                agent_code=open("my_agent.py").read(),
                event_data={"event_id": "123", "title": "Will X happen?"},
            )
    """

    def __init__(
        self,
        gateway_url: str,
        *,
        chutes_budget: float = DEFAULT_CHUTES_BUDGET,
        desearch_budget: float = DEFAULT_DESEARCH_BUDGET,
        proxy_port: int = DEFAULT_PROXY_PORT,
        force_rebuild: bool = False,
        temp_base_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize the sandbox manager.

        Args:
            gateway_url: URL of the gateway API (e.g., "http://localhost:8000")
            chutes_budget: Maximum cost for LLM calls per run in USD (default $0.02)
            desearch_budget: Maximum cost for search/crawl per run in USD (default $0.10)
            proxy_port: Port for the cost-tracking proxy (default 8888)
            force_rebuild: Force rebuild of Docker images
            temp_base_dir: Base directory for temporary sandbox files
        """
        self.gateway_url = gateway_url
        self.chutes_budget = chutes_budget
        self.desearch_budget = desearch_budget
        self.proxy_port = proxy_port
        self.temp_base_dir = temp_base_dir

        # Start cost-tracking proxy
        self.cost_proxy = CostTrackingProxy(
            gateway_url=gateway_url,
            chutes_budget=chutes_budget,
            desearch_budget=desearch_budget,
            port=proxy_port,
        )
        self.cost_proxy.start_background()
        logger.info(
            f"Cost-tracking proxy started on port {proxy_port}, "
            f"budgets: chutes=${chutes_budget}, desearch=${desearch_budget}"
        )

        # Connect to Docker
        try:
            self.docker_client = docker.from_env()
            logger.info("Connected to Docker daemon")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            raise RuntimeError(f"Failed to connect to Docker: {e}") from e

        # Clean up old containers
        self._cleanup_old_containers()

        # Build Docker image
        self._build_image(force_rebuild)

        # Create network for sandbox containers
        self._create_network()

        logger.info(f"SandboxManager initialized with gateway: {gateway_url}")

    def __enter__(self) -> "SandboxManager":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """Clean up resources."""
        self._cleanup_old_containers()
        if self.cost_proxy:
            self.cost_proxy.stop()
        logger.info("SandboxManager closed")

    def _cleanup_old_containers(self) -> None:
        """Remove any leftover sandbox containers."""
        for container in self.docker_client.containers.list(all=True):
            if container.name.startswith("sandbox_predictous_"):
                try:
                    logger.debug(f"Removing old container: {container.name}")
                    container.stop(timeout=3)
                    container.remove(force=True)
                except Exception as e:
                    logger.warning(f"Could not clean up container {container.name}: {e}")

    def _build_image(self, force_rebuild: bool) -> None:
        """Build the sandbox Docker image if needed."""
        sandbox_dir = Path(__file__).parent

        if force_rebuild or not image_exists(self.docker_client, SANDBOX_IMAGE_NAME):
            build_image(self.docker_client, sandbox_dir, SANDBOX_IMAGE_NAME)
        else:
            logger.info(f"Docker image {SANDBOX_IMAGE_NAME} already exists")

    def _create_network(self) -> None:
        """Create an isolated Docker network for sandboxes."""
        try:
            self.docker_client.networks.get(SANDBOX_NETWORK_NAME)
            logger.debug(f"Network {SANDBOX_NETWORK_NAME} already exists")
        except docker.errors.NotFound:
            # Create network - using bridge mode to allow gateway access
            self.docker_client.networks.create(
                SANDBOX_NETWORK_NAME,
                driver="bridge",
            )
            logger.info(f"Created network: {SANDBOX_NETWORK_NAME}")

    def run_agent(
        self,
        agent_code: str,
        event_data: dict,
        *,
        run_id: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        env_vars: Optional[dict[str, str]] = None,
    ) -> SandboxResult:
        """
        Run an agent in an isolated Docker container.

        Args:
            agent_code: Python source code containing agent_main() function
            event_data: Event data to pass to the agent (must include event_id)
            run_id: Unique identifier for this run (generated if not provided)
            timeout: Maximum execution time in seconds
            env_vars: Additional environment variables for the container

        Returns:
            SandboxResult with status, output, logs, and any errors
        """
        if not agent_code:
            return SandboxResult(
                status="error",
                error="agent_code cannot be empty",
                error_type=SandboxErrorType.INVALID_OUTPUT,
            )

        if not isinstance(event_data, dict):
            return SandboxResult(
                status="error",
                error="event_data must be a dictionary",
                error_type=SandboxErrorType.INVALID_OUTPUT,
            )

        run_id = run_id or str(uuid.uuid4())
        temp_dir = create_temp_dir(prefix="sandbox_predictous_", base_dir=self.temp_base_dir)
        sandbox_id = f"sandbox_predictous_{temp_dir.name}"

        logger.debug(f"Created sandbox {sandbox_id} for run {run_id}")

        try:
            # Write agent code and input data
            (temp_dir / "agent.py").write_text(agent_code)
            (temp_dir / "input.json").write_text(json.dumps(event_data, indent=2))

            # Copy agent_runner.py to temp directory
            runner_src = Path(__file__).parent / "agent_runner.py"
            shutil.copy2(runner_src, temp_dir / "agent_runner.py")

            # Run container
            result = self._run_container(
                sandbox_id=sandbox_id,
                temp_dir=temp_dir,
                run_id=run_id,
                timeout=timeout,
                env_vars=env_vars or {},
            )

            # Get cost from proxy and add to result
            result.cost = self.cost_proxy.get_cost(run_id)
            logger.info(f"Run {run_id} completed, cost=${result.cost:.6f}")

            return result

        except Exception as e:
            logger.error(f"Sandbox {sandbox_id} failed: {e}")
            return SandboxResult(
                status="error",
                error=str(e),
                error_type=SandboxErrorType.CONTAINER_ERROR,
                cost=self.cost_proxy.get_cost(run_id),
            )
        finally:
            cleanup_temp_dir(temp_dir)
            # Clear cost tracking for this run
            self.cost_proxy.clear_run(run_id)

    def _run_container(
        self,
        sandbox_id: str,
        temp_dir: Path,
        run_id: str,
        timeout: int,
        env_vars: dict[str, str],
    ) -> SandboxResult:
        """Run the Docker container and collect results."""
        container = None
        result = SandboxResult(status="success", logs="")

        start_time = time.monotonic()

        try:
            container = self.docker_client.containers.run(
                image=SANDBOX_IMAGE_NAME,
                command="python /sandbox/agent_runner.py",
                name=sandbox_id,
                volumes={str(temp_dir): {"bind": "/sandbox", "mode": "rw"}},
                environment={
                    # Point to cost-tracking proxy, not gateway directly
                    "GATEWAY_URL": self.cost_proxy.proxy_url,
                    "SANDBOX_PROXY_URL": self.cost_proxy.proxy_url,  # Numinous agent compatibility
                    "RUN_ID": run_id,
                    "PYTHONUNBUFFERED": "1",
                    "PYTHONDONTWRITEBYTECODE": "1",
                    **env_vars,
                },
                network_mode="bridge",  # Allow network access to gateway
                extra_hosts={"host.docker.internal": "host-gateway"},  # Linux support
                mem_limit=MEMORY_LIMIT,
                memswap_limit=MEMORY_LIMIT,  # No swap
                cpu_quota=CPU_QUOTA,
                cpu_period=CPU_PERIOD,
                remove=False,
                detach=True,
            )

            container_start_time = time.monotonic()
            startup_duration = container_start_time - start_time
            logger.info(f"Container {sandbox_id} started in {startup_duration:.2f}s")

            # Wait for container to finish
            try:
                container.wait(timeout=timeout)
            except Exception as wait_error:
                # Any wait error (timeout, connection error, etc.) means we need to kill
                if "timed out" in str(wait_error).lower() or "timeout" in str(wait_error).lower():
                    try:
                        container.kill()
                    except Exception:
                        pass
                    elapsed = time.monotonic() - start_time
                    result.logs = self._get_container_logs(container)
                    result.status = "error"
                    result.error = f"Timeout exceeded ({timeout}s, actual elapsed: {elapsed:.1f}s)"
                    result.error_type = SandboxErrorType.TIMEOUT
                    return result
                else:
                    raise  # Re-raise non-timeout exceptions

            elapsed = time.monotonic() - start_time
            logger.info(f"Container {sandbox_id} finished in {elapsed:.2f}s (timeout was {timeout}s)")

            # Collect logs
            result.logs = self._get_container_logs(container)

            # Remove container
            container.remove()
            container = None

        except Exception as e:
            result.status = "error"
            result.error = f"Container error: {e}"
            result.error_type = SandboxErrorType.CONTAINER_ERROR
            return result
        finally:
            if container:
                try:
                    container.stop(timeout=3)
                    container.remove(force=True)
                except Exception:
                    pass

        # Read output.json
        output_path = temp_dir / "output.json"
        try:
            output_dict = json.loads(output_path.read_text())
        except Exception as e:
            result.status = "error"
            result.error = f"Failed to read output.json: {e}"
            result.error_type = SandboxErrorType.INVALID_OUTPUT
            return result

        # Parse output
        return self._parse_output(output_dict, result)

    def _get_container_logs(self, container) -> str:
        """Get container logs safely."""
        try:
            return container.logs(stderr=False).decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to get container logs: {e}")
            return ""

    def _parse_output(self, output_dict: dict, result: SandboxResult) -> SandboxResult:
        """Parse and validate the agent output."""
        status = output_dict.get("status")

        if status == "success":
            output = output_dict.get("output")
            if output is None:
                result.status = "error"
                result.error = "output.json has status='success' but no 'output' field"
                result.error_type = SandboxErrorType.INVALID_OUTPUT
                return result

            try:
                agent_output = AgentOutput(**output)
                result.output = agent_output.model_dump()
            except Exception as e:
                result.status = "error"
                result.error = f"Invalid agent output: {e}"
                result.error_type = SandboxErrorType.INVALID_OUTPUT
                return result

        elif status == "error":
            result.status = "error"
            result.error = output_dict.get("error", "Unknown error")
            result.traceback = output_dict.get("traceback")
            result.error_type = SandboxErrorType.AGENT_ERROR

        else:
            result.status = "error"
            result.error = f"Invalid status in output.json: {status}"
            result.error_type = SandboxErrorType.INVALID_OUTPUT

        return result
