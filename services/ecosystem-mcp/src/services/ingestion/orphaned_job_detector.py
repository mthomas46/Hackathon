"""
Orphaned Job Detection

Detects and handles jobs left in 'processing' state after container restarts.
Runs on service startup.

Protection mechanisms:
- Maximum 3 retry attempts before failing
- 1 hour age threshold for re-queuing
- 4 hour hard timeout for jobs
- Retry count tracking in job metadata
"""

import logging
from datetime import datetime, timedelta
from typing import List
from uuid import UUID

from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from ...storage.db_models import IngestionJobModel
from ...utils.redis_client import get_redis_client
from sqlalchemy.orm.attributes import flag_modified

logger = logging.getLogger(__name__)

# Configuration constants
MAX_ORPHAN_RETRIES = 3  # Maximum times to re-queue an orphaned job
ORPHAN_AGE_THRESHOLD = timedelta(hours=1)  # Age before failing old jobs
JOB_HARD_TIMEOUT = timedelta(hours=4)  # Maximum processing time
REQUEUE_AGE_LIMIT = timedelta(hours=1)  # Only requeue jobs younger than this


async def check_redis_has_job(redis_client, job_id: UUID) -> bool:
    """
    Check if a job has a message in Redis queue.
    
    Args:
        redis_client: Redis client instance
        job_id: Job UUID to check
    
    Returns:
        True if job has Redis message, False otherwise
    """
    try:
        # Check if job exists in ingestion stream
        # XRANGE gets all messages in stream
        messages = await redis_client.client.xrange(
            redis_client.INGESTION_STREAM,
            min="-",
            max="+",
            count=1000  # Check last 1000 messages
        )
        
        # Check if any message contains this job_id
        for message_id, message_data in messages:
            if message_data.get(b"job_id") == str(job_id).encode():
                return True
        
        return False
    
    except Exception as e:
        logger.debug(f"Could not check Redis for job {job_id}: {e}")
        return False


