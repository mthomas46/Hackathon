"""
Embeddings Administration Routes

Provides endpoints for managing embeddings, including regeneration
and health monitoring.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from ...storage import get_database
from ...storage.chromadb_client import get_chroma_client
from ...storage.repositories import DocumentRepository
from ...services.embeddings.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Models
# ============================================================================

class EmbeddingStatsResponse(BaseModel):
    """Response model for embedding statistics."""
    total_documents: int
    total_embeddings: int
    missing_embeddings: int
    coverage_percent: float
    timestamp: str


class RegenerateRequest(BaseModel):
    """Request to regenerate embeddings."""
    batch_size: int = 10
    skip_existing: bool = True


class RegenerateResponse(BaseModel):
    """Response from regeneration request."""
    status: str
    message: str
    estimated_time_minutes: int


# ============================================================================
# Background Task
# ============================================================================

async def regenerate_embeddings_task(batch_size: int = 10, skip_existing: bool = True):
    """
    Background task to regenerate embeddings.
    
    Args:
        batch_size: Number of documents to process per batch
        skip_existing: Whether to skip documents that already have embeddings
    """
    logger.info("🚀 Starting embedding regeneration task...")
    
    try:
        db = get_database()
        chroma = get_chroma_client()
        embedding_service = EmbeddingService()
        
        # Get all documents
        async with db.session() as session:
            doc_repo = DocumentRepository(session)
            all_docs = await doc_repo.get_all(limit=10000)
            total_docs = len(all_docs)
        
        logger.info(f"📚 Found {total_docs} documents to process")
        
        # Get existing embeddings if skipping
        existing_ids = set()
        if skip_existing:
            try:
                import asyncio
                existing_result = await asyncio.to_thread(
                    chroma.collection.get,
                    include=[]
                )
                existing_ids = set(existing_result['ids'])
                logger.info(f"⏭️  Will skip {len(existing_ids)} existing embeddings")
            except Exception as e:
                logger.warning(f"Could not fetch existing IDs: {e}")
        
        # Process in batches
        processed = 0
        succeeded = 0
        failed = 0
        skipped = 0
        
        for i in range(0, total_docs, batch_size):
            batch = all_docs[i:i + batch_size]
            
            for doc in batch:
                processed += 1
                doc_id = str(doc.id)
                
                # Skip if exists
                if skip_existing and doc_id in existing_ids:
                    skipped += 1
                    continue
                
                try:
                    # Generate embedding
                    logger.info(f"🔄 [{processed}/{total_docs}] {doc.file_path}")
                    
                    embedding_result = await embedding_service.generate_embedding(
                        text=doc.normalized_content or doc.original_content
                    )
                    
                    if not embedding_result or not embedding_result.get("embedding"):
                        failed += 1
                        logger.error(f"❌ Failed: {doc.file_path}")
                        continue
                    
                    # Store in ChromaDB
                    metadata = {
                        "file_path": doc.file_path,
                        "service_name": doc.service_name or "unknown",
                        "file_type": doc.file_type or "unknown",
                        "commit_sha": doc.git_commit_sha or "unknown",
                        "content_hash": doc.content_hash
                    }
                    
                    success = await chroma.add_embeddings_with_retry(
                        embeddings=[embedding_result["embedding"]],
                        metadatas=[metadata],
                        ids=[doc_id],
                        documents=[doc.normalized_content or doc.original_content],
                        max_retries=3
                    )
                    
                    if success:
                        succeeded += 1
                        logger.info(f"✅ Success: {doc.file_path}")
                    else:
                        failed += 1
                        logger.error(f"❌ Storage failed: {doc.file_path}")
                
                except Exception as e:
                    failed += 1
                    logger.error(f"❌ Error {doc.file_path}: {e}")
            
            # Small delay between batches
            if i + batch_size < total_docs:
                import asyncio
                await asyncio.sleep(0.5)
        
        # Log summary
        logger.info("=" * 70)
        logger.info("🎉 Embedding Regeneration Complete!")
        logger.info(f"Processed: {processed} | ✅ {succeeded} | ❌ {failed} | ⏭️ {skipped}")
        logger.info(f"Final count: {await chroma.count()} embeddings")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Regeneration task failed: {e}", exc_info=True)


# ============================================================================
# Routes
# ============================================================================

@router.get(
    "/embeddings/stats",
    response_model=EmbeddingStatsResponse,
    summary="Get embedding statistics",
    description="Get statistics about documents and embeddings coverage"
)
async def get_embedding_stats():
    """
    Get embedding statistics.
    
    Returns:
        Statistics about documents, embeddings, and coverage
    """
    try:
        db = get_database()
        chroma = get_chroma_client()
        
        # Get document count
        async with db.session() as session:
            doc_repo = DocumentRepository(session)
            all_docs = await doc_repo.get_all(limit=10000)
            total_documents = len(all_docs)
        
        # Get embedding count
        total_embeddings = await chroma.count()
        
        # Calculate stats
        missing = max(0, total_documents - total_embeddings)
        coverage = (total_embeddings / total_documents * 100) if total_documents > 0 else 0
        
        return EmbeddingStatsResponse(
            total_documents=total_documents,
            total_embeddings=total_embeddings,
            missing_embeddings=missing,
            coverage_percent=round(coverage, 2),
            timestamp=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Failed to get embedding stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/embeddings/regenerate",
    response_model=RegenerateResponse,
    summary="Regenerate embeddings",
    description="Start background task to regenerate missing embeddings"
)
async def regenerate_embeddings(
    request: RegenerateRequest,
    background_tasks: BackgroundTasks
):
    """
    Start embedding regeneration process.
    
    Args:
        request: Regeneration configuration
        background_tasks: FastAPI background tasks
    
    Returns:
        Status and estimated completion time
    """
    try:
        # Get stats for estimation
        db = get_database()
        chroma = get_chroma_client()
        
        async with db.session() as session:
            doc_repo = DocumentRepository(session)
            all_docs = await doc_repo.get_all(limit=10000)
            total_docs = len(all_docs)
        
        total_embeddings = await chroma.count()
        missing = max(0, total_docs - total_embeddings)
        
        if missing == 0:
            return RegenerateResponse(
                status="success",
                message="All documents already have embeddings",
                estimated_time_minutes=0
            )
        
        # Estimate time (roughly 2 seconds per document)
        estimated_minutes = max(1, int((missing * 2) / 60))
        
        # Add background task
        background_tasks.add_task(
            regenerate_embeddings_task,
            batch_size=request.batch_size,
            skip_existing=request.skip_existing
        )
        
        logger.info(f"🚀 Started embedding regeneration for {missing} documents")
        
        return RegenerateResponse(
            status="started",
            message=f"Regeneration started for {missing} documents",
            estimated_time_minutes=estimated_minutes
        )
    
    except Exception as e:
        logger.error(f"Failed to start regeneration: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/embeddings/health",
    summary="Check embedding system health",
    description="Check if embedding system is operational"
)
async def embedding_health():
    """
    Check embedding system health.
    
    Returns:
        Health status of embedding components
    """
    try:
        chroma = get_chroma_client()
        embedding_service = EmbeddingService()
        
        # Test ChromaDB
        chroma_healthy = await chroma.health_check()
        chroma_count = await chroma.count() if chroma_healthy else 0
        
        # Test embedding generation
        try:
            test_result = await embedding_service.generate_embedding("test")
            embedding_healthy = bool(test_result.get("embedding"))
        except Exception as e:
            logger.error(f"Embedding test failed: {e}")
            embedding_healthy = False
        
        overall_healthy = chroma_healthy and embedding_healthy
        
        return {
            "status": "healthy" if overall_healthy else "degraded",
            "chromadb": {
                "healthy": chroma_healthy,
                "count": chroma_count
            },
            "embedding_service": {
                "healthy": embedding_healthy
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

