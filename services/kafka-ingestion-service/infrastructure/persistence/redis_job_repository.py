"""Redis Job Repository Implementation."""

import json
import logging
from typing import List, Optional
from datetime import datetime
import redis.asyncio as aioredis

from ...domain.entities.ingestion_job import IngestionJob
from ...domain.value_objects.job_status import JobStatus
from ...domain.repositories.job_repository import JobRepository

logger = logging.getLogger(__name__)


class RedisJobRepository(JobRepository):
    """
    Redis implementation of job repository.
    
    Stores jobs in Redis with indices for querying.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize repository.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis: Optional[aioredis.Redis] = None
    
    async def connect(self) -> None:
        """Connect to Redis."""
        logger.info(f"Connecting to Redis: {self.redis_url}")
        self._redis = await aioredis.from_url(self.redis_url, decode_responses=True)
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    def _get_job_key(self, job_id: str) -> str:
        """Get Redis key for job."""
        return f"job:{job_id}"
    
    def _get_status_index_key(self, status: JobStatus) -> str:
        """Get Redis key for status index."""
        return f"jobs:status:{status.value}"
    
    def _get_all_jobs_key(self) -> str:
        """Get Redis key for all jobs index."""
        return "jobs:all"
    
    async def save(self, job: IngestionJob) -> None:
        """Save job."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        job_key = self._get_job_key(job.job_id)
        job_data = json.dumps(job.to_dict())
        
        # Save job
        await self._redis.set(job_key, job_data)
        
        # Add to status index
        status_key = self._get_status_index_key(job.status)
        await self._redis.sadd(status_key, job.job_id)
        
        # Add to all jobs index with timestamp score
        all_jobs_key = self._get_all_jobs_key()
        timestamp = job.created_at.timestamp()
        await self._redis.zadd(all_jobs_key, {job.job_id: timestamp})
        
        logger.debug(f"Saved job {job.job_id}")
    
    async def get_by_id(self, job_id: str) -> Optional[IngestionJob]:
        """Get job by ID."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        job_key = self._get_job_key(job_id)
        job_data = await self._redis.get(job_key)
        
        if not job_data:
            return None
        
        data = json.loads(job_data)
        
        # Reconstruct job (simplified - would need proper deserialization)
        return IngestionJob(
            job_id=data["job_id"],
            name=data["name"],
            description=data["description"],
            status=JobStatus(data["status"]),
            source_type=data["source_type"],
            source_config=data["source_config"],
            # ... other fields
        )
    
    async def get_by_status(
        self,
        status: JobStatus,
        limit: int = 100
    ) -> List[IngestionJob]:
        """Get jobs by status."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        status_key = self._get_status_index_key(status)
        job_ids = await self._redis.srandmember(status_key, limit)
        
        if not job_ids:
            return []
        
        # Handle single result
        if isinstance(job_ids, str):
            job_ids = [job_ids]
        
        jobs = []
        for job_id in job_ids:
            job = await self.get_by_id(job_id)
            if job:
                jobs.append(job)
        
        return jobs
    
    async def get_active_jobs(self, limit: int = 100) -> List[IngestionJob]:
        """Get all active jobs."""
        return await self.get_by_status(JobStatus.RUNNING, limit)
    
    async def get_jobs_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100
    ) -> List[IngestionJob]:
        """Get jobs within time range."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        all_jobs_key = self._get_all_jobs_key()
        start_score = start_time.timestamp()
        end_score = end_time.timestamp()
        
        job_ids = await self._redis.zrangebyscore(
            all_jobs_key,
            start_score,
            end_score,
            start=0,
            num=limit
        )
        
        jobs = []
        for job_id in job_ids:
            job = await self.get_by_id(job_id)
            if job:
                jobs.append(job)
        
        return jobs
    
    async def update(self, job: IngestionJob) -> None:
        """Update job."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        # Get old job to update indices
        old_job = await self.get_by_id(job.job_id)
        
        if old_job and old_job.status != job.status:
            # Remove from old status index
            old_status_key = self._get_status_index_key(old_job.status)
            await self._redis.srem(old_status_key, job.job_id)
        
        # Save updated job (this will add to new status index)
        await self.save(job)
        
        logger.debug(f"Updated job {job.job_id}")
    
    async def delete(self, job_id: str) -> bool:
        """Delete job."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        # Get job to update indices
        job = await self.get_by_id(job_id)
        if not job:
            return False
        
        # Remove from indices
        status_key = self._get_status_index_key(job.status)
        await self._redis.srem(status_key, job_id)
        
        all_jobs_key = self._get_all_jobs_key()
        await self._redis.zrem(all_jobs_key, job_id)
        
        # Delete job
        job_key = self._get_job_key(job_id)
        await self._redis.delete(job_key)
        
        logger.debug(f"Deleted job {job_id}")
        return True
    
    async def count_by_status(self, status: JobStatus) -> int:
        """Count jobs by status."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        status_key = self._get_status_index_key(status)
        return await self._redis.scard(status_key)
    
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[IngestionJob]:
        """List all jobs with pagination."""
        if not self._redis:
            raise RuntimeError("Repository not connected")
        
        all_jobs_key = self._get_all_jobs_key()
        
        # Get job IDs (sorted by timestamp, descending)
        job_ids = await self._redis.zrevrange(
            all_jobs_key,
            skip,
            skip + limit - 1
        )
        
        jobs = []
        for job_id in job_ids:
            job = await self.get_by_id(job_id)
            if job:
                jobs.append(job)
        
        return jobs

