"""
Progress Tracker

Real-time progress tracking and reporting for sub-job execution.
Uses Redis Pub/Sub for live updates.
"""

import logging
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from src.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class ProgressUpdate:
    """Progress update event."""
    plan_id: str
    sub_job_id: Optional[str]
    files_processed: int
    files_failed: int
    files_skipped: int
    total_files: int
    progress_pct: float
    eta_seconds: Optional[float]
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class ProgressReport:
    """Complete progress report for a plan."""
    plan_id: str
    total_files: int
    files_processed: int
    files_failed: int
    files_skipped: int
    progress_pct: float
    sub_jobs_total: int
    sub_jobs_completed: int
    sub_jobs_failed: int
    sub_jobs_active: int
    eta_seconds: Optional[float]
    start_time: Optional[str]
    elapsed_seconds: Optional[float]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class ProgressTracker:
    """
    Tracks and reports execution progress in real-time.
    
    Features:
    - File-level progress tracking
    - Sub-job progress aggregation
    - Plan-level progress calculation
    - Real-time updates via Redis Pub/Sub
    - ETA calculation
    - Progress persistence
    """
    
    def __init__(self):
        self.redis = get_redis_client()
        
        # In-memory progress cache
        self.plan_progress: Dict[str, Dict] = {}
        self.sub_job_progress: Dict[str, Dict[str, Dict]] = {}
        self.start_times: Dict[str, datetime] = {}
        
        logger.info("ProgressTracker initialized")
    
    async def start_tracking(self, plan_id: str, total_files: int, sub_jobs_total: int) -> None:
        """
        Start tracking progress for a plan.
        
        Args:
            plan_id: Processing plan ID
            total_files: Total files to process
            sub_jobs_total: Total sub-jobs
        """
        logger.info(f"📊 Starting progress tracking for plan {plan_id}")
        
        self.start_times[plan_id] = datetime.utcnow()
        
        self.plan_progress[plan_id] = {
            "total_files": total_files,
            "files_processed": 0,
            "files_failed": 0,
            "files_skipped": 0,
            "sub_jobs_total": sub_jobs_total,
            "sub_jobs_completed": 0,
            "sub_jobs_failed": 0,
            "sub_jobs_active": 0
        }
        
        self.sub_job_progress[plan_id] = {}
        
        # Store in Redis
        await self._persist_progress(plan_id)
    
    async def update_sub_job_progress(
        self,
        plan_id: str,
        sub_job_id: str,
        files_processed: int,
        files_failed: int,
        files_skipped: int,
        total_files: int
    ) -> None:
        """
        Update progress for a sub-job.
        
        Args:
            plan_id: Processing plan ID
            sub_job_id: Sub-job ID
            files_processed: Files processed so far
            files_failed: Files failed
            files_skipped: Files skipped
            total_files: Total files in sub-job
        """
        if plan_id not in self.sub_job_progress:
            self.sub_job_progress[plan_id] = {}
        
        # Update sub-job progress
        self.sub_job_progress[plan_id][sub_job_id] = {
            "files_processed": files_processed,
            "files_failed": files_failed,
            "files_skipped": files_skipped,
            "total_files": total_files,
            "progress_pct": (files_processed + files_failed + files_skipped) / total_files * 100 if total_files > 0 else 0
        }
        
        # Aggregate to plan level
        await self._aggregate_progress(plan_id)
        
        # Calculate ETA
        eta = await self.calculate_eta(plan_id)
        
        # Create progress update
        progress_pct = self.plan_progress[plan_id]["files_processed"] / self.plan_progress[plan_id]["total_files"] * 100 if self.plan_progress[plan_id]["total_files"] > 0 else 0
        
        update = ProgressUpdate(
            plan_id=plan_id,
            sub_job_id=sub_job_id,
            files_processed=files_processed,
            files_failed=files_failed,
            files_skipped=files_skipped,
            total_files=total_files,
            progress_pct=progress_pct,
            eta_seconds=eta,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Publish update
        await self.publish_progress_update(update)
        
        # Persist to Redis
        await self._persist_progress(plan_id)
    
    async def mark_sub_job_complete(self, plan_id: str, sub_job_id: str, success: bool = True) -> None:
        """
        Mark a sub-job as completed.
        
        Args:
            plan_id: Processing plan ID
            sub_job_id: Sub-job ID
            success: Whether completed successfully
        """
        if plan_id in self.plan_progress:
            if success:
                self.plan_progress[plan_id]["sub_jobs_completed"] += 1
            else:
                self.plan_progress[plan_id]["sub_jobs_failed"] += 1
            
            # Update active count
            if self.plan_progress[plan_id]["sub_jobs_active"] > 0:
                self.plan_progress[plan_id]["sub_jobs_active"] -= 1
            
            await self._persist_progress(plan_id)
            
            logger.debug(f"✅ Sub-job {sub_job_id} marked as {'completed' if success else 'failed'}")
    
    async def mark_sub_job_active(self, plan_id: str, sub_job_id: str) -> None:
        """
        Mark a sub-job as active.
        
        Args:
            plan_id: Processing plan ID
            sub_job_id: Sub-job ID
        """
        if plan_id in self.plan_progress:
            self.plan_progress[plan_id]["sub_jobs_active"] += 1
            await self._persist_progress(plan_id)
            logger.debug(f"▶️  Sub-job {sub_job_id} marked as active")
    
    async def get_progress(self, plan_id: str) -> Optional[ProgressReport]:
        """
        Get current progress for a plan.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            ProgressReport if tracking, None otherwise
        """
        if plan_id not in self.plan_progress:
            # Try to load from Redis
            await self._load_progress(plan_id)
            
            if plan_id not in self.plan_progress:
                return None
        
        progress = self.plan_progress[plan_id]
        
        # Calculate progress percentage
        total = progress["total_files"]
        processed = progress["files_processed"]
        progress_pct = (processed / total * 100) if total > 0 else 0
        
        # Calculate elapsed time
        elapsed = None
        start_time_str = None
        if plan_id in self.start_times:
            start_time = self.start_times[plan_id]
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            start_time_str = start_time.isoformat()
        
        # Calculate ETA
        eta = await self.calculate_eta(plan_id)
        
        return ProgressReport(
            plan_id=plan_id,
            total_files=progress["total_files"],
            files_processed=progress["files_processed"],
            files_failed=progress["files_failed"],
            files_skipped=progress["files_skipped"],
            progress_pct=progress_pct,
            sub_jobs_total=progress["sub_jobs_total"],
            sub_jobs_completed=progress["sub_jobs_completed"],
            sub_jobs_failed=progress["sub_jobs_failed"],
            sub_jobs_active=progress["sub_jobs_active"],
            eta_seconds=eta,
            start_time=start_time_str,
            elapsed_seconds=elapsed
        )
    
    async def calculate_eta(self, plan_id: str) -> Optional[float]:
        """
        Calculate estimated time to completion.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            ETA in seconds, or None if not enough data
        """
        if plan_id not in self.plan_progress or plan_id not in self.start_times:
            return None
        
        progress = self.plan_progress[plan_id]
        processed = progress["files_processed"]
        total = progress["total_files"]
        
        if processed == 0:
            return None
        
        # Calculate elapsed time
        elapsed = (datetime.utcnow() - self.start_times[plan_id]).total_seconds()
        
        # Calculate rate
        rate = processed / elapsed  # files per second
        
        if rate == 0:
            return None
        
        # Calculate remaining
        remaining = total - processed
        eta = remaining / rate
        
        return eta
    
    async def publish_progress_update(self, update: ProgressUpdate) -> None:
        """
        Publish progress update to Redis Pub/Sub.
        
        Args:
            update: Progress update to publish
        """
        try:
            channel = f"progress:{update.plan_id}"
            message = update.to_json()
            
            redis = await self.redis.get_client()
            await redis.publish(channel, message)
            
            logger.debug(f"📢 Published progress update to {channel}")
            
        except Exception as e:
            logger.error(f"Failed to publish progress update: {e}")
    
    async def subscribe_to_progress(self, plan_id: str):
        """
        Subscribe to progress updates for a plan.
        
        Args:
            plan_id: Processing plan ID
        
        Yields:
            ProgressUpdate objects as they arrive
        """
        try:
            channel = f"progress:{plan_id}"
            redis = await self.redis.get_client()
            pubsub = redis.pubsub()
            
            await pubsub.subscribe(channel)
            logger.info(f"📡 Subscribed to progress updates: {channel}")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        yield ProgressUpdate(**data)
                    except Exception as e:
                        logger.error(f"Failed to parse progress update: {e}")
            
        except Exception as e:
            logger.error(f"Progress subscription error: {e}")
    
    async def stop_tracking(self, plan_id: str) -> None:
        """
        Stop tracking progress for a plan.
        
        Args:
            plan_id: Processing plan ID
        """
        if plan_id in self.plan_progress:
            del self.plan_progress[plan_id]
        
        if plan_id in self.sub_job_progress:
            del self.sub_job_progress[plan_id]
        
        if plan_id in self.start_times:
            del self.start_times[plan_id]
        
        # Remove from Redis
        try:
            redis = await self.redis.get_client()
            await redis.delete(f"progress:plan:{plan_id}")
            await redis.delete(f"progress:subjobs:{plan_id}")
        except Exception as e:
            logger.error(f"Failed to remove progress from Redis: {e}")
        
        logger.info(f"🛑 Stopped tracking progress for plan {plan_id}")
    
    async def _aggregate_progress(self, plan_id: str) -> None:
        """Aggregate sub-job progress to plan level."""
        if plan_id not in self.sub_job_progress or plan_id not in self.plan_progress:
            return
        
        total_processed = 0
        total_failed = 0
        total_skipped = 0
        
        for sub_job_progress in self.sub_job_progress[plan_id].values():
            total_processed += sub_job_progress["files_processed"]
            total_failed += sub_job_progress["files_failed"]
            total_skipped += sub_job_progress["files_skipped"]
        
        self.plan_progress[plan_id]["files_processed"] = total_processed
        self.plan_progress[plan_id]["files_failed"] = total_failed
        self.plan_progress[plan_id]["files_skipped"] = total_skipped
    
    async def _persist_progress(self, plan_id: str) -> None:
        """Persist progress to Redis."""
        try:
            redis = await self.redis.get_client()
            
            # Store plan progress
            if plan_id in self.plan_progress:
                await redis.set(
                    f"progress:plan:{plan_id}",
                    json.dumps(self.plan_progress[plan_id]),
                    ex=86400  # 24 hour expiry
                )
            
            # Store sub-job progress
            if plan_id in self.sub_job_progress:
                await redis.set(
                    f"progress:subjobs:{plan_id}",
                    json.dumps(self.sub_job_progress[plan_id]),
                    ex=86400
                )
            
        except Exception as e:
            logger.error(f"Failed to persist progress to Redis: {e}")
    
    async def _load_progress(self, plan_id: str) -> None:
        """Load progress from Redis."""
        try:
            redis = await self.redis.get_client()
            
            # Load plan progress
            plan_data = await redis.get(f"progress:plan:{plan_id}")
            if plan_data:
                self.plan_progress[plan_id] = json.loads(plan_data)
            
            # Load sub-job progress
            subjob_data = await redis.get(f"progress:subjobs:{plan_id}")
            if subjob_data:
                self.sub_job_progress[plan_id] = json.loads(subjob_data)
            
        except Exception as e:
            logger.error(f"Failed to load progress from Redis: {e}")


# Singleton instance
_progress_tracker_instance = None

def get_progress_tracker() -> ProgressTracker:
    """Get singleton progress tracker instance."""
    global _progress_tracker_instance
    if _progress_tracker_instance is None:
        _progress_tracker_instance = ProgressTracker()
    return _progress_tracker_instance

