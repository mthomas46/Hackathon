"""
Job Cleanup Service

Periodically cleans up old completed/failed jobs from the database
to prevent unbounded growth.

Runs in background, cleaning jobs older than a configured threshold.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from ...storage import get_database
from ...storage.repositories import IngestionJobRepository

logger = logging.getLogger(__name__)

# Configuration
CLEANUP_INTERVAL_HOURS = 24  # Run cleanup once per day
JOB_RETENTION_DAYS = 7  # Keep jobs for 7 days
BATCH_SIZE = 100  # Delete in batches


class JobCleanupService:
    """
    Background service that periodically cleans up old jobs.
    
    Features:
    - Runs every 24 hours
    - Removes completed/failed jobs older than 7 days
    - Batch processing to avoid overloading database
    - Graceful shutdown
    """
    
    def __init__(
        self,
        cleanup_interval_hours: int = CLEANUP_INTERVAL_HOURS,
        retention_days: int = JOB_RETENTION_DAYS,
        batch_size: int = BATCH_SIZE
    ):
        """
        Initialize cleanup service.
        
        Args:
            cleanup_interval_hours: Hours between cleanup runs
            retention_days: Days to retain completed/failed jobs
            batch_size: Number of jobs to delete per batch
        """
        self.cleanup_interval_hours = cleanup_interval_hours
        self.retention_days = retention_days
        self.batch_size = batch_size
        
        # Service state
        self.running = False
        self.service_id = f"cleanup_{id(self)}"
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        # Statistics
        self.stats = {
            "total_cleaned": 0,
            "last_cleanup_at": None,
            "last_cleanup_count": 0,
            "cleanup_runs": 0,
            "errors": 0
        }
        
        logger.info(
            f"🧹 JobCleanupService initialized: "
            f"interval={cleanup_interval_hours}h, "
            f"retention={retention_days}d, "
            f"batch_size={batch_size}"
        )
    
    async def start(self) -> None:
        """Start the cleanup service."""
        if self.running:
            logger.warning(f"⚠️  JobCleanupService {self.service_id} already running")
            return
        
        self.running = True
        self._stop_event.clear()
        
        # Start background task
        self._task = asyncio.create_task(self._cleanup_loop())
        
        logger.info(f"✅ JobCleanupService {self.service_id} started")
    
    async def stop(self) -> None:
        """Stop the cleanup service."""
        if not self.running:
            return
        
        logger.info(f"🛑 Stopping JobCleanupService {self.service_id}...")
        
        self.running = False
        self._stop_event.set()
        
        # Wait for task to finish
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Cleanup service did not stop gracefully, cancelling...")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        
        logger.info(f"✅ JobCleanupService {self.service_id} stopped")
    
    async def _cleanup_loop(self) -> None:
        """
        Main cleanup loop.
        
        Runs cleanup every N hours and removes old jobs.
        """
        logger.info(f"🧹 Cleanup loop started (interval: {self.cleanup_interval_hours}h)")
        
        # Run initial cleanup after 1 hour
        await asyncio.sleep(3600)
        
        try:
            while self.running and not self._stop_event.is_set():
                try:
                    await self._run_cleanup()
                    
                    # Wait for next cleanup interval
                    wait_seconds = self.cleanup_interval_hours * 3600
                    logger.info(f"😴 Next cleanup in {self.cleanup_interval_hours} hours...")
                    
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(),
                            timeout=wait_seconds
                        )
                        # If we get here, stop was called
                        break
                    except asyncio.TimeoutError:
                        # Normal timeout, continue to next cleanup
                        continue
                
                except Exception as e:
                    self.stats["errors"] += 1
                    logger.error(f"❌ Error in cleanup loop: {e}", exc_info=True)
                    
                    # Wait 1 hour before retry on error
                    await asyncio.sleep(3600)
        
        except asyncio.CancelledError:
            logger.info("Cleanup loop cancelled")
        
        logger.info("🧹 Cleanup loop stopped")
    
    async def _run_cleanup(self) -> int:
        """
        Run a single cleanup cycle.
        
        Returns:
            Number of jobs deleted
        """
        try:
            logger.info(f"🧹 Starting cleanup (retention: {self.retention_days} days)...")
            
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            db = get_database()
            total_deleted = 0
            
            async with db.session() as session:
                repo = IngestionJobRepository(session)
                
                # Get count of old jobs
                from sqlalchemy import select, func
                from ...storage.db_models import IngestionJobModel
                
                # Count jobs that are completed/failed and older than cutoff
                count_query = select(func.count(IngestionJobModel.id)).where(
                    IngestionJobModel.status.in_(["completed", "failed"]),
                    IngestionJobModel.completed_at < cutoff_date
                )
                result = await session.execute(count_query)
                total_count = result.scalar()
                
                if total_count == 0:
                    logger.info(f"✅ No old jobs to clean up")
                    self.stats["cleanup_runs"] += 1
                    self.stats["last_cleanup_at"] = datetime.utcnow().isoformat()
                    self.stats["last_cleanup_count"] = 0
                    return 0
                
                logger.info(f"📊 Found {total_count} old jobs to clean up")
                
                # Delete in batches
                while total_deleted < total_count:
                    # Get batch of old jobs
                    query = select(IngestionJobModel).where(
                        IngestionJobModel.status.in_(["completed", "failed"]),
                        IngestionJobModel.completed_at < cutoff_date
                    ).limit(self.batch_size)
                    
                    result = await session.execute(query)
                    jobs = result.scalars().all()
                    
                    if not jobs:
                        break
                    
                    # Delete batch
                    for job in jobs:
                        await session.delete(job)
                    
                    await session.commit()
                    batch_size = len(jobs)
                    total_deleted += batch_size
                    
                    logger.info(f"   🗑️  Deleted batch of {batch_size} jobs (total: {total_deleted}/{total_count})")
                    
                    # Small delay between batches
                    await asyncio.sleep(0.1)
            
            # Update stats
            self.stats["total_cleaned"] += total_deleted
            self.stats["last_cleanup_at"] = datetime.utcnow().isoformat()
            self.stats["last_cleanup_count"] = total_deleted
            self.stats["cleanup_runs"] += 1
            
            logger.info(
                f"✅ Cleanup complete: deleted {total_deleted} jobs "
                f"(total lifetime: {self.stats['total_cleaned']})"
            )
            
            return total_deleted
        
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}", exc_info=True)
            raise
    
    async def get_status(self) -> dict:
        """Get cleanup service status."""
        return {
            "running": self.running,
            "service_id": self.service_id,
            "cleanup_interval_hours": self.cleanup_interval_hours,
            "retention_days": self.retention_days,
            "stats": self.stats
        }


# Global instance
_cleanup_service: Optional[JobCleanupService] = None


def get_cleanup_service() -> JobCleanupService:
    """
    Get global cleanup service instance.
    
    Creates instance on first call (singleton pattern).
    """
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = JobCleanupService()
    return _cleanup_service


async def init_cleanup_service():
    """Initialize and start cleanup service on application startup."""
    service = get_cleanup_service()
    await service.start()
    logger.info("✅ Job cleanup service initialized")

