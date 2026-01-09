"""Tests for cost tracking functionality with split budgets."""

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
import requests

from sandbox.cost_proxy import (
    CostTracker,
    CostTrackingProxy,
    SERVICE_CHUTES,
    SERVICE_DESEARCH,
    SERVICE_OTHER,
)


class TestCostTracker:
    """Tests for the CostTracker class with split budgets."""

    def test_add_and_get_cost_per_service(self):
        """Test adding and retrieving costs per service."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        total = tracker.add_cost("run-1", SERVICE_CHUTES, 0.005)
        assert total == 0.005
        assert tracker.get_cost("run-1", SERVICE_CHUTES) == 0.005
        assert tracker.get_cost("run-1", SERVICE_DESEARCH) == 0.0
        assert tracker.get_cost("run-1") == 0.005  # Total

        total = tracker.add_cost("run-1", SERVICE_DESEARCH, 0.02)
        assert total == 0.02
        assert tracker.get_cost("run-1", SERVICE_DESEARCH) == 0.02
        assert tracker.get_cost("run-1") == 0.025  # Total

    def test_separate_run_ids(self):
        """Test that different run_ids are tracked separately."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        tracker.add_cost("run-1", SERVICE_CHUTES, 0.01)
        tracker.add_cost("run-2", SERVICE_CHUTES, 0.005)

        assert tracker.get_cost("run-1", SERVICE_CHUTES) == 0.01
        assert tracker.get_cost("run-2", SERVICE_CHUTES) == 0.005

    def test_is_over_budget_chutes(self):
        """Test chutes budget limit checking."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        tracker.add_cost("run-1", SERVICE_CHUTES, 0.015)
        assert not tracker.is_over_budget("run-1", SERVICE_CHUTES)
        assert not tracker.is_over_budget("run-1")  # Any service

        tracker.add_cost("run-1", SERVICE_CHUTES, 0.01)  # Now at 0.025
        assert tracker.is_over_budget("run-1", SERVICE_CHUTES)
        assert tracker.is_over_budget("run-1")  # Any service

    def test_is_over_budget_desearch(self):
        """Test desearch budget limit checking."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        tracker.add_cost("run-1", SERVICE_DESEARCH, 0.08)
        assert not tracker.is_over_budget("run-1", SERVICE_DESEARCH)
        assert not tracker.is_over_budget("run-1")

        tracker.add_cost("run-1", SERVICE_DESEARCH, 0.03)  # Now at 0.11
        assert tracker.is_over_budget("run-1", SERVICE_DESEARCH)
        assert tracker.is_over_budget("run-1")

    def test_independent_budgets(self):
        """Test that chutes and desearch budgets are independent."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        # Max out chutes budget
        tracker.add_cost("run-1", SERVICE_CHUTES, 0.025)
        assert tracker.is_over_budget("run-1", SERVICE_CHUTES)

        # Desearch should still be fine
        assert not tracker.is_over_budget("run-1", SERVICE_DESEARCH)
        tracker.add_cost("run-1", SERVICE_DESEARCH, 0.05)
        assert not tracker.is_over_budget("run-1", SERVICE_DESEARCH)

    def test_unknown_run_id(self):
        """Test that unknown run_ids return 0 cost."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        assert tracker.get_cost("unknown") == 0.0
        assert tracker.get_cost("unknown", SERVICE_CHUTES) == 0.0
        assert not tracker.is_over_budget("unknown")

    def test_get_costs_by_service(self):
        """Test getting cost breakdown by service."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        tracker.add_cost("run-1", SERVICE_CHUTES, 0.01)
        tracker.add_cost("run-1", SERVICE_DESEARCH, 0.05)

        costs = tracker.get_costs_by_service("run-1")
        assert costs[SERVICE_CHUTES] == 0.01
        assert costs[SERVICE_DESEARCH] == 0.05
        assert costs[SERVICE_OTHER] == 0.0

    def test_get_budget_status(self):
        """Test getting budget status for all services."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        tracker.add_cost("run-1", SERVICE_CHUTES, 0.025)  # Over
        tracker.add_cost("run-1", SERVICE_DESEARCH, 0.05)  # Under

        status = tracker.get_budget_status("run-1")
        assert status[SERVICE_CHUTES]["cost"] == 0.025
        assert status[SERVICE_CHUTES]["budget"] == 0.02
        assert status[SERVICE_CHUTES]["over"] is True

        assert status[SERVICE_DESEARCH]["cost"] == 0.05
        assert status[SERVICE_DESEARCH]["budget"] == 0.10
        assert status[SERVICE_DESEARCH]["over"] is False

    def test_clear_run(self):
        """Test clearing cost tracking for a run_id."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        tracker.add_cost("run-1", SERVICE_CHUTES, 0.01)
        tracker.add_cost("run-1", SERVICE_DESEARCH, 0.05)
        assert abs(tracker.get_cost("run-1") - 0.06) < 0.0001

        tracker.clear("run-1")
        assert tracker.get_cost("run-1") == 0.0

    def test_clear_all(self):
        """Test clearing all cost tracking."""
        tracker = CostTracker(chutes_budget=0.02, desearch_budget=0.10)

        tracker.add_cost("run-1", SERVICE_CHUTES, 0.01)
        tracker.add_cost("run-2", SERVICE_DESEARCH, 0.05)

        tracker.clear_all()
        assert tracker.get_cost("run-1") == 0.0
        assert tracker.get_cost("run-2") == 0.0

    def test_thread_safety(self):
        """Test that cost tracking is thread-safe."""
        tracker = CostTracker(chutes_budget=1.0, desearch_budget=1.0)
        num_threads = 10
        increments_per_thread = 100

        def add_costs():
            for _ in range(increments_per_thread):
                tracker.add_cost("run-1", SERVICE_CHUTES, 0.001)

        threads = [threading.Thread(target=add_costs) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected = num_threads * increments_per_thread * 0.001
        assert abs(tracker.get_cost("run-1", SERVICE_CHUTES) - expected) < 0.0001


class MockGatewayHandler(BaseHTTPRequestHandler):
    """Mock gateway that returns configurable costs."""

    cost_to_return = 0.001

    def log_message(self, format, *args):
        pass  # Suppress logging

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        response = json.dumps({
            "result": "mock response",
            "cost": self.cost_to_return,
        }).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)


class TestCostTrackingProxy:
    """Integration tests for CostTrackingProxy with split budgets."""

    @pytest.fixture
    def mock_gateway(self):
        """Start a mock gateway server."""
        server = HTTPServer(("127.0.0.1", 0), MockGatewayHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield f"http://127.0.0.1:{port}"
        server.shutdown()

    @pytest.fixture
    def proxy(self, mock_gateway):
        """Create a cost-tracking proxy connected to mock gateway."""
        proxy = CostTrackingProxy(
            gateway_url=mock_gateway,
            chutes_budget=0.01,
            desearch_budget=0.05,
            port=0,  # Let OS pick a free port
        )
        # Manually set up the server on an available port
        from http.server import ThreadingHTTPServer
        from sandbox.cost_proxy import CostProxyHandler

        CostProxyHandler.gateway_url = proxy.gateway_url
        CostProxyHandler.cost_tracker = proxy.cost_tracker

        proxy.server = ThreadingHTTPServer(("127.0.0.1", 0), CostProxyHandler)
        proxy.port = proxy.server.server_address[1]
        proxy._thread = threading.Thread(target=proxy.server.serve_forever, daemon=True)
        proxy._thread.start()

        yield proxy
        proxy.stop()

    def test_proxy_forwards_requests(self, proxy, mock_gateway):
        """Test that proxy forwards requests to gateway."""
        proxy_url = f"http://127.0.0.1:{proxy.port}"

        response = requests.post(
            f"{proxy_url}/api/gateway/chutes/chat/completions",
            json={"run_id": "test-run", "message": "hello"},
            timeout=5,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "mock response"

    def test_proxy_tracks_chutes_costs(self, proxy, mock_gateway):
        """Test that proxy tracks chutes costs separately."""
        proxy_url = f"http://127.0.0.1:{proxy.port}"
        MockGatewayHandler.cost_to_return = 0.002

        # Make a chutes request
        requests.post(
            f"{proxy_url}/api/gateway/chutes/chat/completions",
            json={"run_id": "test-run", "message": "hello"},
            timeout=5,
        )

        assert proxy.get_cost("test-run", SERVICE_CHUTES) == 0.002
        assert proxy.get_cost("test-run", SERVICE_DESEARCH) == 0.0
        assert proxy.get_cost("test-run") == 0.002

    def test_proxy_tracks_desearch_costs(self, proxy, mock_gateway):
        """Test that proxy tracks desearch costs separately."""
        proxy_url = f"http://127.0.0.1:{proxy.port}"
        MockGatewayHandler.cost_to_return = 0.003

        # Make a desearch request
        requests.post(
            f"{proxy_url}/api/gateway/desearch/web/search",
            json={"run_id": "test-run", "query": "test"},
            timeout=5,
        )

        assert proxy.get_cost("test-run", SERVICE_DESEARCH) == 0.003
        assert proxy.get_cost("test-run", SERVICE_CHUTES) == 0.0
        assert proxy.get_cost("test-run") == 0.003

    def test_proxy_rejects_over_chutes_budget(self, proxy, mock_gateway):
        """Test that proxy rejects chutes requests when budget exceeded."""
        proxy_url = f"http://127.0.0.1:{proxy.port}"
        MockGatewayHandler.cost_to_return = 0.006  # Chutes budget is 0.01

        # First request should succeed
        response = requests.post(
            f"{proxy_url}/api/gateway/chutes/chat/completions",
            json={"run_id": "test-run", "message": "first"},
            timeout=5,
        )
        assert response.status_code == 200

        # Second request should succeed (0.012 total, checked before)
        response = requests.post(
            f"{proxy_url}/api/gateway/chutes/chat/completions",
            json={"run_id": "test-run", "message": "second"},
            timeout=5,
        )
        assert response.status_code == 200

        # Third chutes request should be rejected
        response = requests.post(
            f"{proxy_url}/api/gateway/chutes/chat/completions",
            json={"run_id": "test-run", "message": "third"},
            timeout=5,
        )
        assert response.status_code == 402
        data = response.json()
        assert "Budget exceeded" in data["error"]
        assert data["service"] == SERVICE_CHUTES

    def test_desearch_allowed_when_chutes_over_budget(self, proxy, mock_gateway):
        """Test that desearch requests still work when chutes is over budget."""
        proxy_url = f"http://127.0.0.1:{proxy.port}"
        MockGatewayHandler.cost_to_return = 0.015  # Over chutes budget (0.01)

        # Make chutes request to exceed chutes budget
        requests.post(
            f"{proxy_url}/api/gateway/chutes/chat/completions",
            json={"run_id": "test-run", "message": "hello"},
            timeout=5,
        )

        # Verify chutes is over budget
        assert proxy.get_cost("test-run", SERVICE_CHUTES) == 0.015
        assert proxy.cost_tracker.is_over_budget("test-run", SERVICE_CHUTES)

        # Desearch should still work
        MockGatewayHandler.cost_to_return = 0.01
        response = requests.post(
            f"{proxy_url}/api/gateway/desearch/web/search",
            json={"run_id": "test-run", "query": "test"},
            timeout=5,
        )
        assert response.status_code == 200

    def test_get_costs_by_service(self, proxy, mock_gateway):
        """Test getting costs breakdown by service."""
        proxy_url = f"http://127.0.0.1:{proxy.port}"

        MockGatewayHandler.cost_to_return = 0.002
        requests.post(
            f"{proxy_url}/api/gateway/chutes/chat/completions",
            json={"run_id": "test-run", "message": "hello"},
            timeout=5,
        )

        MockGatewayHandler.cost_to_return = 0.003
        requests.post(
            f"{proxy_url}/api/gateway/desearch/web/search",
            json={"run_id": "test-run", "query": "test"},
            timeout=5,
        )

        costs = proxy.get_costs_by_service("test-run")
        assert costs[SERVICE_CHUTES] == 0.002
        assert costs[SERVICE_DESEARCH] == 0.003

    def test_proxy_url_property(self):
        """Test the proxy_url property."""
        proxy = CostTrackingProxy(
            gateway_url="http://example.com",
            chutes_budget=0.02,
            desearch_budget=0.10,
            port=9999,
        )
        assert proxy.proxy_url == "http://host.docker.internal:9999"
