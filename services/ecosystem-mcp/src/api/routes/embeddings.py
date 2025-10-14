"""
Embeddings endpoints for exploring and analyzing vector embeddings.

Provides access to raw embeddings, sampling, and analysis capabilities.
"""

import logging
import random
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...storage.chromadb_client import get_chroma_client
from ...utils.cache_decorator import cache

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class EmbeddingMetadata(BaseModel):
    """Metadata for an embedding."""
    service: Optional[str] = None
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    chunk_index: Optional[int] = None


class EmbeddingSample(BaseModel):
    """Single embedding sample with metadata."""
    id: str
    file_path: str
    service: str
    embedding_model: str = "nomic-embed-text"
    dimensions: int = 768
    content_preview: str
    metadata: dict
    vector_preview: Optional[List[float]] = None  # First 10 dimensions
    vector_stats: Optional[dict] = None  # Mean, std, norm, etc.


class SampleResponse(BaseModel):
    """Response for embedding samples."""
    samples: List[EmbeddingSample]
    count: int
    total_documents: int
    collection: str


class EmbeddingDetail(BaseModel):
    """Detailed embedding information."""
    id: str
    file_path: str
    service: str
    content: str
    metadata: dict
    embedding_model: str = "nomic-embed-text"
    dimensions: int = 768
    vector: Optional[List[float]] = None
    vector_stats: dict


@router.get(
    "/sample",
    response_model=SampleResponse,
    summary="Sample random embeddings",
    description="Get random sample of embeddings for exploration and analysis"
)
@limiter.limit("10/minute")
@cache(ttl=60, key_prefix="embedding_sample")
async def sample_embeddings(
    request: Request,
    n: int = Query(10, ge=1, le=100, description="Number of samples to return"),
    service: Optional[str] = Query(None, description="Filter by service name"),
    include_vectors: bool = Query(False, description="Include full 768D vectors (slower)")
):
    """
    Get random sample of embeddings from ChromaDB.
    
    This endpoint is useful for:
    - Exploring the vector space
    - Quality checking embeddings
    - Visualizing document distribution
    - Debugging embedding issues
    
    Args:
        n: Number of random samples (1-100)
        service: Optional service name filter
        include_vectors: Whether to include full 768D vectors
    
    Returns:
        Random sample of embeddings with metadata
    
    Example:
        GET /api/v1/embeddings/sample?n=20&service=ecosystem-mcp
    """
    try:
        logger.info(f"Sampling {n} embeddings (service={service}, include_vectors={include_vectors})")
        
        # Get ChromaDB client (singleton with existing collection)
        chroma_client = get_chroma_client()
        collection = chroma_client.collection  # Use the pre-initialized collection
        
        logger.info(f"Collection name: {collection.name}, count: {collection.count()}")
        
        # Get all document IDs (with optional service filter)
        if service:
            # Query with service filter
            all_results = collection.get(
                where={"service": service},
                include=["metadatas"]
            )
        else:
            # Get all documents
            all_results = collection.get(
                include=["metadatas"]
            )
        
        all_ids = all_results["ids"]
        total_count = len(all_ids)
        logger.info(f"Retrieved {total_count} document IDs from ChromaDB")
        
        if total_count == 0:
            if service:
                raise HTTPException(
                    status_code=404,
                    detail=f"No documents found for service '{service}'. Check if documents are ingested."
                )
            else:
                raise HTTPException(
                    status_code=404,
                    detail="No documents found in ChromaDB. Ensure documents are ingested and embedded."
                )
        
        # Random sample of IDs
        sample_size = min(n, total_count)
        sampled_ids = random.sample(all_ids, sample_size)
        
        logger.info(f"Sampled {sample_size} IDs from {total_count} total documents")
        
        # Get full data for sampled IDs
        include_fields = ["metadatas", "documents"]
        if include_vectors:
            include_fields.append("embeddings")
        
        samples_data = collection.get(
            ids=sampled_ids,
            include=include_fields
        )
        
        # Format response
        samples = []
        for i, doc_id in enumerate(sampled_ids):
            metadata = samples_data["metadatas"][i] if samples_data["metadatas"] else {}
            document = samples_data["documents"][i] if samples_data["documents"] else ""
            
            sample = EmbeddingSample(
                id=doc_id,
                file_path=metadata.get("file_path", "Unknown"),
                service=metadata.get("service", "Unknown"),
                embedding_model="nomic-embed-text",
                dimensions=768,
                content_preview=document[:200] if document else "No content",
                metadata=metadata
            )
            
            # Add vector info if requested
            if include_vectors and "embeddings" in samples_data and samples_data["embeddings"]:
                import numpy as np
                vector = np.array(samples_data["embeddings"][i])
                
                sample.vector_preview = vector[:10].tolist()  # First 10 dimensions
                sample.vector_stats = {
                    "norm": float(np.linalg.norm(vector)),
                    "mean": float(np.mean(vector)),
                    "std": float(np.std(vector)),
                    "min": float(np.min(vector)),
                    "max": float(np.max(vector))
                }
            
            samples.append(sample)
        
        return SampleResponse(
            samples=samples,
            count=len(samples),
            total_documents=total_count,
            collection="ecosystem_docs"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sampling embeddings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sample embeddings: {str(e)}"
        )


