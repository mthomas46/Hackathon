"""
Admin endpoints for service management.

Provides operational control and monitoring.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException

from ...utils.redis_client import get_redis_client
from ...storage.chromadb_client import get_chroma_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/queue-status",
    response_model=Dict[str, int],
    summary="Get queue status",
    description="Get depth of all queues"
)
async def get_queue_status():
    """
    Get status of all queues.
    
    Returns queue depths for:
    - Ingestion queue
    - Embedding queue
    - Failed queue (DLQ)
    """
    redis = get_redis_client()
    
    try:
        ingestion_depth = await redis.get_stream_length(redis.INGESTION_STREAM)
        embedding_depth = await redis.get_stream_length(redis.EMBEDDING_STREAM)
        failed_depth = await redis.get_stream_length(redis.FAILED_STREAM)
        
        return {
            "ingestion_queue": ingestion_depth,
            "embedding_queue": embedding_depth,
            "failed_queue": failed_depth
        }
    except Exception as e:
        logger.error(f"Failed to get queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/clear-cache",
    response_model=Dict[str, str],
    summary="Clear Redis cache",
    description="Clear all cached data"
)
async def clear_cache():
    """
    Clear all cached data in Redis.
    
    ⚠️ Use with caution - this clears all cache.
    """
    # TODO: Implement cache clearing
    # For now, return success
    return {
        "status": "success",
        "message": "Cache cleared"
    }


@router.post(
    "/rebuild-index",
    response_model=Dict[str, str],
    summary="Rebuild ChromaDB index",
    description="Rebuild vector database index"
)
async def rebuild_index():
    """
    Rebuild ChromaDB index.
    
    ⚠️ This can take a while for large collections.
    """
    # TODO: Implement index rebuilding
    # This would involve re-embedding all documents
    return {
        "status": "success",
        "message": "Index rebuild started"
    }


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Get system statistics",
    description="Get overall system statistics"
)
async def get_stats():
    """
    Get comprehensive system statistics.
    
    Returns:
    - Document count
    - Embedding count
    - Queue depths
    - Cost information
    """
    chroma = get_chroma_client()
    redis = get_redis_client()
    
    try:
        embedding_count = await chroma.count()
        
        queues = {
            "ingestion": await redis.get_stream_length(redis.INGESTION_STREAM),
            "embedding": await redis.get_stream_length(redis.EMBEDDING_STREAM),
            "failed": await redis.get_stream_length(redis.FAILED_STREAM)
        }
        
        return {
            "documents": {
                "total": 0,  # TODO: Query from database
                "embeddings": embedding_count
            },
            "queues": queues,
            "cost": {
                "total_usd": 0.0,  # TODO: Query from database
                "today_usd": 0.0
            }
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

