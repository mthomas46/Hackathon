"""SyncJob Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.sync_job import SyncJob


class SyncJobRepository(ABC):
    """Abstract repository for SyncJob entities."""
    
    @abstractmethod
    async def add(self, job: SyncJob) -> None:
        """Add sync job."""
        pass
    
    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[SyncJob]:
        """Get sync job by ID."""
        pass
    
    @abstractmethod
    async def update(self, job: SyncJob) -> None:
        """Update sync job."""
        pass
    
    @abstractmethod
    async def delete(self, job_id: str) -> None:
        """Delete sync job."""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[SyncJob]:
        """List all sync jobs."""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: str) -> List[SyncJob]:
        """Find sync jobs by status."""
        pass
    
    @abstractmethod
    async def find_scheduled(self) -> List[SyncJob]:
        """Find scheduled sync jobs."""
        pass
    
    @abstractmethod
    async def find_running(self) -> List[SyncJob]:
        """Find running sync jobs."""
        pass

