"""Redis Job Repository Implementation."""

import json
import logging
from typing import List, Optional

import redis.asyncio as redis

from services.training_coordinator.domain.entities.training_job import TrainingJob
from services.training_coordinator.domain.repositories.job_repository import JobRepository
from services.training_coordinator.domain.value_objects.job_status import JobStatus
from services.training_coordinator.domain.value_objects.job_priority import JobPriority

logger = logging.getLogger(__name__)


class RedisJobRepository(JobRepository):
    """Redis implementation of JobRepository."""
    
    def __init__(self, redis_client: redis.Redis, key_prefix: str = "training:job:"):
        self.redis = redis_client
        self.key_prefix = key_prefix
    
    def _job_key(self, job_id: str) -> str:
        return f"{self.key_prefix}{job_id}"
    
    async def save(self, job: TrainingJob) -> None:
        """Save training job."""
        job_key = self._job_key(job.job_id)
        job_data = json.dumps(job.to_dict())
        await self.redis.set(job_key, job_data)
        
        # Add to status index
        status_key = f"{self.key_prefix}status:{job.status.value}"
        await self.redis.sadd(status_key, job.job_id)
        
        # Add to MCP index
        mcp_key = f"{self.key_prefix}mcp:{job.mcp_id}"
        await self.redis.sadd(mcp_key, job.job_id)
    
    async def get_by_id(self, job_id: str) -> Optional[TrainingJob]:
        """Get job by ID."""
        job_key = self._job_key(job_id)
        data = await self.redis.get(job_key)
        if not data:
            return None
        
        job_dict = json.loads(data)
        return self._from_dict(job_dict)
    
    async def get_by_mcp_id(self, mcp_id: str) -> List[TrainingJob]:
        """Get all jobs for an MCP."""
        mcp_key = f"{self.key_prefix}mcp:{mcp_id}"
        job_ids = await self.redis.smembers(mcp_key)
        
        jobs = []
        for job_id in job_ids:
            job = await self.get_by_id(job_id.decode())
            if job:
                jobs.append(job)
        return jobs
    
    async def list_by_status(self, status: JobStatus, limit: Optional[int] = None) -> List[TrainingJob]:
        """List jobs by status."""
        status_key = f"{self.key_prefix}status:{status.value}"
        job_ids = await self.redis.smembers(status_key)
        
        jobs = []
        for job_id in job_ids:
            job = await self.get_by_id(job_id.decode())
            if job:
                jobs.append(job)
                if limit and len(jobs) >= limit:
                    break
        return jobs
    
    async def list_pending_by_priority(self, limit: Optional[int] = None) -> List[TrainingJob]:
        """List pending jobs ordered by priority."""
        jobs = await self.list_by_status(JobStatus.PENDING)
        jobs.sort(key=lambda j: j.priority, reverse=True)
        return jobs[:limit] if limit else jobs
    
    async def list_active(self, limit: Optional[int] = None) -> List[TrainingJob]:
        """List active jobs."""
        active_jobs = []
        for status in [JobStatus.VALIDATING, JobStatus.EXTRACTING, JobStatus.NORMALIZING, JobStatus.EMBEDDING, JobStatus.STORING]:
            jobs = await self.list_by_status(status)
            active_jobs.extend(jobs)
        return active_jobs[:limit] if limit else active_jobs
    
    async def delete(self, job_id: str) -> bool:
        """Delete job."""
        job = await self.get_by_id(job_id)
        if not job:
            return False
        
        job_key = self._job_key(job_id)
        await self.redis.delete(job_key)
        return True
    
    async def count_by_status(self, status: JobStatus) -> int:
        """Count jobs by status."""
        status_key = f"{self.key_prefix}status:{status.value}"
        return await self.redis.scard(status_key)
    
    def _from_dict(self, data: dict) -> TrainingJob:
        """Convert dict to TrainingJob."""
        from datetime import datetime
        from services.training_coordinator.domain.value_objects.data_source import DataSource
        
        return TrainingJob(
            job_id=data["job_id"],
            mcp_id=data["mcp_id"],
            name=data["name"],
            description=data["description"],
            status=JobStatus(data["status"]),
            priority=JobPriority(data["priority"]),
            data_sources=[DataSource(ds) for ds in data["data_sources"]],
            source_config=data["source_config"],
            enable_extraction=data["enable_extraction"],
            enable_normalization=data["enable_normalization"],
            enable_embedding=data["enable_embedding"],
            enable_storage=data["enable_storage"],
            max_documents=data.get("max_documents"),
            max_duration_seconds=data.get("max_duration_seconds"),
            max_cost=data.get("max_cost"),
            progress_percentage=data["progress_percentage"],
            current_stage=data.get("current_stage"),
            documents_processed=data["documents_processed"],
            documents_total=data["documents_total"],
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            result_summary=data["result_summary"],
            error_message=data.get("error_message"),
            created_by=data["created_by"],
            metadata=data["metadata"],
        )

