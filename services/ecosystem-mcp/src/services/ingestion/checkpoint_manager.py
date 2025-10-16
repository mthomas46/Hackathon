"""
Checkpoint Manager for Job Recovery

Manages checkpoint creation, loading, and job resumption after interruptions.
Enables workers to resume processing from where they left off.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID

from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from sqlalchemy.orm.attributes import flag_modified

logger = logging.getLogger(__name__)


class Checkpoint:
    """Represents a job checkpoint."""
    
    def __init__(
        self,
        job_id: UUID,
        commit_sha: str,
        processed_files: List[str],
        current_file_index: int,
        total_files: int,
        processed_count: int,
        skipped_count: int,
        failed_count: int,
        embeddings_count: int,
        checkpoint_time: datetime
    ):
        self.job_id = job_id
        self.commit_sha = commit_sha
        self.processed_files = processed_files
        self.current_file_index = current_file_index
        self.total_files = total_files
        self.processed_count = processed_count
        self.skipped_count = skipped_count
        self.failed_count = failed_count
        self.embeddings_count = embeddings_count
        self.checkpoint_time = checkpoint_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary for storage."""
        return {
            "job_id": str(self.job_id),
            "commit_sha": self.commit_sha,
            "processed_files": self.processed_files,
            "current_file_index": self.current_file_index,
            "total_files": self.total_files,
            "processed_count": self.processed_count,
            "skipped_count": self.skipped_count,
            "failed_count": self.failed_count,
            "embeddings_count": self.embeddings_count,
            "checkpoint_time": self.checkpoint_time.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Checkpoint':
        """Create checkpoint from dictionary."""
        return cls(
            job_id=UUID(data["job_id"]),
            commit_sha=data["commit_sha"],
            processed_files=data.get("processed_files", []),
            current_file_index=data.get("current_file_index", 0),
            total_files=data.get("total_files", 0),
            processed_count=data.get("processed_count", 0),
            skipped_count=data.get("skipped_count", 0),
            failed_count=data.get("failed_count", 0),
            embeddings_count=data.get("embeddings_count", 0),
            checkpoint_time=datetime.fromisoformat(data["checkpoint_time"])
        )


class CheckpointManager:
    """
    Manages checkpoints for job recovery.
    
    Features:
    - Save checkpoint every N files
    - Load checkpoint on job resume
    - Skip already-processed files
    - Track resume count
    - Validate checkpoint integrity
    """
    
    def __init__(self, checkpoint_interval: int = 50):
        """
        Initialize checkpoint manager.
        
        Args:
            checkpoint_interval: Save checkpoint every N files
        """
        self.checkpoint_interval = checkpoint_interval
        logger.info(f"CheckpointManager initialized (interval: {checkpoint_interval} files)")
    
    async def save_checkpoint(
        self,
        job_id: UUID,
        commit_sha: str,
        processed_files: List[str],
        current_file_index: int,
        total_files: int,
        processed_count: int,
        skipped_count: int,
        failed_count: int,
        embeddings_count: int
    ) -> bool:
        """
        Save a checkpoint for the job.
        
        Args:
            job_id: Job UUID
            commit_sha: Current commit being processed
            processed_files: List of processed file paths
            current_file_index: Current position in file list
            total_files: Total files to process
            processed_count: Total files processed
            skipped_count: Total files skipped
            failed_count: Total files failed
            embeddings_count: Total embeddings generated
        
        Returns:
            True if checkpoint saved successfully
        """
        try:
            checkpoint = Checkpoint(
                job_id=job_id,
                commit_sha=commit_sha,
                processed_files=processed_files,
                current_file_index=current_file_index,
                total_files=total_files,
                processed_count=processed_count,
                skipped_count=skipped_count,
                failed_count=failed_count,
                embeddings_count=embeddings_count,
                checkpoint_time=datetime.utcnow()
            )
            
            # Save to database
            db = get_database()
            async with db.session() as session:
                repo = IngestionJobRepository(session)
                job = await repo.get_by_id(job_id)
                
                if not job:
                    logger.error(f"Job {job_id} not found for checkpoint")
                    return False
                
                # Update job metadata with checkpoint
                metadata = job.job_metadata.copy() if job.job_metadata else {}
                metadata['checkpoint'] = checkpoint.to_dict()
                metadata['checkpoint_count'] = metadata.get('checkpoint_count', 0) + 1
                metadata['last_checkpoint_at'] = datetime.utcnow().isoformat()
                
                job.job_metadata = metadata
                flag_modified(job, 'job_metadata')
                
                await repo.update(job)
                await session.commit()
                
                logger.info(
                    f"💾 Checkpoint saved for job {job_id}: "
                    f"{current_file_index}/{total_files} files "
                    f"({processed_count} processed, {skipped_count} skipped, {failed_count} failed)"
                )
                return True
        
        except Exception as e:
            logger.error(f"Failed to save checkpoint for job {job_id}: {e}", exc_info=True)
            return False
    
    async def load_checkpoint(self, job_id: UUID) -> Optional[Checkpoint]:
        """
        Load checkpoint for a job.
        
        Args:
            job_id: Job UUID
        
        Returns:
            Checkpoint if exists, None otherwise
        """
        try:
            db = get_database()
            async with db.session() as session:
                repo = IngestionJobRepository(session)
                job = await repo.get_by_id(job_id)
                
                if not job or not job.job_metadata:
                    return None
                
                checkpoint_data = job.job_metadata.get('checkpoint')
                if not checkpoint_data:
                    return None
                
                checkpoint = Checkpoint.from_dict(checkpoint_data)
                
                logger.info(
                    f"📂 Loaded checkpoint for job {job_id}: "
                    f"position {checkpoint.current_file_index}/{checkpoint.total_files}"
                )
                
                return checkpoint
        
        except Exception as e:
            logger.error(f"Failed to load checkpoint for job {job_id}: {e}", exc_info=True)
            return None
    
    async def should_resume(self, job_id: UUID) -> bool:
        """
        Check if job should be resumed from checkpoint.
        
        Args:
            job_id: Job UUID
        
        Returns:
            True if job has valid checkpoint and should resume
        """
        try:
            checkpoint = await self.load_checkpoint(job_id)
            if not checkpoint:
                return False
            
            # Check if checkpoint is recent enough (within last 24 hours)
            age = datetime.utcnow() - checkpoint.checkpoint_time
            if age.total_seconds() > 24 * 3600:
                logger.warning(
                    f"Checkpoint for job {job_id} is too old "
                    f"({age.total_seconds() / 3600:.1f} hours), skipping resume"
                )
                return False
            
            # Check if there's meaningful progress to resume from
            if checkpoint.current_file_index < 10:
                logger.info(
                    f"Checkpoint for job {job_id} has minimal progress "
                    f"({checkpoint.current_file_index} files), starting fresh"
                )
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error checking resume status for job {job_id}: {e}")
            return False
    
    async def mark_resumed(self, job_id: UUID):
        """
        Mark job as resumed from checkpoint.
        
        Args:
            job_id: Job UUID
        """
        try:
            db = get_database()
            async with db.session() as session:
                repo = IngestionJobRepository(session)
                job = await repo.get_by_id(job_id)
                
                if job and job.job_metadata:
                    metadata = job.job_metadata.copy()
                    metadata['resumed_at'] = datetime.utcnow().isoformat()
                    metadata['resume_count'] = metadata.get('resume_count', 0) + 1
                    
                    job.job_metadata = metadata
                    flag_modified(job, 'job_metadata')
                    
                    await repo.update(job)
                    await session.commit()
                    
                    logger.info(f"✅ Job {job_id} marked as resumed (count: {metadata['resume_count']})")
        
        except Exception as e:
            logger.error(f"Failed to mark job {job_id} as resumed: {e}")
    
    async def clear_checkpoint(self, job_id: UUID):
        """
        Clear checkpoint after job completion.
        
        Args:
            job_id: Job UUID
        """
        try:
            db = get_database()
            async with db.session() as session:
                repo = IngestionJobRepository(session)
                job = await repo.get_by_id(job_id)
                
                if job and job.job_metadata:
                    metadata = job.job_metadata.copy()
                    if 'checkpoint' in metadata:
                        del metadata['checkpoint']
                        metadata['checkpoint_cleared_at'] = datetime.utcnow().isoformat()
                        
                        job.job_metadata = metadata
                        flag_modified(job, 'job_metadata')
                        
                        await repo.update(job)
                        await session.commit()
                        
                        logger.info(f"🗑️  Checkpoint cleared for job {job_id}")
        
        except Exception as e:
            logger.error(f"Failed to clear checkpoint for job {job_id}: {e}")
    
    def should_save_checkpoint(self, current_index: int) -> bool:
        """
        Check if checkpoint should be saved at current position.
        
        Args:
            current_index: Current file index
        
        Returns:
            True if checkpoint should be saved
        """
        return current_index > 0 and current_index % self.checkpoint_interval == 0
    
    def get_resume_info(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        """
        Get human-readable resume information.
        
        Args:
            checkpoint: Checkpoint to describe
        
        Returns:
            Dict with resume information
        """
        progress_pct = (checkpoint.current_file_index / checkpoint.total_files * 100) if checkpoint.total_files > 0 else 0
        
        return {
            "resume_from_file": checkpoint.current_file_index,
            "total_files": checkpoint.total_files,
            "progress_percent": round(progress_pct, 1),
            "processed": checkpoint.processed_count,
            "skipped": checkpoint.skipped_count,
            "failed": checkpoint.failed_count,
            "embeddings": checkpoint.embeddings_count,
            "checkpoint_age_seconds": (datetime.utcnow() - checkpoint.checkpoint_time).total_seconds(),
            "files_to_skip": len(checkpoint.processed_files)
        }


# Global singleton instance
_checkpoint_manager: Optional[CheckpointManager] = None


def get_checkpoint_manager(checkpoint_interval: int = 50) -> CheckpointManager:
    """
    Get the global checkpoint manager instance.
    
    Args:
        checkpoint_interval: Save checkpoint every N files
    
    Returns:
        CheckpointManager instance
    """
    global _checkpoint_manager
    
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager(checkpoint_interval)
    
    return _checkpoint_manager

