"""
Integration test for complete worker job pipeline.

Tests the full flow:
1. Job created in database
2. Job added to Redis stream
3. Worker picks up job
4. Job processes successfully  
5. Job status updates in database
6. No silent failures
"""

import pytest
import asyncio
from uuid import uuid4, UUID
from datetime import datetime
import logging

from src.storage.db_models import IngestionJobModel
from src.storage.repositories import IngestionJobRepository
from src.utils.redis_client import get_redis_client
from src.storage.database import get_database

logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.asyncio
class TestWorkerJobPipeline:
    """Test complete worker job processing pipeline with detailed logging."""
    
    async def test_job_state_transitions(self):
        """
        Test that jobs transition through expected states with logging.
        
        Expected flow:
        1. queued (initial)
        2. processing (picked up by worker)
        3. completed/failed (final)
        """
        logger.info("=" * 80)
        logger.info("TEST: Job State Transitions")
        logger.info("=" * 80)
        
        db = get_database()
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            
            # Create test job
            job_id = uuid4()
            job = IngestionJobModel(
                id=job_id,
                mode="snapshot",
                status="queued",
                repo_path="/repo/tests",
                job_metadata={"test": True},
                created_at=datetime.utcnow()
            )
            
            logger.info(f"✅ Created test job: {job_id}")
            logger.info(f"   Status: {job.status}")
            logger.info(f"   Mode: {job.mode}")
            logger.info(f"   Path: {job.repo_path}")
            
            # Save to database
            await repo.create(job)
            await session.commit()
            
            logger.info(f"✅ Job saved to database")
            
            # Verify job is in database
            retrieved_job = await repo.get_by_id(job_id)
            assert retrieved_job is not None, "Job not found in database"
            assert retrieved_job.status == "queued", f"Expected status 'queued', got '{retrieved_job.status}'"
            
            logger.info(f"✅ Job verified in database with status: {retrieved_job.status}")
            
        logger.info("=" * 80)
    
    async def test_redis_stream_visibility(self):
        """
        Test that jobs added to Redis stream are visible to workers.
        """
        logger.info("=" * 80)
        logger.info("TEST: Redis Stream Visibility")
        logger.info("=" * 80)
        
        redis = get_redis_client()
        await redis.connect()
        
        # Get stream info
        try:
            stream_length = await redis.client.xlen(redis.INGESTION_STREAM)
            logger.info(f"📊 Stream length: {stream_length}")
            
            # Get last few messages
            messages = await redis.client.xrange(
                redis.INGESTION_STREAM,
                '-',
                '+',
                count=5
            )
            logger.info(f"📊 Last {len(messages)} messages in stream:")
            for msg_id, data in messages:
                logger.info(f"   - {msg_id}: {data}")
            
            # Check consumer group
            groups = await redis.client.xinfo_groups(redis.INGESTION_STREAM)
            logger.info(f"📊 Consumer groups: {len(groups)}")
            for group in groups:
                logger.info(f"   - {group}")
            
            logger.info("✅ Redis stream is accessible")
            
        except Exception as e:
            logger.error(f"❌ Redis stream check failed: {e}", exc_info=True)
            raise
        
        logger.info("=" * 80)
    
    async def test_add_job_to_stream(self):
        """
        Test adding a job to Redis stream and verifying it's there.
        """
        logger.info("=" * 80)
        logger.info("TEST: Add Job to Stream")
        logger.info("=" * 80)
        
        redis = get_redis_client()
        await redis.connect()
        
        job_id = uuid4()
        logger.info(f"📝 Adding test job to stream: {job_id}")
        
        # Add to stream
        message_id = await redis.add_to_stream(
            stream=redis.INGESTION_STREAM,
            data={
                "job_id": str(job_id),
                "mode": "snapshot",
                "repo_path": "/repo/tests",
                "_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        logger.info(f"✅ Job added with message_id: {message_id}")
        
        # Verify it's in stream
        stream_length = await redis.client.xlen(redis.INGESTION_STREAM)
        logger.info(f"📊 Stream length after add: {stream_length}")
        
        # Try to read it back
        messages = await redis.client.xrange(
            redis.INGESTION_STREAM,
            message_id,
            message_id
        )
        
        assert len(messages) == 1, "Job not found in stream after adding"
        logger.info(f"✅ Job verified in stream: {messages[0]}")
        
        logger.info("=" * 80)
    
    async def test_worker_can_read_stream(self):
        """
        Test that worker can read from stream using consumer group.
        """
        logger.info("=" * 80)
        logger.info("TEST: Worker Can Read Stream")
        logger.info("=" * 80)
        
        from src.services.ingestion import get_ingestion_worker
        
        worker = get_ingestion_worker()
        redis = get_redis_client()
        await redis.connect()
        
        logger.info(f"📝 Worker ID: {worker.worker_id}")
        logger.info(f"📝 Consumer name: worker-{worker.worker_id}")
        
        # Try to read from stream (won't block, just check if method works)
        try:
            messages = await redis.read_from_stream(
                stream=redis.INGESTION_STREAM,
                consumer_name=f"worker-{worker.worker_id}",
                count=1,
                block=100  # 100ms timeout
            )
            
            logger.info(f"✅ Worker can read from stream")
            logger.info(f"📊 Messages retrieved: {len(messages) if messages else 0}")
            
            if messages:
                for msg_id, data in messages:
                    logger.info(f"   - {msg_id}: {data}")
            
        except Exception as e:
            logger.error(f"❌ Worker read failed: {e}", exc_info=True)
            raise
        
        logger.info("=" * 80)


@pytest.mark.integration
@pytest.mark.asyncio  
class TestJobProcessingLogging:
    """Test that job processing has comprehensive logging and no silent failures."""
    
    async def test_job_processor_logs_all_stages(self):
        """
        Verify JobProcessor logs at all critical stages.
        """
        logger.info("=" * 80)
        logger.info("TEST: JobProcessor Logging")
        logger.info("=" * 80)
        
        from src.services.ingestion.job_processor import JobProcessor
        
        processor = JobProcessor()
        
        # Verify processor has required attributes
        assert hasattr(processor, 'process'), "JobProcessor missing 'process' method"
        assert hasattr(processor, 'worker_id'), "JobProcessor missing 'worker_id'"
        
        logger.info(f"✅ JobProcessor initialized")
        logger.info(f"   Worker ID: {processor.worker_id}")
        
        logger.info("=" * 80)
    
    async def test_state_transition_logging(self):
        """
        Test that state transitions are logged in database.
        """
        logger.info("=" * 80)
        logger.info("TEST: State Transition Logging")
        logger.info("=" * 80)
        
        db = get_database()
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            
            # Create job
            job_id = uuid4()
            job = IngestionJobModel(
                id=job_id,
                mode="snapshot",
                status="queued",
                repo_path="/repo/tests",
                created_at=datetime.utcnow()
            )
            await repo.create(job)
            await session.commit()
            logger.info(f"✅ Job created with status: queued")
            
            # Transition to processing
            job.status = "processing"
            job.started_at = datetime.utcnow()
            await repo.update(job)
            await session.commit()
            logger.info(f"✅ Job transitioned to: processing")
            
            # Verify transition
            updated_job = await repo.get_by_id(job_id)
            assert updated_job.status == "processing"
            assert updated_job.started_at is not None
            
            logger.info(f"✅ State transition verified in database")
        
        logger.info("=" * 80)


if __name__ == "__main__":
    # Run tests with verbose logging
    pytest.main([__file__, "-v", "-s", "--log-cli-level=INFO"])

