"""
Retry Worker

Automatically retries failed document processing with intelligent backoff and circuit breaker.

Features:
- Polls RETRY_STREAM for failed documents
- Exponential backoff (2^n minutes)
- Circuit breaker (prevents overwhelming services)
- Max 5 retries before dead letter
- Batch processing (10 docs at a time)
- Statistics tracking
- Singleton pattern

Created: 2025-10-26
Phase: 2.1 (Retry Infrastructure)
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit tripped, blocking retries
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent overwhelming failing services.
    
    Features:
    - Tracks failure rate
    - Opens circuit after threshold failures
    - Auto-recovery after cooldown period
    - Half-open state for testing recovery
    
    States:
    - CLOSED: Normal operation, all retries allowed
    - OPEN: Circuit tripped, all retries blocked
    - HALF_OPEN: Testing recovery, limited retries allowed
    """
    
    def __init__(
        self,
        failure_threshold: int = 10,
        recovery_timeout_seconds: int = 300,  # 5 minutes
        half_open_max_calls: int = 3
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures to trip circuit
            recovery_timeout_seconds: Time to wait before testing recovery
            half_open_max_calls: Max calls to allow in half-open state
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None
        self.half_open_calls = 0
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        logger.info(
            f"🔌 CircuitBreaker initialized: "
            f"threshold={failure_threshold}, "
            f"recovery_timeout={recovery_timeout_seconds}s"
        )
    
    def call(self) -> bool:
        """
        Check if a call should be allowed.
        
        Returns:
            True if call is allowed, False if circuit is open
        """
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            
            elif self.state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self.opened_at:
                    elapsed = (datetime.utcnow() - self.opened_at).total_seconds()
                    if elapsed >= self.recovery_timeout_seconds:
                        # Transition to half-open
                        self.state = CircuitState.HALF_OPEN
                        self.half_open_calls = 0
                        logger.info(
                            f"🔌 Circuit breaker → HALF_OPEN "
                            f"(testing recovery after {elapsed:.0f}s)"
                        )
                        return True
                
                # Still open, block call
                return False
            
            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited calls to test recovery
                if self.half_open_calls < self.half_open_max_calls:
                    self.half_open_calls += 1
                    return True
                
                # Max half-open calls reached, block
                return False
            
            return False
    
    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self.success_count += 1
            
            if self.state == CircuitState.HALF_OPEN:
                # Successful recovery, close circuit
                logger.info(
                    f"✅ Circuit breaker → CLOSED "
                    f"(recovery confirmed after {self.half_open_calls} test calls)"
                )
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
                self.opened_at = None
            
            elif self.state == CircuitState.CLOSED:
                # Reset failure count on success
                if self.failure_count > 0:
                    logger.debug(
                        f"Circuit breaker: Success after {self.failure_count} failures, resetting"
                    )
                    self.failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.state == CircuitState.HALF_OPEN:
                # Failed recovery, reopen circuit
                logger.warning(
                    f"🔴 Circuit breaker → OPEN "
                    f"(recovery failed on attempt {self.half_open_calls})"
                )
                self.state = CircuitState.OPEN
                self.opened_at = datetime.utcnow()
                self.half_open_calls = 0
            
            elif self.state == CircuitState.CLOSED:
                # Check if threshold reached
                if self.failure_count >= self.failure_threshold:
                    logger.warning(
                        f"🔴 Circuit breaker → OPEN "
                        f"(threshold reached: {self.failure_count} failures)"
                    )
                    self.state = CircuitState.OPEN
                    self.opened_at = datetime.utcnow()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        with self._lock:
            time_until_recovery = None
            if self.state == CircuitState.OPEN and self.opened_at:
                elapsed = (datetime.utcnow() - self.opened_at).total_seconds()
                time_until_recovery = max(0, self.recovery_timeout_seconds - elapsed)
            
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "opened_at": self.opened_at.isoformat() if self.opened_at else None,
                "time_until_recovery_seconds": time_until_recovery,
                "half_open_calls": self.half_open_calls if self.state == CircuitState.HALF_OPEN else None
            }


