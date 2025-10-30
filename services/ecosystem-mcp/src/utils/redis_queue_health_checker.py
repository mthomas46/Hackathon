"""
Redis Queue Health Checker

Verifies consistency between Redis queue and PostgreSQL job state.
Detects orphaned messages, missing jobs, and state mismatches.
"""

import logging
from typing import Dict, Any, List
from uuid import UUID

from .redis_client import get_redis_client
from ..storage import get_database
from ..storage.repositories import IngestionJobRepository

logger = logging.getLogger(__name__)


async def check_redis_queue_health() -> Dict[str, Any]:
    """
    Comprehensive health check of Redis queue vs PostgreSQL state.
    
    Checks:
    - Job count consistency
    - Orphaned Redis messages
    - Missing Redis messages for queued jobs
    - Consumer group status
    
    Returns:
        Dict with health check results
    """
    result = {
        "healthy": True,
        "postgres_queued": 0,
        "postgres_processing": 0,
        "redis_messages": 0,
        "redis_pending": 0,
        "orphaned_messages": [],
        "missing_messages": [],
        "warnings": [],
        "recommendations": []
    }
    
    try:
        redis = get_redis_client()
        db = get_database()
        
        # Get Redis stream info
        try:
            # Get stream length
            stream_len = await redis.client.xlen(redis.INGESTION_STREAM)
            result["redis_messages"] = stream_len
            
            # Get consumer group info
            try:
                groups = await redis.client.xinfo_groups(redis.INGESTION_STREAM)
                if groups:
                    for group in groups:
                        if group.get(b"name") == redis.CONSUMER_GROUP.encode():
                            result["redis_pending"] = group.get(b"pending", 0)
                            break
            except Exception as e:
                logger.debug(f"Could not get consumer group info: {e}")
        
        except Exception as e:
            logger.error(f"Failed to get Redis stream info: {e}")
            result["warnings"].append(f"Redis stream error: {e}")
            result["healthy"] = False
        
        # Get PostgreSQL job state
        postgres_jobs = {}
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            
            # Get all queued and processing jobs
            running_jobs = await repo.get_running_jobs()
            result["postgres_processing"] = len(running_jobs)
            
            # Track all active jobs
            for job in running_jobs:
                postgres_jobs[str(job.id)] = {
                    "status": job.status,
                    "started_at": job.started_at.isoformat() if job.started_at else None
                }
            
            # Get queued jobs separately
            try:
                from sqlalchemy import select
                from ...storage.db_models import IngestionJobModel
                
                queued_query = select(IngestionJobModel).where(
                    IngestionJobModel.status == "queued"
                )
                queued_result = await session.execute(queued_query)
                queued_jobs = queued_result.scalars().all()
                result["postgres_queued"] = len(queued_jobs)
                
                for job in queued_jobs:
                    postgres_jobs[str(job.id)] = {
                        "status": "queued",
                        "started_at": job.started_at.isoformat() if job.started_at else None
                    }
            
            except Exception as e:
                logger.error(f"Could not get queued jobs: {e}")
        
        # Get Redis messages and check consistency
        try:
            # Get all messages in stream
            messages = await redis.client.xrange(
                redis.INGESTION_STREAM,
                min="-",
                max="+",
                count=1000
            )
            
            redis_job_ids = set()
            for message_id, message_data in messages:
                job_id = message_data.get(b"job_id", b"").decode()
                if job_id:
                    redis_job_ids.add(job_id)
                    
                    # Check if job exists in PostgreSQL
                    if job_id not in postgres_jobs:
                        result["orphaned_messages"].append({
                            "job_id": job_id,
                            "message_id": message_id.decode(),
                            "reason": "No corresponding PostgreSQL job"
                        })
                        result["healthy"] = False
            
            # Check for missing Redis messages
            for job_id, job_info in postgres_jobs.items():
                if job_info["status"] == "queued" and job_id not in redis_job_ids:
                    result["missing_messages"].append({
                        "job_id": job_id,
                        "status": job_info["status"],
                        "reason": "Queued in PostgreSQL but no Redis message"
                    })
                    result["healthy"] = False
        
        except Exception as e:
            logger.error(f"Failed to check Redis messages: {e}")
            result["warnings"].append(f"Redis message check error: {e}")
            result["healthy"] = False
        
        # Generate warnings and recommendations
        if result["orphaned_messages"]:
            warning = f"Found {len(result['orphaned_messages'])} orphaned Redis messages"
            result["warnings"].append(warning)
            result["recommendations"].append(
                "Run cleanup to remove orphaned messages from Redis stream"
            )
            logger.warning(f"⚠️  {warning}")
        
        if result["missing_messages"]:
            warning = f"Found {len(result['missing_messages'])} jobs missing Redis messages"
            result["warnings"].append(warning)
            result["recommendations"].append(
                "Re-queue jobs that are missing Redis messages"
            )
            logger.warning(f"⚠️  {warning}")
        
        # Check for count discrepancies
        expected_redis = result["postgres_queued"]
        actual_redis = result["redis_messages"]
        
        if expected_redis != actual_redis:
            discrepancy = abs(expected_redis - actual_redis)
            if discrepancy > 0:
                warning = (
                    f"Job count mismatch: PostgreSQL queued={expected_redis}, "
                    f"Redis messages={actual_redis} (diff: {discrepancy})"
                )
                result["warnings"].append(warning)
                logger.warning(f"⚠️  {warning}")
                
                if actual_redis > expected_redis:
                    result["recommendations"].append(
                        f"Redis has {discrepancy} extra messages - likely orphaned"
                    )
                else:
                    result["recommendations"].append(
                        f"PostgreSQL has {discrepancy} jobs without Redis messages - should re-queue"
                    )
        
        # Final health assessment
        if result["healthy"]:
            if result["warnings"]:
                logger.warning("⚠️  Redis queue health check completed with warnings")
            else:
                logger.info("✅ Redis queue health check passed")
        else:
            logger.error("❌ Redis queue health check FAILED")
    
    except Exception as e:
        error_msg = f"Failed to check Redis queue health: {e}"
        logger.error(error_msg, exc_info=True)
        result["warnings"].append(error_msg)
        result["healthy"] = False
    
    return result


