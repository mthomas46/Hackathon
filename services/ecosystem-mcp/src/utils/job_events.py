"""
Job Event Publisher for real-time dashboard updates.

⚡ PHASE 2 ITEM 2.3 (Option B): Targeted event system for job lifecycle.

Publishes events on:
- Job completion
- Job failure
- Progress milestones

Architecture:
- Redis pub/sub for event distribution
- Graceful fallback if Redis unavailable
- Zero impact on worker loops (they stay efficient)
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class JobEventType(str, Enum):
    """Job event types."""
    JOB_STARTED = "job_started"
    JOB_PROGRESS = "job_progress"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    JOB_CANCELLED = "job_cancelled"


class JobEventPublisher:
    """
    Publishes job lifecycle events to Redis pub/sub.
    
    Features:
    - Event-driven dashboard updates
    - Graceful fallback (no Redis? no problem)
    - Minimal overhead
    - Zero changes to worker loops
    
    Usage:
        publisher = JobEventPublisher()
        await publisher.publish_job_completed(job_id, metadata)
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize event publisher.
        
        Args:
            redis_client: Optional Redis client. If not provided, will attempt
                         to get from redis_client utility.
        """
        self.redis_client = redis_client
        self._enabled = False
        self._events_published = 0
        self._events_failed = 0
        
        if not self.redis_client:
            try:
                from .redis_client import get_redis_client
                self.redis_client = get_redis_client()
                self._enabled = True
                logger.info("✅ Job event publisher initialized (Redis pub/sub)")
            except Exception as e:
                logger.warning(f"⚠️  Job events disabled (Redis unavailable): {e}")
                self._enabled = False
        else:
            self._enabled = True
    
    def _make_channel_name(self, job_id: str, event_type: JobEventType) -> str:
        """Generate Redis channel name for event."""
        return f"job_events:{job_id}:{event_type.value}"
    
    def _make_global_channel_name(self, event_type: JobEventType) -> str:
        """Generate global channel name (all jobs of this type)."""
        return f"job_events:all:{event_type.value}"
    
    async def publish_event(
        self,
        job_id: str,
        event_type: JobEventType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish job event.
        
        Args:
            job_id: Job ID
            event_type: Type of event
            metadata: Optional event metadata
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self._enabled or not self.redis_client:
            return False
        
        try:
            event_data = {
                "job_id": job_id,
                "event_type": event_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
            
            event_json = json.dumps(event_data)
            
            # Publish to job-specific channel
            job_channel = self._make_channel_name(job_id, event_type)
            await self.redis_client.publish(job_channel, event_json)
            
            # Also publish to global channel
            global_channel = self._make_global_channel_name(event_type)
            await self.redis_client.publish(global_channel, event_json)
            
            self._events_published += 1
            logger.debug(
                f"📢 Published event: {event_type.value} for job {job_id}"
            )
            return True
            
        except Exception as e:
            self._events_failed += 1
            logger.warning(f"Failed to publish job event: {e}")
            return False
    
    async def publish_job_started(
        self,
        job_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Publish job started event."""
        return await self.publish_event(job_id, JobEventType.JOB_STARTED, metadata)
    
    async def publish_job_progress(
        self,
        job_id: str,
        progress_pct: float,
        phase: str,
        files_processed: int,
        total_files: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish job progress event.
        
        Args:
            job_id: Job ID
            progress_pct: Progress percentage (0-100)
            phase: Current phase name
            files_processed: Number of files processed
            total_files: Total number of files
            metadata: Optional additional metadata
        """
        event_metadata = {
            "progress_pct": progress_pct,
            "phase": phase,
            "files_processed": files_processed,
            "total_files": total_files,
            **(metadata or {})
        }
        return await self.publish_event(job_id, JobEventType.JOB_PROGRESS, event_metadata)
    
    async def publish_job_completed(
        self,
        job_id: str,
        files_processed: int,
        duration_seconds: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish job completed event.
        
        Args:
            job_id: Job ID
            files_processed: Number of files successfully processed
            duration_seconds: Total job duration
            metadata: Optional additional metadata
        """
        event_metadata = {
            "files_processed": files_processed,
            "duration_seconds": duration_seconds,
            "status": "completed",
            **(metadata or {})
        }
        return await self.publish_event(job_id, JobEventType.JOB_COMPLETED, event_metadata)
    
    async def publish_job_failed(
        self,
        job_id: str,
        error_message: str,
        files_processed: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish job failed event.
        
        Args:
            job_id: Job ID
            error_message: Error message
            files_processed: Number of files processed before failure
            metadata: Optional additional metadata
        """
        event_metadata = {
            "error_message": error_message,
            "files_processed": files_processed,
            "status": "failed",
            **(metadata or {})
        }
        return await self.publish_event(job_id, JobEventType.JOB_FAILED, event_metadata)
    
    async def publish_job_cancelled(
        self,
        job_id: str,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Publish job cancelled event.
        
        Args:
            job_id: Job ID
            reason: Cancellation reason
            metadata: Optional additional metadata
        """
        event_metadata = {
            "reason": reason,
            "status": "cancelled",
            **(metadata or {})
        }
        return await self.publish_event(job_id, JobEventType.JOB_CANCELLED, event_metadata)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event publisher statistics."""
        return {
            "enabled": self._enabled,
            "events_published": self._events_published,
            "events_failed": self._events_failed,
            "success_rate": (
                f"{(self._events_published / (self._events_published + self._events_failed) * 100):.1f}%"
                if (self._events_published + self._events_failed) > 0
                else "N/A"
            )
        }


# Global instance (singleton)
_global_publisher: Optional[JobEventPublisher] = None


def get_job_event_publisher() -> JobEventPublisher:
    """
    Get global job event publisher instance.
    
    Returns:
        JobEventPublisher instance (singleton)
    """
    global _global_publisher
    if _global_publisher is None:
        _global_publisher = JobEventPublisher()
    return _global_publisher


# Convenience functions for quick access
async def publish_job_started(job_id: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Convenience: Publish job started event."""
    return await get_job_event_publisher().publish_job_started(job_id, metadata)


async def publish_job_progress(
    job_id: str,
    progress_pct: float,
    phase: str,
    files_processed: int,
    total_files: int,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Convenience: Publish job progress event."""
    return await get_job_event_publisher().publish_job_progress(
        job_id, progress_pct, phase, files_processed, total_files, metadata
    )


async def publish_job_completed(
    job_id: str,
    files_processed: int,
    duration_seconds: float,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Convenience: Publish job completed event."""
    return await get_job_event_publisher().publish_job_completed(
        job_id, files_processed, duration_seconds, metadata
    )


async def publish_job_failed(
    job_id: str,
    error_message: str,
    files_processed: int,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Convenience: Publish job failed event."""
    return await get_job_event_publisher().publish_job_failed(
        job_id, error_message, files_processed, metadata
    )


async def publish_job_cancelled(
    job_id: str,
    reason: str,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """Convenience: Publish job cancelled event."""
    return await get_job_event_publisher().publish_job_cancelled(job_id, reason, metadata)

