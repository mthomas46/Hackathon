"""
Job Progress API

Real-time progress tracking for ingestion jobs.
"""

import logging
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...storage.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


class JobProgressResponse(BaseModel):
    """Real-time job progress information."""
    job_id: str
    phase: str
    current: int
    total: int
    percentage: float
    message: str
    timestamp: str
    extra_data: Dict[str, Any] = {}


@router.get(
    "/jobs/{job_id}/progress",
    response_model=JobProgressResponse,
    summary="Get real-time job progress",
    description="""
    Retrieve real-time progress information for an ingestion job.
    
    This endpoint returns live progress updates including:
    - Current phase (initializing, scanning, processing, completed, failed)
    - Progress percentage
    - Detailed metrics (processed, failed, skipped documents)
    - Current commit being processed
    - Embeddings generated
    
    Progress is updated in real-time as the job processes.
    """
)
async def get_job_progress(job_id: str) -> JobProgressResponse:
    """
    Get real-time progress for an ingestion job.
    
    Args:
        job_id: UUID of the ingestion job
        
    Returns:
        Current progress information
        
    Raises:
        HTTPException: If job not found or progress unavailable
    """
    try:
        redis_client = get_redis_client()
        progress_key = f"job_progress:{job_id}"
        
        # Get progress data from Redis
        progress_data = await redis_client.get(progress_key)
        
        if not progress_data:
            raise HTTPException(
                status_code=404,
                detail=f"No progress information available for job {job_id}"
            )
        
        # Parse progress data
        data = json.loads(progress_data)
        
        # Extract known fields
        response = JobProgressResponse(
            job_id=data["job_id"],
            phase=data["phase"],
            current=data["current"],
            total=data["total"],
            percentage=data["percentage"],
            message=data.get("message", ""),
            timestamp=data["timestamp"],
            extra_data={
                k: v for k, v in data.items()
                if k not in ["job_id", "phase", "current", "total", "percentage", "message", "timestamp"]
            }
        )
        
        return response
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse progress data for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to parse progress data"
        )
    except Exception as e:
        logger.error(f"Error retrieving progress for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving progress: {str(e)}"
        )


@router.get(
    "/jobs/{job_id}/progress/stream",
    summary="Stream real-time job progress",
    description="""
    Server-Sent Events endpoint for streaming real-time progress updates.
    
    This endpoint uses Server-Sent Events (SSE) to push progress updates
    to the client as they occur. Connect to this endpoint to receive
    live updates without polling.
    
    Example:
    ```javascript
    const eventSource = new EventSource('/api/v1/admin/jobs/{job_id}/progress/stream');
    eventSource.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        console.log(progress);
    };
    ```
    """
)
async def stream_job_progress(job_id: str):
    """
    Stream real-time progress updates via Server-Sent Events.
    
    Args:
        job_id: UUID of the ingestion job
        
    Yields:
        Progress updates as they occur
    """
    from fastapi.responses import StreamingResponse
    import asyncio
    
    async def event_generator():
        redis_client = get_redis_client()
        pubsub = redis_client.pubsub()
        
        try:
            # Subscribe to progress channel
            channel = f"job_progress_channel:{job_id}"
            await pubsub.subscribe(channel)
            
            logger.info(f"📡 Client connected to progress stream for job {job_id}")
            
            # Send initial progress
            progress_key = f"job_progress:{job_id}"
            initial_progress = await redis_client.get(progress_key)
            if initial_progress:
                yield f"data: {initial_progress}\n\n"
            
            # Stream updates
            timeout = 300  # 5 minutes
            start_time = asyncio.get_event_loop().time()
            
            while True:
                # Check timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.info(f"⏰ Progress stream timeout for job {job_id}")
                    break
                
                # Get message with timeout
                try:
                    message = await asyncio.wait_for(
                        pubsub.get_message(ignore_subscribe_messages=True),
                        timeout=5.0
                    )
                    
                    if message and message["type"] == "message":
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode('utf-8')
                        yield f"data: {data}\n\n"
                        
                        # Check if job is complete
                        progress_data = json.loads(data)
                        if progress_data.get("phase") in ["completed", "failed"]:
                            logger.info(f"✅ Job {job_id} {progress_data['phase']}, closing stream")
                            break
                        
                except asyncio.TimeoutError:
                    # Send keep-alive
                    yield ": keepalive\n\n"
                    continue
                    
        except Exception as e:
            logger.error(f"Error streaming progress for job {job_id}: {e}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"📡 Client disconnected from progress stream for job {job_id}")
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.delete(
    "/jobs/{job_id}/progress",
    summary="Clear job progress data",
    description="Clear progress tracking data for a completed or failed job"
)
async def clear_job_progress(job_id: str) -> Dict[str, str]:
    """
    Clear progress data for a job.
    
    Args:
        job_id: UUID of the ingestion job
        
    Returns:
        Success message
    """
    try:
        redis_client = get_redis_client()
        progress_key = f"job_progress:{job_id}"
        
        deleted = await redis_client.delete(progress_key)
        
        if deleted:
            return {"message": f"Progress data cleared for job {job_id}"}
        else:
            return {"message": f"No progress data found for job {job_id}"}
            
    except Exception as e:
        logger.error(f"Error clearing progress for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing progress: {str(e)}"
        )

