"""
Documentation Run Manager

Manages documentation generation runs, including creation, tracking,
artifact association, and lifecycle management.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.models_documentation import DocumentationRunModel as DBDocumentationRunModel
from ...storage.models_documentation import DocumentationArtifactModel as DBDocumentationArtifactModel
from ...storage.repositories import DocumentationRunRepository

logger = logging.getLogger(__name__)


class DocumentationRunManager:
    """
    Manages documentation generation runs.
    
    Features:
    - Run creation and lifecycle management
    - Artifact association
    - Status tracking
    - Metadata management
    - Query and retrieval
    """
    
    def __init__(self, session: AsyncSession, repository: Optional[DocumentationRunRepository] = None):
        """
        Initialize documentation run manager.
        
        Args:
            session: Database session
            repository: Optional repository (creates if not provided)
        """
        self.session = session
        self.repository = repository or DocumentationRunRepository(session)
        logger.info("DocumentationRunManager initialized")
    
    async def create_run(
        self,
        repo_path: str,
        config: Dict[str, Any],
        snapshot_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        test_session_id: Optional[str] = None
    ) -> DBDocumentationRunModel:
        """
        Create a new documentation run.
        
        Args:
            repo_path: Repository path
            config: Run configuration
            snapshot_id: Optional snapshot ID
            metadata: Optional metadata
            test_session_id: Optional test session ID
        
        Returns:
            Created run model
        """
        logger.info(f"Creating documentation run: repo={repo_path}")
        
        # Prepare metadata
        run_metadata = metadata or {}
        if snapshot_id:
            run_metadata["snapshot_id"] = snapshot_id
        if test_session_id:
            run_metadata["test_session_id"] = test_session_id
        
        # Generate plan_id and repo_id from repo_path
        plan_id = snapshot_id or str(uuid4())
        repo_id = repo_path  # Use repo_path as repo_id
        
        # Extract total_passes from config
        total_passes = config.get("passes", 5)
        
        # Create run using actual repository API
        run = await self.repository.create_run(
            plan_id=plan_id,
            repo_id=repo_id,
            status="pending",
            total_passes=total_passes,
            config=config
        )
        
        # Update metadata if provided
        if run_metadata:
            run.metadata = run_metadata
            await self.session.flush()
        
        await self.session.commit()
        logger.info(f"✅ Created documentation run: {run.id}")
        
        return run
    
    async def get_run(self, run_id: UUID) -> Optional[DBDocumentationRunModel]:
        """
        Get run by ID.
        
        Args:
            run_id: Run UUID
        
        Returns:
            Run model or None
        """
        return await self.repository.get_by_id(run_id)
    
    async def get_runs_by_repo(
        self,
        repo_path: str,
        limit: int = 100
    ) -> List[DBDocumentationRunModel]:
        """
        Get runs by repository path.
        
        Args:
            repo_path: Repository path
            limit: Max results
        
        Returns:
            List of runs
        """
        return await self.repository.get_by_repo_id(repo_path)
    
    async def get_runs_by_snapshot(
        self,
        snapshot_id: str
    ) -> List[DBDocumentationRunModel]:
        """
        Get runs by snapshot ID.
        
        Args:
            snapshot_id: Snapshot ID
        
        Returns:
            List of runs
        """
        return await self.repository.get_runs_by_snapshot(snapshot_id)
    
    async def update_status(
        self,
        run_id: UUID,
        status: str,
        error_message: Optional[str] = None
    ) -> bool:
        """
        Update run status.
        
        Args:
            run_id: Run UUID
            status: New status
            error_message: Optional error message
        
        Returns:
            True if updated
        """
        logger.info(f"Updating run status: {run_id} -> {status}")
        
        success = await self.repository.update_status(
            run_id=run_id,
            status=status,
            error_message=error_message
        )
        
        await self.session.commit()
        
        if success:
            logger.info(f"✅ Updated run status: {run_id}")
        else:
            logger.warning(f"⚠️ Failed to update run status: {run_id}")
        
        return success
    
    async def add_artifact(
        self,
        run_id: UUID,
        document_type: str,
        file_path: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DBDocumentationArtifactModel:
        """
        Add artifact to run.
        
        Args:
            run_id: Run UUID
            document_type: Document type
            file_path: File path
            content: Document content
            metadata: Optional metadata
        
        Returns:
            Created artifact
        """
        logger.info(f"Adding artifact to run: {run_id} - {document_type}")
        
        artifact = await self.repository.add_artifact(
            run_id=run_id,
            document_type=document_type,
            file_path=file_path,
            content=content,
            metadata=metadata or {}
        )
        
        await self.session.commit()
        logger.info(f"✅ Added artifact: {artifact.id}")
        
        return artifact
    
    async def get_artifacts(
        self,
        run_id: UUID
    ) -> List[DBDocumentationArtifactModel]:
        """
        Get artifacts for run.
        
        Args:
            run_id: Run UUID
        
        Returns:
            List of artifacts
        """
        return await self.repository.get_artifacts(run_id)
    
    async def get_artifact(
        self,
        artifact_id: UUID
    ) -> Optional[DBDocumentationArtifactModel]:
        """
        Get artifact by ID.
        
        Args:
            artifact_id: Artifact UUID
        
        Returns:
            Artifact or None
        """
        return await self.repository.get_artifact(artifact_id)
    
    async def update_metadata(
        self,
        run_id: UUID,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update run metadata.
        
        Args:
            run_id: Run UUID
            metadata: New metadata
        
        Returns:
            True if updated
        """
        logger.info(f"Updating run metadata: {run_id}")
        
        success = await self.repository.update_metadata(run_id, metadata)
        await self.session.commit()
        
        return success
    
    async def delete_run(self, run_id: UUID) -> bool:
        """
        Delete run and its artifacts.
        
        Args:
            run_id: Run UUID
        
        Returns:
            True if deleted
        """
        logger.info(f"Deleting run: {run_id}")
        
        success = await self.repository.delete_run(run_id)
        await self.session.commit()
        
        if success:
            logger.info(f"✅ Deleted run: {run_id}")
        else:
            logger.warning(f"⚠️ Failed to delete run: {run_id}")
        
        return success
    
    async def get_run_statistics(self, run_id: UUID) -> Dict[str, Any]:
        """
        Get statistics for a run.
        
        Args:
            run_id: Run UUID
        
        Returns:
            Statistics dictionary
        """
        return await self.repository.get_run_statistics(run_id)


# Singleton instance (optional)
_run_manager: Optional[DocumentationRunManager] = None


def get_run_manager(
    session: AsyncSession,
    repository: Optional[DocumentationRunRepository] = None
) -> DocumentationRunManager:
    """
    Get documentation run manager.
    
    Args:
        session: Database session
        repository: Optional repository
    
    Returns:
        DocumentationRunManager instance
    """
    return DocumentationRunManager(session, repository)
