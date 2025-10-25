"""
Progress-Aware Timeout

A timeout mechanism that only triggers when no progress is being made,
allowing long-running jobs to continue as long as they're actively processing.

Key Features:
- Monitors progress updates in Redis
- Only times out if idle (no progress) for threshold period
- Resets timeout whenever progress is detected
- Prevents premature termination of actively processing jobs
"""

import asyncio
import logging
import time
from typing import Any, Awaitable, Optional, Callable
import json

logger = logging.getLogger(__name__)


class ProgressAwareTimeout:
    """
    A timeout that only triggers when no progress is being made.
    
    Instead of timing out after a fixed duration regardless of activity,
    this timeout monitors progress updates and only triggers if the job
    has been idle (no progress) for the specified threshold.
    
    Example:
        Job processing 10,000 files:
        - Fixed timeout: 600s → kills job at 600s even if processing file #9,999
        - Progress-aware: Only times out if stuck on same file for 600s
    """
    
    def __init__(
        self,
        redis_client,
        job_id: str,
        idle_timeout_seconds: int = 600,
        check_interval_seconds: int = 10,
        progress_key_pattern: str = "job_progress:{job_id}"
    ):
        """
        Initialize progress-aware timeout.
        
        Args:
            redis_client: Redis client for checking progress
            job_id: Job ID to monitor
            idle_timeout_seconds: Seconds of no progress before timeout (default: 600 = 10 min)
            check_interval_seconds: How often to check for progress (default: 10s)
            progress_key_pattern: Redis key pattern for progress data
        """
        self.redis_client = redis_client
        self.job_id = job_id
        self.idle_timeout_seconds = idle_timeout_seconds
        self.check_interval_seconds = check_interval_seconds
        self.progress_key = progress_key_pattern.format(job_id=job_id)
        
        self.last_progress_time = time.time()
        self.last_progress_data = None
        self.monitoring_task = None
        self.timeout_event = asyncio.Event()
        
        logger.info(
            f"🧠 Progress-aware timeout initialized for job {job_id}: "
            f"idle_timeout={idle_timeout_seconds}s, check_interval={check_interval_seconds}s"
        )
    
    async def _monitor_progress(self):
        """Background task that monitors progress and triggers timeout if idle."""
        try:
            while not self.timeout_event.is_set():
                # Check current progress
                current_progress = await self._get_current_progress()
                
                # Determine if progress was made
                progress_made = self._has_progress_changed(current_progress)
                
                if progress_made:
                    # Reset idle timer
                    self.last_progress_time = time.time()
                    self.last_progress_data = current_progress
                    logger.debug(
                        f"📈 Progress detected for job {self.job_id}: "
                        f"{current_progress.get('phase', 'unknown')} - "
                        f"{current_progress.get('current', 0)}/{current_progress.get('total', 0)}"
                    )
                else:
                    # Check if idle for too long
                    idle_seconds = time.time() - self.last_progress_time
                    
                    if idle_seconds > self.idle_timeout_seconds:
                        logger.warning(
                            f"⏰ IDLE TIMEOUT: Job {self.job_id} has been idle for {idle_seconds:.1f}s "
                            f"(threshold: {self.idle_timeout_seconds}s)"
                        )
                        self.timeout_event.set()
                        break
                    elif idle_seconds > self.idle_timeout_seconds * 0.5:
                        # Warning at 50% of threshold
                        logger.warning(
                            f"⚠️  Job {self.job_id} has been idle for {idle_seconds:.1f}s "
                            f"(threshold: {self.idle_timeout_seconds}s)"
                        )
                
                # Wait before next check
                await asyncio.sleep(self.check_interval_seconds)
        
        except asyncio.CancelledError:
            logger.debug(f"Progress monitoring cancelled for job {self.job_id}")
        except Exception as e:
            logger.error(f"Error in progress monitoring for job {self.job_id}: {e}")
            self.timeout_event.set()
    
    async def _get_current_progress(self) -> Optional[dict]:
        """Get current progress from Redis."""
        try:
            if not self.redis_client:
                return None
            
            progress_json = await self.redis_client.get(self.progress_key)
            if not progress_json:
                return None
            
            return json.loads(progress_json)
        except Exception as e:
            logger.debug(f"Could not get progress for job {self.job_id}: {e}")
            return None
    
    def _has_progress_changed(self, current_progress: Optional[dict]) -> bool:
        """
        Determine if progress has changed since last check.
        
        Args:
            current_progress: Current progress data
        
        Returns:
            True if progress was made, False if idle
        """
        if current_progress is None:
            return False
        
        if self.last_progress_data is None:
            return True  # First progress update
        
        # Check if key metrics changed
        current_items = current_progress.get("current", 0)
        last_items = self.last_progress_data.get("current", 0)
        
        current_phase = current_progress.get("phase", "")
        last_phase = self.last_progress_data.get("phase", "")
        
        # Progress made if:
        # 1. More items processed
        # 2. Phase changed
        return current_items > last_items or current_phase != last_phase
    
    async def run_with_progress_timeout(
        self,
        coro: Awaitable[Any],
        fallback_timeout: Optional[int] = None
    ) -> Any:
        """
        Run a coroutine with progress-aware timeout.
        
        Args:
            coro: Coroutine to run
            fallback_timeout: Optional absolute maximum timeout (safety net)
        
        Returns:
            Result of the coroutine
        
        Raises:
            asyncio.TimeoutError: If job is idle for too long or fallback timeout reached
        """
        # Start progress monitoring
        self.monitoring_task = asyncio.create_task(self._monitor_progress())
        
        try:
            if fallback_timeout:
                # Use both progress-aware AND absolute timeout (safety net)
                logger.info(
                    f"🧠 Running with progress-aware timeout (idle: {self.idle_timeout_seconds}s, "
                    f"absolute max: {fallback_timeout}s)"
                )
                
                # Create tasks for both
                main_task = asyncio.create_task(coro)
                timeout_task = asyncio.create_task(self._wait_for_timeout())
                
                # Wait for either: completion, idle timeout, or fallback timeout
                done, pending = await asyncio.wait(
                    [main_task, timeout_task],
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=fallback_timeout
                )
                
                # Cancel monitoring
                self.monitoring_task.cancel()
                
                # Check what completed
                if main_task in done:
                    # Job completed successfully
                    # Cancel pending tasks
                    for task in pending:
                        task.cancel()
                    return await main_task
                elif self.timeout_event.is_set():
                    # Idle timeout triggered
                    main_task.cancel()
                    for task in pending:
                        task.cancel()
                    raise asyncio.TimeoutError(
                        f"Job idle for {self.idle_timeout_seconds}s (progress-aware timeout)"
                    )
                else:
                    # Fallback timeout triggered
                    main_task.cancel()
                    timeout_task.cancel()
                    raise asyncio.TimeoutError(
                        f"Job exceeded absolute maximum timeout of {fallback_timeout}s"
                    )
            else:
                # Only progress-aware timeout, no fallback
                logger.info(
                    f"🧠 Running with progress-aware timeout only (idle: {self.idle_timeout_seconds}s)"
                )
                
                main_task = asyncio.create_task(coro)
                timeout_task = asyncio.create_task(self._wait_for_timeout())
                
                # Wait for either completion or idle timeout
                done, pending = await asyncio.wait(
                    [main_task, timeout_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel monitoring
                self.monitoring_task.cancel()
                
                if main_task in done:
                    # Job completed
                    for task in pending:
                        task.cancel()
                    return await main_task
                else:
                    # Idle timeout
                    main_task.cancel()
                    timeout_task.cancel()
                    raise asyncio.TimeoutError(
                        f"Job idle for {self.idle_timeout_seconds}s (progress-aware timeout)"
                    )
        
        finally:
            # Cleanup
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
    
    async def _wait_for_timeout(self):
        """Wait for timeout event to be set."""
        await self.timeout_event.wait()


# Convenience function
async def run_with_progress_timeout(
    coro: Awaitable[Any],
    redis_client,
    job_id: str,
    idle_timeout_seconds: int = 600,
    fallback_timeout_seconds: Optional[int] = None,
    check_interval_seconds: int = 10
) -> Any:
    """
    Run a coroutine with progress-aware timeout.
    
    Convenience function that creates a ProgressAwareTimeout instance
    and runs the coroutine with it.
    
    Args:
        coro: Coroutine to run
        redis_client: Redis client for progress monitoring
        job_id: Job ID to monitor
        idle_timeout_seconds: Seconds of no progress before timeout (default: 600)
        fallback_timeout_seconds: Optional absolute maximum timeout
        check_interval_seconds: How often to check progress (default: 10)
    
    Returns:
        Result of the coroutine
    
    Raises:
        asyncio.TimeoutError: If idle or fallback timeout reached
    
    Example:
        ```python
        result = await run_with_progress_timeout(
            job_processor.process(job),
            redis_client=redis,
            job_id=str(job.id),
            idle_timeout_seconds=600,  # 10 minutes idle
            fallback_timeout_seconds=7200  # 2 hours absolute max
        )
        ```
    """
    timeout_manager = ProgressAwareTimeout(
        redis_client=redis_client,
        job_id=job_id,
        idle_timeout_seconds=idle_timeout_seconds,
        check_interval_seconds=check_interval_seconds
    )
    
    return await timeout_manager.run_with_progress_timeout(
        coro,
        fallback_timeout=fallback_timeout_seconds
    )

