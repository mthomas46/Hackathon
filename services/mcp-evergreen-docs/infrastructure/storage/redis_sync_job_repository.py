"""Redis SyncJob Repository Implementation."""

from typing import List, Optional
import json
import redis.asyncio as redis

from ...domain.entities.sync_job import SyncJob
from ...domain.repositories.sync_job_repository import SyncJobRepository


class RedisSyncJobRepository(SyncJobRepository):
    """Redis implementation of SyncJobRepository."""
    
    def __init__(self, redis_client: redis.Redis):
        """Initialize repository."""
        self.redis = redis_client
        self.prefix = "evergreen:job:"
        self.index_key = "evergreen:jobs:all"
    
    async def add(self, job: SyncJob) -> None:
        """Add sync job."""
        key = f"{self.prefix}{job.job_id}"
        await self.redis.set(key, json.dumps(job.to_dict()))
        await self.redis.sadd(self.index_key, job.job_id)
    
    async def get_by_id(self, job_id: str) -> Optional[SyncJob]:
        """Get sync job by ID."""
        key = f"{self.prefix}{job_id}"
        data = await self.redis.get(key)
        if not data:
            return None
        return self._from_dict(json.loads(data))
    
    async def update(self, job: SyncJob) -> None:
        """Update sync job."""
        await self.add(job)
    
    async def delete(self, job_id: str) -> None:
        """Delete sync job."""
        key = f"{self.prefix}{job_id}"
        await self.redis.delete(key)
        await self.redis.srem(self.index_key, job_id)
    
    async def list_all(self) -> List[SyncJob]:
        """List all sync jobs."""
        job_ids = await self.redis.smembers(self.index_key)
        jobs = []
        for job_id in job_ids:
            job = await self.get_by_id(job_id.decode() if isinstance(job_id, bytes) else job_id)
            if job:
                jobs.append(job)
        return jobs
    
    async def find_by_status(self, status: str) -> List[SyncJob]:
        """Find sync jobs by status."""
        jobs = await self.list_all()
        return [job for job in jobs if job.status == status]
    
    async def find_scheduled(self) -> List[SyncJob]:
        """Find scheduled sync jobs."""
        jobs = await self.list_all()
        return [job for job in jobs if job.schedule is not None]
    
    async def find_running(self) -> List[SyncJob]:
        """Find running sync jobs."""
        return await self.find_by_status("running")
    
    def _from_dict(self, data: dict) -> SyncJob:
        """Convert dict to SyncJob entity."""
        from datetime import datetime
        
        # Convert ISO strings back to datetime
        for field in ("created_at", "started_at", "completed_at"):
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        return SyncJob(**data)

