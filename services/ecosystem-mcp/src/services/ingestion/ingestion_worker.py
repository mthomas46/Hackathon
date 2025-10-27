"""
Ingestion Worker

Background worker that processes document ingestion jobs from Redis streams.
Coordinates the entire ingestion pipeline from Git → Database → ChromaDB.
"""

import asyncio
import logging
import time
import threading
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

from ...config import settings
from ...utils.redis_client import get_redis_client
from ...utils.graceful_shutdown import get_shutdown_handler, is_shutdown_requested
from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from .job_processor import JobProcessor

logger = logging.getLogger(__name__)


class IngestionWorker:
    """
    Background worker for processing ingestion jobs.
    
    Polls Redis streams for new ingestion jobs and processes them
    asynchronously using the JobProcessor.
    
    Features:
    - Automatic job polling
    - Error handling with retries
    - Graceful shutdown
    - Job status tracking
    - Performance monitoring
    """
    
    def __init__(self):
        """Initialize the ingestion worker."""
        self.worker_id = str(uuid4())[:8]  # Short unique ID for this worker instance
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.job_processor = JobProcessor(worker_id=self.worker_id)
        self.shutdown_handler = None
        self.current_job_id: Optional[UUID] = None
        self._start_time = time.time()  # Track uptime
        self._iteration_count = 0  # Track loop iterations
        self._last_heartbeat = time.time()  # Track heartbeat
        logger.info(f"🏗️  IngestionWorker initialized (ID: {self.worker_id})")
    
    async def start(self):
        """
        Start the ingestion worker.
        
        Begins polling Redis streams for ingestion jobs and processing them.
        """
        logger.info(f"🚀 start() called, current running state: {self.running}")
        
        if self.running:
            logger.warning("IngestionWorker already running")
            return
        
        # Setup graceful shutdown handler
        logger.info("🔧 Setting up graceful shutdown handler...")
        self.shutdown_handler = get_shutdown_handler(
            max_shutdown_time=60,
            checkpoint_callback=self._save_checkpoint,
            cleanup_callback=self._cleanup
        )
        logger.info("✅ Shutdown handler setup complete")
        
        # 🧪 TEST: Verify Redis connection before starting
        logger.info("🧪 Testing Redis connection...")
        try:
            redis = get_redis_client()
            await redis.connect()
            
            # Test read from stream
            test_messages = await redis.client.xrange(redis.INGESTION_STREAM, '-', '+', count=1)
            logger.info(f"🧪 Redis connection test PASSED: {len(test_messages)} messages found in stream")
            logger.info(f"🧪 Stream name: {redis.INGESTION_STREAM}")
            logger.info(f"🧪 Consumer group: {redis.CONSUMER_GROUP}")
            
            # Test consumer group
            try:
                group_info = await redis.client.xinfo_groups(redis.INGESTION_STREAM)
                logger.info(f"🧪 Consumer groups: {group_info}")
            except Exception as e:
                logger.warning(f"⚠️  Could not get consumer group info: {e}")
                
        except Exception as e:
            logger.error(f"❌ Redis connection test FAILED: {e}", exc_info=True)
            raise
        
        self.running = True
        logger.info(f"🚀 Creating worker loop task... (running={self.running})")
        self._task = asyncio.create_task(self._worker_loop())
        
        # ✅ CRITICAL: Ensure task persists (prevent garbage collection)
        asyncio.ensure_future(self._task)
        
        logger.info(f"✅ Task created: {self._task}")
        logger.info(f"✅ Task done: {self._task.done()}")
        logger.info(f"✅ Task cancelled: {self._task.cancelled()}")
        logger.info(f"✅ Task ID: {id(self._task)}")
        logger.info("✅ IngestionWorker started with graceful shutdown handler and persistence")
        
        # Monitor task for a few seconds to see if it starts
        logger.info("🔍 Monitoring task startup...")
        for i in range(3):
            await asyncio.sleep(1)
            logger.info(f"📊 Task state after {i+1}s: done={self._task.done()}, cancelled={self._task.cancelled()}")
            if self._task.done():
                try:
                    result = self._task.result()
                    logger.error(f"⚠️  Task completed unexpectedly with result: {result}")
                except Exception as e:
                    logger.error(f"❌ Task failed with exception: {e}", exc_info=True)
                break
        logger.info("🔍 Task monitoring complete")
        
        # Give the task a moment to start
        await asyncio.sleep(0.1)
        logger.info(f"🔍 Task status after 0.1s: {self._task}")
        if self._task.done():
            try:
                result = self._task.result()
                logger.error(f"❌ Task completed immediately with result: {result}")
            except Exception as e:
                logger.error(f"❌ Task failed immediately: {e}", exc_info=True)
    
    async def stop(self):
        """
        Stop the ingestion worker gracefully.
        
        Waits for the current job to complete before stopping.
        """
        if not self.running:
            logger.warning("IngestionWorker not running")
            return
        
        logger.info("Stopping IngestionWorker...")
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ IngestionWorker stopped")
    
    async def _worker_loop(self):
        """
        Main worker loop.
        
        Continuously polls Redis streams for new jobs and processes them.
        """
        try:
            logger.info("=" * 80)
            logger.info("🔄 WORKER LOOP STARTING")
            logger.info("=" * 80)
            logger.info("🔍 DEBUG: About to log worker ID")
            logger.info(f"🔄 Worker ID: {self.worker_id}")
            logger.info("🔍 DEBUG: About to log running flag")
            logger.info(f"🔄 Running flag: {self.running}")
            logger.info("🔍 DEBUG: About to get event loop")
            try:
                event_loop = asyncio.get_event_loop()
                logger.info(f"🔄 Current event loop: {event_loop}")
            except Exception as e:
                logger.error(f"❌ Failed to get event loop: {e}")
            logger.info("=" * 80)
            
            logger.info("🔍 DEBUG: About to initialize loop_count")
            loop_count = 0
            logger.info(f"🔍 DEBUG: loop_count initialized to {loop_count}")
            logger.info(f"🔍 DEBUG: About to check self.running value: {self.running}")
            logger.info("🔍 DEBUG: About to enter while loop")
            
            while self.running:
                logger.info(f"🔍 DEBUG: ✅ INSIDE while loop! Iteration {loop_count + 1}")
                logger.info(f"🔍 DEBUG: self.running = {self.running}")
                loop_count += 1
                
                # 💓 Heartbeat every 5 iterations
                if loop_count % 5 == 1:
                    logger.info(f"💓 WORKER HEARTBEAT - Loop #{loop_count} - Running: {self.running}")
                
                try:
                    # Check for shutdown request
                    if is_shutdown_requested():
                        logger.info("🛑 Shutdown requested, stopping worker loop")
                        if self.shutdown_handler:
                            await self.shutdown_handler.shutdown()
                        break
                    
                    # Get next job from Redis stream
                    logger.info(f"📡 Calling _get_next_job()...")
                    result = await self._get_next_job()
                    logger.info(f"📡 _get_next_job() returned: {result}")
                    
                    if result:
                        message_id, job_id = result
                        self.current_job_id = job_id
                        
                        logger.info(f"🎯 Processing job: {job_id}")
                        
                        # Mark that we're finishing current work
                        if self.shutdown_handler and is_shutdown_requested():
                            await self.shutdown_handler.finish_current_work(f"job {job_id}")
                        
                        # Add timeout to prevent jobs from blocking forever
                        try:
                            full_job_timeout = 14400  # 4 hours
                            logger.info(f"⏱️  Starting job processing with {full_job_timeout/3600:.1f} hour timeout...")
                            await asyncio.wait_for(
                                self._process_job(job_id, message_id),
                                timeout=full_job_timeout
                            )
                            logger.info(f"✅ Job processing completed: {job_id}")
                        except asyncio.TimeoutError:
                            logger.error(f"⏰ Job {job_id} timed out after {full_job_timeout/3600:.1f} hours!")
                            # Mark job as failed due to timeout
                            async with get_database().session() as session:
                                from ...storage.repositories import IngestionJobRepository
                                from datetime import datetime
                                repo = IngestionJobRepository(session)
                                job = await repo.get_by_id(job_id)
                                if job:
                                    job.status = "failed"
                                    job.completed_at = ensure_utc_naive(datetime.utcnow())  # ✅ UTC STANDARDIZATION Sprint 2
                                    job.error_message = f"Job timed out after {full_job_timeout/3600:.1f} hours"
                                    await repo.update(job)
                                    await session.commit()
                                    logger.info(f"✅ Marked job {job_id} as failed due to timeout")
                        
                        # ✅ CRITICAL: ACK the message after processing
                        redis = get_redis_client()
                        await redis.client.xack(
                            redis.INGESTION_STREAM,
                            redis.CONSUMER_GROUP,
                            message_id
                        )
                        logger.debug(f"✅ ACK'd message {message_id}")
                        
                        self.current_job_id = None
                    else:
                        # No jobs available, wait before checking again
                        logger.info(f"😴 No jobs available, sleeping 5s...")
                        await asyncio.sleep(5)
                
                except Exception as e:
                    logger.error(f"❌ Error in worker loop: {e}", exc_info=True)
                    logger.error(f"❌ Exception type: {type(e).__name__}")
                    logger.error(f"❌ Sleeping 10s before retry...")
                    await asyncio.sleep(10)  # Back off on errors
            
            logger.info(f"✅ Worker loop stopped after {loop_count} iterations")
            logger.info(f"✅ Final running flag: {self.running}")
        except Exception as e:
            logger.error(f"❌ FATAL ERROR in _worker_loop: {e}", exc_info=True)
            raise
    
    async def _get_next_job(self) -> Optional[tuple[str, UUID]]:
        """
        Get the next job from Redis stream.
        
        Returns:
            Tuple of (message_id, job_id) if available, None otherwise
        """
        try:
            logger.info(f"🔍 _get_next_job() START")
            redis = get_redis_client()
            logger.info(f"🔍 Got Redis client: {redis}")
            logger.info(f"🔍 Redis connected: {redis._connected}")
            
            # 🔍 Enhanced logging to debug Redis stream issues
            logger.info(f"🔍 Stream name: {redis.INGESTION_STREAM}")
            logger.info(f"🔍 Consumer group: {redis.CONSUMER_GROUP}")
            logger.info(f"🔍 Consumer name: worker-{self.worker_id}")
            
            # Read from ingestion stream
            logger.info(f"🔍 Calling redis.read_from_stream()...")
            messages = await redis.read_from_stream(
                stream=redis.INGESTION_STREAM,
                consumer_name=f"worker-{self.worker_id}",
                count=1,
                block=1000  # Block for 1 second
            )
            
            logger.info(f"🔍 Redis returned {len(messages) if messages else 0} messages")
            logger.info(f"🔍 Messages: {messages}")
            
            if messages:
                # Extract message_id and job_id from message
                # messages is a list of (message_id, data) tuples
                message_id, data = messages[0]
                logger.info(f"📨 Received message {message_id}: {data}")
                job_id_str = data.get("job_id")
                
                # 🎯 FIX #2: Validate message has job_id
                if not job_id_str:
                    logger.error(f"❌ Message {message_id} missing job_id: {data}")
                    # ACK invalid message to remove from queue
                    await redis.client.xack(redis.INGESTION_STREAM, redis.CONSUMER_GROUP, message_id)
                    return None
                
                # 🎯 FIX #2: Validate job_id format
                try:
                    job_id = UUID(job_id_str)
                except ValueError as e:
                    logger.error(f"❌ Invalid job_id format '{job_id_str}': {e}")
                    # ACK invalid message to remove from queue
                    await redis.client.xack(redis.INGESTION_STREAM, redis.CONSUMER_GROUP, message_id)
                    return None
                
                logger.info(f"✅ Found job_id: {job_id}")
                return (message_id, job_id)
            
            return None
        
        except Exception as e:
            logger.error(f"❌ Error reading from Redis stream: {e}", exc_info=True)
            return None
    
    async def _process_job(self, job_id: UUID, message_id: str):
        """
        Process a single ingestion job.
        
        Args:
            job_id: ID of the job to process
            message_id: Redis message ID for ACKing
        """
        logger.info(f"📍 _process_job START: {job_id}")
        
        async with get_database().session() as session:
            repo = IngestionJobRepository(session)
            
            try:
                # Get job from database
                logger.info(f"📍 Fetching job from database...")
                job = await repo.get_by_id(job_id)
                logger.info(f"📍 Job fetched: {job}")
                
                # 🎯 FIX #3: Handle orphaned jobs (job doesn't exist in DB)
                if not job:
                    logger.error(f"❌ Job {job_id} not found in database - orphaned Redis message")
                    # ACK message to remove from queue
                    redis = get_redis_client()
                    await redis.client.xack(redis.INGESTION_STREAM, redis.CONSUMER_GROUP, message_id)
                    logger.info(f"✅ Orphaned message {message_id} ACK'd and removed from queue")
                    return
                
                # 🎯 FIX #1: Validate job state before processing
                if job.status not in ["queued", "pending"]:
                    logger.warning(f"⚠️  Job {job_id} is in '{job.status}' state (expected 'queued' or 'pending'), skipping")
                    logger.warning(f"   Created: {job.created_at}, Started: {job.started_at}, Completed: {job.completed_at}")
                    # ACK message to remove from queue
                    redis = get_redis_client()
                    await redis.client.xack(redis.INGESTION_STREAM, redis.CONSUMER_GROUP, message_id)
                    logger.info(f"✅ Already-processed job message {message_id} ACK'd and removed from queue")
                    return
                
                # Update status to processing
                logger.info(f"📍 Updating job status to 'processing'...")
                job.status = "processing"
                await repo.update(job)
                await session.commit()
                logger.info(f"📍 Status updated successfully")
                
                logger.info(f"📍 Starting job processor: mode={job.mode}, repo={job.repo_path}")
                
                # Process the job using JobProcessor with full job timeout protection
                logger.info(f"📍 Calling job_processor.process()...")
                
                # TODO: Re-enable progress-aware timeout once asyncio.wait() issue is fixed
                # For now, use extended timeout to allow large jobs
                full_job_timeout = 14400  # 4 hours for large repositories
                
                try:
                    logger.info(f"⏱️  Using extended timeout: {full_job_timeout}s (4 hours)")
                    
                    result = await asyncio.wait_for(
                        self.job_processor.process(job),
                        timeout=full_job_timeout
                    )
                    logger.info(f"📍 Job processor returned: success={result.get('success')}, processed={result.get('processed_documents')}")
                except asyncio.TimeoutError:
                    logger.error(f"⏱️  TIMEOUT: Job exceeded {full_job_timeout}s")
                    result = {
                        "success": False,
                        "processed_documents": 0,
                        "total_documents": 0,
                        "failed_documents": 0,
                        "skipped_documents": 0,
                        "embeddings_generated": 0,
                        "total_cost_usd": 0.0,
                        "error": f"Job timed out after {full_job_timeout} seconds"
                    }
                    logger.info(f"📍 Job processor timed out, returning failure result")
                
                # Update job with results
                logger.info(f"📍 Updating job with results...")
                job.status = "completed" if result["success"] else "failed"
                job.completed_at = ensure_utc_naive(datetime.utcnow())  # ✅ UTC STANDARDIZATION Sprint 2
                job.processed_documents = result.get("processed_documents", 0)
                job.total_documents = result.get("total_documents", 0)
                job.failed_documents = result.get("failed_documents", 0)
                job.skipped_documents = result.get("skipped_documents", 0)  # NEW
                job.embeddings_generated = result.get("embeddings_generated", 0)
                job.total_cost_usd = result.get("total_cost_usd", 0.0)
                
                if not result["success"]:
                    job.error_message = result.get("error", "Unknown error")
                
                logger.info(f"📍 Saving job updates to database...")
                await repo.update(job)
                await session.commit()
                logger.info(f"📍 Job updates saved")
                
                if result["success"]:
                    logger.info(
                        f"✅ Job {job_id} completed: "
                        f"{result['processed_documents']}/{result['total_documents']} documents, "
                        f"{result['skipped_documents']} skipped, "
                        f"{result['embeddings_generated']} embeddings, "
                        f"${result['total_cost_usd']:.4f} cost"
                    )
                else:
                    logger.error(f"❌ Job {job_id} failed: {result.get('error')}")
                
                logger.info(f"📍 _process_job END: {job_id}")
            
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
                
                # Update job status to failed
                try:
                    job = await repo.get_by_id(job_id)
                    if job:
                        job.status = "failed"
                        job.completed_at = ensure_utc_naive(datetime.utcnow())  # ✅ UTC STANDARDIZATION Sprint 2
                        job.error_message = str(e)
                        await repo.update(job)
                        await session.commit()
                except Exception as update_error:
                    logger.error(f"Failed to update job status: {update_error}")
    
    async def _save_checkpoint(self):
        """
        Save checkpoint for current job.
        
        Called during graceful shutdown to preserve job state.
        """
        if not self.current_job_id:
            logger.debug("No current job to checkpoint")
            return
        
        try:
            logger.info(f"💾 Saving checkpoint for job {self.current_job_id}")
            
            async with get_database().session() as session:
                repo = IngestionJobRepository(session)
                job = await repo.get_by_id(self.current_job_id)
                
                if job:
                    # Update metadata with shutdown info
                    from sqlalchemy.orm.attributes import flag_modified
                    
                    metadata = job.job_metadata.copy() if job.job_metadata else {}
                    metadata['checkpoint_saved_at'] = datetime.utcnow().isoformat()
                    metadata['shutdown_requested'] = True
                    metadata['worker_id'] = self.worker_id
                    job.job_metadata = metadata
                    flag_modified(job, 'job_metadata')
                    
                    await repo.update(job)
                    await session.commit()
                    
                    logger.info(f"✅ Checkpoint saved for job {self.current_job_id}")
        
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}", exc_info=True)
    
    async def _cleanup(self):
        """
        Cleanup tasks before shutdown.
        
        Called during graceful shutdown.
        """
        try:
            logger.info("🧹 Running cleanup tasks...")
            
            # Log worker status
            logger.info(f"Worker {self.worker_id} shutdown complete")
            
            # Future: Close any open connections, flush buffers, etc.
            
            logger.info("✅ Cleanup complete")
        
        except Exception as e:
            logger.error(f"Failed to run cleanup: {e}", exc_info=True)


# Global worker instance
_worker_instance: Optional[IngestionWorker] = None
_worker_lock = threading.Lock()

def get_ingestion_worker() -> IngestionWorker:
    global _worker_instance
    
    with _worker_lock:
        if _worker_instance is None:
            logger.info("🏗️  [SINGLETON] Creating NEW worker instance")
            _worker_instance = IngestionWorker()
        else:
            logger.info(
                f"♻️  [SINGLETON] Reusing EXISTING worker "
                f"(ID: {_worker_instance.worker_id}, running={_worker_instance.running})"
            )
        return _worker_instance


async def start_ingestion_worker():
    """Start the global ingestion worker."""
    worker = get_ingestion_worker()
    await worker.start()


async def stop_ingestion_worker():
    """Stop the global ingestion worker."""
    worker = get_ingestion_worker()
    await worker.stop()

