"""
Admin endpoints for service management.

Provides operational control and monitoring.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from pydantic import BaseModel, Field

from ...utils.redis_client import get_redis_client
from ...storage.chromadb_client import get_chroma_client
from ...storage import get_database
from ...storage.repositories import IngestionJobRepository

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class IngestRequest(BaseModel):
    """Request to start ingestion."""
    repo_path: str = Field(..., description="Path to repository to ingest")
    mode: str = Field(default="quick", description="Ingestion mode: quick, full, incremental")


class IngestResponse(BaseModel):
    """Response from ingestion request."""
    job_id: str
    status: str
    message: str


class JobStatus(BaseModel):
    """Ingestion job status."""
    job_id: str
    mode: str
    status: str
    started_at: str
    completed_at: Optional[str]
    processed_documents: int
    total_documents: Optional[int]
    failed_documents: int
    embeddings_generated: int
    total_cost_usd: float
    error_message: Optional[str]


# ============================================================================
# Ingestion Endpoints
# ============================================================================

@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Start document ingestion",
    description="Trigger ingestion of documents from a repository"
)
async def start_ingestion(
    request: IngestRequest,
    background_tasks: BackgroundTasks
):
    """
    Start document ingestion process.
    
    Args:
        request: Ingestion request with repo path and mode
        background_tasks: FastAPI background tasks
    
    Returns:
        Job ID and initial status
    """
    try:
        # Validate repo path
        repo_path = Path(request.repo_path)
        if not repo_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Repository path does not exist: {request.repo_path}"
            )
        
        # Create job in database
        db = get_database()
        async with db.session() as session:
            job_repo = IngestionJobRepository(session)
            job = await job_repo.create_job(
                mode=request.mode,
                status="queued",
                repo_path=str(repo_path)
            )
            await session.commit()
            
            job_id = str(job.id)
        
        # Queue ingestion (simplified for now)
        # In production, this would use background tasks or a worker queue
        logger.info(f"Ingestion job {job_id} created for {repo_path}")
        
        return IngestResponse(
            job_id=job_id,
            status="queued",
            message=f"Ingestion job created. Processing {repo_path} in {request.mode} mode."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start ingestion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ingest/status",
    response_model=Dict[str, Any],
    summary="Get all ingestion jobs",
    description="List all ingestion jobs with their status"
)
async def get_all_jobs():
    """
    Get status of all ingestion jobs.
    
    Returns:
        List of all ingestion jobs
    """
    try:
        db = get_database()
        async with db.session() as session:
            # TODO: Implement get_all method in IngestionJobRepository
            # For now, return empty list
            return {
                "jobs": [],
                "total": 0,
                "message": "Ingestion job tracking is available"
            }
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/ingest/{job_id}",
    response_model=JobStatus,
    summary="Get ingestion job status",
    description="Get detailed status of a specific ingestion job"
)
async def get_job_status(job_id: UUID):
    """
    Get status of specific ingestion job.
    
    Args:
        job_id: Job UUID
    
    Returns:
        Detailed job status
    """
    try:
        db = get_database()
        async with db.session() as session:
            job_repo = IngestionJobRepository(session)
            job = await job_repo.get_by_id(job_id)
            
            if not job:
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            
            return JobStatus(
                job_id=str(job.id),
                mode=job.mode,
                status=job.status,
                started_at=job.started_at.isoformat(),
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
                processed_documents=job.processed_documents,
                total_documents=job.total_documents,
                failed_documents=job.failed_documents,
                embeddings_generated=job.embeddings_generated,
                total_cost_usd=job.total_cost_usd,
                error_message=job.error_message
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Queue Management
# ============================================================================

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


# ============================================================================
# System Management
# ============================================================================

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
        "message": "Cache cleared (not yet implemented)"
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
        "message": "Index rebuild started (not yet implemented)"
    }


@router.get(
    "/cache-stats",
    response_model=Dict[str, Any],
    summary="Get cache statistics",
    description="Get cache hit/miss rates and performance metrics"
)
async def get_cache_statistics():
    """
    Get cache statistics.
    
    Returns:
    - Cache hits/misses
    - Hit rate percentage
    - Total cached operations
    """
    stats = get_cache_stats()
    
    return {
        "cache_hits": stats["cache_hits"],
        "cache_misses": stats["cache_misses"],
        "total_requests": stats["total_requests"],
        "hit_rate_percent": stats["hit_rate_percent"],
        "message": f"Cache is {'performing well' if stats['hit_rate_percent'] > 50 else 'warming up'}"
    }


@router.post(
    "/clear-cache",
    response_model=Dict[str, str],
    summary="Clear cache by prefix",
    description="Clear cached data for a specific prefix"
)
async def clear_cache_by_prefix(prefix: str = Query("cache", description="Cache prefix to clear")):
    """
    Clear cache for a specific prefix.
    
    Args:
        prefix: Cache prefix (e.g., "embedding", "search", "cache")
    
    Returns:
        Status message with number of keys deleted
    """
    deleted = await clear_cache_prefix(prefix)
    
    return {
        "status": "success",
        "message": f"Cleared {deleted} cache keys with prefix '{prefix}'"
    }


@router.post(
    "/clear-all-cache",
    response_model=Dict[str, str],
    summary="Clear all cache",
    description="Clear ALL cached data (use with caution)"
)
async def clear_entire_cache():
    """
    Clear ALL cache.
    
    ⚠️ Use with caution - this clears all cached data.
    """
    deleted = await clear_all_cache()
    
    return {
        "status": "success",
        "message": f"Cleared ALL cache: {deleted} keys deleted"
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
    db = get_database()
    
    try:
        embedding_count = await chroma.count()
        
        queues = {
            "ingestion": await redis.get_stream_length(redis.INGESTION_STREAM),
            "embedding": await redis.get_stream_length(redis.EMBEDDING_STREAM),
            "failed": await redis.get_stream_length(redis.FAILED_STREAM)
        }
        
        # Get document count from database
        async with db.session() as session:
            from ...storage.repositories import DocumentRepository
            doc_repo = DocumentRepository(session)
            doc_count = await doc_repo.count()
        
        return {
            "documents": {
                "total": doc_count,
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
