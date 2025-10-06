"""Create Job Use Case."""

import logging
import uuid

from services.training_coordinator.domain.entities.training_job import TrainingJob
from services.training_coordinator.domain.repositories.job_repository import JobRepository
from services.training_coordinator.application.dto.create_job_request import CreateJobRequest
from services.training_coordinator.application.dto.job_response import JobResponse
from services.training_coordinator.domain.value_objects.job_status import JobStatus

logger = logging.getLogger(__name__)


class CreateJobUseCase:
    """Use case for creating a new training job."""
    
    def __init__(self, job_repository: JobRepository):
        self.job_repo = job_repository
    
    async def execute(self, request: CreateJobRequest) -> JobResponse:
        """
        Create a new training job.
        
        Args:
            request: Create job request
        
        Returns:
            Job response
        """
        logger.info(f"Creating training job for MCP: {request.mcp_id}")
        
        # Create job entity
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        job = TrainingJob(
            job_id=job_id,
            mcp_id=request.mcp_id,
            name=request.name,
            description=request.description,
            status=JobStatus.PENDING,
            priority=request.priority,
            data_sources=request.data_sources,
            source_config=request.source_config,
            max_documents=request.max_documents,
            max_duration_seconds=request.max_duration_seconds,
            created_by=request.created_by,
            metadata=request.metadata,
        )
        
        # Save job
        await self.job_repo.save(job)
        logger.info(f"Created job: {job_id}")
        
        # Return response
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