class RetryWorker:
    """
    Retry Worker for automatic document retry.
    
    Features:
    - Polls RETRY_STREAM for documents ready to retry
    - Exponential backoff (2^n minutes)
    - Circuit breaker to prevent service overload
    - Max retries before moving to dead letter queue
    - Batch processing for efficiency
    - Statistics tracking
    
    Architecture:
    - Similar to IngestionWorker (reuses pattern)
    - Singleton pattern (one worker per service)
    - Async event loop
    - Graceful shutdown
    """
    
    def __init__(
        self,
        batch_size: int = 10,
        poll_interval_seconds: int = 10,
        max_retries: int = 5
    ):
        """
        Initialize retry worker.
        
        Args:
            batch_size: Number of documents to retry per batch
            poll_interval_seconds: How often to poll retry queue
            max_retries: Maximum retry attempts before dead letter
        """
        self.batch_size = batch_size
        self.poll_interval_seconds = poll_interval_seconds
        self.max_retries = max_retries
        
        # Worker state
        self.running = False
        self.worker_id = f"retry_worker_{id(self)}"
        self._task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=10,
            recovery_timeout_seconds=300,  # 5 minutes
            half_open_max_calls=3
        )
        
        # Statistics
        self.stats = {
            "total_retried": 0,
            "total_recovered": 0,
            "total_failed": 0,
            "total_moved_to_dlq": 0,
            "batches_processed": 0,
            "circuit_breaker_trips": 0,
            "started_at": None,
            "last_poll_at": None
        }
        
        logger.info(
            f"🔄 RetryWorker initialized: "
            f"batch_size={batch_size}, "
            f"poll_interval={poll_interval_seconds}s, "
            f"max_retries={max_retries}"
        )
    
    async def start(self) -> None:
        """Start the retry worker."""
        if self.running:
            logger.warning("RetryWorker already running")
            return
        
        logger.info(f"🚀 Starting RetryWorker {self.worker_id}")
        
        self.running = True
        self.stats["started_at"] = datetime.utcnow().isoformat()
        self._stop_event.clear()
        
        # Start worker loop
        self._task = asyncio.create_task(self._worker_loop())
        
        logger.info(f"✅ RetryWorker {self.worker_id} started")
    
    async def stop(self) -> None:
        """Stop the retry worker gracefully."""
        if not self.running:
            logger.warning("RetryWorker not running")
            return
        
        logger.info(f"🛑 Stopping RetryWorker {self.worker_id}")
        
        self.running = False
        self._stop_event.set()
        
        # Wait for worker loop to finish
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=30.0)
                logger.info("✅ RetryWorker stopped gracefully")
            except asyncio.TimeoutError:
                logger.warning("⚠️  RetryWorker stop timed out, cancelling task")
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass
        
        logger.info(f"✅ RetryWorker {self.worker_id} stopped")
    
    async def _worker_loop(self) -> None:
        """
        Main worker loop.
        
        Continuously polls retry queue and processes ready documents.
        """
        logger.info(f"🔄 RetryWorker loop started")
        
        try:
            while self.running and not self._stop_event.is_set():
                try:
                    # Check circuit breaker
                    if not self.circuit_breaker.call():
                        cb_state = self.circuit_breaker.get_state()
                        logger.warning(
                            f"🔴 Circuit breaker OPEN, skipping retry poll "
                            f"(recovery in {cb_state.get('time_until_recovery_seconds', 0):.0f}s)"
                        )
                        
                        # Wait before next check
                        await asyncio.sleep(self.poll_interval_seconds)
                        continue
                    
                    # Poll for documents ready to retry
                    self.stats["last_poll_at"] = datetime.utcnow().isoformat()
                    
                    retry_items = await self._get_next_retries()
                    
                    if retry_items:
                        logger.info(f"📥 Found {len(retry_items)} documents ready for retry")
                        
                        # Process batch
                        batch_result = await self._process_retry_batch(retry_items)
                        
                        # Update stats
                        self.stats["batches_processed"] += 1
                        self.stats["total_recovered"] += batch_result["recovered"]
                        self.stats["total_failed"] += batch_result["failed"]
                        self.stats["total_moved_to_dlq"] += batch_result["moved_to_dlq"]
                        
                        # Update circuit breaker based on batch success rate
                        success_rate = batch_result["recovered"] / len(retry_items) if len(retry_items) > 0 else 0
                        
                        if success_rate >= 0.5:  # At least 50% success
                            self.circuit_breaker.record_success()
                        else:
                            self.circuit_breaker.record_failure()
                            if self.circuit_breaker.state == CircuitState.OPEN:
                                self.stats["circuit_breaker_trips"] += 1
                        
                        logger.info(
                            f"✅ Batch complete: "
                            f"{batch_result['recovered']} recovered, "
                            f"{batch_result['failed']} failed, "
                            f"{batch_result['moved_to_dlq']} → DLQ"
                        )
                    else:
                        logger.debug("No documents ready for retry")
                    
                    # Wait before next poll
                    try:
                        await asyncio.wait_for(
                            self._stop_event.wait(),
                            timeout=self.poll_interval_seconds
                        )
                        # Stop event was set
                        break
                    except asyncio.TimeoutError:
                        # Normal timeout, continue loop
                        pass
                
                except Exception as e:
                    logger.error(f"❌ Error in retry worker loop: {e}", exc_info=True)
                    self.circuit_breaker.record_failure()
                    
                    # Wait before retrying
                    await asyncio.sleep(self.poll_interval_seconds)
        
        except asyncio.CancelledError:
            logger.info("RetryWorker loop cancelled")
            raise
        
        finally:
            logger.info("🛑 RetryWorker loop ended")
    
    async def _get_next_retries(self) -> List[Dict[str, Any]]:
        """
        Get documents ready for retry from Redis stream.
        
        Returns:
            List of retry item dicts
        """
        from ...utils.redis_client import get_redis_client
        
        try:
            redis_client = get_redis_client()
            
            # Read from retry stream
            # Only get documents where next_retry_at <= now
            messages = await redis_client.read_from_stream(
                stream=redis_client.RETRY_STREAM,
                consumer_name=self.worker_id,
                count=self.batch_size,
                block=1000  # Block for 1 second
            )
            
            if not messages:
                return []
            
            # Filter by next_retry_at
            now = datetime.utcnow()
            ready_items = []
            
            for msg_id, data in messages:
                try:
                    next_retry_str = data.get("next_retry_at")
                    if next_retry_str:
                        next_retry = datetime.fromisoformat(next_retry_str)
                        
                        if next_retry <= now:
                            # Parse document_info
                            import json
                            document_info = json.loads(data.get("document_info", "{}"))
                            
                            ready_items.append({
                                "message_id": msg_id,
                                "job_id": data.get("job_id"),
                                "document_info": document_info,
                                "error_type": data.get("error_type"),
                                "error_message": data.get("error_message"),
                                "retry_count": int(data.get("retry_count", 0)),
                                "failed_at": data.get("failed_at"),
                                "next_retry_at": next_retry_str
                            })
                        else:
                            # Not ready yet, acknowledge and skip
                            await redis_client.client.xack(
                                redis_client.RETRY_STREAM,
                                redis_client.CONSUMER_GROUP,
                                msg_id
                            )
                
                except Exception as e:
                    logger.error(f"Error parsing retry item: {e}")
                    # Acknowledge to prevent reprocessing bad messages
                    await redis_client.client.xack(
                        redis_client.RETRY_STREAM,
                        redis_client.CONSUMER_GROUP,
                        msg_id
                    )
            
            return ready_items
        
        except Exception as e:
            logger.error(f"Error getting next retries: {e}", exc_info=True)
            return []
    
    async def _process_retry_batch(self, retry_items: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Process a batch of retry items.
        
        Args:
            retry_items: List of retry item dicts
        
        Returns:
            Dict with counts: recovered, failed, moved_to_dlq
        """
        result = {
            "recovered": 0,
            "failed": 0,
            "moved_to_dlq": 0
        }
        
        from ...utils.redis_client import get_redis_client
        redis_client = get_redis_client()
        
        for item in retry_items:
            try:
                retry_result = await self._retry_document(item)
                
                if retry_result["success"]:
                    result["recovered"] += 1
                    
                    # Acknowledge successful retry
                    await redis_client.client.xack(
                        redis_client.RETRY_STREAM,
                        redis_client.CONSUMER_GROUP,
                        item["message_id"]
                    )
                    
                    logger.info(
                        f"✅ Document recovered: {item['document_info'].get('file_path', 'unknown')} "
                        f"(retry {item['retry_count'] + 1}/{self.max_retries})"
                    )
                
                else:
                    result["failed"] += 1
                    
                    # Handle retry failure
                    await self._handle_retry_failure(item)
            
            except Exception as e:
                logger.error(f"Error processing retry item: {e}", exc_info=True)
                result["failed"] += 1
                
                try:
                    await self._handle_retry_failure(item)
                except Exception as handle_error:
                    logger.error(f"Error handling retry failure: {handle_error}")
        
        return result
    
    async def _retry_document(self, item: Dict[str, Any]) -> Dict[str, bool]:
        """
        Retry processing a single document.
        
        Args:
            item: Retry item dict
        
        Returns:
            Dict with success boolean
        """
        from ..ingestion.job_processor import JobProcessor
        from ...storage import get_database
        from ...storage.repositories import IngestionJobRepository
        
        try:
            document_info = item["document_info"]
            job_id = item["job_id"]
            
            logger.info(
                f"🔄 Retrying document: {document_info.get('file_path', 'unknown')} "
                f"(attempt {item['retry_count'] + 1}/{self.max_retries})"
            )
            
            # Get job from database
            db = get_database()
            async with db.session() as session:
                job_repo = IngestionJobRepository(session)
                from uuid import UUID
                job = await job_repo.get_by_id(UUID(job_id))
                
                if not job:
                    logger.error(f"Job {job_id} not found, cannot retry document")
                    return {"success": False}
                
                # Create job processor
                processor = JobProcessor(job_id=UUID(job_id))
                
                # Retry document processing
                # Note: This is a simplified retry - in production you'd want to
                # reconstruct the exact processing context
                from pathlib import Path
                file_path = document_info.get("file_path")
                
                if not file_path:
                    logger.error("No file_path in document_info")
                    return {"success": False}
                
                # Read file content
                full_path = Path(document_info.get("repo_path", "")) / file_path
                
                if not full_path.exists():
                    logger.error(f"File not found: {full_path}")
                    return {"success": False}
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Process document
                process_result = await processor._process_snapshot_document(
                    file_path=file_path,
                    content=content,
                    job=job
                )
                
                return {"success": process_result.get("success", False)}
        
        except Exception as e:
            logger.error(f"Error retrying document: {e}", exc_info=True)
            return {"success": False}
    
    async def _handle_retry_failure(self, item: Dict[str, Any]) -> None:
        """
        Handle a retry failure.
        
        Either re-enqueue with incremented retry count or move to dead letter queue.
        
        Args:
            item: Retry item dict
        """
        from ...utils.redis_client import get_redis_client
        
        redis_client = get_redis_client()
        new_retry_count = item["retry_count"] + 1
        
        if new_retry_count >= self.max_retries:
            # Max retries exceeded, move to dead letter queue
            logger.warning(
                f"💀 Max retries exceeded for {item['document_info'].get('file_path', 'unknown')}, "
                f"moving to dead letter queue"
            )
            
            await redis_client.move_to_dead_letter(
                job_id=item["job_id"],
                document_info=item["document_info"],
                error_type=item["error_type"],
                error_message=item["error_message"],
                retry_count=new_retry_count
            )
            
            # Acknowledge from retry stream
            await redis_client.client.xack(
                redis_client.RETRY_STREAM,
                redis_client.CONSUMER_GROUP,
                item["message_id"]
            )
            
            self.stats["total_moved_to_dlq"] += 1
        
        else:
            # Re-enqueue with incremented retry count
            logger.info(
                f"🔄 Re-enqueueing {item['document_info'].get('file_path', 'unknown')} "
                f"for retry {new_retry_count + 1}/{self.max_retries}"
            )
            
            await redis_client.enqueue_failed_document(
                job_id=item["job_id"],
                document_info=item["document_info"],
                error_type=item["error_type"],
                error_message=item["error_message"],
                retry_count=new_retry_count
            )
            
            # Acknowledge from retry stream
            await redis_client.client.xack(
                redis_client.RETRY_STREAM,
                redis_client.CONSUMER_GROUP,
                item["message_id"]
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry worker statistics."""
        return {
            **self.stats,
            "running": self.running,
            "worker_id": self.worker_id,
            "circuit_breaker": self.circuit_breaker.get_state()
        }


# ============================================================================
# Singleton Pattern
# ============================================================================

_retry_worker_instance: Optional[RetryWorker] = None
_retry_worker_lock = threading.Lock()


def get_retry_worker() -> RetryWorker:
    """
    Get the global retry worker instance.
    
    Ensures only one instance of the worker is created and managed.
    """
    global _retry_worker_instance
    
    with _retry_worker_lock:
        if _retry_worker_instance is None:
            logger.info("🏗️  [SINGLETON] Creating new RetryWorker instance")
            _retry_worker_instance = RetryWorker()
        else:
            logger.debug("♻️  [SINGLETON] Reusing existing RetryWorker instance")
    
    return _retry_worker_instance

