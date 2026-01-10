"""Tests for Database class."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from db import Database


@pytest.fixture
def db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    database = Database(db_path)
    yield database
    database.close()
    Path(db_path).unlink(missing_ok=True)


class TestRateLimiting:
    def test_count_requests_empty(self, db):
        since = datetime.now() - timedelta(hours=24)
        count = db.count_requests_since("192.168.1.1", since)
        assert count == 0

    def test_record_and_count_requests(self, db):
        ip = "192.168.1.1"
        since = datetime.now() - timedelta(hours=1)

        db.record_request("req-1", ip)
        db.record_request("req-2", ip)
        db.record_request("req-3", ip)

        count = db.count_requests_since(ip, since)
        assert count == 3

    def test_record_and_count_with_units(self, db):
        ip = "192.168.1.1"
        since = datetime.now() - timedelta(hours=1)

        db.record_request("req-1", ip, units=1)  # champion
        db.record_request("req-2", ip, units=3)  # council
        db.record_request("req-3", ip, units=1)  # selected

        count = db.count_requests_since(ip, since)
        assert count == 5  # 1 + 3 + 1

    def test_count_requests_filters_by_ip(self, db):
        since = datetime.now() - timedelta(hours=1)

        db.record_request("req-1", "192.168.1.1")
        db.record_request("req-2", "192.168.1.1")
        db.record_request("req-3", "192.168.1.2")

        count_ip1 = db.count_requests_since("192.168.1.1", since)
        count_ip2 = db.count_requests_since("192.168.1.2", since)

        assert count_ip1 == 2
        assert count_ip2 == 1

    def test_count_requests_filters_by_time(self, db):
        ip = "192.168.1.1"

        db.record_request("req-1", ip)

        # Count from 1 hour ago - should include the request
        count_recent = db.count_requests_since(ip, datetime.now() - timedelta(hours=1))
        assert count_recent == 1

        # Count from future - should not include the request
        count_future = db.count_requests_since(ip, datetime.now() + timedelta(hours=1))
        assert count_future == 0


class TestBudgetTracking:
    def test_get_total_cost_empty(self, db):
        since = datetime.now() - timedelta(hours=24)
        total = db.get_total_cost_since(since)
        assert total == 0.0

    def test_record_and_get_cost(self, db):
        since = datetime.now() - timedelta(hours=1)

        db.record_cost("req-1", 0.02)
        db.record_cost("req-2", 0.03)
        db.record_cost("req-3", 0.05)

        total = db.get_total_cost_since(since)
        assert total == pytest.approx(0.10)

    def test_get_cost_filters_by_time(self, db):
        db.record_cost("req-1", 0.02)

        # Sum from 1 hour ago - should include the cost
        total_recent = db.get_total_cost_since(datetime.now() - timedelta(hours=1))
        assert total_recent == pytest.approx(0.02)

        # Sum from future - should not include the cost
        total_future = db.get_total_cost_since(datetime.now() + timedelta(hours=1))
        assert total_future == 0.0


class TestThreadSafety:
    def test_concurrent_writes(self, db):
        """Test that concurrent writes don't cause errors."""
        import threading

        def write_requests():
            for i in range(10):
                db.record_request(f"req-{threading.current_thread().name}-{i}", "127.0.0.1")

        threads = [threading.Thread(target=write_requests) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        since = datetime.now() - timedelta(hours=1)
        count = db.count_requests_since("127.0.0.1", since)
        assert count == 50  # 5 threads * 10 requests each
