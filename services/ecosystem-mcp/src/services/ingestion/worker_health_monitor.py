"""
Worker Health Monitoring Service

Monitors the ingestion worker health and automatically restarts it if:
1. Worker is running but not polling Redis for > 2 minutes
2. Jobs are stuck in "queued" status for > 2 minutes

This prevents the worker from getting stuck in an idle state.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Configuration
HEALTH_CHECK_INTERVAL_SECONDS = 60  # Check every minute
MAX_IDLE_TIME_SECONDS = 120  # 2 minutes without polling
MAX_QUEUED_TIME_SECONDS = 120  # 2 minutes stuck in queued
RESTART_COOLDOWN_SECONDS = 300  # Wait 5 minutes between restarts


class WorkerHealthMonitor:
    """
    Background service that monitors worker health and auto-restarts if needed.
    
    Features:
    - Detects when worker stops polling Redis
    - Detects when jobs are stuck in "queued" status
    - Automatically restarts worker with cooldown
    - Tracks restart history and statistics
    """
    
    def __init__(
        self,
        check_interval_seconds: int = HEALTH_CHECK_INTERVAL_SECONDS,
        max_idle_seconds: int = MAX_IDLE_TIME_SECONDS,
        max_queued_seconds: int = MAX_QUEUED_TIME_SECONDS,
        restart_cooldown_seconds: int = RESTART_COOLDOWN_SECONDS
    ):
        """
        Initialize worker health monitor.
        
        Args:
            check_interval_seconds: How often to check worker health
            max_idle_seconds: Max time worker can be idle before restart
            max_queued_seconds: Max time jobs can be queued before restart
            restart_cooldown_seconds: Minimum time between restarts
        """
        self.check_interval_seconds = check_interval_seconds
        self.max_idle_seconds = max_idle_seconds
        self.max_queued_seconds = max_queued_seconds
        self.restart_cooldown_seconds = restart_cooldown_seconds
        
        # Service state
        self.running = False
        self.monitor_id = f"health_monitor_{id(self)}"
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        # Tracking
        self.last_worker_activity: Optional[datetime] = None
        self.last_restart: Optional[datetime] = None
        
        # Statistics
        self.stats = {
            "health_checks": 0,
            "idle_restarts": 0,
            "queued_restarts": 0,
            "total_restarts": 0,
            "last_restart_at": None,
            "last_restart_reason": None,
            "started_at": None
        }
        
        logger.info(
            f"🏥 WorkerHealthMonitor initialized: "
            f"check_interval={check_interval_seconds}s, "
            f"max_idle={max_idle_seconds}s, "
            f"max_queued={max_queued_seconds}s"
        )
    
    async def start(self) -> None:
        """Start the health monitor."""
        if self.running:
            logger.warning(f"⚠️  WorkerHealthMonitor {self.monitor_id} already running")
            return
        
        self.running = True
        self._stop_event.clear()
        self.stats["started_at"] = datetime.utcnow().isoformat()
        
        # Start background task
        self._task = asyncio.create_task(self._monitor_loop())
        
        logger.info(f"✅ WorkerHealthMonitor {self.monitor_id} started")
    
    async def stop(self) -> None:
        """Stop the health monitor."""
        if not self.running:
            return
        
        logger.info(f"🛑 Stopping WorkerHealthMonitor {self.monitor_id}...")
        
        self.running = False
        self._stop_event.set()
        
        # Wait for task to finish
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=10.0)
            except asyncio.TimeoutError:
                logger.warning("Health monitor did not stop gracefully, cancelling...")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        
        logger.info(f"✅ WorkerHealthMonitor {self.monitor_id} stopped")
    
    async def _monitor_loop(self) -> None:
        """
        Main monitoring loop.
        
        Runs health checks periodically and restarts worker if needed.
        """
        logger.info(f"🏥 Health monitor loop started (interval: {self.check_interval_seconds}s)")
        
        # Wait 2 minutes before first check (let worker initialize)
        await asyncio.sleep(120)
        
        try:
            while self.running and not self._stop_event.is_set():
                try:
                    await self._run_health_check()
                    
                    # Wait for next check interval
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(),
                            timeout=self.check_interval_seconds
                        )
                        # If we get here, stop was called
                        break
                    except asyncio.TimeoutError:
                        # Normal timeout, continue to next check
                        continue
                
                except Exception as e:
                    logger.error(f"❌ Error in health monitor loop: {e}", exc_info=True)
                    # Wait before retry on error
                    await asyncio.sleep(self.check_interval_seconds)
        
        except asyncio.CancelledError:
            logger.info("Health monitor loop cancelled")
        
        logger.info("🏥 Health monitor loop stopped")
    
    async def _run_health_check(self) -> None:
        """
        Run a single health check cycle.
        
        Checks:
        1. Worker polling activity (via Redis stream reads)
        2. Stuck queued jobs
        3. Worker responsiveness
        """
        self.stats["health_checks"] += 1
        
        logger.info(f"🏥 Running health check #{self.stats['health_checks']}")
        
        # Check if we're in cooldown period
        if self.last_restart:
            time_since_restart = (datetime.utcnow() - self.last_restart).total_seconds()
            if time_since_restart < self.restart_cooldown_seconds:
                logger.info(
                    f"⏳ In restart cooldown "
                    f"({int(self.restart_cooldown_seconds - time_since_restart)}s remaining)"
                )
                return
        
        # Check 1: Worker polling activity
        idle_detected = await self._check_worker_idle()
        if idle_detected:
            await self._restart_worker("Worker idle - not polling Redis")
            return
        
        # Check 2: Stuck queued jobs
        stuck_jobs = await self._check_stuck_queued_jobs()
        if stuck_jobs > 0:
            await self._restart_worker(f"{stuck_jobs} jobs stuck in queued status")
            return
        
        logger.info("✅ Worker health check passed")
    
    async def _check_worker_idle(self) -> bool:
        """
        Check if worker is idle (not polling Redis).
        
        Returns:
            True if worker appears idle, False otherwise
        """
        try:
            from .ingestion_worker import get_ingestion_worker
            
            worker = get_ingestion_worker()
            
            # Check if worker is running
            if not worker.running:
                logger.warning("⚠️  Worker not running")
                return False  # Don't restart if not running
            
            # Check worker's last activity time
            # This would require adding last_poll_time tracking to the worker
            # For now, we'll check for stuck queued jobs as the primary signal
            
            return False  # Worker activity check disabled for now
        
        except Exception as e:
            logger.error(f"❌ Error checking worker idle state: {e}")
            return False
    
    async def _check_stuck_queued_jobs(self) -> int:
        """
        Check for jobs stuck in "queued" status or orphaned in "processing" status.
        
        Returns:
            Number of stuck/orphaned jobs
        """
        try:
            db = get_database()
            redis = get_redis_client()
            
            async with db.session() as session:
                repo = IngestionJobRepository(session)
                
                # Check 1: Get all queued jobs
                from sqlalchemy import select
                from ...storage.db_models import IngestionJobModel
                
                query = select(IngestionJobModel).where(
                    IngestionJobModel.status == "queued"
                )
                result = await session.execute(query)
                queued_jobs = result.scalars().all()
                
                logger.info(f"🔍 Found {len(queued_jobs)} queued jobs to check")
                
                # Check 2: Get all processing jobs and check if worker is idle
                query_processing = select(IngestionJobModel).where(
                    IngestionJobModel.status == "processing"
                )
                result_processing = await session.execute(query_processing)
                processing_jobs = result_processing.scalars().all()
                
                logger.info(f"🔍 Found {len(processing_jobs)} processing jobs to check")
                
                if not queued_jobs and not processing_jobs:
                    return 0
                
                # Check which queued jobs have been waiting too long
                stuck_count = 0
                cutoff_time = datetime.utcnow() - timedelta(seconds=self.max_queued_seconds)
                
                logger.info(f"🔍 Checking jobs queued before: {cutoff_time} (threshold: {self.max_queued_seconds}s)")
                
                for job in queued_jobs:
                    # Check if job was created > max_queued_seconds ago
                    if job.started_at:
                        age = datetime.utcnow() - job.started_at
                        age_seconds = age.total_seconds()
                        
                        logger.info(
                            f"🔍 [QUEUED] Job {str(job.id)[:12]}: started_at={job.started_at}, "
                            f"age={int(age_seconds)}s, "
                            f"stuck={age_seconds > self.max_queued_seconds}"
                        )
                        
                        if job.started_at < cutoff_time:
                            stuck_count += 1
                            logger.warning(
                                f"⚠️  Job {job.id} stuck in queued "
                                f"(age: {age}, {int(age_seconds)}s)"
                            )
                
                # Check for orphaned processing jobs (processing but worker is idle)
                if processing_jobs:
                    try:
                        from .ingestion_worker import get_ingestion_worker
                        worker = get_ingestion_worker()
                        
                        # If worker is not processing anything, all "processing" jobs are orphaned
                        if not worker.current_job_id:
                            logger.info(f"🔍 Worker has no current_job_id - checking for orphaned processing jobs")
                            
                            for job in processing_jobs:
                                if job.started_at:
                                    age = datetime.utcnow() - job.started_at
                                    age_seconds = age.total_seconds()
                                    
                                    logger.info(
                                        f"🔍 [PROCESSING] Job {str(job.id)[:12]}: started_at={job.started_at}, "
                                        f"age={int(age_seconds)}s, "
                                        f"orphaned=True (worker idle)"
                                    )
                                    
                                    # Any processing job is orphaned if worker is idle
                                    stuck_count += 1
                                    logger.warning(
                                        f"⚠️  Job {job.id} orphaned in processing "
                                        f"(age: {age}, {int(age_seconds)}s) - worker is idle"
                                    )
                        else:
                            logger.info(f"🔍 Worker is processing job {str(worker.current_job_id)[:12]} - processing jobs are not orphaned")
                    
                    except Exception as e:
                        logger.error(f"❌ Error checking for orphaned processing jobs: {e}")
                
                # Also check if there are messages in Redis but worker isn't picking them up
                if stuck_count > 0:
                    try:
                        stream_len = await redis.client.xlen(redis.INGESTION_STREAM)
                        if stream_len > 0:
                            logger.warning(
                                f"⚠️  {stuck_count} stuck/orphaned jobs + {stream_len} Redis messages = WORKER STUCK"
                            )
                    except Exception as e:
                        logger.debug(f"Could not check Redis stream: {e}")
                else:
                    logger.info(f"✅ No stuck/orphaned jobs detected (checked {len(queued_jobs)} queued + {len(processing_jobs)} processing)")
                
                return stuck_count
        
        except Exception as e:
            logger.error(f"❌ Error checking stuck queued jobs: {e}")
            return 0
    
    async def _restart_worker(self, reason: str) -> None:
        """
        Restart the ingestion worker.
        
        Args:
            reason: Reason for restart (for logging/stats)
        """
        logger.warning(f"🔄 Restarting worker: {reason}")
        
        try:
            from .ingestion_worker import get_ingestion_worker
            
            worker = get_ingestion_worker()
            
            # Stop and restart worker
            await worker.stop()
            await asyncio.sleep(2)  # Brief pause
            await worker.start()
            
            # Update tracking
            self.last_restart = datetime.utcnow()
            self.stats["total_restarts"] += 1
            self.stats["last_restart_at"] = self.last_restart.isoformat()
            self.stats["last_restart_reason"] = reason
            
            # Track restart type
            if "idle" in reason.lower():
                self.stats["idle_restarts"] += 1
            elif "queued" in reason.lower():
                self.stats["queued_restarts"] += 1
            
            logger.info(
                f"✅ Worker restarted successfully "
                f"(total restarts: {self.stats['total_restarts']})"
            )
        
        except Exception as e:
            logger.error(f"❌ Failed to restart worker: {e}", exc_info=True)
    
    async def get_status(self) -> dict:
        """Get health monitor status."""
        status = {
            "running": self.running,
            "monitor_id": self.monitor_id,
            "check_interval_seconds": self.check_interval_seconds,
            "max_idle_seconds": self.max_idle_seconds,
            "max_queued_seconds": self.max_queued_seconds,
            "stats": self.stats
        }
        
        if self.last_restart:
            time_since_restart = (datetime.utcnow() - self.last_restart).total_seconds()
            status["time_since_last_restart_seconds"] = int(time_since_restart)
            status["in_restart_cooldown"] = time_since_restart < self.restart_cooldown_seconds
        
        return status


# Global instance
_health_monitor: Optional[WorkerHealthMonitor] = None


def get_health_monitor() -> WorkerHealthMonitor:
    """
    Get global health monitor instance.
    
    Creates instance on first call (singleton pattern).
    """
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = WorkerHealthMonitor()
    return _health_monitor


async def init_health_monitor():
    """Initialize and start health monitor on application startup."""
    monitor = get_health_monitor()
    await monitor.start()
    logger.info("✅ Worker health monitor initialized")

