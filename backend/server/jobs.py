"""Background job management for async predictions."""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from uuid import uuid4


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: str
    status: JobStatus = JobStatus.PENDING
    result: Any = None
    error: str | None = None


class JobStore:
    """In-memory job storage with background execution."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._ip_jobs: dict[str, set[str]] = {}  # ip -> active job_ids

    def count_active_for_ip(self, ip: str) -> int:
        """Count active jobs for an IP."""
        return len(self._ip_jobs.get(ip, set()))

    def create(self, ip: str | None = None) -> Job:
        """Create a new pending job, optionally tracking by IP."""
        job = Job(id=str(uuid4()))
        self._jobs[job.id] = job
        if ip:
            self._ip_jobs.setdefault(ip, set()).add(job.id)
        return job

    def get(self, job_id: str) -> Job | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def run_in_background(
        self, job: Job, func: Callable, *args, ip: str | None = None, **kwargs
    ) -> None:
        """Run a sync function in background thread and update job status."""

        async def wrapper():
            job.status = JobStatus.RUNNING
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: func(*args, **kwargs))
                job.result = result
                job.status = JobStatus.COMPLETED
            except Exception as e:
                job.error = str(e)
                job.status = JobStatus.FAILED
            finally:
                if ip and ip in self._ip_jobs:
                    self._ip_jobs[ip].discard(job.id)

        asyncio.create_task(wrapper())


# Global instance
jobs = JobStore()
