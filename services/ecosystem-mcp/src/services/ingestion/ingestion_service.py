"""
Ingestion Service

High-level service for document ingestion operations.
Wraps JobProcessor and provides a clean interface for tests and API routes.
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from uuid import UUID

from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from ...storage.db_models import IngestionJobModel
from .job_processor import JobProcessor
from .job_processor_router import JobProcessorRouter

logger = logging.getLogger(__name__)


class IngestionService:
    """
    High-level ingestion service.
    
    Provides:
    - Job creation and management
    - Document ingestion coordination
    - Progress tracking
    - Error handling
    
    Wraps existing JobProcessor infrastructure.
    """
    
    def __init__(self):
        """Initialize ingestion service."""
        self.processor = JobProcessor()
        logger.info("IngestionService initialized")
    
    async def create_job(
        self,
        repo_path: str,
        mode: str = "standard",
        metadata: Optional[Dict[str, Any]] = None
    ) -> IngestionJobModel:
        """
        Create a new ingestion job.
        
        Args:
            repo_path: Path to repository
            mode: Ingestion mode (standard, snapshot, etc.)
            metadata: Optional job metadata
        
        Returns:
            Created job model
        """
        logger.info(f"Creating ingestion job: repo={repo_path}, mode={mode}")
        
        db = get_database()
        async with db.session() as session:
            job_repo = IngestionJobRepository(session)
            job = await job_repo.create_job(
                mode=mode,
                status="pending",
                repo_path=repo_path,
                job_metadata=metadata or {}
            )
            await session.commit()
            logger.info(f"✅ Created ingestion job: {job.id}")
            return job
    
    async def process_job(self, job: IngestionJobModel) -> Dict[str, Any]:
        """
        Process an ingestion job.
        
        Args:
            job: Ingestion job to process
        
        Returns:
            Processing result
        """
        logger.info(f"Processing ingestion job: {job.id}")
        
        try:
            # Route to appropriate processor
            result = await JobProcessorRouter.process(job)
            logger.info(f"✅ Completed ingestion job: {job.id}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to process job {job.id}: {e}")
            raise
    
    async def get_job(self, job_id: UUID) -> Optional[IngestionJobModel]:
        """
        Get job by ID.
        
        Args:
            job_id: Job UUID
        
        Returns:
            Job model or None
        """
        db = get_database()
        async with db.session() as session:
            job_repo = IngestionJobRepository(session)
            return await job_repo.get_by_id(job_id)
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[IngestionJobModel]:
        """
        List ingestion jobs.
        
        Args:
            status: Optional status filter
            limit: Max results
        
        Returns:
            List of jobs
        """
        db = get_database()
        async with db.session() as session:
            job_repo = IngestionJobRepository(session)
            
            # Get all jobs (repository doesn't have list method, so we query directly)
            from sqlalchemy import select
            from ...storage.db_models import IngestionJobModel as JobModel
            
            query = select(JobModel).order_by(JobModel.created_at.desc()).limit(limit)
            
            if status:
                query = query.where(JobModel.status == status)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def cancel_job(self, job_id: UUID) -> bool:
        """
        Cancel a job.
        
        Args:
            job_id: Job UUID
        
        Returns:
            True if cancelled
        """
        logger.info(f"Cancelling job: {job_id}")
        
        db = get_database()
        async with db.session() as session:
            job_repo = IngestionJobRepository(session)
            success = await job_repo.update_status(job_id, "cancelled")
            await session.commit()
            
            if success:
                logger.info(f"✅ Cancelled job: {job_id}")
            else:
                logger.warning(f"⚠️ Failed to cancel job: {job_id}")
            
            return success
    
    async def ingest(
        self,
        repo_path: str,
        mode: str = "standard",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest documents from a repository (convenience method).
        
        Args:
            repo_path: Path to repository
            mode: Ingestion mode
            metadata: Optional metadata
        
        Returns:
            Ingestion result
        """
        logger.info(f"Starting ingestion: repo={repo_path}, mode={mode}")
        
        # Create job
        job = await self.create_job(repo_path, mode, metadata)
        
        # Process job
        result = await self.process_job(job)
        
        return result


# Singleton instance
_ingestion_service: Optional[IngestionService] = None


def get_ingestion_service() -> IngestionService:
    """Get singleton ingestion service."""
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = IngestionService()
    return _ingestion_service

