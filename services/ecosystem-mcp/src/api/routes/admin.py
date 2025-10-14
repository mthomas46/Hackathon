"""
Admin endpoints for service management.

Provides operational control and monitoring.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, BackgroundTasks, Body, Query
from pydantic import BaseModel, Field

from ...utils.redis_client import get_redis_client
from ...storage.chromadb_client import get_chroma_client
from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from ...utils.cache_decorator import get_cache_stats, clear_cache_prefix, clear_all_cache
from ...services.models.ollama_client import get_ollama_client

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
    skipped_documents: int = 0  # NEW: Duplicates, not errors
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
        
        # ✅ Add job to Redis stream for worker to process
        redis = get_redis_client()
        
        # Ensure Redis is connected (lazy connection)
        if not redis._connected or redis.client is None:
            logger.warning("Redis not connected, connecting now...")
            await redis.connect()
        
        await redis.add_to_stream(
            stream=redis.INGESTION_STREAM,
            data={"job_id": job_id, "mode": request.mode, "repo_path": str(repo_path)}
        )
        logger.info(f"✅ Ingestion job {job_id} created and queued for {repo_path}")
        
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
        List of all ingestion jobs with their details
    """
    try:
        db = get_database()
        async with db.session() as session:
            job_repo = IngestionJobRepository(session)
            
            # Get all jobs, most recent first
            jobs = await job_repo.get_all(limit=100, offset=0)
            total = len(jobs)
            
            # Convert to response format
            job_list = []
            for job in jobs:
                job_list.append({
                    "job_id": str(job.id),
                    "mode": job.mode,
                    "status": job.status,
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "processed_documents": job.processed_documents or 0,
                    "total_documents": job.total_documents,
                    "failed_documents": job.failed_documents or 0,
                    "skipped_documents": job.skipped_documents or 0,
                    "embeddings_generated": job.embeddings_generated or 0,
                    "total_cost_usd": float(job.total_cost_usd or 0),
                    "error_message": job.error_message,
                    "job_metadata": job.job_metadata or {}  # Include metadata for live updates
                })
            
            return {
                "jobs": job_list,
                "total": total,
                "message": f"Found {total} ingestion job(s)"
            }
    except Exception as e:
        logger.error(f"Failed to get job status: {e}", exc_info=True)
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
                skipped_documents=job.skipped_documents or 0,  # NEW
                embeddings_generated=job.embeddings_generated,
                total_cost_usd=job.total_cost_usd,
                error_message=job.error_message
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/ingest/{job_id}/cancel",
    response_model=Dict[str, Any],
    summary="Cancel ingestion job",
    description="Cancel a processing ingestion job"
)
async def cancel_job(job_id: UUID):
    """
    Cancel a processing ingestion job.
    
    Args:
        job_id: Job UUID to cancel
    
    Returns:
        Updated job status
    
    Note:
        - Can only cancel jobs with status 'processing' or 'queued'
        - Job will be marked as 'failed' with cancellation message
        - Currently processing documents may complete
    """
    try:
        db = get_database()
        async with db.session() as session:
            job_repo = IngestionJobRepository(session)
            job = await job_repo.get_by_id(job_id)
            
            if not job:
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            
            # Check if job can be cancelled
            if job.status not in ["processing", "queued"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot cancel job with status '{job.status}'. Only 'processing' or 'queued' jobs can be cancelled."
                )
            
            # Update job to cancelled/failed status
            job.status = "failed"
            job.completed_at = datetime.utcnow()
            job.error_message = "Job cancelled by user"
            
            await job_repo.update(job)
            await session.commit()
            
            logger.info(f"Job {job_id} cancelled by user")
            
            return {
                "job_id": str(job_id),
                "status": "cancelled",
                "message": f"Job {job_id} has been cancelled",
                "note": "Currently processing documents may complete. Job marked as failed."
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/jobs/completed",
    response_model=Dict[str, Any],
    summary="Clear completed jobs",
    description="Delete all completed ingestion job records from the database"
)
async def clear_completed_jobs():
    """
    Clear all completed ingestion jobs from the database.
    
    ⚠️ WARNING: This permanently deletes job records. Cannot be undone.
    
    Returns:
        Number of jobs deleted
    """
    try:
        db = get_database()
        async with db.session() as session:
            from sqlalchemy import delete
            from ...storage.db_models import IngestionJobModel
            
            # Delete all jobs with status 'completed'
            stmt = delete(IngestionJobModel).where(IngestionJobModel.status == "completed")
            result = await session.execute(stmt)
            await session.commit()
            
            deleted_count = result.rowcount
            
            logger.info(f"Cleared {deleted_count} completed ingestion jobs")
            
            return {
                "deleted": deleted_count,
                "message": f"Cleared {deleted_count} completed job(s)"
            }
    except Exception as e:
        logger.error(f"Failed to clear completed jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/jobs/failed",
    response_model=Dict[str, Any],
    summary="Clear failed jobs",
    description="Delete all failed ingestion job records from the database"
)
async def clear_failed_jobs():
    """
    Clear all failed ingestion jobs from the database.
    
    ⚠️ WARNING: This permanently deletes job records. Cannot be undone.
    
    Returns:
        Number of jobs deleted
    """
    try:
        db = get_database()
        async with db.session() as session:
            from sqlalchemy import delete
            from ...storage.db_models import IngestionJobModel
            
            # Delete all jobs with status 'failed'
            stmt = delete(IngestionJobModel).where(IngestionJobModel.status == "failed")
            result = await session.execute(stmt)
            await session.commit()
            
            deleted_count = result.rowcount
            
            logger.info(f"Cleared {deleted_count} failed ingestion jobs")
            
            return {
                "deleted": deleted_count,
                "message": f"Cleared {deleted_count} failed job(s)"
            }
    except Exception as e:
        logger.error(f"Failed to clear failed jobs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/jobs/all",
    response_model=Dict[str, Any],
    summary="Clear all jobs",
    description="Delete ALL ingestion job records from the database (⚠️ NUCLEAR OPTION)"
)
async def clear_all_jobs():
    """
    Clear all ingestion jobs from the database.
    
    ⚠️⚠️⚠️ NUCLEAR OPTION: This deletes ALL job records. Cannot be undone.
    
    Returns:
        Number of jobs deleted
    """
    try:
        db = get_database()
        async with db.session() as session:
            from sqlalchemy import delete
            from ...storage.db_models import IngestionJobModel
            
            # Delete all jobs
            stmt = delete(IngestionJobModel)
            result = await session.execute(stmt)
            await session.commit()
            
            deleted_count = result.rowcount
            
            logger.warning(f"⚠️ CLEARED ALL {deleted_count} INGESTION JOBS")
            
            return {
                "deleted": deleted_count,
                "message": f"Cleared all {deleted_count} job(s)"
            }
    except Exception as e:
        logger.error(f"Failed to clear all jobs: {e}", exc_info=True)
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
    "/circuit-breakers",
    response_model=Dict[str, Any],
    summary="Get circuit breaker status",
    description="Get status of all circuit breakers"
)
async def get_circuit_breaker_status():
    """
    Get circuit breaker status for all protected services.
    
    Returns:
    - State (CLOSED, OPEN, HALF_OPEN)
    - Failure counts
    - Recovery time remaining
    """
    try:
        ollama = get_ollama_client()
        chroma = get_chroma_client()
        
        circuit_breakers = {}
        
        # Check if clients have circuit breakers
        if hasattr(ollama, 'circuit_breaker') and hasattr(ollama.circuit_breaker, 'get_state'):
            circuit_breakers["ollama"] = ollama.circuit_breaker.get_state()
        else:
            circuit_breakers["ollama"] = {
                "state": "NOT_CONFIGURED",
                "message": "Circuit breaker not configured for Ollama"
            }
        
        if hasattr(chroma, 'circuit_breaker') and hasattr(chroma.circuit_breaker, 'get_state'):
            circuit_breakers["chromadb"] = chroma.circuit_breaker.get_state()
        else:
            circuit_breakers["chromadb"] = {
                "state": "NOT_CONFIGURED",
                "message": "Circuit breaker not configured for ChromaDB"
            }
        
        return {
            "circuit_breakers": circuit_breakers,
            "message": "Circuit breakers protect against cascading failures"
        }
    
    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {e}")
        return {
            "circuit_breakers": {},
            "message": f"Error retrieving circuit breakers: {str(e)}"
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


# ============================================================================
# Data Management Endpoints
# ============================================================================

@router.delete(
    "/data/postgres",
    response_model=Dict[str, Any],
    summary="Clear PostgreSQL documents",
    description="Delete all documents from PostgreSQL (⚠️ DESTRUCTIVE)"
)
async def clear_postgres_data():
    """
    Clear all document data from PostgreSQL.
    
    ⚠️ WARNING: This is a destructive operation that cannot be undone!
    
    Deletes:
    - All documents
    - Document versions
    - Document metadata
    - Git commit history
    
    Returns:
        Status message with count of deleted items
    """
    try:
        db = get_database()
        async with db.session() as session:
            # Delete all documents (cascade will handle versions)
            from sqlalchemy import delete
            from ...storage.db_models import DocumentModel, GitCommitModel
            
            # Count before delete
            from ...storage.repositories import DocumentRepository
            doc_repo = DocumentRepository(session)
            count_before = await doc_repo.count()
            
            # Delete documents
            await session.execute(delete(DocumentModel))
            
            # Delete git commits
            await session.execute(delete(GitCommitModel))
            
            await session.commit()
            
            logger.warning(f"🗑️ DELETED {count_before} documents from PostgreSQL")
            
            return {
                "success": True,
                "deleted": count_before,
                "datastore": "postgresql",
                "message": f"Deleted {count_before} documents from PostgreSQL"
            }
            
    except Exception as e:
        logger.error(f"Failed to clear PostgreSQL data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/data/chromadb",
    response_model=Dict[str, Any],
    summary="Clear ChromaDB embeddings",
    description="Delete all embeddings from ChromaDB (⚠️ DESTRUCTIVE)"
)
async def clear_chromadb_data():
    """
    Clear all embeddings from ChromaDB.
    
    ⚠️ WARNING: This is a destructive operation that cannot be undone!
    
    Deletes:
    - All document embeddings
    - Vector metadata
    - Collection data
    
    Note: Documents in PostgreSQL will remain intact.
    
    Returns:
        Status message with count of deleted embeddings
    """
    try:
        chroma = get_chroma_client()
        
        # Get count before delete
        count_before = await chroma.count()
        
        # Delete the entire collection and recreate it
        import chromadb
        client = chromadb.HttpClient(
            host=chroma.host,
            port=chroma.port
        )
        
        # Delete collection
        try:
            client.delete_collection(name=chroma.collection_name)
            logger.info(f"Deleted collection: {chroma.collection_name}")
        except Exception as e:
            logger.warning(f"Collection may not exist: {e}")
        
        # Recreate collection
        client.create_collection(
            name=chroma.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Recreated collection: {chroma.collection_name}")
        
        logger.warning(f"🗑️ DELETED {count_before} embeddings from ChromaDB")
        
        return {
            "success": True,
            "deleted": count_before,
            "datastore": "chromadb",
            "message": f"Deleted {count_before} embeddings from ChromaDB"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear ChromaDB data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/data/stats",
    response_model=Dict[str, Any],
    summary="Get data statistics",
    description="Get counts of data in each datastore"
)
async def get_data_stats():
    """
    Get data statistics across all datastores.
    
    Returns:
        Counts for documents, embeddings, and cache keys
    """
    try:
        db = get_database()
        chroma = get_chroma_client()
        redis = get_redis_client()
        
        # Get document count
        async with db.session() as session:
            from ...storage.repositories import DocumentRepository
            doc_repo = DocumentRepository(session)
            doc_count = await doc_repo.count()
        
        # Get embedding count
        embedding_count = await chroma.count()
        
        # Get cache key count
        cache_stats = await get_cache_stats()
        cache_key_count = cache_stats.get("total_keys", 0)
        
        return {
            "documents": doc_count,
            "embeddings": embedding_count,
            "cache_keys": cache_key_count
        }
        
    except Exception as e:
        logger.error(f"Failed to get data stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