@router.get(
    "/{embedding_id}",
    response_model=EmbeddingDetail,
    summary="Get embedding by ID",
    description="Retrieve detailed embedding information including the full 768D vector"
)
@limiter.limit("20/minute")
@cache(ttl=300, key_prefix="embedding_detail")
async def get_embedding_by_id(
    request: Request,
    embedding_id: str,
    include_vector: bool = Query(True, description="Include full 768D vector")
):
    """
    Get detailed information about a specific embedding.
    
    Args:
        embedding_id: Document ID
        include_vector: Whether to include the full 768D vector
    
    Returns:
        Complete embedding information with statistics
    
    Example:
        GET /api/v1/embeddings/abc123?include_vector=true
    """
    try:
        logger.info(f"Fetching embedding: {embedding_id} (include_vector={include_vector})")
        
        # Get ChromaDB client (singleton with existing collection)
        chroma_client = get_chroma_client()
        collection = chroma_client.collection  # Use the pre-initialized collection
        
        # Get document by ID
        include_fields = ["metadatas", "documents"]
        if include_vector:
            include_fields.append("embeddings")
        
        result = collection.get(
            ids=[embedding_id],
            include=include_fields
        )
        
        if not result["ids"]:
            raise HTTPException(
                status_code=404,
                detail=f"Embedding '{embedding_id}' not found in ChromaDB"
            )
        
        # Extract data
        metadata = result["metadatas"][0] if result["metadatas"] else {}
        document = result["documents"][0] if result["documents"] else ""
        
        embedding_detail = EmbeddingDetail(
            id=embedding_id,
            file_path=metadata.get("file_path", "Unknown"),
            service=metadata.get("service", "Unknown"),
            content=document,
            metadata=metadata,
            embedding_model="nomic-embed-text",
            dimensions=768,
            vector_stats={}
        )
        
        # Add vector and stats if requested
        if include_vector and "embeddings" in result and result["embeddings"]:
            import numpy as np
            vector = np.array(result["embeddings"][0])
            
            embedding_detail.vector = vector.tolist()
            embedding_detail.vector_stats = {
                "norm": float(np.linalg.norm(vector)),
                "mean": float(np.mean(vector)),
                "std": float(np.std(vector)),
                "min": float(np.min(vector)),
                "max": float(np.max(vector)),
                "dimensions": len(vector)
            }
        
        return embedding_detail
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching embedding {embedding_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch embedding: {str(e)}"
        )


@router.get(
    "/export/batch",
    summary="Export embeddings in batch",
    description="Export multiple embeddings for visualization or analysis"
)
@limiter.limit("5/minute")
async def export_embeddings_batch(
    request: Request,
    limit: int = Query(100, ge=1, le=500, description="Number of embeddings to export"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    service: Optional[str] = Query(None, description="Filter by service name")
):
    """
    Export embeddings in batch for visualization tools (t-SNE, UMAP, etc.).
    
    This endpoint returns embeddings in a format suitable for:
    - Dimensionality reduction (t-SNE, UMAP, PCA)
    - Clustering analysis
    - Similarity heatmaps
    - Quality assessment
    
    Args:
        limit: Number of embeddings (1-500)
        offset: Starting position for pagination
        service: Optional service filter
    
    Returns:
        Batch of embeddings with metadata
    
    Example:
        GET /api/v1/embeddings/export/batch?limit=100&service=ecosystem-mcp
    """
    try:
        logger.info(f"Exporting embeddings batch: limit={limit}, offset={offset}, service={service}")
        
        # Get ChromaDB client (singleton with existing collection)
        chroma_client = get_chroma_client()
        collection = chroma_client.collection  # Use the pre-initialized collection
        
        # First get all IDs (without embeddings to save memory)
        if service:
            all_results = collection.get(
                where={"service": service},
                include=["metadatas"]
            )
        else:
            all_results = collection.get(
                include=["metadatas"]
            )
        
        all_ids = all_results["ids"]
        
        if not all_ids:
            raise HTTPException(
                status_code=404,
                detail="No embeddings found matching the criteria"
            )
        
        # Apply pagination
        start_idx = offset
        end_idx = min(offset + limit, len(all_ids))
        paginated_ids = all_ids[start_idx:end_idx]
        
        logger.info(f"Fetching {len(paginated_ids)} embeddings (from {len(all_ids)} total)")
        
        # Get full data for paginated IDs
        results = collection.get(
            ids=paginated_ids,
            include=["metadatas", "embeddings", "documents"]
        )
        
        # Convert embeddings to plain Python lists for JSON serialization
        embeddings_list = [[float(x) for x in embedding] for embedding in results["embeddings"]]
        
        return {
            "embeddings": embeddings_list,
            "ids": results["ids"],
            "metadata": results["metadatas"],
            "documents": [doc[:200] if doc else "" for doc in (results.get("documents") or [])],
            "count": len(results["ids"]),
            "offset": offset,
            "limit": limit
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting embeddings batch: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export embeddings: {str(e)}"
        )

