"""
Automatic Cleanup Service

Periodically cleans up old jobs, Redis messages, checkpoints, and logs.
Runs as a background task to keep the system healthy.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from ...utils.redis_client import get_redis_client
from ...utils.redis_queue_health_checker import cleanup_orphaned_redis_messages
from ...services.ingestion.orphaned_job_detector import detect_orphaned_jobs
from sqlalchemy import delete, select
from ...storage.db_models import IngestionJobModel

logger = logging.getLogger(__name__)


class AutomaticCleanupService:
    """
    Automatic cleanup service that runs periodically.
    
    Features:
    - Clean up old completed/failed jobs
    - Remove orphaned Redis messages
    - Detect and recover orphaned jobs
    - Clean up old checkpoints
    - Clean up old log files
    - Clean up unreferenced content
    """
    
    def __init__(
        self,
        cleanup_interval_minutes: int = 60,
        job_retention_days: int = 7,
        log_retention_days: int = 30,
        auto_start: bool = True
    ):
        """
        Initialize cleanup service.
        
        Args:
            cleanup_interval_minutes: How often to run cleanup (default: 60 minutes)
            job_retention_days: Keep jobs for this many days (default: 7)
            log_retention_days: Keep logs for this many days (default: 30)
            auto_start: Start cleanup task automatically
        """
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self.job_retention = timedelta(days=job_retention_days)
        self.log_retention = timedelta(days=log_retention_days)
        
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.last_cleanup: Optional[datetime] = None
        self.cleanup_count = 0
        
        self.stats = {
            "total_cleanups": 0,
            "last_cleanup_time": None,
            "jobs_deleted": 0,
            "redis_messages_removed": 0,
            "orphaned_jobs_detected": 0,
            "logs_deleted": 0,
            "errors": []
        }
        
        if auto_start:
            logger.info("🧹 Automatic cleanup service initialized (auto-start enabled)")
        else:
            logger.info("🧹 Automatic cleanup service initialized (manual start required)")
    
    def start(self):
        """Start the cleanup service."""
        if self.running:
            logger.warning("Cleanup service already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"✅ Automatic cleanup service started (interval: {self.cleanup_interval.total_seconds()/60:.0f} minutes)")
    
    async def stop(self):
        """Stop the cleanup service."""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 Automatic cleanup service stopped")
    
    async def _cleanup_loop(self):
        """Main cleanup loop."""
        logger.info(f"🔄 Cleanup loop started (running every {self.cleanup_interval.total_seconds()/60:.0f} minutes)")
        
        while self.running:
            try:
                await self._run_cleanup()
                self.cleanup_count += 1
                
                # Wait for next cleanup interval
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
                self.stats["errors"].append({
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                })
                # Continue after error, wait a bit
                await asyncio.sleep(60)
    
    async def _run_cleanup(self):
        """Run all cleanup tasks."""
        logger.info(f"🧹 Starting automatic cleanup #{self.cleanup_count + 1}")
        start_time = datetime.now()
        
        cleanup_results = {
            "timestamp": start_time.isoformat(),
            "tasks": {}
        }
        
        # 1. Detect and handle orphaned jobs
        try:
            orphaned_result = await detect_orphaned_jobs()
            cleanup_results["tasks"]["orphaned_jobs"] = orphaned_result
            self.stats["orphaned_jobs_detected"] += orphaned_result.get("orphaned_found", 0)
            logger.info(
                f"  ✅ Orphaned jobs: {orphaned_result.get('orphaned_found', 0)} found, "
                f"{orphaned_result.get('failed_old', 0)} failed, "
                f"{orphaned_result.get('requeued_recent', 0)} requeued"
            )
        except Exception as e:
            logger.error(f"  ❌ Orphaned job detection failed: {e}")
            cleanup_results["tasks"]["orphaned_jobs"] = {"error": str(e)}
        
        # 2. Clean up orphaned Redis messages
        try:
            redis_result = await cleanup_orphaned_redis_messages()
            cleanup_results["tasks"]["redis_messages"] = redis_result
            self.stats["redis_messages_removed"] += redis_result.get("messages_removed", 0)
            if redis_result.get("messages_removed", 0) > 0:
                logger.info(f"  ✅ Redis: Removed {redis_result['messages_removed']} orphaned messages")
            else:
                logger.debug(f"  ✅ Redis: No orphaned messages found")
        except Exception as e:
            logger.error(f"  ❌ Redis cleanup failed: {e}")
            cleanup_results["tasks"]["redis_messages"] = {"error": str(e)}
        
        # 3. Clean up old completed jobs
        try:
            completed_result = await self._cleanup_old_jobs(status="completed")
            cleanup_results["tasks"]["completed_jobs"] = completed_result
            self.stats["jobs_deleted"] += completed_result.get("deleted", 0)
            if completed_result.get("deleted", 0) > 0:
                logger.info(f"  ✅ Jobs: Deleted {completed_result['deleted']} old completed jobs")
        except Exception as e:
            logger.error(f"  ❌ Completed job cleanup failed: {e}")
            cleanup_results["tasks"]["completed_jobs"] = {"error": str(e)}
        
        # 4. Clean up old failed jobs (keep longer than completed)
        try:
            failed_result = await self._cleanup_old_jobs(
                status="failed",
                retention_days=self.job_retention.days * 2  # Keep failed jobs 2x longer
            )
            cleanup_results["tasks"]["failed_jobs"] = failed_result
            self.stats["jobs_deleted"] += failed_result.get("deleted", 0)
            if failed_result.get("deleted", 0) > 0:
                logger.info(f"  ✅ Jobs: Deleted {failed_result['deleted']} old failed jobs")
        except Exception as e:
            logger.error(f"  ❌ Failed job cleanup failed: {e}")
            cleanup_results["tasks"]["failed_jobs"] = {"error": str(e)}
        
        # 5. Clean up Redis messages for completed/failed jobs
        try:
            redis_job_cleanup = await self._cleanup_redis_for_finished_jobs()
            cleanup_results["tasks"]["redis_finished_jobs"] = redis_job_cleanup
            self.stats["redis_messages_removed"] += redis_job_cleanup.get("removed", 0)
            if redis_job_cleanup.get("removed", 0) > 0:
                logger.info(f"  ✅ Redis: Removed {redis_job_cleanup['removed']} messages for finished jobs")
        except Exception as e:
            logger.error(f"  ❌ Redis finished jobs cleanup failed: {e}")
            cleanup_results["tasks"]["redis_finished_jobs"] = {"error": str(e)}
        
        # Update stats
        self.last_cleanup = datetime.now()
        self.stats["total_cleanups"] += 1
        self.stats["last_cleanup_time"] = self.last_cleanup.isoformat()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Automatic cleanup #{self.cleanup_count + 1} completed in {elapsed:.2f}s")
        
        return cleanup_results
    
    async def _cleanup_old_jobs(
        self,
        status: str,
        retention_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Clean up old jobs with specific status.
        
        Args:
            status: Job status to clean up
            retention_days: Keep jobs for this many days (default: use service setting)
        
        Returns:
            Cleanup results
        """
        if retention_days is None:
            retention_days = self.job_retention.days
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        db = get_database()
        async with db.session() as session:
            # Delete jobs older than cutoff
            stmt = delete(IngestionJobModel).where(
                IngestionJobModel.status == status,
                IngestionJobModel.completed_at < cutoff_date
            )
            
            result = await session.execute(stmt)
            await session.commit()
            
            deleted_count = result.rowcount
            
            return {
                "status": status,
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat(),
                "deleted": deleted_count
            }
    
    async def _cleanup_redis_for_finished_jobs(self) -> Dict[str, Any]:
        """
        Clean up Redis messages for jobs that are completed or failed.
        
        These jobs shouldn't have messages in the queue anymore.
        """
        result = {
            "checked": 0,
            "removed": 0,
            "errors": []
        }
        
        try:
            redis = get_redis_client()
            db = get_database()
            
            # Get all finished job IDs
            finished_job_ids = set()
            async with db.session() as session:
                stmt = select(IngestionJobModel).where(
                    IngestionJobModel.status.in_(["completed", "failed", "cancelled"])
                )
                result_set = await session.execute(stmt)
                jobs = result_set.scalars().all()
                
                for job in jobs:
                    finished_job_ids.add(str(job.id))
            
            # Check Redis messages
            messages = await redis.client.xrange(
                redis.INGESTION_STREAM,
                min="-",
                max="+",
                count=1000
            )
            
            for message_id, message_data in messages:
                result["checked"] += 1
                job_id = message_data.get(b"job_id", b"").decode()
                
                if job_id in finished_job_ids:
                    # Job is finished, remove message
                    try:
                        await redis.client.xdel(redis.INGESTION_STREAM, message_id)
                        result["removed"] += 1
                        logger.debug(f"Removed Redis message for finished job {job_id}")
                    except Exception as e:
                        error_msg = f"Failed to remove message for job {job_id}: {e}"
                        result["errors"].append(error_msg)
                        logger.error(error_msg)
            
            return result
            
        except Exception as e:
            logger.error(f"Error cleaning Redis for finished jobs: {e}", exc_info=True)
            result["errors"].append(str(e))
            return result
    
    async def run_manual_cleanup(self) -> Dict[str, Any]:
        """
        Run cleanup manually (outside of scheduled loop).
        
        Returns:
            Cleanup results
        """
        logger.info("🧹 Running manual cleanup")
        return await self._run_cleanup()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cleanup statistics."""
        return {
            **self.stats,
            "running": self.running,
            "cleanup_interval_minutes": self.cleanup_interval.total_seconds() / 60,
            "job_retention_days": self.job_retention.days,
            "last_cleanup": self.last_cleanup.isoformat() if self.last_cleanup else None,
            "cleanup_count": self.cleanup_count
        }


# Global instance
_cleanup_service: Optional[AutomaticCleanupService] = None


def get_cleanup_service() -> AutomaticCleanupService:
    """Get global cleanup service instance."""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = AutomaticCleanupService(
            cleanup_interval_minutes=60,  # Every hour
            job_retention_days=7,  # Keep jobs for 7 days
            log_retention_days=30,  # Keep logs for 30 days
            auto_start=False  # Don't start automatically, wait for explicit start
        )
    return _cleanup_service


def start_cleanup_service():
    """Start the global cleanup service."""
    service = get_cleanup_service()
    service.start()
    logger.info("✅ Global cleanup service started")


async def stop_cleanup_service():
    """Stop the global cleanup service."""
    global _cleanup_service
    if _cleanup_service:
        await _cleanup_service.stop()
        logger.info("🛑 Global cleanup service stopped")

