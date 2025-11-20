"""
Enhanced Query Endpoints with Multiple Modes and Tier Selection.

Provides three query modes:
1. RAG (Full): Retrieval + Augmentation + Generation
2. Contextual: Simple document context + LLM
3. Basic: Pure LLM query without documents

Plus manual tier selection with automatic fallback.
"""

import logging
from typing import Optional, Literal
from enum import Enum

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...services.rag import get_rag_service
from ...services.rag.enhanced_rag_service import get_enhanced_rag_service
from ...services.models.ollama_router import get_ollama_router, LLMInstance
from ...services.embeddings.embedding_service import get_embedding_service
from ...storage.chromadb_client import get_chroma_client
from ...utils.cache_decorator import cache

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryMode(str, Enum):
    """Query processing modes."""
    RAG = "rag"  # Full RAG: Retrieval + Augmentation + Generation
    CONTEXTUAL = "contextual"  # Simple context + LLM
    BASIC = "basic"  # Pure LLM, no documents


class TierPreference(str, Enum):
    """LLM tier preferences."""
    AUTO = "auto"  # Automatic based on complexity
    CURSOR = "cursor"  # Force Cursor IDE (Tier 1)
    DESKTOP = "desktop"  # Force Desktop Ollama (Tier 2)
    DOCKER = "docker"  # Force Docker Ollama (Tier 3)


class EnhancedQueryRequest(BaseModel):
    """Enhanced query request with mode and tier selection."""
    question: str = Field(
        ...,
        description="Question to answer",
        min_length=3,
        max_length=1000
    )
    mode: QueryMode = Field(
        default=QueryMode.RAG,
        description="Query mode: 'rag' (full), 'contextual' (simple), or 'basic' (LLM only)"
    )
    tier: TierPreference = Field(
        default=TierPreference.AUTO,
        description="LLM tier: 'auto', 'cursor', 'desktop', or 'docker'"
    )
    use_enhancements: bool = Field(
        default=True,  # ✨ PHASE 8: Changed from False to True
        description="Use enhanced RAG with optional config (glossary, exclusions, multi-signal ranking)"
    )
    context_id: Optional[str] = Field(
        default=None,
        description="[PHASE 9] Repository context ID for filtered queries (optional)"
    )
    service_name: Optional[str] = Field(
        default=None,
        description="Service name for filtering documents (e.g., 'adminservice', 'ecosystem-mcp')"
    )
    n_results: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of documents to retrieve (for rag/contextual modes)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="LLM temperature"
    )
    response_length: Optional[int] = Field(
        default=1000,
        ge=100,
        le=4000,
        description="Max tokens in response (affects answer length)"
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Max retry attempts if tier unavailable"
    )


class EnhancedQueryResponse(BaseModel):
    """Enhanced query response."""
    answer: str
    mode: str
    tier_used: str
    tier_requested: str
    sources: list = []
    metadata: dict


@router.post(
    "/query/enhanced",
    response_model=EnhancedQueryResponse,
    summary="Enhanced query with mode and tier selection",
    description="Query with full control over processing mode and LLM tier"
)
async def enhanced_query(request: EnhancedQueryRequest):
    """
    Enhanced query endpoint with multiple modes and tier selection.
    
    **Query Modes:**
    - `rag`: Full RAG (Retrieval + Augmentation + Generation)
    - `contextual`: Simple document context + LLM generation
    - `basic`: Pure LLM query without documents
    
    **Tier Selection:**
    - `auto`: Automatic based on query complexity (default)
    - `cursor`: Prefer Cursor IDE (Claude 4.5 Sonnet)
    - `desktop`: Prefer Desktop Ollama (GPU)
    - `docker`: Use Docker Ollama (CPU)
    
    **Retry Logic:**
    If requested tier is unavailable, automatically falls back to next available tier.
    
    Example:
    ```json
    {
        "question": "How does caching work?",
        "mode": "rag",
        "tier": "desktop",
        "n_results": 10,
        "max_retries": 2
    }
    ```
    """
    try:
        logger.info(
            f"Enhanced query: mode={request.mode}, tier={request.tier}, "
            f"question='{request.question[:50]}...'"
        )
        
        # Process based on mode
        if request.mode == QueryMode.RAG:
            result = await _process_rag_query(request)
        elif request.mode == QueryMode.CONTEXTUAL:
            result = await _process_contextual_query(request)
        else:  # BASIC
            result = await _process_basic_query(request)
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


