"""Job Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from services.training_coordinator.domain.entities.training_job import TrainingJob
from services.training_coordinator.domain.value_objects.job_status import JobStatus
from services.training_coordinator.domain.value_objects.job_priority import JobPriority


class JobRepository(ABC):
    """
    Repository for training job persistence.
    
    Manages storage and retrieval of training jobs.
    """
    
    @abstractmethod
    async def save(self, job: TrainingJob) -> None:
        """Save training job."""
        pass
    
    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[TrainingJob]:
        """Get job by ID."""
        pass
    
    @abstractmethod
    async def get_by_mcp_id(self, mcp_id: str) -> List[TrainingJob]:
        """Get all jobs for an MCP."""
        pass
    
    @abstractmethod
    async def list_by_status(self, status: JobStatus, limit: Optional[int] = None) -> List[TrainingJob]:
        """List jobs by status."""
        pass
    
    @abstractmethod
    async def list_pending_by_priority(self, limit: Optional[int] = None) -> List[TrainingJob]:
        """List pending jobs ordered by priority."""
        pass
    
    @abstractmethod
    async def list_active(self, limit: Optional[int] = None) -> List[TrainingJob]:
        """List active jobs."""
        pass
    
    @abstractmethod
    async def delete(self, job_id: str) -> bool:
        """Delete job."""
        pass
    
    @abstractmethod
    async def count_by_status(self, status: JobStatus) -> int:
        """Count jobs by status."""
        pass

