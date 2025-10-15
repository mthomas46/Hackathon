"""
Job Recovery System

Provides checkpoint management, state persistence, and graceful resumption
for long-running jobs (ingestion, embeddings, documentation).

Features:
- Automatic checkpoint creation
- State persistence to database
- Graceful interruption handling
- Resume from last checkpoint
- Progress recovery
- Idempotent operations
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class JobType(str, Enum):
    """Types of recoverable jobs."""
    INGESTION = "ingestion"
    EMBEDDING = "embedding"
    DOCUMENTATION = "documentation"


class CheckpointStatus(str, Enum):
    """Checkpoint status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class JobCheckpoint:
    """
    Represents a checkpoint in job execution.
    
    Attributes:
        job_id: Unique job identifier
        job_type: Type of job
        checkpoint_id: Unique checkpoint identifier
        sequence: Checkpoint sequence number
        status: Current status
        data: Checkpoint-specific data
        created_at: Checkpoint creation time
        completed_at: Checkpoint completion time
    """
    
    def __init__(
        self,
        job_id: str,
        job_type: JobType,
        checkpoint_id: str,
        sequence: int,
        status: CheckpointStatus = CheckpointStatus.PENDING,
        data: Optional[Dict[str, Any]] = None
    ):
        self.job_id = job_id
        self.job_type = job_type
        self.checkpoint_id = checkpoint_id
        self.sequence = sequence
        self.status = status
        self.data = data or {}
        self.created_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert checkpoint to dictionary."""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type.value,
            "checkpoint_id": self.checkpoint_id,
            "sequence": self.sequence,
            "status": self.status.value,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobCheckpoint':
        """Create checkpoint from dictionary."""
        checkpoint = cls(
            job_id=data["job_id"],
            job_type=JobType(data["job_type"]),
            checkpoint_id=data["checkpoint_id"],
            sequence=data["sequence"],
            status=CheckpointStatus(data["status"]),
            data=data.get("data", {})
        )
        
        if data.get("created_at"):
            checkpoint.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            checkpoint.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return checkpoint


class JobRecoveryManager:
    """
    Manages job state persistence and recovery.
    
    Features:
    - Create checkpoints at key intervals
    - Persist state to database
    - Detect interrupted jobs
    - Resume from last checkpoint
    - Clean up completed checkpoints
    """
    
    def __init__(self, db_session):
        """
        Initialize recovery manager.
        
        Args:
            db_session: Database session for persistence
        """
        self.db = db_session
        self.checkpoints: Dict[str, List[JobCheckpoint]] = {}
    
    async def create_checkpoint(
        self,
        job_id: str,
        job_type: JobType,
        checkpoint_id: str,
        data: Dict[str, Any]
    ) -> JobCheckpoint:
        """
        Create a new checkpoint.
        
        Args:
            job_id: Job identifier
            job_type: Type of job
            checkpoint_id: Unique checkpoint identifier
            data: Checkpoint data
        
        Returns:
            Created checkpoint
        """
        # Get existing checkpoints for this job
        job_checkpoints = self.checkpoints.get(job_id, [])
        sequence = len(job_checkpoints)
        
        # Create new checkpoint
        checkpoint = JobCheckpoint(
            job_id=job_id,
            job_type=job_type,
            checkpoint_id=checkpoint_id,
            sequence=sequence,
            data=data
        )
        
        # Store in memory
        job_checkpoints.append(checkpoint)
        self.checkpoints[job_id] = job_checkpoints
        
        # Persist to database
        await self._persist_checkpoint(checkpoint)
        
        logger.info(
            f"📌 Checkpoint created: job={job_id}, "
            f"checkpoint={checkpoint_id}, sequence={sequence}"
        )
        
        return checkpoint
    
    async def update_checkpoint_status(
        self,
        job_id: str,
        checkpoint_id: str,
        status: CheckpointStatus,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Update checkpoint status.
        
        Args:
            job_id: Job identifier
            checkpoint_id: Checkpoint identifier
            status: New status
            data: Optional updated data
        """
        job_checkpoints = self.checkpoints.get(job_id, [])
        
        for checkpoint in job_checkpoints:
            if checkpoint.checkpoint_id == checkpoint_id:
                checkpoint.status = status
                
                if data:
                    checkpoint.data.update(data)
                
                if status == CheckpointStatus.COMPLETED:
                    checkpoint.completed_at = datetime.utcnow()
                
                # Persist update
                await self._persist_checkpoint(checkpoint)
                
                logger.info(
                    f"✅ Checkpoint updated: job={job_id}, "
                    f"checkpoint={checkpoint_id}, status={status.value}"
                )
                break
    
    async def get_last_checkpoint(
        self,
        job_id: str,
        status: Optional[CheckpointStatus] = None
    ) -> Optional[JobCheckpoint]:
        """
        Get the last checkpoint for a job.
        
        Args:
            job_id: Job identifier
            status: Optional status filter
        
        Returns:
            Last checkpoint or None
        """
        job_checkpoints = self.checkpoints.get(job_id, [])
        
        if status:
            job_checkpoints = [
                cp for cp in job_checkpoints
                if cp.status == status
            ]
        
        return job_checkpoints[-1] if job_checkpoints else None
    
    async def get_incomplete_checkpoints(
        self,
        job_id: str
    ) -> List[JobCheckpoint]:
        """
        Get all incomplete checkpoints for a job.
        
        Args:
            job_id: Job identifier
        
        Returns:
            List of incomplete checkpoints
        """
        job_checkpoints = self.checkpoints.get(job_id, [])
        
        return [
            cp for cp in job_checkpoints
            if cp.status in [CheckpointStatus.PENDING, CheckpointStatus.IN_PROGRESS]
        ]
    
    async def can_resume(self, job_id: str) -> bool:
        """
        Check if a job can be resumed.
        
        Args:
            job_id: Job identifier
        
        Returns:
            True if job has checkpoints and can resume
        """
        job_checkpoints = self.checkpoints.get(job_id, [])
        
        if not job_checkpoints:
            return False
        
        # Job can resume if it has completed checkpoints
        completed = [
            cp for cp in job_checkpoints
            if cp.status == CheckpointStatus.COMPLETED
        ]
        
        return len(completed) > 0
    
    async def get_resume_state(self, job_id: str) -> Dict[str, Any]:
        """
        Get state for resuming a job.
        
        Args:
            job_id: Job identifier
        
        Returns:
            Resume state with last checkpoint data
        """
        last_completed = await self.get_last_checkpoint(
            job_id,
            status=CheckpointStatus.COMPLETED
        )
        
        if not last_completed:
            return {
                "can_resume": False,
                "reason": "No completed checkpoints found"
            }
        
        incomplete = await self.get_incomplete_checkpoints(job_id)
        
        return {
            "can_resume": True,
            "last_checkpoint": last_completed.to_dict(),
            "resume_from_sequence": last_completed.sequence + 1,
            "incomplete_count": len(incomplete),
            "progress": {
                "completed_checkpoints": last_completed.sequence + 1,
                "total_checkpoints": len(self.checkpoints.get(job_id, []))
            }
        }
    
    async def cleanup_checkpoints(
        self,
        job_id: str,
        keep_last: int = 3
    ):
        """
        Clean up old checkpoints, keeping only recent ones.
        
        Args:
            job_id: Job identifier
            keep_last: Number of recent checkpoints to keep
        """
        job_checkpoints = self.checkpoints.get(job_id, [])
        
        if len(job_checkpoints) <= keep_last:
            return
        
        # Keep only the last N checkpoints
        to_remove = job_checkpoints[:-keep_last]
        self.checkpoints[job_id] = job_checkpoints[-keep_last:]
        
        # Remove from database
        for checkpoint in to_remove:
            await self._delete_checkpoint(checkpoint)
        
        logger.info(
            f"🧹 Cleaned up {len(to_remove)} old checkpoints for job {job_id}"
        )
    
    async def _persist_checkpoint(self, checkpoint: JobCheckpoint):
        """Persist checkpoint to database."""
        # Store checkpoint in job metadata
        from ..storage.repositories import IngestionJobRepository
        
        # Update job metadata with checkpoint info
        job_repo = IngestionJobRepository(self.db)
        
        try:
            job = await job_repo.get_by_id(checkpoint.job_id)
            
            if job:
                if not job.job_metadata:
                    job.job_metadata = {}
                
                # Store checkpoints in metadata
                if "checkpoints" not in job.job_metadata:
                    job.job_metadata["checkpoints"] = []
                
                job.job_metadata["checkpoints"].append(checkpoint.to_dict())
                
                # Mark as modified
                from sqlalchemy import update
                from ..storage.db_models import IngestionJobModel
                
                stmt = update(IngestionJobModel).where(
                    IngestionJobModel.id == checkpoint.job_id
                ).values(
                    job_metadata=job.job_metadata
                )
                
                await self.db.execute(stmt)
                await self.db.commit()
                
                logger.debug(f"💾 Persisted checkpoint {checkpoint.checkpoint_id}")
        
        except Exception as e:
            logger.error(f"Failed to persist checkpoint: {e}")
    
    async def _delete_checkpoint(self, checkpoint: JobCheckpoint):
        """Delete checkpoint from database."""
        from ..storage.repositories import IngestionJobRepository
        
        try:
            job_repo = IngestionJobRepository(self.db)
            job = await job_repo.get_by_id(checkpoint.job_id)
            
            if job and job.job_metadata and "checkpoints" in job.job_metadata:
                # Remove checkpoint from metadata
                job.job_metadata["checkpoints"] = [
                    cp for cp in job.job_metadata["checkpoints"]
                    if cp["checkpoint_id"] != checkpoint.checkpoint_id
                ]
                
                from sqlalchemy import update
                from ..storage.db_models import IngestionJobModel
                
                stmt = update(IngestionJobModel).where(
                    IngestionJobModel.id == checkpoint.job_id
                ).values(
                    job_metadata=job.job_metadata
                )
                
                await self.db.execute(stmt)
                await self.db.commit()
        
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
    
    async def load_checkpoints(self, job_id: str):
        """
        Load checkpoints from database for a job.
        
        Args:
            job_id: Job identifier
        """
        from ..storage.repositories import IngestionJobRepository
        
        try:
            job_repo = IngestionJobRepository(self.db)
            job = await job_repo.get_by_id(job_id)
            
            if job and job.job_metadata and "checkpoints" in job.job_metadata:
                checkpoints = [
                    JobCheckpoint.from_dict(cp_data)
                    for cp_data in job.job_metadata["checkpoints"]
                ]
                
                self.checkpoints[job_id] = checkpoints
                
                logger.info(
                    f"📂 Loaded {len(checkpoints)} checkpoints for job {job_id}"
                )
        
        except Exception as e:
            logger.error(f"Failed to load checkpoints: {e}")


