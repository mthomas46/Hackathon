"""Get Job Use Case."""

import logging
from typing import List, Optional

from services.training_coordinator.domain.repositories.job_repository import JobRepository
from services.training_coordinator.application.dto.job_response import JobResponse
from services.training_coordinator.domain.value_objects.job_status import JobStatus

logger = logging.getLogger(__name__)


class GetJobUseCase:
    """Use case for retrieving training jobs."""
    
    def __init__(self, job_repository: JobRepository):
        self.job_repo = job_repository
    
    async def get_by_id(self, job_id: str) -> Optional[JobResponse]:
        """Get job by ID."""
        job = await self.job_repo.get_by_id(job_id)
        if not job:
            return None
        
        return JobResponse(
            job_id=job.job_id,
            mcp_id=job.mcp_id,
            name=job.name,
            description=job.description,
            status=job.status.value,
            priority=job.priority.value,
            progress_percentage=job.progress_percentage,
            current_stage=job.current_stage,
            documents_processed=job.documents_processed,
            documents_total=job.documents_total,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            duration_seconds=job.get_duration_seconds(),
            created_by=job.created_by,
            metadata=job.metadata,
        )
    
    async def list_by_mcp(self, mcp_id: str) -> List[JobResponse]:
        """List jobs for an MCP."""
        jobs = await self.job_repo.get_by_mcp_id(mcp_id)
        return [self._to_response(job) for job in jobs]
    
    async def list_active(self, limit: Optional[int] = None) -> List[JobResponse]:
        """List active jobs."""
        jobs = await self.job_repo.list_active(limit)
        return [self._to_response(job) for job in jobs]
    
    def _to_response(self, job) -> JobResponse:
        """Convert job to response."""
        return JobResponse(
            job_id=job.job_id,
            mcp_id=job.mcp_id,
            name=job.name,
            description=job.description,
            status=job.status.value,
            priority=job.priority.value,
            progress_percentage=job.progress_percentage,
            current_stage=job.current_stage,
            documents_processed=job.documents_processed,
            documents_total=job.documents_total,
            created_at=job.created_at.isoformat(),
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            duration_seconds=job.get_duration_seconds(),
            created_by=job.created_by,
            metadata=job.metadata,
        )