async def cleanup_orphaned_redis_messages() -> Dict[str, Any]:
    """
    Clean up orphaned messages in Redis stream.
    
    Removes messages that don't correspond to any PostgreSQL job.
    
    Returns:
        Dict with cleanup results
    """
    result = {
        "messages_checked": 0,
        "messages_removed": 0,
        "errors": []
    }
    
    try:
        redis = get_redis_client()
        db = get_database()
        
        # Get all valid job IDs from PostgreSQL
        valid_job_ids = set()
        async with db.session() as session:
            repo = IngestionJobRepository(session)
            
            # Get all active jobs (queued + processing)
            running_jobs = await repo.get_running_jobs()
            for job in running_jobs:
                valid_job_ids.add(str(job.id))
            
            # Get queued jobs
            try:
                from sqlalchemy import select
                from ...storage.db_models import IngestionJobModel
                
                queued_query = select(IngestionJobModel).where(
                    IngestionJobModel.status == "queued"
                )
                queued_result = await session.execute(queued_query)
                queued_jobs = queued_result.scalars().all()
                for job in queued_jobs:
                    valid_job_ids.add(str(job.id))
            
            except Exception as e:
                logger.error(f"Could not get queued jobs: {e}")
        
        # Check and remove orphaned messages
        messages = await redis.client.xrange(
            redis.INGESTION_STREAM,
            min="-",
            max="+",
            count=1000
        )
        
        for message_id, message_data in messages:
            result["messages_checked"] += 1
            job_id = message_data.get(b"job_id", b"").decode()
            
            if job_id and job_id not in valid_job_ids:
                # Orphaned message - remove it
                try:
                    await redis.client.xdel(redis.INGESTION_STREAM, message_id)
                    result["messages_removed"] += 1
                    logger.info(f"Removed orphaned message for job {job_id}")
                except Exception as e:
                    error_msg = f"Failed to remove message {message_id}: {e}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)
        
        logger.info(
            f"Cleanup complete: {result['messages_removed']} of "
            f"{result['messages_checked']} messages removed"
        )
    
    except Exception as e:
        error_msg = f"Failed to cleanup orphaned messages: {e}"
        logger.error(error_msg, exc_info=True)
        result["errors"].append(error_msg)
    
    return result


async def requeue_missing_jobs() -> Dict[str, Any]:
    """
    Re-queue jobs that are in 'queued' state but missing Redis messages.
    
    Returns:
        Dict with re-queue results
    """
    result = {
        "jobs_checked": 0,
        "jobs_requeued": 0,
        "errors": []
    }
    
    try:
        redis = get_redis_client()
        db = get_database()
        
        # Get all Redis job IDs
        messages = await redis.client.xrange(
            redis.INGESTION_STREAM,
            min="-",
            max="+",
            count=1000
        )
        
        redis_job_ids = set()
        for message_id, message_data in messages:
            job_id = message_data.get(b"job_id", b"").decode()
            if job_id:
                redis_job_ids.add(job_id)
        
        # Check all queued jobs
        async with db.session() as session:
            from sqlalchemy import select
            from ...storage.db_models import IngestionJobModel
            
            queued_query = select(IngestionJobModel).where(
                IngestionJobModel.status == "queued"
            )
            queued_result = await session.execute(queued_query)
            queued_jobs = queued_result.scalars().all()
            
            for job in queued_jobs:
                result["jobs_checked"] += 1
                job_id_str = str(job.id)
                
                if job_id_str not in redis_job_ids:
                    # Missing Redis message - re-queue
                    try:
                        await redis.client.xadd(
                            redis.INGESTION_STREAM,
                            {"job_id": job_id_str}
                        )
                        result["jobs_requeued"] += 1
                        logger.info(f"Re-queued job {job_id_str}")
                    except Exception as e:
                        error_msg = f"Failed to re-queue job {job_id_str}: {e}"
                        result["errors"].append(error_msg)
                        logger.error(error_msg)
        
        logger.info(
            f"Re-queue complete: {result['jobs_requeued']} of "
            f"{result['jobs_checked']} jobs re-queued"
        )
    
    except Exception as e:
        error_msg = f"Failed to re-queue missing jobs: {e}"
        logger.error(error_msg, exc_info=True)
        result["errors"].append(error_msg)
    
    return result

