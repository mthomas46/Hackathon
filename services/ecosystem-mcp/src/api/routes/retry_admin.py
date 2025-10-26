"""
Retry Infrastructure Admin API

Provides endpoints for monitoring and managing the retry infrastructure.

Features:
- Retry queue statistics
- Retry queue item listing
- Manual reprocess
- Dead letter queue management
- Retry worker status

Created: 2025-10-26
Phase: 2.3 (Retry Infrastructure)
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ...utils.redis_client import get_redis_client
from ...services.ingestion.retry_worker import get_retry_worker
from ...storage import get_database
from ...storage.repositories.ingestion_job_repository import IngestionJobRepository

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class RetryQueueStatsResponse(BaseModel):
    """Retry queue statistics."""
    total_items: int = Field(..., description="Total items in retry queue")
    ready_to_retry: int = Field(..., description="Items ready for immediate retry")
    pending: int = Field(..., description="Items waiting for next retry time")
    circuit_breaker_state: str = Field(..., description="Circuit breaker state")
    worker_running: bool = Field(..., description="Whether retry worker is running")


class RetryQueueItem(BaseModel):
    """Single retry queue item."""
    message_id: str
    job_id: str
    file_path: str
    error_type: str
    error_message: str
    retry_count: int
    failed_at: str
    next_retry_at: str


class RetryQueueItemsResponse(BaseModel):
    """List of retry queue items."""
    items: List[RetryQueueItem]
    total: int
    limit: int
    offset: int


class DeadLetterItem(BaseModel):
    """Single dead letter queue item."""
    message_id: str
    job_id: str
    file_path: str
    error_type: str
    error_message: str
    retry_count: int
    failed_at: str
    moved_to_dlq_at: str


class DeadLetterItemsResponse(BaseModel):
    """List of dead letter queue items."""
    items: List[DeadLetterItem]
    total: int
    limit: int
    offset: int


class ReprocessRequest(BaseModel):
    """Request to reprocess failed documents."""
    message_ids: Optional[List[str]] = Field(None, description="Specific message IDs to reprocess")
    job_id: Optional[str] = Field(None, description="Reprocess all failures for this job")
    file_path: Optional[str] = Field(None, description="Reprocess failures for this file")
    all: bool = Field(False, description="Reprocess all items in dead letter queue")


class ReprocessResponse(BaseModel):
    """Response from reprocess operation."""
    success: bool
    reprocessed_count: int
    message: str


class RetryWorkerStatusResponse(BaseModel):
    """Retry worker status and statistics."""
    running: bool
    worker_id: str
    started_at: Optional[str]
    last_poll_at: Optional[str]
    total_retried: int
    total_recovered: int
    total_failed: int
    total_moved_to_dlq: int
    batches_processed: int
    circuit_breaker_trips: int
    circuit_breaker: Dict[str, Any]


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/retry-queue/stats",
    response_model=RetryQueueStatsResponse,
    summary="Get retry queue statistics",
    description="Get current statistics about the retry queue and worker"
)
async def get_retry_queue_stats() -> RetryQueueStatsResponse:
    """
    Get retry queue statistics.
    
    Returns counts of items in various states and circuit breaker status.
    """
    try:
        redis_client = get_redis_client()
        retry_worker = get_retry_worker()
        
        # Get queue length from Redis
        queue_length = await redis_client.client.xlen(redis_client.RETRY_STREAM)
        
        # Get pending group info to count items
        try:
            pending_info = await redis_client.client.xpending(
                redis_client.RETRY_STREAM,
                redis_client.CONSUMER_GROUP
            )
            # pending_info is a dict with 'pending', 'min', 'max', 'consumers'
            pending_count = pending_info.get('pending', 0) if isinstance(pending_info, dict) else 0
        except Exception as e:
            logger.warning(f"Could not get pending count: {e}")
            pending_count = 0
        
        # Get worker stats
        worker_stats = retry_worker.get_stats()
        circuit_breaker_state = worker_stats.get("circuit_breaker", {}).get("state", "unknown")
        worker_running = worker_stats.get("running", False)
        
        # Calculate ready vs pending (simplified - items are ready if next_retry_at <= now)
        # For exact count we'd need to read all messages, so we approximate
        ready_count = min(10, queue_length)  # Approximate based on batch size
        
        return RetryQueueStatsResponse(
            total_items=queue_length,
            ready_to_retry=ready_count,
            pending=queue_length - ready_count,
            circuit_breaker_state=circuit_breaker_state,
            worker_running=worker_running
        )
    
    except Exception as e:
        logger.error(f"Error getting retry queue stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get retry queue stats: {str(e)}"
        )


@router.get(
    "/retry-queue/items",
    response_model=RetryQueueItemsResponse,
    summary="List retry queue items",
    description="Get a paginated list of items in the retry queue"
)
async def list_retry_queue_items(
    limit: int = 50,
    offset: int = 0
) -> RetryQueueItemsResponse:
    """
    List items in retry queue.
    
    Args:
        limit: Maximum number of items to return
        offset: Number of items to skip
    
    Returns:
        Paginated list of retry queue items
    """
    try:
        redis_client = get_redis_client()
        
        # Read from stream (simplified - in production you'd want cursor-based pagination)
        # XRANGE returns all messages, we'll slice for pagination
        messages = await redis_client.client.xrange(
            redis_client.RETRY_STREAM,
            min='-',
            max='+',
            count=limit + offset
        )
        
        # Skip offset items
        messages = messages[offset:offset + limit]
        
        # Get total count
        total = await redis_client.client.xlen(redis_client.RETRY_STREAM)
        
        # Parse items
        items = []
        for msg_id, data in messages:
            try:
                import json
                document_info = json.loads(data.get("document_info", "{}"))
                
                items.append(RetryQueueItem(
                    message_id=msg_id,
                    job_id=data.get("job_id", "unknown"),
                    file_path=document_info.get("file_path", "unknown"),
                    error_type=data.get("error_type", "unknown"),
                    error_message=data.get("error_message", "")[:200],  # Truncate
                    retry_count=int(data.get("retry_count", 0)),
                    failed_at=data.get("failed_at", ""),
                    next_retry_at=data.get("next_retry_at", "")
                ))
            except Exception as e:
                logger.warning(f"Error parsing retry item {msg_id}: {e}")
        
        return RetryQueueItemsResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        logger.error(f"Error listing retry queue items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list retry queue items: {str(e)}"
        )


@router.post(
    "/retry-queue/reprocess",
    response_model=ReprocessResponse,
    summary="Reprocess failed documents",
    description="Manually reprocess documents from dead letter queue"
)
async def reprocess_failed_documents(
    request: ReprocessRequest
) -> ReprocessResponse:
    """
    Reprocess failed documents.
    
    Can reprocess:
    - Specific message IDs
    - All failures for a job
    - All failures for a file
    - All items in dead letter queue
    
    Args:
        request: Reprocess request with filters
    
    Returns:
        Count of reprocessed items
    """
    try:
        redis_client = get_redis_client()
        reprocessed_count = 0
        
        if request.all:
            # Reprocess all items in dead letter queue
            logger.info("Reprocessing all items in dead letter queue")
            
            # Read all DLQ items
            messages = await redis_client.client.xrange(
                redis_client.FAILED_STREAM,
                min='-',
                max='+'
            )
            
            for msg_id, data in messages:
                try:
                    import json
                    document_info = json.loads(data.get("document_info", "{}"))
                    
                    # Move back to retry queue with retry_count reset
                    await redis_client.enqueue_failed_document(
                        job_id=data.get("job_id"),
                        document_info=document_info,
                        error_type=data.get("error_type"),
                        error_message=data.get("error_message"),
                        retry_count=0  # Reset retry count
                    )
                    
                    # Remove from DLQ
                    await redis_client.client.xdel(redis_client.FAILED_STREAM, msg_id)
                    
                    reprocessed_count += 1
                
                except Exception as e:
                    logger.error(f"Error reprocessing message {msg_id}: {e}")
            
            return ReprocessResponse(
                success=True,
                reprocessed_count=reprocessed_count,
                message=f"Reprocessed {reprocessed_count} items from dead letter queue"
            )
        
        elif request.message_ids:
            # Reprocess specific message IDs
            logger.info(f"Reprocessing {len(request.message_ids)} specific messages")
            
            for msg_id in request.message_ids:
                try:
                    # Read message from DLQ
                    messages = await redis_client.client.xrange(
                        redis_client.FAILED_STREAM,
                        min=msg_id,
                        max=msg_id
                    )
                    
                    if not messages:
                        continue
                    
                    _, data = messages[0]
                    
                    import json
                    document_info = json.loads(data.get("document_info", "{}"))
                    
                    # Move back to retry queue
                    await redis_client.enqueue_failed_document(
                        job_id=data.get("job_id"),
                        document_info=document_info,
                        error_type=data.get("error_type"),
                        error_message=data.get("error_message"),
                        retry_count=0
                    )
                    
                    # Remove from DLQ
                    await redis_client.client.xdel(redis_client.FAILED_STREAM, msg_id)
                    
                    reprocessed_count += 1
                
                except Exception as e:
                    logger.error(f"Error reprocessing message {msg_id}: {e}")
            
            return ReprocessResponse(
                success=True,
                reprocessed_count=reprocessed_count,
                message=f"Reprocessed {reprocessed_count} items"
            )
        
        elif request.job_id:
            # Reprocess all failures for a job
            logger.info(f"Reprocessing all failures for job {request.job_id}")
            
            messages = await redis_client.client.xrange(
                redis_client.FAILED_STREAM,
                min='-',
                max='+'
            )
            
            for msg_id, data in messages:
                if data.get("job_id") == request.job_id:
                    try:
                        import json
                        document_info = json.loads(data.get("document_info", "{}"))
                        
                        await redis_client.enqueue_failed_document(
                            job_id=data.get("job_id"),
                            document_info=document_info,
                            error_type=data.get("error_type"),
                            error_message=data.get("error_message"),
                            retry_count=0
                        )
                        
                        await redis_client.client.xdel(redis_client.FAILED_STREAM, msg_id)
                        
                        reprocessed_count += 1
                    
                    except Exception as e:
                        logger.error(f"Error reprocessing message {msg_id}: {e}")
            
            return ReprocessResponse(
                success=True,
                reprocessed_count=reprocessed_count,
                message=f"Reprocessed {reprocessed_count} items for job {request.job_id}"
            )
        
        elif request.file_path:
            # Reprocess all failures for a file
            logger.info(f"Reprocessing all failures for file {request.file_path}")
            
            messages = await redis_client.client.xrange(
                redis_client.FAILED_STREAM,
                min='-',
                max='+'
            )
            
            for msg_id, data in messages:
                try:
                    import json
                    document_info = json.loads(data.get("document_info", "{}"))
                    
                    if document_info.get("file_path") == request.file_path:
                        await redis_client.enqueue_failed_document(
                            job_id=data.get("job_id"),
                            document_info=document_info,
                            error_type=data.get("error_type"),
                            error_message=data.get("error_message"),
                            retry_count=0
                        )
                        
                        await redis_client.client.xdel(redis_client.FAILED_STREAM, msg_id)
                        
                        reprocessed_count += 1
                
                except Exception as e:
                    logger.error(f"Error reprocessing message {msg_id}: {e}")
            
            return ReprocessResponse(
                success=True,
                reprocessed_count=reprocessed_count,
                message=f"Reprocessed {reprocessed_count} items for file {request.file_path}"
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Must specify message_ids, job_id, file_path, or all=true"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess documents: {str(e)}"
        )


@router.get(
    "/dead-letter/items",
    response_model=DeadLetterItemsResponse,
    summary="List dead letter queue items",
    description="Get a paginated list of items in the dead letter queue"
)
async def list_dead_letter_items(
    limit: int = 50,
    offset: int = 0
) -> DeadLetterItemsResponse:
    """
    List items in dead letter queue.
    
    Args:
        limit: Maximum number of items to return
        offset: Number of items to skip
    
    Returns:
        Paginated list of dead letter queue items
    """
    try:
        redis_client = get_redis_client()
        
        # Read from dead letter stream
        messages = await redis_client.client.xrange(
            redis_client.FAILED_STREAM,
            min='-',
            max='+',
            count=limit + offset
        )
        
        # Skip offset items
        messages = messages[offset:offset + limit]
        
        # Get total count
        total = await redis_client.client.xlen(redis_client.FAILED_STREAM)
        
        # Parse items
        items = []
        for msg_id, data in messages:
            try:
                import json
                document_info = json.loads(data.get("document_info", "{}"))
                
                items.append(DeadLetterItem(
                    message_id=msg_id,
                    job_id=data.get("job_id", "unknown"),
                    file_path=document_info.get("file_path", "unknown"),
                    error_type=data.get("error_type", "unknown"),
                    error_message=data.get("error_message", "")[:200],  # Truncate
                    retry_count=int(data.get("retry_count", 0)),
                    failed_at=data.get("failed_at", ""),
                    moved_to_dlq_at=data.get("moved_to_dlq_at", "")
                ))
            except Exception as e:
                logger.warning(f"Error parsing dead letter item {msg_id}: {e}")
        
        return DeadLetterItemsResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        logger.error(f"Error listing dead letter items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list dead letter items: {str(e)}"
        )


@router.delete(
    "/dead-letter/{message_id}",
    summary="Delete dead letter item",
    description="Permanently delete an item from the dead letter queue"
)
async def delete_dead_letter_item(message_id: str) -> Dict[str, Any]:
    """
    Delete a dead letter queue item.
    
    Args:
        message_id: Redis stream message ID
    
    Returns:
        Success confirmation
    """
    try:
        redis_client = get_redis_client()
        
        # Delete from stream
        deleted = await redis_client.client.xdel(
            redis_client.FAILED_STREAM,
            message_id
        )
        
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message {message_id} not found in dead letter queue"
            )
        
        logger.info(f"Deleted dead letter item: {message_id}")
        
        return {
            "success": True,
            "message": f"Deleted message {message_id}",
            "message_id": message_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dead letter item: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dead letter item: {str(e)}"
        )


@router.get(
    "/retry-worker/status",
    response_model=RetryWorkerStatusResponse,
    summary="Get retry worker status",
    description="Get current status and statistics of the retry worker"
)
async def get_retry_worker_status() -> RetryWorkerStatusResponse:
    """
    Get retry worker status and statistics.
    
    Returns:
        Current worker state and stats
    """
    try:
        retry_worker = get_retry_worker()
        stats = retry_worker.get_stats()
        
        return RetryWorkerStatusResponse(
            running=stats.get("running", False),
            worker_id=stats.get("worker_id", "unknown"),
            started_at=stats.get("started_at"),
            last_poll_at=stats.get("last_poll_at"),
            total_retried=stats.get("total_retried", 0),
            total_recovered=stats.get("total_recovered", 0),
            total_failed=stats.get("total_failed", 0),
            total_moved_to_dlq=stats.get("total_moved_to_dlq", 0),
            batches_processed=stats.get("batches_processed", 0),
            circuit_breaker_trips=stats.get("circuit_breaker_trips", 0),
            circuit_breaker=stats.get("circuit_breaker", {})
        )
    
    except Exception as e:
        logger.error(f"Error getting retry worker status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get retry worker status: {str(e)}"
        )

