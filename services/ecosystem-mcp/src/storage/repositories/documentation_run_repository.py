"""
Repository for documentation run operations.

Provides CRUD operations for tracking documentation generation runs and artifacts.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, update as sql_update, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models_documentation import DocumentationRunModel, DocumentationArtifactModel
from .base import BaseRepository


class DocumentationRunRepository(BaseRepository[DocumentationRunModel]):
    """
    Repository for documentation run operations.
    
    Handles creation, updates, and queries for documentation runs.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(session, DocumentationRunModel)
    
    async def create_run(
        self,
        plan_id: str,
        repo_id: str,
        status: str = "pending",
        total_passes: int = 5,
        config: Optional[dict] = None
    ) -> DocumentationRunModel:
        """
        Create new documentation run.
        
        Args:
            plan_id: Plan identifier
            repo_id: Repository identifier
            status: Initial status (default: pending)
            total_passes: Total number of passes (default: 5)
            config: Optional configuration
        
        Returns:
            Created run model
        """
        run = DocumentationRunModel(
            plan_id=plan_id,
            repo_id=repo_id,
            status=status,
            total_passes=total_passes,
            passes_completed=0,
            config=config or {},
            total_artifacts=0,
            total_words=0
        )
        return await self.create(run)
    
    async def get_by_plan_id(self, plan_id: str) -> Optional[DocumentationRunModel]:
        """
        Get run by plan ID.
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            Run model or None
        """
        result = await self.session.execute(
            select(DocumentationRunModel)
            .where(DocumentationRunModel.plan_id == plan_id)
            .options(selectinload(DocumentationRunModel.artifacts))
        )
        return result.scalar_one_or_none()
    
    async def get_by_repo_id(self, repo_id: str) -> List[DocumentationRunModel]:
        """
        Get all runs for a repository.
        
        Args:
            repo_id: Repository identifier
        
        Returns:
            List of run models
        """
        result = await self.session.execute(
            select(DocumentationRunModel)
            .where(DocumentationRunModel.repo_id == repo_id)
            .order_by(DocumentationRunModel.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def update_status(
        self,
        run_id: UUID,
        status: str,
        completed_at: Optional[datetime] = None
    ) -> bool:
        """
        Update run status.
        
        Args:
            run_id: Run UUID
            status: New status
            completed_at: Optional completion time
        
        Returns:
            True if updated successfully
        """
        values = {"status": status}
        if completed_at:
            values["completed_at"] = completed_at
        
        result = await self.session.execute(
            sql_update(DocumentationRunModel)
            .where(DocumentationRunModel.id == run_id)
            .values(**values)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def increment_passes(self, run_id: UUID) -> bool:
        """
        Increment completed passes count.
        
        Args:
            run_id: Run UUID
        
        Returns:
            True if updated successfully
        """
        result = await self.session.execute(
            sql_update(DocumentationRunModel)
            .where(DocumentationRunModel.id == run_id)
            .values(passes_completed=DocumentationRunModel.passes_completed + 1)
        )
        await self.session.flush()
        return result.rowcount > 0
    
    async def add_artifact(
        self,
        run_id: UUID,
        artifact_type: str,
        pass_number: int,
        pass_type: str,
        title: str,
        content: str,
        component_name: Optional[str] = None,
        format: str = "markdown",
        word_count: int = 0,
        quality_score: Optional[float] = None
    ) -> DocumentationArtifactModel:
        """
        Add artifact to run.
        
        Args:
            run_id: Run UUID
            artifact_type: Type of artifact
            pass_number: Pass number
            pass_type: Pass type
            title: Artifact title
            content: Artifact content
            component_name: Optional component name
            format: Content format (default: markdown)
            word_count: Word count (default: 0)
            quality_score: Optional quality score
        
        Returns:
            Created artifact model
        """
        artifact = DocumentationArtifactModel(
            run_id=run_id,
            artifact_type=artifact_type,
            pass_number=pass_number,
            pass_type=pass_type,
            component_name=component_name,
            title=title,
            content=content,
            format=format,
            word_count=word_count,
            quality_score=quality_score
        )
        
        self.session.add(artifact)
        await self.session.flush()
        
        # Update run totals using func.coalesce to handle NULL values
        await self.session.execute(
            sql_update(DocumentationRunModel)
            .where(DocumentationRunModel.id == run_id)
            .values(
                total_artifacts=func.coalesce(DocumentationRunModel.total_artifacts, 0) + 1,
                total_words=func.coalesce(DocumentationRunModel.total_words, 0) + word_count
            )
        )
        await self.session.flush()
        
        return artifact
    
    async def get_artifacts(self, run_id: UUID) -> List[DocumentationArtifactModel]:
        """
        Get all artifacts for a run.
        
        Args:
            run_id: Run UUID
        
        Returns:
            List of artifact models
        """
        result = await self.session.execute(
            select(DocumentationArtifactModel)
            .where(DocumentationArtifactModel.run_id == run_id)
            .order_by(DocumentationArtifactModel.pass_number, DocumentationArtifactModel.created_at)
        )
        return list(result.scalars().all())
    
    async def get_artifacts_by_type(
        self,
        run_id: UUID,
        artifact_type: str
    ) -> List[DocumentationArtifactModel]:
        """
        Get artifacts by type for a run.
        
        Args:
            run_id: Run UUID
            artifact_type: Artifact type
        
        Returns:
            List of artifact models
        """
        result = await self.session.execute(
            select(DocumentationArtifactModel)
            .where(
                DocumentationArtifactModel.run_id == run_id,
                DocumentationArtifactModel.artifact_type == artifact_type
            )
            .order_by(DocumentationArtifactModel.pass_number)
        )
        return list(result.scalars().all())
    
    async def get_run_statistics(self, run_id: UUID) -> dict:
        """
        Get statistics for a run.
        
        Args:
            run_id: Run UUID
        
        Returns:
            Dictionary with statistics
        """
        # Get artifact counts by type
        result = await self.session.execute(
            select(
                DocumentationArtifactModel.artifact_type,
                func.count(DocumentationArtifactModel.id).label('count'),
                func.sum(DocumentationArtifactModel.word_count).label('words'),
                func.avg(DocumentationArtifactModel.quality_score).label('avg_quality')
            )
            .where(DocumentationArtifactModel.run_id == run_id)
            .group_by(DocumentationArtifactModel.artifact_type)
        )
        
        by_type = {}
        for row in result:
            by_type[row.artifact_type] = {
                "count": row.count,
                "words": row.words or 0,
                "avg_quality": float(row.avg_quality) if row.avg_quality else None
            }
        
        # Get run info
        run = await self.get_by_id(run_id)
        
        return {
            "run_id": str(run_id),
            "status": run.status if run else None,
            "passes_completed": run.passes_completed if run else 0,
            "total_passes": run.total_passes if run else 0,
            "total_artifacts": run.total_artifacts if run else 0,
            "total_words": run.total_words if run else 0,
            "overall_quality_score": run.overall_quality_score if run else None,
            "by_type": by_type
        }
    
    async def list_runs(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentationRunModel]:
        """
        List documentation runs with optional filtering.
        
        Args:
            status: Optional status filter
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of run models
        """
        query = select(DocumentationRunModel)
        
        if status:
            query = query.where(DocumentationRunModel.status == status)
        
        query = query.order_by(DocumentationRunModel.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def delete_run(self, run_id: UUID) -> bool:
        """
        Delete a run and all its artifacts.
        
        Args:
            run_id: Run UUID
        
        Returns:
            True if deleted successfully
        """
        run = await self.get_by_id(run_id)
        if run:
            await self.delete(run)
            return True
        return False

