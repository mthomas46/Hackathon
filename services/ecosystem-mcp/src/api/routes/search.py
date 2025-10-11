"""
Search endpoints for semantic search across documents.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...storage import get_database
from ...storage.chromadb_client import get_chroma_client
from ...storage.repositories import DocumentRepository
from ...services.models.ollama_client import get_ollama_client

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class SearchResult(BaseModel):
    """Single search result."""
    document_id: str
    service_name: str
    file_path: str
    score: float  # Renamed from relevance_score to match implementation
    snippet: str


class SearchRequest(BaseModel):
    """Search request model."""
    query: str = Field(..., description="Search query", min_length=1)
    service_name: Optional[str] = Field(None, description="Filter by service name")
    limit: int = Field(10, ge=1, le=100, description="Maximum results")


class SearchResponse(BaseModel):
    """Search response model."""
    results: List[SearchResult]
    query: str
    total_results: int


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search",
    description="Search across all documents using semantic similarity"
)
@limiter.limit("10/minute")  # ✅ Rate limit: 10 searches per minute
async def search_documents(http_request: Request, request: SearchRequest):
    """
    Perform semantic search across documents.
    
    Uses Ollama for embedding generation and ChromaDB for vector similarity search.
    
    Args:
        http_request: FastAPI request (for rate limiting)
        request: Search request with query and filters
    
    Returns:
        Search results with relevance scores and metadata
    
    Raises:
        HTTPException: If embedding generation or search fails
    """
    try:
        # Step 1: Generate embedding for query using Ollama
        logger.info(f"Generating embedding for query: {request.query[:50]}...")
        ollama = get_ollama_client()
        
        if not await ollama.is_available():
            raise HTTPException(
                status_code=503, 
                detail="Ollama service unavailable - cannot generate query embedding"
            )
        
        # Generate query embedding
        query_embedding = await ollama.generate_embedding(
            request.query,
            model=None  # Uses default embedding model
        )
        
        if not query_embedding:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate query embedding"
            )
        
        logger.info(f"Query embedding generated: {len(query_embedding)} dimensions")
        
        # Step 2: Search ChromaDB for similar vectors
        logger.info(f"Searching ChromaDB for {request.limit} similar documents...")
        chroma = get_chroma_client()
        
        # Build where filter if service filter provided
        where_filter = None
        if request.service_name:
            where_filter = {"service_name": request.service_name}
        
        # Query ChromaDB
        search_results = await chroma.query(
            query_embeddings=[query_embedding],
            n_results=request.limit,
            where=where_filter,
            include=["metadatas", "documents", "distances"]
        )
        
        # Step 3: Extract results and fetch full document metadata from PostgreSQL
        if not search_results or not search_results.get("ids"):
            logger.info("No results found")
            return SearchResponse(
                results=[],
                query=request.query,
                total_results=0
            )
        
        # Get document IDs from ChromaDB results
        document_ids = search_results["ids"][0]  # First query results
        distances = search_results["distances"][0]  # Similarity scores
        metadatas = search_results["metadatas"][0] if "metadatas" in search_results else []
        snippets = search_results["documents"][0] if "documents" in search_results else []
        
        logger.info(f"Found {len(document_ids)} results from ChromaDB")
        
        # Step 4: Fetch full document data from PostgreSQL
        db = get_database()
        results = []
        
        async with db.session() as session:
            repo = DocumentRepository(session)
            
            for idx, doc_id in enumerate(document_ids):
                try:
                    # Convert distance to similarity score (0-1, higher is better)
                    # ChromaDB uses cosine distance, so: similarity = 1 - distance
                    distance = distances[idx]
                    similarity = max(0.0, 1.0 - distance)  # Clamp to [0, 1]
                    
                    # Get metadata from ChromaDB
                    metadata = metadatas[idx] if idx < len(metadatas) else {}
                    snippet = snippets[idx] if idx < len(snippets) else ""
                    
                    # Fetch document from database
                    from uuid import UUID
                    try:
                        document = await repo.get_by_id(UUID(doc_id))
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid document ID: {doc_id}")
                        continue
                    
                    if not document:
                        logger.warning(f"Document not found in database: {doc_id}")
                        continue
                    
                    # Create search result
                    result = SearchResult(
                        document_id=str(document.id),
                        service_name=document.service_name,
                        file_path=document.file_path,
                        score=round(similarity, 4),
                        snippet=snippet[:500] if snippet else document.normalized_content[:500]
                    )
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"Error processing result {idx}: {e}")
                    continue
        
        logger.info(f"Returning {len(results)} search results")
        
        return SearchResponse(
            results=results,
            query=request.query,
            total_results=len(results)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