class RecoverableJob:
    """
    Base class for recoverable jobs.
    
    Provides checkpoint management and graceful recovery.
    """
    
    def __init__(
        self,
        job_id: str,
        job_type: JobType,
        recovery_manager: JobRecoveryManager
    ):
        """
        Initialize recoverable job.
        
        Args:
            job_id: Job identifier
            job_type: Type of job
            recovery_manager: Recovery manager instance
        """
        self.job_id = job_id
        self.job_type = job_type
        self.recovery_manager = recovery_manager
        self.current_checkpoint: Optional[JobCheckpoint] = None
    
    async def create_checkpoint(
        self,
        checkpoint_id: str,
        data: Dict[str, Any]
    ) -> JobCheckpoint:
        """
        Create a checkpoint for this job.
        
        Args:
            checkpoint_id: Checkpoint identifier
            data: Checkpoint data
        
        Returns:
            Created checkpoint
        """
        checkpoint = await self.recovery_manager.create_checkpoint(
            job_id=self.job_id,
            job_type=self.job_type,
            checkpoint_id=checkpoint_id,
            data=data
        )
        
        self.current_checkpoint = checkpoint
        return checkpoint
    
    async def complete_checkpoint(self, data: Optional[Dict[str, Any]] = None):
        """
        Mark current checkpoint as completed.
        
        Args:
            data: Optional updated data
        """
        if self.current_checkpoint:
            await self.recovery_manager.update_checkpoint_status(
                job_id=self.job_id,
                checkpoint_id=self.current_checkpoint.checkpoint_id,
                status=CheckpointStatus.COMPLETED,
                data=data
            )
    
    async def fail_checkpoint(self, error: str):
        """
        Mark current checkpoint as failed.
        
        Args:
            error: Error message
        """
        if self.current_checkpoint:
            await self.recovery_manager.update_checkpoint_status(
                job_id=self.job_id,
                checkpoint_id=self.current_checkpoint.checkpoint_id,
                status=CheckpointStatus.FAILED,
                data={"error": error}
            )
    
    async def can_resume(self) -> bool:
        """Check if job can be resumed."""
        return await self.recovery_manager.can_resume(self.job_id)
    
    async def get_resume_state(self) -> Dict[str, Any]:
        """Get state for resuming."""
        return await self.recovery_manager.get_resume_state(self.job_id)


# Helper function to get recovery manager
_recovery_manager: Optional[JobRecoveryManager] = None


def get_recovery_manager(db_session) -> JobRecoveryManager:
    """
    Get or create recovery manager singleton.
    
    Args:
        db_session: Database session
    
    Returns:
        Recovery manager instance
    """
    global _recovery_manager
    
    if _recovery_manager is None:
        _recovery_manager = JobRecoveryManager(db_session)
    
    return _recovery_manager

