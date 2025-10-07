"""Job Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.tagging_job import TaggingJob


class JobRepository(ABC):
    """
    Abstract repository for tagging jobs.
    
    Defines contract for job persistence operations.
    """
    
    @abstractmethod
    async def save(self, job: TaggingJob) -> None:
        """
        Save job.
        
        Args:
            job: Job to save
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[TaggingJob]:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_active(self, limit: int = 100) -> List[TaggingJob]:
        """
        Get active jobs.
        
        Args:
            limit: Maximum number of jobs
            
        Returns:
            List of active jobs
        """
        pass
    
    @abstractmethod
    async def update(self, job: TaggingJob) -> None:
        """
        Update job.
        
        Args:
            job: Job to update
        """
        pass
    
    @abstractmethod
    async def delete(self, job_id: str) -> bool:
        """
        Delete job.
        
        Args:
            job_id: Job ID
            
        Returns:
            True if deleted, False if not found
        """
        pass

