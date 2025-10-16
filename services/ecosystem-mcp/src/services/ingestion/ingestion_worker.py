"""
Ingestion Worker

Background worker that processes document ingestion jobs from Redis streams.
Coordinates the entire ingestion pipeline from Git → Database → ChromaDB.
"""

import asyncio
import logging
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
        logger.info(f"IngestionWorker initialized (ID: {self.worker_id})")
    
    async def start(self):
        """
        Start the ingestion worker.
        
        Begins polling Redis streams for ingestion jobs and processing them.
        """
        if self.running:
            logger.warning("IngestionWorker already running")
            return
        
        # Setup graceful shutdown handler
        self.shutdown_handler = get_shutdown_handler(
            max_shutdown_time=60,
            checkpoint_callback=self._save_checkpoint,
            cleanup_callback=self._cleanup
        )
        
        self.running = True
        self._task = asyncio.create_task(self._worker_loop())
        logger.info("✅ IngestionWorker started with graceful shutdown handler")
    
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
        logger.info("Worker loop started")
        
        while self.running:
            try:
                # Check for shutdown request
                if is_shutdown_requested():
                    logger.info("🛑 Shutdown requested, stopping worker loop")
                    if self.shutdown_handler:
                        await self.shutdown_handler.shutdown()
                    break
                
                # Get next job from Redis stream
                result = await self._get_next_job()
                
                if result:
                    message_id, job_id = result
                    self.current_job_id = job_id
                    
                    logger.info(f"Processing job: {job_id}")
                    
                    # Mark that we're finishing current work
                    if self.shutdown_handler and is_shutdown_requested():
                        await self.shutdown_handler.finish_current_work(f"job {job_id}")
                    
                    await self._process_job(job_id)
                    
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
                    await asyncio.sleep(5)
            
            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)
                await asyncio.sleep(10)  # Back off on errors
        
        logger.info("✅ Worker loop stopped")
    
    async def _get_next_job(self) -> Optional[tuple[str, UUID]]:
        """
        Get the next job from Redis stream.
        
        Returns:
            Tuple of (message_id, job_id) if available, None otherwise
        """
        try:
            redis = get_redis_client()
            
            # Read from ingestion stream
            messages = await redis.read_from_stream(
                stream=redis.INGESTION_STREAM,
                consumer_name=f"worker-{self.worker_id}",
                count=1,
                block=1000  # Block for 1 second
            )
            
            if messages:
                # Extract message_id and job_id from message
                # messages is a list of (message_id, data) tuples
                message_id, data = messages[0]
                job_id_str = data.get("job_id")
                
                if job_id_str:
                    return (message_id, UUID(job_id_str))  # ✅ Return both!
            
            return None
        
        except Exception as e:
            logger.error(f"Error reading from Redis stream: {e}", exc_info=True)
            return None
    
    async def _process_job(self, job_id: UUID):
        """
        Process a single ingestion job.
        
        Args:
            job_id: ID of the job to process
        """
        async with get_database().session() as session:
            repo = IngestionJobRepository(session)
            
            try:
                # Get job from database
                job = await repo.get_by_id(job_id)
                
                if not job:
                    logger.error(f"Job not found: {job_id}")
                    return
                
                # Update status to processing
                job.status = "processing"
                await repo.update(job)
                await session.commit()
                
                logger.info(f"Starting job {job_id}: mode={job.mode}, repo={job.repo_path}")
                
                # Process the job using JobProcessor
                result = await self.job_processor.process(job)
                
                # Update job with results
                job.status = "completed" if result["success"] else "failed"
                job.completed_at = datetime.utcnow()
                job.processed_documents = result.get("processed_documents", 0)
                job.total_documents = result.get("total_documents", 0)
                job.failed_documents = result.get("failed_documents", 0)
                job.skipped_documents = result.get("skipped_documents", 0)  # NEW
                job.embeddings_generated = result.get("embeddings_generated", 0)
                job.total_cost_usd = result.get("total_cost_usd", 0.0)
                
                if not result["success"]:
                    job.error_message = result.get("error", "Unknown error")
                
                await repo.update(job)
                await session.commit()
                
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
            
            except Exception as e:
                logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
                
                # Update job status to failed
                try:
                    job = await repo.get_by_id(job_id)
                    if job:
                        job.status = "failed"
                        job.completed_at = datetime.utcnow()
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


def get_ingestion_worker() -> IngestionWorker:
    """
    Get the global ingestion worker instance.
    
    Returns:
        IngestionWorker instance
    """
    global _worker_instance
    
    if _worker_instance is None:
        _worker_instance = IngestionWorker()
    
    return _worker_instance


async def start_ingestion_worker():
    """Start the global ingestion worker."""
    worker = get_ingestion_worker()
    await worker.start()


async def stop_ingestion_worker():
    """Stop the global ingestion worker."""
    worker = get_ingestion_worker()
    await worker.stop()

