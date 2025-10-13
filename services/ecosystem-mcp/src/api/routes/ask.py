"""
RAG (Ask) endpoint for intelligent question answering.

Provides LLM-powered answers with source citation.
"""

import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...services.rag import get_rag_service
from ...utils.validation import sanitize_html
from ...utils.cache_decorator import cache
from ...config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class ConversationTurn(BaseModel):
    """Single turn in conversation history."""
    question: str
    answer: str


class AskRequest(BaseModel):
    """Request for RAG question answering."""
    question: str = Field(
        ...,
        description="Question to answer",
        min_length=3,
        max_length=500
    )
    n_results: int = Field(
        default=10,
        ge=1,
        le=25,
        description="Number of documents to retrieve"
    )
    prefer_recent: bool = Field(
        default=True,
        description="Boost recent documents in scoring"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="LLM temperature (0=deterministic, 1=creative)"
    )
    context: Optional[List[ConversationTurn]] = Field(
        default=None,
        description="Previous conversation for follow-up questions"
    )


class Source(BaseModel):
    """Source citation."""
    id: int
    file_path: str
    relevance_score: float
    adjusted_score: float
    recency_days: Optional[int]
    updated_at: Optional[str]


class AskResponse(BaseModel):
    """Response from RAG system."""
    answer: str = Field(description="Generated answer")
    sources: List[Source] = Field(description="Source citations")
    confidence: float = Field(description="Confidence score (0.0-1.0)")
    metadata: Dict[str, Any] = Field(description="Additional metadata")
    request_id: str


def _make_rag_cache_key(request_data: AskRequest, request: Request) -> str:
    """Generate cache key based only on query parameters, not request object."""
    import json
    import hashlib
    
    key_data = {
        "question": request_data.question,
        "n_results": request_data.n_results,
        "prefer_recent": request_data.prefer_recent,
        "temperature": request_data.temperature,
        # Don't include context for now - would reduce cache hit rate
    }
    serialized = json.dumps(key_data, sort_keys=True)
    key_hash = hashlib.md5(serialized.encode()).hexdigest()[:12]
    return key_hash


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask a question (RAG)",
    description="Answer questions using retrieval-augmented generation with intelligent synthesis"
)
@cache(ttl=3600, key_prefix="rag", key_fn=_make_rag_cache_key)  # ⚡ Cache RAG responses for 1 hour
async def ask_question(request_data: AskRequest, request: Request):
    """
    Answer a question using RAG (Retrieval Augmented Generation).
    
    This endpoint:
    1. Searches for relevant documents using semantic similarity
    2. Adjusts scores based on recency and version matching
    3. Generates an intelligent answer using LLM
    4. Returns answer with source citations
    
    Features:
    - Version-aware scoring (boosts matching versions)
    - Recency-aware scoring (boosts recent documents)
    - Conversational context support
    - Confidence scoring
    - Source citation
    
    Args:
        request_data: Question and parameters
        request: FastAPI request object
    
    Returns:
        Generated answer with sources and metadata
    
    Example:
        ```json
        {
            "question": "What is ecosystem-mcp and what does it do?",
            "n_results": 10,
            "prefer_recent": true,
            "temperature": 0.7
        }
        ```
    
    Response:
        ```json
        {
            "answer": "Ecosystem-MCP is a microservices...",
            "sources": [
                {"id": 1, "file_path": "...", "relevance_score": 0.85}
            ],
            "confidence": 0.92,
            "metadata": {...}
        }
        ```
    """
    # Rate limiting would go here if configured in settings
    # Currently not enabled - would need to add rate_limit_enabled and rag_rate_limit to Settings
    
    try:
        # Sanitize input
        question = sanitize_html(request_data.question)
        
        # Convert conversation context to dict format
        context = None
        if request_data.context:
            context = [
                {"question": turn.question, "answer": turn.answer}
                for turn in request_data.context
            ]
        
        # Get RAG service
        rag_service = get_rag_service()
        
        # Generate answer
        result = await rag_service.ask(
            question=question,
            n_results=request_data.n_results,
            context=context,
            prefer_recent=request_data.prefer_recent,
            temperature=request_data.temperature
        )
        
        # Format response
        response = AskResponse(
            answer=result["answer"],
            sources=[Source(**s) for s in result["sources"]],
            confidence=result["confidence"],
            metadata=result["metadata"],
            request_id=request.state.request_id if hasattr(request.state, "request_id") else "unknown"
        )
        
        logger.info(
            f"RAG answer generated: {len(result['answer'])} chars, "
            f"{len(result['sources'])} sources, "
            f"confidence={result['confidence']}"
        )
        
        return response
    
    except Exception as e:
        logger.error(f"Ask endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}"
        )


@router.get(
    "/ask/info",
    summary="RAG endpoint information",
    description="Get information about the RAG (Ask) endpoint capabilities"
)
async def rag_info():
    """
    Get information about RAG capabilities.
    
    Returns:
        Information about the RAG system
    """
    return {
        "name": "RAG Question Answering",
        "description": "Intelligent question answering with retrieval-augmented generation",
        "features": [
            "Semantic search with ChromaDB + Ollama embeddings",
            "Version-aware scoring (boosts matching versions)",
            "Recency-aware scoring (boosts recent documents)",
            "LLM-based answer synthesis via Ollama",
            "Source citation and confidence scoring",
            "Conversational context support",
            "Adjustable temperature for creativity"
        ],
        "models": {
            "embedding": "nomic-embed-text",
            "generation": "llama3 (or configured model)"
        },
        "scoring_factors": {
            "semantic_similarity": "Base score from vector similarity",
            "recency_boost": "0-15% boost for recent documents (0-90 days)",
            "version_match": "10% boost for matching version numbers"
        },
        "rate_limit": "20 requests per minute",
        "max_question_length": 500,
        "max_context_turns": 3
    }

