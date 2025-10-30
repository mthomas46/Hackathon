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
from ...utils.datetime_utils import ensure_utc_naive  # ✅ FIX: Add missing import
from ...utils.graceful_shutdown import get_shutdown_handler, is_shutdown_requested
from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from ...utils.job_events import publish_job_started, publish_job_completed, publish_job_failed  # ⚡ PHASE 2 ITEM 2.3
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
        self._jobs_processed = 0  # Track total jobs processed
        logger.info(f"🏗️  IngestionWorker initialized (ID: {self.worker_id})")
    
    async def send_heartbeat(self):
        """
        Send worker heartbeat to Redis.
        
        ⚡ OPTIMIZATION: Worker health monitoring
        Allows dashboard to show live worker status and detect crashes.
        """
        try:
            redis = get_redis_client()
            heartbeat_key = f"worker_heartbeat:{self.worker_id}"
            
            heartbeat_data = {
                "worker_id": self.worker_id,
                "last_heartbeat": datetime.utcnow().isoformat(),
                "jobs_processed": self._jobs_processed,
                "current_job": str(self.current_job_id) if self.current_job_id else None,
                "status": "healthy",
                "uptime_seconds": int(time.time() - self._start_time),
                "iteration_count": self._iteration_count
            }
            
            import json
            # Set with 30 second TTL - if worker crashes, key expires automatically
            await redis.client.setex(
                heartbeat_key,
                30,  # TTL in seconds
                json.dumps(heartbeat_data)
            )
            
            self._last_heartbeat = time.time()
            logger.debug(f"💓 Heartbeat sent: {self.worker_id}")
            
        except Exception as e:
            logger.warning(f"Failed to send heartbeat: {e}")
    
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
            
            # 🧹 PHASE 2: Clean up dead consumers before processing
            try:
                logger.info("🧹 Cleaning up dead consumers...")
                deleted_count = await self._cleanup_dead_consumers(redis)
                if deleted_count > 0:
                    logger.warning(f"⚠️  Removed {deleted_count} dead consumers")
                else:
                    logger.info("✅ No dead consumers to clean up")
            except Exception as e:
                logger.warning(f"⚠️  Dead consumer cleanup failed: {e}")
            
            # 🎯 PHASE 3: Smart pointer management - only reset if needed
            try:
                logger.info("🔧 Checking if consumer group pointer needs reset...")
                needs_reset = await self._check_if_pointer_needs_reset(redis)
                
                if needs_reset:
                    logger.warning("⚠️  Pointer is ahead of messages, resetting to beginning...")
                    await redis.client.xgroup_setid(
                        name=redis.INGESTION_STREAM,
                        groupname=redis.CONSUMER_GROUP,
                        id="0-0"  # Start from very beginning
                    )
                    logger.info("✅ Consumer group reset to beginning (0-0)")
                else:
                    logger.info("✅ Pointer position is correct, no reset needed")
            except Exception as e:
                logger.warning(f"⚠️  Could not manage consumer group pointer: {e}")
            
            # 💾 PHASE 1: Recover stuck jobs from database
            try:
                logger.info("💾 Checking for stuck jobs in database...")
                recovered_count = await self._recover_stuck_jobs(redis)
                if recovered_count > 0:
                    logger.warning(f"⚠️  Recovered {recovered_count} stuck jobs from database")
                else:
                    logger.info("✅ No stuck jobs to recover")
            except Exception as e:
                logger.error(f"❌ Job recovery failed: {e}", exc_info=True)
            
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
    
    async def _cleanup_dead_consumers(self, redis) -> int:
        """
        Clean up dead/idle consumers from the consumer group.
        
        Phase 2 implementation: Remove consumers that have been idle for >1 hour
        to prevent consumer group bloat.
        
        Returns:
            Number of consumers deleted
        """
        try:
            # Get all consumers in the group
            consumers = await redis.client.xinfo_consumers(
                redis.INGESTION_STREAM,
                redis.CONSUMER_GROUP
            )
            
            deleted_count = 0
            ONE_HOUR_MS = 3600000  # 1 hour in milliseconds
            
            for consumer in consumers:
                consumer_name = consumer['name']
                idle_time = consumer['idle']
                pending_count = consumer['pending']
                
                # Only delete if idle >1 hour AND no pending messages
                if idle_time > ONE_HOUR_MS and pending_count == 0:
                    logger.info(
                        f"🧹 Deleting dead consumer: {consumer_name} "
                        f"(idle {idle_time/1000:.0f}s, pending {pending_count})"
                    )
                    await redis.client.xgroup_delconsumer(
                        redis.INGESTION_STREAM,
                        redis.CONSUMER_GROUP,
                        consumer_name
                    )
                    deleted_count += 1
                elif idle_time > ONE_HOUR_MS:
                    logger.warning(
                        f"⚠️  Consumer {consumer_name} is idle but has {pending_count} pending messages, not deleting"
                    )
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up dead consumers: {e}", exc_info=True)
            return 0
    
    async def _check_if_pointer_needs_reset(self, redis) -> bool:
        """
        Check if consumer group pointer is ahead of all messages.
        
        Phase 3 implementation: Smart pointer management - only reset if needed.
        
        Returns:
            True if pointer needs reset, False otherwise
        """
        try:
            # Get consumer group info
            groups = await redis.client.xinfo_groups(redis.INGESTION_STREAM)
            if not groups:
                return False
            
            group = groups[0]  # We only have one group
            last_delivered_id = group['last-delivered-id']
            
            # Get the max message ID in the stream
            messages = await redis.client.xrange(
                redis.INGESTION_STREAM,
                '-',
                '+',
                count=1
            )
            
            if not messages:
                # Stream is empty, no need to reset
                logger.info("Stream is empty, no pointer reset needed")
                return False
            
            # Get the last (most recent) message ID
            last_message_id = messages[-1][0]
            
            # Compare IDs (Redis stream IDs are in format "timestamp-sequence")
            # If last_delivered_id >= last_message_id, pointer is ahead or equal
            if last_delivered_id >= last_message_id:
                logger.warning(
                    f"Pointer ({last_delivered_id}) is ahead of/equal to last message ({last_message_id})"
                )
                return True
            else:
                logger.info(
                    f"Pointer ({last_delivered_id}) is behind last message ({last_message_id}), OK"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error checking pointer position: {e}", exc_info=True)
            # Conservative: don't reset if we can't determine
            return False
    
    async def _recover_stuck_jobs(self, redis) -> int:
        """
        Recover jobs stuck in 'queued' or 'processing' state.
        
        Phase 1 implementation: Database as source of truth.
        Re-queues jobs that are stuck (older than 5 minutes) and not in Redis.
        
        Returns:
            Number of jobs recovered
        """
        from datetime import datetime, timedelta
        
        try:
            db = get_database()
            async with db.session() as session:
                from ...storage.repositories import IngestionJobRepository
                repo = IngestionJobRepository(session)
                
                # Find jobs stuck in queued or processing state for >5 minutes
                cutoff_time = datetime.utcnow() - timedelta(minutes=5)
                
                # Get all potentially stuck jobs
                from sqlalchemy import select, or_
                from ...storage.db_models import IngestionJobModel
                
                stmt = select(IngestionJobModel).where(
                    or_(
                        IngestionJobModel.status == "queued",
                        IngestionJobModel.status == "processing"
                    ),
                    IngestionJobModel.updated_at < cutoff_time
                )
                
                result = await session.execute(stmt)
                stuck_jobs = result.scalars().all()
                
                if not stuck_jobs:
                    return 0
                
                logger.info(f"Found {len(stuck_jobs)} potentially stuck jobs")
                
                # Check which ones are actually in Redis (to avoid duplicates)
                recovered_count = 0
                
                for job in stuck_jobs:
                    job_id = str(job.id)
                    
                    # Check if job is already in Redis
                    in_redis = await self._is_job_in_redis(redis, job_id)
                    
                    if in_redis:
                        logger.debug(f"Job {job_id} is already in Redis, skipping")
                        continue
                    
                    # Re-queue the job
                    logger.warning(
                        f"💾 Recovering stuck job: {job_id} "
                        f"(status={job.status}, updated={job.updated_at})"
                    )
                    
                    try:
                        # Add to Redis stream
                        message_id = await redis.add_to_stream(
                            stream=redis.INGESTION_STREAM,
                            data={
                                "job_id": job_id,
                                "mode": job.mode,
                                "repo_path": job.repo_path or ""
                            }
                        )
                        
                        # Update job status back to queued
                        job.status = "queued"
                        job.updated_at = datetime.utcnow()
                        await session.commit()
                        
                        logger.info(f"✅ Recovered job {job_id}, message_id: {message_id}")
                        recovered_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to recover job {job_id}: {e}")
                        await session.rollback()
                
                return recovered_count
                
        except Exception as e:
            logger.error(f"Error recovering stuck jobs: {e}", exc_info=True)
            return 0
    
    async def _is_job_in_redis(self, redis, job_id: str) -> bool:
        """Check if a job ID exists in Redis stream (last 100 messages)."""
        try:
            # Check last 100 messages in stream
            messages = await redis.client.xrevrange(
                redis.INGESTION_STREAM,
                '+',
                '-',
                count=100
            )
            
            for message_id, data in messages:
                if data.get('job_id') == job_id:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking if job in Redis: {e}")
            # Conservative: assume it's not in Redis
            return False
    
    async def recover_pending_messages(self):
        """
        Recover messages stuck in pending state.
        
        ⚡ OPTIMIZATION: Pending message recovery
        Automatically claims and reprocesses stale messages (> 5 minutes idle).
        Prevents message loss from worker crashes.
        """
        try:
            redis = get_redis_client()
            
            # Get pending messages
            pending = await redis.client.xpending_range(
                name=redis.INGESTION_STREAM,
                groupname=redis.CONSUMER_GROUP,
                min="-",
                max="+",
                count=10
            )
            
            if not pending:
                return
            
            recovered_count = 0
            for msg in pending:
                # Check if message is stale (idle > 5 minutes = 300,000 ms)
                idle_time_ms = msg.get('time_since_delivered', 0)
                
                if idle_time_ms > 300000:
                    message_id = msg['message_id']
                    logger.warning(
                        f"🔧 Found stale message (idle {idle_time_ms/1000:.0f}s): {message_id}"
                    )
                    
                    try:
                        # Claim the message
                        claimed = await redis.client.xclaim(
                            name=redis.INGESTION_STREAM,
                            groupname=redis.CONSUMER_GROUP,
                            consumername=f"worker-{self.worker_id}",
                            min_idle_time=300000,
                            message_ids=[message_id]
                        )
                        
                        if claimed:
                            # Extract job_id from claimed message
                            message_data = claimed[0][1]  # (message_id, data) tuple
                            
                            import json
                            job_id_str = message_data.get('job_id')
                            if job_id_str:
                                job_id = UUID(json.loads(job_id_str) if isinstance(job_id_str, str) and job_id_str.startswith('"') else job_id_str)
                                logger.info(f"✅ Claimed and reprocessing stale job: {job_id}")
                                
                                # Reprocess the job
                                await self._process_job(job_id, message_id)
                                
                                # ACK the message after successful processing
                                await redis.client.xack(
                                    redis.INGESTION_STREAM,
                                    redis.CONSUMER_GROUP,
                                    message_id
                                )
                                
                                recovered_count += 1
                    
                    except Exception as e:
                        logger.error(f"Failed to recover message {message_id}: {e}")
            
            if recovered_count > 0:
                logger.info(f"✅ Recovered {recovered_count} stale messages")
        
        except Exception as e:
            logger.error(f"Pending message recovery failed: {e}", exc_info=True)
    
    async def _worker_loop(self):
        """
        Main worker loop.
        
        Continuously polls Redis streams for new jobs and processes them.
        Includes periodic heartbeat and pending message recovery.
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
            last_heartbeat_time = time.time()
            last_recovery_time = time.time()
            logger.info(f"🔍 DEBUG: loop_count initialized to {loop_count}")
            logger.info(f"🔍 DEBUG: About to check self.running value: {self.running}")
            logger.info("🔍 DEBUG: About to enter while loop")
            
            while self.running:
                logger.info(f"🔍 DEBUG: ✅ INSIDE while loop! Iteration {loop_count + 1}")
                logger.info(f"🔍 DEBUG: self.running = {self.running}")
                loop_count += 1
                self._iteration_count = loop_count
                
                # ⚡ OPTIMIZATION: Send heartbeat every 10 seconds
                if time.time() - last_heartbeat_time > 10:
                    await self.send_heartbeat()
                    last_heartbeat_time = time.time()
                    logger.info(f"💓 WORKER HEARTBEAT - Loop #{loop_count} - Running: {self.running}")
                
                # ⚡ OPTIMIZATION: Recover pending messages every 5 minutes
                if time.time() - last_recovery_time > 300:  # 5 minutes
                    logger.info("🔧 Running pending message recovery...")
                    await self.recover_pending_messages()
                    last_recovery_time = time.time()
                
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
                            self._jobs_processed += 1  # Track successful completions
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
            
            # Read from ingestion stream with timeout to prevent hangs
            logger.info(f"🔍 Calling redis.read_from_stream() with 3s timeout...")
            try:
                messages = await asyncio.wait_for(
                    redis.read_from_stream(
                        stream=redis.INGESTION_STREAM,
                        consumer_name=f"worker-{self.worker_id}",
                        count=1,
                        block=1000  # Block for 1 second
                    ),
                    timeout=3.0  # 3 second timeout to prevent infinite hangs
                )
                logger.info(f"🔍 Redis returned {len(messages) if messages else 0} messages")
                logger.info(f"🔍 Messages: {messages}")
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ read_from_stream() timed out after 3s - continuing...")
                return None
            
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
                    logger.warning(f"   Started: {job.started_at}, Completed: {job.completed_at}")
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
                
                # ⚡ PHASE 2 ITEM 2.3: Publish job event for dashboard
                if result["success"]:
                    # Calculate duration
                    duration_seconds = (job.completed_at - job.started_at).total_seconds() if job.started_at and job.completed_at else 0.0
                    
                    await publish_job_completed(
                        job_id=str(job_id),
                        files_processed=result.get("processed_documents", 0),
                        duration_seconds=duration_seconds,
                        metadata={
                            "total_documents": result.get("total_documents", 0),
                            "embeddings_generated": result.get("embeddings_generated", 0),
                            "skipped_documents": result.get("skipped_documents", 0),
                            "total_cost_usd": result.get("total_cost_usd", 0.0)
                        }
                    )
                    logger.info(
                        f"✅ Job {job_id} completed: "
                        f"{result['processed_documents']}/{result['total_documents']} documents, "
                        f"{result['skipped_documents']} skipped, "
                        f"{result['embeddings_generated']} embeddings, "
                        f"${result['total_cost_usd']:.4f} cost"
                    )
                else:
                    await publish_job_failed(
                        job_id=str(job_id),
                        error_message=result.get("error", "Unknown error"),
                        files_processed=result.get("processed_documents", 0),
                        metadata={
                            "total_documents": result.get("total_documents", 0),
                            "failed_documents": result.get("failed_documents", 0)
                        }
                    )
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

