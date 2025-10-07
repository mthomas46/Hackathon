"""Job Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from ..entities.ingestion_job import IngestionJob
from ..value_objects.job_status import JobStatus


class JobRepository(ABC):
    """
    Abstract repository for ingestion jobs.
    
    Defines the contract for persisting and retrieving jobs.
    """
    
    @abstractmethod
    async def save(self, job: IngestionJob) -> None:
        """
        Save job.
        
        Args:
            job: Job to save
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[IngestionJob]:
        """
        Get job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Job if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_status(
        self,
        status: JobStatus,
        limit: int = 100
    ) -> List[IngestionJob]:
        """
        Get jobs by status.
        
        Args:
            status: Job status
            limit: Maximum number of jobs
            
        Returns:
            List of jobs
        """
        pass
    
    @abstractmethod
    async def get_active_jobs(self, limit: int = 100) -> List[IngestionJob]:
        """
        Get all active jobs.
        
        Args:
            limit: Maximum number of jobs
            
        Returns:
            List of active jobs
        """
        pass
    
    @abstractmethod
    async def get_jobs_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100
    ) -> List[IngestionJob]:
        """
        Get jobs within time range.
        
        Args:
            start_time: Start time
            end_time: End time
            limit: Maximum number of jobs
            
        Returns:
            List of jobs
        """
        pass
    
    @abstractmethod
    async def update(self, job: IngestionJob) -> None:
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
    
    @abstractmethod
    async def count_by_status(self, status: JobStatus) -> int:
        """
        Count jobs by status.
        
        Args:
            status: Job status
            
        Returns:
            Number of jobs with status
        """
        pass
    
    @abstractmethod
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[IngestionJob]:
        """
        List all jobs with pagination.
        
        Args:
            skip: Number of jobs to skip
            limit: Maximum number of jobs to return
            
        Returns:
            List of jobs
        """
        pass

