"""Job repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.job import Job
from ..value_objects.job_id import JobId
from ..value_objects.job_status import JobStatus


class JobRepository(ABC):
    """Abstract repository for job persistence."""

    @abstractmethod
    async def save(self, job: Job) -> None:
        """Save a job."""
        pass

    @abstractmethod
    async def find_by_id(self, job_id: JobId) -> Optional[Job]:
        """Find a job by ID."""
        pass

    @abstractmethod
    async def find_by_workflow_id(self, workflow_id: str) -> List[Job]:
        """Find jobs by workflow ID."""
        pass

    @abstractmethod
    async def find_by_status(self, status: JobStatus) -> List[Job]:
        """Find jobs by status."""
        pass

    @abstractmethod
    async def find_all(self) -> List[Job]:
        """Find all jobs."""
        pass

    @abstractmethod
    async def delete(self, job_id: JobId) -> None:
        """Delete a job by ID."""
        pass