async def detect_orphaned_jobs() -> dict:
    """
    Detect and handle orphaned jobs on service startup.
    
    An orphaned job is one that:
    1. Has status='processing' in PostgreSQL
    2. Has no corresponding message in Redis queue
    3. Either old (>1h) or recent (can be recovered)
    
    Protection mechanisms:
    - Maximum 3 retry attempts
    - 1 hour age threshold for re-queuing
    - 4 hour hard timeout
    - Retry count tracking
    
    Returns:
        Dict with detection results
    """
    result = {
        "total_processing": 0,
        "orphaned_found": 0,
        "failed_old": 0,
        "failed_max_retries": 0,
        "failed_timeout": 0,
        "requeued_recent": 0,
        "errors": []
    }
    
    try:
        db = get_database()
        redis = get_redis_client()
        
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            
            # Get all processing jobs
            processing_jobs = await repo.get_running_jobs()
            result["total_processing"] = len(processing_jobs)
            
            logger.info(f"🔍 Checking {len(processing_jobs)} processing jobs for orphans...")
            
            for job in processing_jobs:
                try:
                    # Check if job has Redis message
                    has_message = await check_redis_has_job(redis, job.id)
                    
                    if not has_message:
                        result["orphaned_found"] += 1
                        logger.warning(f"⚠️  Orphaned job detected: {job.id}")
                        
                        # Get or initialize metadata
                        if job.job_metadata:
                            metadata = job.job_metadata.copy()
                        else:
                            metadata = {}
                        
                        # Track retry count
                        retry_count = metadata.get("orphan_retry_count", 0)
                        
                        # Check last update time
                        last_update = None
                        if "last_update" in metadata:
                            try:
                                last_update = datetime.fromisoformat(metadata["last_update"])
                            except:
                                pass
                        
                        # If no last_update, use started_at
                        if not last_update and job.started_at:
                            last_update = job.started_at
                        
                        if last_update:
                            age = datetime.utcnow() - last_update
                            
                            # Check for hard timeout (4 hours)
                            if age > JOB_HARD_TIMEOUT:
                                logger.error(f"   ❌ Job {job.id} exceeded hard timeout ({JOB_HARD_TIMEOUT}) - FAILING")
                                
                                job.status = "failed"
                                job.error_message = f"Job exceeded hard timeout of {JOB_HARD_TIMEOUT} (age: {age})"
                                job.completed_at = datetime.utcnow()
                                
                                metadata["orphaned_detected_at"] = datetime.utcnow().isoformat()
                                metadata["orphaned_age_seconds"] = age.total_seconds()
                                metadata["orphaned_action"] = "failed_timeout"
                                metadata["orphan_retry_count"] = retry_count
                                job.job_metadata = metadata
                                
                                flag_modified(job, "job_metadata")
                                await repo.update(job)
                                await session.commit()
                                
                                result["failed_timeout"] += 1
                            
                            # Check for max retries exceeded
                            elif retry_count >= MAX_ORPHAN_RETRIES:
                                logger.error(f"   ❌ Job {job.id} exceeded max retries ({MAX_ORPHAN_RETRIES}) - FAILING")
                                
                                job.status = "failed"
                                job.error_message = f"Job exceeded maximum retry attempts ({MAX_ORPHAN_RETRIES})"
                                job.completed_at = datetime.utcnow()
                                
                                metadata["orphaned_detected_at"] = datetime.utcnow().isoformat()
                                metadata["orphaned_age_seconds"] = age.total_seconds()
                                metadata["orphaned_action"] = "failed_max_retries"
                                metadata["orphan_retry_count"] = retry_count
                                job.job_metadata = metadata
                                
                                flag_modified(job, "job_metadata")
                                await repo.update(job)
                                await session.commit()
                                
                                result["failed_max_retries"] += 1
                            
                            # Check if too old to requeue (> 1 hour)
                            elif age > ORPHAN_AGE_THRESHOLD:
                                logger.warning(f"   ⏰ Job {job.id} too old to requeue (age: {age}) - FAILING")
                                
                                job.status = "failed"
                                job.error_message = f"Job orphaned after container restart (age: {age}, retry_count: {retry_count})"
                                job.completed_at = datetime.utcnow()
                                
                                metadata["orphaned_detected_at"] = datetime.utcnow().isoformat()
                                metadata["orphaned_age_seconds"] = age.total_seconds()
                                metadata["orphaned_action"] = "failed_old"
                                metadata["orphan_retry_count"] = retry_count
                                job.job_metadata = metadata
                                
                                flag_modified(job, "job_metadata")
                                await repo.update(job)
                                await session.commit()
                                
                                result["failed_old"] += 1
                            
                            else:
                                # Recent job - try to recover by re-queuing
                                new_retry_count = retry_count + 1
                                logger.info(f"   🔄 Re-queuing orphaned job {job.id} (age: {age}, retry: {new_retry_count}/{MAX_ORPHAN_RETRIES})")
                                
                                # 🐛 CRITICAL FIX: Reset job status to "queued" so worker will pick it up
                                job.status = "queued"
                                
                                # Add back to Redis
                                await redis.client.xadd(
                                    redis.INGESTION_STREAM,
                                    {
                                        "job_id": str(job.id),
                                        "mode": job.mode,
                                        "repo_path": job.repo_path,
                                        "_timestamp": datetime.utcnow().isoformat(),
                                        "_retry": str(new_retry_count)
                                    }
                                )
                                
                                # Update metadata with incremented retry count
                                metadata["orphaned_detected_at"] = datetime.utcnow().isoformat()
                                metadata["orphaned_age_seconds"] = age.total_seconds()
                                metadata["orphaned_action"] = "requeued"
                                metadata["orphan_retry_count"] = new_retry_count
                                metadata["last_requeue_at"] = datetime.utcnow().isoformat()
                                job.job_metadata = metadata
                                
                                flag_modified(job, "job_metadata")
                                await repo.update(job)
                                await session.commit()
                                
                                result["requeued_recent"] += 1
                        
                        else:
                            # No timestamp info - fail it to be safe
                            logger.warning(f"   ❌ Job {job.id} has no timestamp (retry_count: {retry_count}) - FAILING")
                            
                            job.status = "failed"
                            job.error_message = "Job orphaned after container restart (no timestamp)"
                            job.completed_at = datetime.utcnow()
                            
                            metadata["orphaned_detected_at"] = datetime.utcnow().isoformat()
                            metadata["orphaned_action"] = "failed_no_timestamp"
                            metadata["orphan_retry_count"] = retry_count
                            job.job_metadata = metadata
                            
                            flag_modified(job, "job_metadata")
                            await repo.update(job)
                            await session.commit()
                            
                            result["failed_old"] += 1
                
                except Exception as e:
                    error_msg = f"Error checking job {job.id}: {e}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
        
        # Log summary
        if result["orphaned_found"] > 0:
            logger.warning(
                f"🧹 Orphaned job cleanup complete: "
                f"{result['orphaned_found']} found, "
                f"{result['failed_old']} failed (old), "
                f"{result['failed_max_retries']} failed (max retries), "
                f"{result['failed_timeout']} failed (timeout), "
                f"{result['requeued_recent']} re-queued"
            )
        else:
            logger.info(f"✅ No orphaned jobs found ({result['total_processing']} jobs active)")
    
    except Exception as e:
        error_msg = f"Failed to detect orphaned jobs: {e}"
        logger.error(error_msg, exc_info=True)
        result["errors"].append(error_msg)
    
    return result

