"""
Orphaned Job Detection

Detects and handles jobs left in 'processing' state after container restarts.
Runs on service startup.
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
    
    Returns:
        Dict with detection results
    """
    result = {
        "total_processing": 0,
        "orphaned_found": 0,
        "failed_old": 0,
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
                        
                        # Check last update time
                        last_update = None
                        if job.job_metadata and "last_update" in job.job_metadata:
                            try:
                                last_update = datetime.fromisoformat(job.job_metadata["last_update"])
                            except:
                                pass
                        
                        # If no last_update, use started_at
                        if not last_update and job.started_at:
                            last_update = job.started_at
                        
                        if last_update:
                            age = datetime.utcnow() - last_update
                            
                            if age > timedelta(hours=1):
                                # Old job - fail it
                                logger.warning(f"   Failing old orphaned job {job.id} (age: {age})")
                                
                                job.status = "failed"
                                job.error_message = f"Job orphaned after container restart (age: {age})"
                                job.completed_at = datetime.utcnow()
                                
                                # Update metadata
                                if job.job_metadata:
                                    metadata = job.job_metadata.copy()
                                else:
                                    metadata = {}
                                
                                metadata["orphaned_detected_at"] = datetime.utcnow().isoformat()
                                metadata["orphaned_age_seconds"] = age.total_seconds()
                                metadata["orphaned_action"] = "failed_old"
                                job.job_metadata = metadata
                                
                                flag_modified(job, "job_metadata")
                                await repo.update(job)
                                await session.commit()
                                
                                result["failed_old"] += 1
                            
                            else:
                                # Recent job - try to recover by re-queuing
                                logger.info(f"   Re-queuing recent orphaned job {job.id} (age: {age})")
                                
                                # Add back to Redis
                                await redis.client.xadd(
                                    redis.INGESTION_STREAM,
                                    {"job_id": str(job.id)}
                                )
                                
                                # Update metadata
                                if job.job_metadata:
                                    metadata = job.job_metadata.copy()
                                else:
                                    metadata = {}
                                
                                metadata["orphaned_detected_at"] = datetime.utcnow().isoformat()
                                metadata["orphaned_age_seconds"] = age.total_seconds()
                                metadata["orphaned_action"] = "requeued"
                                job.job_metadata = metadata
                                
                                flag_modified(job, "job_metadata")
                                await repo.update(job)
                                await session.commit()
                                
                                result["requeued_recent"] += 1
                        
                        else:
                            # No timestamp info - fail it to be safe
                            logger.warning(f"   Failing orphaned job {job.id} (no timestamp)")
                            
                            job.status = "failed"
                            job.error_message = "Job orphaned after container restart (no timestamp)"
                            job.completed_at = datetime.utcnow()
                            
                            if job.job_metadata:
                                metadata = job.job_metadata.copy()
                            else:
                                metadata = {}
                            
                            metadata["orphaned_detected_at"] = datetime.utcnow().isoformat()
                            metadata["orphaned_action"] = "failed_no_timestamp"
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
                f"{result['failed_old']} failed, "
                f"{result['requeued_recent']} re-queued"
            )
        else:
            logger.info(f"✅ No orphaned jobs found ({result['total_processing']} jobs active)")
    
    except Exception as e:
        error_msg = f"Failed to detect orphaned jobs: {e}"
        logger.error(error_msg, exc_info=True)
        result["errors"].append(error_msg)
    
    return result

