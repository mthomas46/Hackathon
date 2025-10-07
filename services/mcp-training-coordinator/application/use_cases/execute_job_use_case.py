"""Execute Job Use Case."""

import logging

from services.training_coordinator.domain.repositories.job_repository import JobRepository
from services.training_coordinator.application.dto.execute_job_request import ExecuteJobRequest
from services.training_coordinator.application.dto.job_response import JobResponse
from services.training_coordinator.domain.value_objects.job_status import JobStatus

logger = logging.getLogger(__name__)


class ExecuteJobUseCase:
    """Use case for executing a training job."""
    
    def __init__(self, job_repository: JobRepository):
        self.job_repo = job_repository
    
    async def execute(self, request: ExecuteJobRequest) -> JobResponse:
        """
        Execute a training job.
        
        Args:
            request: Execute job request
        
        Returns:
            Job response
        """
        logger.info(f"Executing job: {request.job_id}")
        
        # Get job
        job = await self.job_repo.get_by_id(request.job_id)
        if not job:
            raise ValueError(f"Job not found: {request.job_id}")
        
        # Update status to validating
        job.update_status(JobStatus.VALIDATING)
        await self.job_repo.save(job)
        
        # TODO: Trigger async execution via Celery
        # For now, just mark as started
        logger.info(f"Job {request.job_id} execution triggered (async={request.async_execution})")
        
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

