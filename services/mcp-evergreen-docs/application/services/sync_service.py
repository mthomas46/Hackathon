"""Synchronization Application Service."""

from typing import List, Optional
import asyncio

from ...domain.entities.documentation import Documentation
from ...domain.entities.sync_job import SyncJob
from ...domain.repositories.documentation_repository import DocumentationRepository
from ...domain.repositories.sync_job_repository import SyncJobRepository


class SyncService:
    """
    Application service for synchronization operations.
    
    Orchestrates synchronization from external sources.
    """
    
    def __init__(
        self,
        doc_repo: DocumentationRepository,
        sync_job_repo: SyncJobRepository,
    ):
        """
        Initialize sync service.
        
        Args:
            doc_repo: Documentation repository
            sync_job_repo: Sync job repository
        """
        self.doc_repo = doc_repo
        self.sync_job_repo = sync_job_repo
    
    async def create_sync_job(
        self,
        name: str,
        source_type: str,
        source_config: dict,
        target_path: str,
        file_patterns: Optional[List[str]] = None,
    ) -> SyncJob:
        """
        Create new sync job.
        
        Args:
            name: Job name
            source_type: Source type (git, api, etc.)
            source_config: Source configuration
            target_path: Target directory path
            file_patterns: File patterns to sync
            
        Returns:
            Created sync job
        """
        job = SyncJob(
            name=name,
            source_type=source_type,
            source_config=source_config,
            target_path=target_path,
            file_patterns=file_patterns or ["*.md", "*.rst"],
        )
        
        await self.sync_job_repo.add(job)
        return job
    
    async def execute_sync_job(self, job_id: str) -> SyncJob:
        """
        Execute synchronization job.
        
        Args:
            job_id: Job ID
            
        Returns:
            Updated sync job
            
        Raises:
            ValueError: If job not found
        """
        job = await self.sync_job_repo.get_by_id(job_id)
        if not job:
            raise ValueError(f"Sync job not found: {job_id}")
        
        # Start job
        job.start()
        await self.sync_job_repo.update(job)
        
        try:
            # Get source-specific syncer
            # This would be injected in a real implementation
            # For now, just simulate sync
            
            # Update progress
            job.update_progress(25)
            await self.sync_job_repo.update(job)
            
            # Simulate syncing some docs
            await asyncio.sleep(0.1)
            job.increment_created()
            job.increment_created()
            
            job.update_progress(50)
            await self.sync_job_repo.update(job)
            
            # More syncing
            await asyncio.sleep(0.1)
            job.increment_updated()
            job.increment_skipped()
            
            job.update_progress(75)
            await self.sync_job_repo.update(job)
            
            # Complete
            job.update_progress(100)
            job.complete()
            await self.sync_job_repo.update(job)
            
        except Exception as e:
            job.fail(str(e))
            await self.sync_job_repo.update(job)
            raise
        
        return job
    
    async def get_sync_job(self, job_id: str) -> Optional[SyncJob]:
        """
        Get sync job by ID.
        
        Args:
            job_id: Job ID
            
        Returns:
            Sync job or None
        """
        return await self.sync_job_repo.get_by_id(job_id)
    
    async def list_sync_jobs(self) -> List[SyncJob]:
        """
        List all sync jobs.
        
        Returns:
            List of sync jobs
        """
        return await self.sync_job_repo.list_all()
    
    async def sync_documentation(
        self,
        source_type: str,
        source_url: str,
        target_path: str,
    ) -> Documentation:
        """
        Synchronize single documentation.
        
        Args:
            source_type: Source type
            source_url: Source URL
            target_path: Target file path
            
        Returns:
            Synchronized documentation
        """
        # Check if documentation exists
        existing = await self.doc_repo.find_by_path(target_path)
        
        # Fetch content (simulated)
        content = f"# Documentation from {source_url}\n\nSynced content..."
        
        if existing:
            # Update existing
            if existing.has_changed(content):
                existing.content = content
                existing.calculate_checksum()
                existing.mark_as_synced()
                existing.increment_version()
                await self.doc_repo.update(existing)
            else:
                existing.mark_as_synced()
                await self.doc_repo.update(existing)
            return existing
        else:
            # Create new
            doc = Documentation(
                title=target_path.split("/")[-1],
                file_path=target_path,
                content=content,
                source_type=source_type,
                source_url=source_url,
            )
            doc.calculate_checksum()
            doc.mark_as_synced()
            await self.doc_repo.add(doc)
            return doc