async def _process_rag_query(request: EnhancedQueryRequest) -> EnhancedQueryResponse:
    """
    Process full RAG query (Retrieval + Augmentation + Generation).
    
    This is the most comprehensive mode:
    1. Retrieval: Semantic search for relevant documents
    2. Augmentation: Build context from retrieved documents
    3. Generation: LLM synthesizes answer from context
    
    Supports optional enhancements (glossary, exclusions, multi-signal ranking).
    """
    # Early return for empty database
    try:
        chroma_client = get_chroma_client()
        collection = chroma_client.get_or_create_collection("documents")
        doc_count = collection.count()
        
        if doc_count == 0:
            logger.warning("RAG query attempted with empty database")
            return EnhancedQueryResponse(
                answer="⚠️ No documents found in the database. Please ingest documents before running RAG queries. You can use 'basic' mode for pure LLM queries without documents.",
                mode="rag",
                tier_used="none",
                tier_requested=request.tier.value,
                sources=[],
                metadata={
                    "error": "empty_database",
                    "message": "No documents available for retrieval",
                    "suggestion": "Run document ingestion first or use 'basic' mode",
                    "document_count": 0
                }
            )
    except Exception as e:
        logger.error(f"Error checking document count: {e}")
        # Continue anyway, let the query fail naturally if there's an issue
    
    # Choose service based on use_enhancements flag
    if request.use_enhancements:
        rag_service = get_enhanced_rag_service()
        logger.info("Using EnhancedRAGService")
    else:
        rag_service = get_rag_service()
        logger.info("Using standard RAGService")
    
    # Execute RAG with tier preference
    result = await rag_service.ask(
        question=request.question,
        n_results=request.n_results,
        temperature=request.temperature,
        response_length=request.response_length,
        service_name=request.service_name  # Pass service filter to RAG
    )
    
    # Handle None result (RAG service error)
    if result is None:
        logger.error("RAG service returned None")
        raise HTTPException(
            status_code=500,
            detail="RAG service failed to process query"
        )
    
    # Validate result structure
    if not isinstance(result, dict) or "answer" not in result:
        logger.error(f"RAG service returned invalid result: {result}")
        raise HTTPException(
            status_code=500,
            detail="RAG service returned invalid response format"
        )
    
    # Get tier information
    tier_used = await _get_tier_used(request.tier, request.question)
    
    return EnhancedQueryResponse(
        answer=result["answer"],
        mode="rag",
        tier_used=tier_used,
        tier_requested=request.tier.value,
        sources=result.get("sources", []),
        metadata={
            **result.get("metadata", {}),
            "confidence": result.get("confidence", 0.0),
            "documents_used": len(result.get("sources", []))
        }
    )


