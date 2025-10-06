"""Repository Interfaces for Training Coordinator."""

from .job_repository import JobRepository
from .worker_pool_repository import WorkerPoolRepository

__all__ = [
    "JobRepository",
    "WorkerPoolRepository",
]

