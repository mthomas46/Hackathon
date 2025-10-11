"""
Repository for ingestion job operations.

Provides CRUD operations for tracking document ingestion jobs.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db_models import IngestionJobModel
from .base import BaseRepository


class IngestionJobRepository(BaseRepository[IngestionJobModel]):
    """
    Repository for ingestion job operations.
    
    Handles creation, updates, and queries for ingestion jobs.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(IngestionJobModel, session)
    
    async def create_job(
        self,
        mode: str,
        status: str = "running",
        repo_path: Optional[str] = None
    ) -> IngestionJobModel:
        """
        Create new ingestion job.
        
        Args:
            mode: Ingestion mode (quick, full, etc.)
            status: Initial status (default: running)
            repo_path: Repository path if applicable
        
        Returns:
            Created job model
        """
        job = await self.create(
            mode=mode,
            status=status,
            repo_path=repo_path,
            total_documents=0,
            processed_documents=0,
            failed_documents=0,
            total_cost_usd=0.0
        )
        return job
    
    async def update_total(self, job_id: UUID, total: int) -> bool:
        """
        Update total document count for job.
        
        Args:
            job_id: Job UUID
            total: Total document count
        
        Returns:
            True if updated successfully
        """
        result = await self.session.execute(
            sql_update(IngestionJobModel)
            .where(IngestionJobModel.id == job_id)
            .values(total_documents=total)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def increment_processed(self, job_id: UUID) -> bool:
        """
        Increment processed document count.
        
        Args:
            job_id: Job UUID
        
        Returns:
            True if updated successfully
        """
        result = await self.session.execute(
            sql_update(IngestionJobModel)
            .where(IngestionJobModel.id == job_id)
            .values(processed_documents=IngestionJobModel.processed_documents + 1)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def increment_failed(self, job_id: UUID) -> bool:
        """
        Increment failed document count.
        
        Args:
            job_id: Job UUID
        
        Returns:
            True if updated successfully
        """
        result = await self.session.execute(
            sql_update(IngestionJobModel)
            .where(IngestionJobModel.id == job_id)
            .values(failed_documents=IngestionJobModel.failed_documents + 1)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def complete_job(
        self,
        job_id: UUID,
        total_cost: float = 0.0,
        summary: Optional[str] = None
    ) -> bool:
        """
        Mark job as completed.
        
        Args:
            job_id: Job UUID
            total_cost: Total cost in USD
            summary: Job summary message
        
        Returns:
            True if updated successfully
        """
        values = {
            "status": "completed",
            "completed_at": datetime.utcnow(),
            "total_cost_usd": total_cost
        }
        if summary:
            values["error_message"] = summary  # Reuse error_message for summary
        
        result = await self.session.execute(
            sql_update(IngestionJobModel)
            .where(IngestionJobModel.id == job_id)
            .values(**values)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def fail_job(self, job_id: UUID, error: str) -> bool:
        """
        Mark job as failed.
        
        Args:
            job_id: Job UUID
            error: Error message
        
        Returns:
            True if updated successfully
        """
        result = await self.session.execute(
            sql_update(IngestionJobModel)
            .where(IngestionJobModel.id == job_id)
            .values(
                status="failed",
                completed_at=datetime.utcnow(),
                error_message=error
            )
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_running_jobs(self) -> List[IngestionJobModel]:
        """
        Get all running jobs.
        
        Returns:
            List of running job models
        """
        result = await self.session.execute(
            select(IngestionJobModel)
            .where(IngestionJobModel.status == "running")
            .order_by(IngestionJobModel.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_recent_jobs(self, limit: int = 10) -> List[IngestionJobModel]:
        """
        Get recent jobs.
        
        Args:
            limit: Maximum number of jobs to return
        
        Returns:
            List of recent job models
        """
        result = await self.session.execute(
            select(IngestionJobModel)
            .order_by(IngestionJobModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

