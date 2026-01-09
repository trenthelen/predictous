"""
Cost-tracking proxy that sits between sandbox containers and the gateway.

Tracks cumulative costs per run_id and service type, rejects requests when budget is exceeded.
Supports split budgets for different services (chutes, desearch).
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Default budgets per service type
DEFAULT_CHUTES_BUDGET = 0.02  # $0.02 for LLM calls
DEFAULT_DESEARCH_BUDGET = 0.10  # $0.10 for search/crawl

# Service type constants
SERVICE_CHUTES = "chutes"
SERVICE_DESEARCH = "desearch"
SERVICE_OTHER = "other"


class CostTracker:
    """Thread-safe cost tracker for multiple run_ids with per-service budgets."""

    def __init__(
        self,
        chutes_budget: float = DEFAULT_CHUTES_BUDGET,
        desearch_budget: float = DEFAULT_DESEARCH_BUDGET,
    ):
        self.chutes_budget = chutes_budget
        self.desearch_budget = desearch_budget
        # {run_id: {"chutes": cost, "desearch": cost, "other": cost}}
        self._costs: dict[str, dict[str, float]] = {}
        self._lock = threading.Lock()

    def _init_run(self, run_id: str) -> None:
        """Initialize cost tracking for a run_id if not exists."""
        if run_id not in self._costs:
            self._costs[run_id] = {
                SERVICE_CHUTES: 0.0,
                SERVICE_DESEARCH: 0.0,
                SERVICE_OTHER: 0.0,
            }

    def add_cost(self, run_id: str, service: str, cost: float) -> float:
        """Add cost for a run_id and service, return new service total."""
        with self._lock:
            self._init_run(run_id)
            current = self._costs[run_id].get(service, 0.0)
            new_total = current + cost
            self._costs[run_id][service] = new_total
            return new_total

    def get_cost(self, run_id: str, service: Optional[str] = None) -> float:
        """Get current cost for a run_id. If service is None, return total."""
        with self._lock:
            if run_id not in self._costs:
                return 0.0
            costs = self._costs[run_id]
            if service is None:
                return sum(costs.values())
            return costs.get(service, 0.0)

    def get_costs_by_service(self, run_id: str) -> dict[str, float]:
        """Get costs breakdown by service for a run_id."""
        with self._lock:
            if run_id not in self._costs:
                return {SERVICE_CHUTES: 0.0, SERVICE_DESEARCH: 0.0, SERVICE_OTHER: 0.0}
            return self._costs[run_id].copy()

    def is_over_budget(self, run_id: str, service: Optional[str] = None) -> bool:
        """Check if run_id has exceeded budget for a specific service or any service."""
        with self._lock:
            if run_id not in self._costs:
                return False
            costs = self._costs[run_id]
            if service == SERVICE_CHUTES:
                return costs.get(SERVICE_CHUTES, 0.0) > self.chutes_budget
            elif service == SERVICE_DESEARCH:
                return costs.get(SERVICE_DESEARCH, 0.0) > self.desearch_budget
            else:
                # Check if any service is over budget
                chutes_over = costs.get(SERVICE_CHUTES, 0.0) > self.chutes_budget
                desearch_over = costs.get(SERVICE_DESEARCH, 0.0) > self.desearch_budget
                return chutes_over or desearch_over

    def get_budget_status(self, run_id: str) -> dict[str, dict]:
        """Get budget status for all services."""
        with self._lock:
            if run_id not in self._costs:
                costs = {SERVICE_CHUTES: 0.0, SERVICE_DESEARCH: 0.0, SERVICE_OTHER: 0.0}
            else:
                costs = self._costs[run_id]
            return {
                SERVICE_CHUTES: {
                    "cost": costs.get(SERVICE_CHUTES, 0.0),
                    "budget": self.chutes_budget,
                    "over": costs.get(SERVICE_CHUTES, 0.0) > self.chutes_budget,
                },
                SERVICE_DESEARCH: {
                    "cost": costs.get(SERVICE_DESEARCH, 0.0),
                    "budget": self.desearch_budget,
                    "over": costs.get(SERVICE_DESEARCH, 0.0) > self.desearch_budget,
                },
            }

    def clear(self, run_id: str) -> None:
        """Clear cost tracking for a run_id."""
        with self._lock:
            self._costs.pop(run_id, None)

    def clear_all(self) -> None:
        """Clear all cost tracking."""
        with self._lock:
            self._costs.clear()


class CostProxyHandler(BaseHTTPRequestHandler):
    """HTTP handler that forwards requests and tracks costs."""

    gateway_url: str = None
    cost_tracker: CostTracker = None

    def log_message(self, format, *args):
        """Override to use logger instead of stderr."""
        logger.debug(f"[COST-PROXY] {format % args}")

    def _detect_service(self, path: str) -> str:
        """Detect service type from URL path."""
        if "/chutes/" in path:
            return SERVICE_CHUTES
        elif "/desearch/" in path:
            return SERVICE_DESEARCH
        else:
            return SERVICE_OTHER

    def _extract_run_id(self, body: bytes) -> Optional[str]:
        """Extract run_id from request body."""
        if not body:
            return None
        try:
            data = json.loads(body)
            return data.get("run_id")
        except (json.JSONDecodeError, TypeError):
            return None

    def _extract_cost(self, response_body: bytes) -> float:
        """Extract cost from response body."""
        if not response_body:
            return 0.0
        try:
            data = json.loads(response_body)
            return float(data.get("cost", 0.0))
        except (json.JSONDecodeError, TypeError, ValueError):
            return 0.0

    def _forward_request(self, method: str):
        """Forward request to gateway and track costs."""
        try:
            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length > 0 else b""

            # Extract run_id and detect service type
            run_id = self._extract_run_id(body)
            service = self._detect_service(self.path)

            # Check if already over budget for this service BEFORE making request
            if run_id and self.cost_tracker.is_over_budget(run_id, service):
                status = self.cost_tracker.get_budget_status(run_id)
                service_status = status.get(service, {})
                logger.warning(
                    f"[COST-PROXY] {service} budget exceeded for run_id={run_id}, "
                    f"cost=${service_status.get('cost', 0):.4f} > "
                    f"budget=${service_status.get('budget', 0):.4f}"
                )
                self._send_budget_exceeded(run_id, service, status)
                return

            # Forward to gateway
            forward_headers = {
                k: v for k, v in self.headers.items()
                if k.lower() not in ("host", "connection", "content-length")
            }
            if body:
                forward_headers["Content-Length"] = str(len(body))

            target_url = f"{self.gateway_url}{self.path}"

            response = requests.request(
                method=method,
                url=target_url,
                headers=forward_headers,
                data=body if body else None,
                timeout=120,
                allow_redirects=False,
            )

            # Extract and track cost per service
            cost = self._extract_cost(response.content)
            if run_id and cost > 0:
                service_total = self.cost_tracker.add_cost(run_id, service, cost)
                total_cost = self.cost_tracker.get_cost(run_id)
                logger.info(
                    f"[COST-PROXY] run_id={run_id} {service} +${cost:.6f} = "
                    f"${service_total:.6f} (total: ${total_cost:.6f})"
                )

            # Check if NOW over budget (after this request)
            if run_id and self.cost_tracker.is_over_budget(run_id, service):
                logger.warning(
                    f"[COST-PROXY] {service} budget exceeded after request for run_id={run_id}"
                )
                # Still return this response, but next request will be rejected

            # Send response back to client
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                if key.lower() not in (
                    "transfer-encoding", "connection", "keep-alive",
                    "content-encoding", "content-length",
                ):
                    self.send_header(key, value)
            self.send_header("Content-Length", str(len(response.content)))
            self.end_headers()

            if response.content:
                self.wfile.write(response.content)

        except BrokenPipeError:
            # Client closed connection before we could send response - this is fine
            logger.debug(f"[COST-PROXY] Client closed connection for {method} {self.path}")
        except Exception as e:
            logger.error(f"[COST-PROXY] Error forwarding {method} {self.path}: {e}")
            try:
                self._send_error(500, f"Proxy error: {e}")
            except BrokenPipeError:
                pass  # Client already gone, nothing to do

    def _send_budget_exceeded(self, run_id: str, service: str, status: dict):
        """Send 402 Payment Required response."""
        service_status = status.get(service, {})
        error_body = json.dumps({
            "error": "Budget exceeded",
            "detail": f"Run {run_id} has exceeded the {service} cost budget",
            "service": service,
            "current_cost": service_status.get("cost", 0),
            "budget": service_status.get("budget", 0),
            "all_services": status,
        }).encode()

        self.send_response(402)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(error_body)))
        self.end_headers()
        self.wfile.write(error_body)

    def _send_error(self, code: int, message: str):
        """Send error response."""
        error_body = json.dumps({"error": message}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(error_body)))
        self.end_headers()
        self.wfile.write(error_body)

    def do_GET(self):
        self._forward_request("GET")

    def do_POST(self):
        self._forward_request("POST")

    def do_PUT(self):
        self._forward_request("PUT")

    def do_DELETE(self):
        self._forward_request("DELETE")


class CostTrackingProxy:
    """
    HTTP proxy server that tracks costs per run_id with split budgets.

    Usage:
        proxy = CostTrackingProxy(
            gateway_url="http://localhost:8000",
            chutes_budget=0.02,
            desearch_budget=0.10,
            port=8888,
        )
        proxy.start()  # Blocks
        # Or in background:
        proxy.start_background()
        # ... do work ...
        proxy.stop()
    """

    def __init__(
        self,
        gateway_url: str,
        chutes_budget: float = DEFAULT_CHUTES_BUDGET,
        desearch_budget: float = DEFAULT_DESEARCH_BUDGET,
        port: int = 8888,
    ):
        self.gateway_url = gateway_url.rstrip("/")
        self.chutes_budget = chutes_budget
        self.desearch_budget = desearch_budget
        self.port = port
        self.cost_tracker = CostTracker(
            chutes_budget=chutes_budget,
            desearch_budget=desearch_budget,
        )
        self.server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the proxy server (blocking)."""
        CostProxyHandler.gateway_url = self.gateway_url
        CostProxyHandler.cost_tracker = self.cost_tracker

        self.server = ThreadingHTTPServer(("0.0.0.0", self.port), CostProxyHandler)
        logger.info(f"[COST-PROXY] Starting on port {self.port}, gateway={self.gateway_url}")
        self.server.serve_forever()

    def start_background(self) -> None:
        """Start the proxy server in a background thread."""
        CostProxyHandler.gateway_url = self.gateway_url
        CostProxyHandler.cost_tracker = self.cost_tracker

        self.server = ThreadingHTTPServer(("0.0.0.0", self.port), CostProxyHandler)

        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()
        logger.info(
            f"[COST-PROXY] Started on port {self.port}, gateway={self.gateway_url}, "
            f"budgets: chutes=${self.chutes_budget}, desearch=${self.desearch_budget}"
        )

    def stop(self) -> None:
        """Stop the proxy server."""
        if self.server:
            self.server.shutdown()
            self.server = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("[COST-PROXY] Stopped")

    def get_cost(self, run_id: str, service: Optional[str] = None) -> float:
        """Get current cost for a run_id. If service is None, return total."""
        return self.cost_tracker.get_cost(run_id, service)

    def get_costs_by_service(self, run_id: str) -> dict[str, float]:
        """Get costs breakdown by service for a run_id."""
        return self.cost_tracker.get_costs_by_service(run_id)

    def clear_run(self, run_id: str) -> None:
        """Clear cost tracking for a run_id."""
        self.cost_tracker.clear(run_id)

    @property
    def proxy_url(self) -> str:
        """URL for containers to use."""
        return f"http://host.docker.internal:{self.port}"
