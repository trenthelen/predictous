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

    def create(self) -> Job:
        """Create a new pending job."""
        job = Job(id=str(uuid4()))
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        """Get job by ID."""
        return self._jobs.get(job_id)

    def run_in_background(self, job: Job, func: Callable, *args, **kwargs) -> None:
        """Run a sync function in background thread and update job status."""
        async def wrapper():
            job.status = JobStatus.RUNNING
            try:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: func(*args, **kwargs))
                job.result = result
                job.status = JobStatus.COMPLETED
            except Exception as e:
                job.error = str(e)
                job.status = JobStatus.FAILED

        asyncio.create_task(wrapper())


# Global instance
jobs = JobStore()