async def _process_contextual_query(request: EnhancedQueryRequest) -> EnhancedQueryResponse:
    """
    Process contextual query (simple document context + LLM).
    
    Simpler than full RAG:
    1. Retrieves relevant documents
    2. Creates simple context
    3. LLM generates answer (less sophisticated prompt)
    
    Faster and uses less tokens than full RAG.
    """
    # Get documents
    embedding_service = get_embedding_service()
    chroma = get_chroma_client()
    
    # Generate embedding
    embedding_result = await embedding_service.generate_embedding(request.question)
    query_embedding = embedding_result["embedding"]
    
    # Search ChromaDB
    results = await chroma.query(
        query_embeddings=[query_embedding],
        n_results=request.n_results
    )
    
    if not results or "documents" not in results or not results["documents"][0]:
        # No documents found - fall back to basic LLM
        logger.warning("No documents found for contextual query, falling back to basic mode")
        request.mode = QueryMode.BASIC
        return await _process_basic_query(request)
    
    # Build simple context
    documents = results["documents"][0][:5]  # Use top 5
    context = "\n\n".join([f"Document {i+1}:\n{doc}" for i, doc in enumerate(documents)])
    
    # Generate answer with tier preference
    ollama_router = get_ollama_router()
    tier_client, tier_used = await _get_tier_client(request.tier, request.question, request.max_retries)
    
    prompt = f"""Based on the following documents, answer the question.

Documents:
{context}

Question: {request.question}

Answer:"""
    
    response = await ollama_router.generate(
        prompt=prompt,
        temperature=request.temperature,
        workload_type='generation'
    )
    
    # Extract sources
    sources = [
        {
            "id": i+1,
            "content_preview": doc[:200] + "..." if len(doc) > 200 else doc
        }
        for i, doc in enumerate(documents)
    ]
    
    return EnhancedQueryResponse(
        answer=response.get("response", response.get("text", "")),
        mode="contextual",
        tier_used=tier_used,
        tier_requested=request.tier.value,
        sources=sources,
        metadata={
            "documents_used": len(documents),
            "model": response.get("model", "unknown")
        }
    )


async def _process_basic_query(request: EnhancedQueryRequest) -> EnhancedQueryResponse:
    """
    Process basic LLM query (no documents).
    
    Pure LLM generation without any document context.
    Fastest mode, but answer quality depends entirely on LLM's knowledge.
    """
    # Get tier client with fallback
    tier_client, tier_used = await _get_tier_client(request.tier, request.question, request.max_retries)
    
    # Generate answer using ollama router
    ollama_router = get_ollama_router()
    
    response = await ollama_router.generate(
        prompt=request.question,
        temperature=request.temperature,
        workload_type='generation'
    )
    
    return EnhancedQueryResponse(
        answer=response.get("response", response.get("text", "")),
        mode="basic",
        tier_used=tier_used,
        tier_requested=request.tier.value,
        sources=[],
        metadata={
            "model": response.get("model", "unknown"),
            "note": "Basic mode - answer from LLM knowledge only, no documents consulted"
        }
    )


async def _get_tier_client(
    tier_pref: TierPreference,
    question: str,
    max_retries: int
) -> tuple[any, str]:
    """
    Get LLM client for specified tier with automatic fallback.
    
    Args:
        tier_pref: Preferred tier
        question: Question (for complexity analysis if auto)
        max_retries: Max retry attempts
    
    Returns:
        Tuple of (client, tier_name)
    """
    ollama_router = get_ollama_router()
    
    if tier_pref == TierPreference.AUTO:
        # Use complexity-based routing
        from ...services.models.complexity_analyzer import get_complexity_analyzer
        analyzer = get_complexity_analyzer()
        complexity = analyzer.analyze(question)  # Fixed: analyze() not analyze_complexity(), and it's not async
        
        instance, model, tier_name = await ollama_router.get_instance_for_complexity(
            complexity_score=complexity,
            prompt=question
        )
        return instance, tier_name
    
    # Manual tier selection with fallback
    tier_attempts = []
    
    if tier_pref == TierPreference.CURSOR:
        tier_attempts = [
            (LLMInstance.CURSOR, "cursor"),
            (LLMInstance.DESKTOP, "desktop"),
            (LLMInstance.DOCKER, "docker")
        ]
    elif tier_pref == TierPreference.DESKTOP:
        tier_attempts = [
            (LLMInstance.DESKTOP, "desktop"),
            (LLMInstance.DOCKER, "docker")
        ]
    else:  # DOCKER
        tier_attempts = [(LLMInstance.DOCKER, "docker")]
    
    # Try tiers in order
    for attempt, (instance_type, tier_name) in enumerate(tier_attempts):
        if attempt >= max_retries + 1:
            break
        
        try:
            # Check availability
            if instance_type == LLMInstance.CURSOR:
                if ollama_router.cursor_client:
                    available = await ollama_router._check_cursor_availability()
                    if available:
                        logger.info(f"✅ Using Cursor IDE (Tier 1)")
                        return ollama_router.cursor_client, "cursor"
                    logger.warning(f"❌ Cursor IDE unavailable, trying next tier")
            
            elif instance_type == LLMInstance.DESKTOP:
                if ollama_router.desktop_client:
                    available = await ollama_router._check_desktop_availability()
                    if available:
                        logger.info(f"✅ Using Desktop Ollama (Tier 2)")
                        return ollama_router.desktop_client, "desktop"
                    logger.warning(f"❌ Desktop Ollama unavailable, trying next tier")
            
            else:  # DOCKER
                logger.info(f"✅ Using Docker Ollama (Tier 3)")
                return ollama_router.docker_client, "docker"
        
        except Exception as e:
            logger.warning(f"Tier {tier_name} check failed: {e}, trying next tier")
            continue
    
    # Fallback to Docker (always available)
    logger.info("🔄 All preferred tiers unavailable, falling back to Docker Ollama")
    return ollama_router.docker_client, "docker (fallback)"


