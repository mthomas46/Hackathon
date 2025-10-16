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
        last_file_index = 0
        last_update = datetime.now()
        check_interval = 0.5  # Check every 0.5 seconds for more responsive updates
        job_start_time = None
        
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
                        total_files = job.total_documents or 0
                        
                        # Get final totals from metadata if available
                        if hasattr(job, 'job_metadata') and job.job_metadata:
                            metadata = job.job_metadata
                            if isinstance(metadata, dict):
                                total_files_in_commit = metadata.get("total_files_in_commit", 0)
                                if total_files_in_commit > 0:
                                    total_files = total_files_in_commit
                        
                        final_data = {
                            "status": job.status,
                            "processed": job.processed_documents or 0,
                            "total": total_files,
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
                    
                    # Get total and progress from metadata (more accurate than total_documents)
                    total = job.total_documents or 0
                    progress_pct = 0
                    current_file_index = 0
                    total_files_in_commit = 0
                    
                    # Read from job_metadata for accurate progress tracking
                    if hasattr(job, 'job_metadata') and job.job_metadata:
                        metadata = job.job_metadata
                        if isinstance(metadata, dict):
                            # Use metadata progress if available (tracks file processing, not just new documents)
                            total_files_in_commit = metadata.get("total_files_in_commit", 0)
                            current_file_index = metadata.get("current_file_index", 0)
                            metadata_progress = metadata.get("progress_pct", 0)
                            
                            # Prefer metadata total over database total_documents
                            if total_files_in_commit > 0:
                                total = total_files_in_commit
                                progress_pct = metadata_progress
                            else:
                                # Fallback to calculated progress
                                progress_pct = (processed / total * 100) if total > 0 else 0
                        else:
                            progress_pct = (processed / total * 100) if total > 0 else 0
                    else:
                        progress_pct = (processed / total * 100) if total > 0 else 0
                    
                    # Check if there's new progress (consider both processed docs and file index)
                    has_update = (processed > last_processed) or (current_file_index > last_file_index)
                    
                    # Calculate processing rate and ETA
                    if job_start_time is None:
                        job_start_time = job.started_at
                    
                    elapsed_seconds = (datetime.now() - job_start_time).total_seconds()
                    elapsed_minutes = elapsed_seconds / 60
                    files_processed = job.skipped_documents + job.failed_documents + job.processed_documents
                    
                    processing_rate = 0
                    eta_minutes = None
                    eta_formatted = "Calculating..."
                    
                    if elapsed_minutes > 0 and files_processed > 0:
                        processing_rate = files_processed / elapsed_minutes  # files per minute
                        
                        if total_files_in_commit > 0 and processing_rate > 0:
                            remaining_files = total_files_in_commit - current_file_index
                            eta_minutes = remaining_files / processing_rate
                            
                            # Format ETA
                            if eta_minutes < 60:
                                eta_formatted = f"{int(eta_minutes)}m"
                            else:
                                eta_hours = int(eta_minutes / 60)
                                eta_mins = int(eta_minutes % 60)
                                eta_formatted = f"{eta_hours}h {eta_mins}m"
                    
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
                        "timestamp": datetime.now().isoformat(),
                        "current_file_index": current_file_index,
                        "total_files": total_files_in_commit,
                        "processing_rate": round(processing_rate, 2),
                        "eta": eta_formatted,
                        "eta_minutes": eta_minutes,
                        "elapsed_seconds": int(elapsed_seconds)
                    }
                    
                    # Add additional metadata fields
                    if hasattr(job, 'job_metadata') and job.job_metadata:
                        metadata = job.job_metadata
                        if isinstance(metadata, dict):
                            progress_data["last_file"] = metadata.get("last_processed_file", "")
                            progress_data["current_commit"] = metadata.get("current_commit", "")
                            progress_data["last_update"] = metadata.get("last_update", "")
                    
                    yield f"data: {progress_data}\n\n"
                    
                    last_processed = processed
                    last_file_index = current_file_index
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

