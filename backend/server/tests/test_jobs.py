"""Tests for job management."""

from server.jobs import JobStore


class TestJobStoreIPTracking:
    def test_count_active_for_ip_empty(self):
        store = JobStore()
        assert store.count_active_for_ip("1.2.3.4") == 0

    def test_create_without_ip_does_not_track(self):
        store = JobStore()
        store.create()
        assert store.count_active_for_ip("1.2.3.4") == 0

    def test_create_with_ip_tracks_job(self):
        store = JobStore()
        store.create(ip="1.2.3.4")
        assert store.count_active_for_ip("1.2.3.4") == 1

    def test_multiple_jobs_same_ip(self):
        store = JobStore()
        store.create(ip="1.2.3.4")
        store.create(ip="1.2.3.4")
        assert store.count_active_for_ip("1.2.3.4") == 2

    def test_different_ips_tracked_separately(self):
        store = JobStore()
        store.create(ip="1.2.3.4")
        store.create(ip="5.6.7.8")
        assert store.count_active_for_ip("1.2.3.4") == 1
        assert store.count_active_for_ip("5.6.7.8") == 1
