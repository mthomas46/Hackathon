"""
Ingestion Log Streaming

Provides real-time streaming of ingestion progress and logs.
"""

import asyncio
import logging
from typing import AsyncGenerator
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


async def stream_job_progress(job_id: str) -> AsyncGenerator[str, None]:
    """
    Stream real-time progress updates for an ingestion job.
    
    Yields Server-Sent Events (SSE) with job progress.
    """
    try:
        db = get_database()
        redis = get_redis_client()
        
        last_processed = 0
        last_update = datetime.now()
        check_interval = 2  # Check every 2 seconds
        
        # Stream updates until job completes or fails
        while True:
            try:
                # Get current job status from database
                async with db.session() as session:
                    job_repo = IngestionJobRepository(session)
                    job = await job_repo.get_by_id(UUID(job_id))
                    
                    if not job:
                        yield f"data: {{'error': 'Job not found'}}\n\n"
                        break
                    
                    # Check if job completed or failed
                    if job.status in ['completed', 'failed', 'cancelled']:
                        # Send final update
                        final_data = {
                            "status": job.status,
                            "processed": job.processed_documents or 0,
                            "total": job.total_documents or 0,
                            "skipped": job.skipped_documents or 0,
                            "failed": job.failed_documents or 0,
                            "embeddings": job.embeddings_generated or 0,
                            "cost": float(job.total_cost_usd or 0),
                            "completed": True,
                            "error": job.error_message,
                            "timestamp": datetime.now().isoformat()
                        }
                        yield f"data: {final_data}\n\n"
                        break
                    
                    # Send progress update
                    processed = job.processed_documents or 0
                    total = job.total_documents or 0
                    
                    # Calculate progress percentage
                    progress_pct = (processed / total * 100) if total > 0 else 0
                    
                    # Check if there's new progress
                    has_update = processed > last_processed
                    
                    progress_data = {
                        "status": job.status,
                        "processed": processed,
                        "total": total,
                        "skipped": job.skipped_documents or 0,
                        "failed": job.failed_documents or 0,
                        "embeddings": job.embeddings_generated or 0,
                        "progress_pct": round(progress_pct, 2),
                        "cost": float(job.total_cost_usd or 0),
                        "completed": False,
                        "has_update": has_update,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Try to get last processed file from job metadata
                    if hasattr(job, 'job_metadata') and job.job_metadata:
                        metadata = job.job_metadata
                        if isinstance(metadata, dict):
                            progress_data["last_file"] = metadata.get("last_processed_file", "")
                            progress_data["current_commit"] = metadata.get("current_commit", "")
                    
                    yield f"data: {progress_data}\n\n"
                    
                    last_processed = processed
                    last_update = datetime.now()
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error streaming job progress: {e}")
                yield f"data: {{'error': '{str(e)}'}}\n\n"
                break
    
    except Exception as e:
        logger.error(f"Failed to start stream for job {job_id}: {e}", exc_info=True)
        yield f"data: {{'error': 'Failed to start stream: {str(e)}'}}\n\n"


@router.get(
    "/ingest/{job_id}/stream",
    summary="Stream ingestion progress",
    description="Stream real-time progress updates for an ingestion job (SSE)"
)
async def stream_ingestion_progress(job_id: str):
    """
    Stream real-time progress updates for an ingestion job.
    
    Uses Server-Sent Events (SSE) to push updates to the client.
    
    Args:
        job_id: UUID of the ingestion job
    
    Returns:
        SSE stream of progress updates
    """
    return StreamingResponse(
        stream_job_progress(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


async def stream_recent_logs(limit: int = 50) -> AsyncGenerator[str, None]:
    """
    Stream recent ingestion logs from Redis.
    
    Yields Server-Sent Events with log entries.
    """
    try:
        redis = get_redis_client()
        
        # Get recent log entries from Redis stream
        try:
            # Read from ingestion-logs stream (if it exists)
            logs = await redis.client.xrevrange(
                "ingestion-logs",
                count=limit
            )
            
            for log_id, log_data in logs:
                log_entry = {
                    "id": log_id,
                    "timestamp": log_data.get(b"timestamp", b"").decode(),
                    "job_id": log_data.get(b"job_id", b"").decode(),
                    "level": log_data.get(b"level", b"INFO").decode(),
                    "message": log_data.get(b"message", b"").decode(),
                    "file": log_data.get(b"file", b"").decode(),
                }
                yield f"data: {log_entry}\n\n"
            
        except Exception as e:
            # Stream doesn't exist or is empty
            yield f"data: {{'info': 'No logs available yet'}}\n\n"
        
        yield f"data: {{'completed': true}}\n\n"
        
    except Exception as e:
        logger.error(f"Failed to stream logs: {e}", exc_info=True)
        yield f"data: {{'error': '{str(e)}'}}\n\n"


@router.get(
    "/logs/stream",
    summary="Stream recent ingestion logs",
    description="Stream recent ingestion log entries (SSE)"
)
async def stream_ingestion_logs(limit: int = 50):
    """
    Stream recent ingestion logs.
    
    Args:
        limit: Maximum number of log entries to return
    
    Returns:
        SSE stream of log entries
    """
    return StreamingResponse(
        stream_recent_logs(limit),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