async def _get_tier_used(tier_pref: TierPreference, question: str) -> str:
    """Get which tier was actually used."""
    _, tier_used = await _get_tier_client(tier_pref, question, max_retries=2)
    return tier_used


@router.get(
    "/query/modes",
    summary="List available query modes",
    description="Get information about available query modes"
)
async def list_query_modes():
    """List available query modes and their descriptions."""
    return {
        "modes": {
            "rag": {
                "name": "Full RAG",
                "description": "Retrieval + Augmentation + Generation",
                "features": [
                    "Semantic search for relevant documents",
                    "Context building from retrieved documents",
                    "LLM synthesis with sophisticated prompting",
                    "Source citations",
                    "Confidence scoring"
                ],
                "best_for": "Complex questions requiring accurate, cited answers",
                "speed": "Slower (3-10s)",
                "quality": "Highest"
            },
            "contextual": {
                "name": "Contextual Search",
                "description": "Simple document context + LLM generation",
                "features": [
                    "Document retrieval",
                    "Simple context creation",
                    "Basic LLM generation"
                ],
                "best_for": "Quick answers with document context",
                "speed": "Medium (1-3s)",
                "quality": "Medium"
            },
            "basic": {
                "name": "Basic LLM Query",
                "description": "Pure LLM without documents",
                "features": [
                    "Direct LLM query",
                    "No document retrieval",
                    "Fastest response"
                ],
                "best_for": "General questions, brainstorming, quick queries",
                "speed": "Fast (<1s)",
                "quality": "Depends on LLM knowledge"
            }
        },
        "tiers": {
            "auto": "Automatic tier selection based on complexity",
            "cursor": "Cursor IDE (Claude 4.5 Sonnet) - Highest quality",
            "desktop": "Desktop Ollama (GPU) - Good performance",
            "docker": "Docker Ollama (CPU) - Always available"
        }
    }


@router.get(
    "/query/tier-status",
    summary="Check tier availability",
    description="Check which LLM tiers are currently available"
)
async def check_tier_status():
    """Check availability of all LLM tiers."""
    ollama_router = get_ollama_router()
    
    # Check each tier
    cursor_available = False
    desktop_available = False
    docker_available = True  # Always available
    
    if ollama_router.cursor_client:
        cursor_available = await ollama_router._check_cursor_availability()
    
    if ollama_router.desktop_client:
        desktop_available = await ollama_router._check_desktop_availability()
    
    return {
        "tiers": {
            "cursor": {
                "tier": 1,
                "name": "Cursor MCP Integration",
                "available": cursor_available,
                "model": "Claude 4.5 Sonnet (via Cursor)",
                "use_case": "Configured" if cursor_available else "Not configured (enable in .env)"
            },
            "desktop": {
                "tier": 2,
                "name": "Desktop Ollama",
                "available": desktop_available,
                "model": "llama3:latest (GPU)",
                "use_case": "Heavy workloads (GPU accelerated)"
            },
            "docker": {
                "tier": 3,
                "name": "Docker Ollama",
                "available": docker_available,
                "model": "llama3.2:3b (CPU)",
                "use_case": "Simple queries (always available)"
            }
        },
        "recommendation": "cursor" if cursor_available else "desktop" if desktop_available else "docker"
    }

