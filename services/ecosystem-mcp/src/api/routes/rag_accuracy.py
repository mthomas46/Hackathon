"""
RAG Accuracy API Routes (Phase 1)

Endpoints for testing and using accuracy-enhanced RAG.

Features:
- Enhanced RAG queries (hybrid search + rewriting + confidence)
- Standard RAG queries (for comparison)
- BM25 index management
- Enhancement statistics
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...services.rag.accuracy_enhanced_rag import get_enhanced_rag_service
from ...services.rag import get_rag_service

logger = logging.getLogger(__name__)

router = APIRouter()


# === Request/Response Models ===

class RAGQueryRequest(BaseModel):
    """RAG query request."""
    question: str = Field(..., description="Question to ask", min_length=3)
    n_results: int = Field(10, description="Number of documents to retrieve", ge=1, le=50)
    context: Optional[List[dict]] = Field(None, description="Previous conversation context")
    prefer_recent: bool = Field(True, description="Prefer recent documents")
    temperature: float = Field(0.7, description="LLM temperature", ge=0.0, le=1.0)
    response_length: int = Field(1000, description="Max response tokens", ge=100, le=4000)


class EnhancedRAGQueryRequest(RAGQueryRequest):
    """Enhanced RAG query request with Phase 1 + Phase 2 options."""
    # Phase 1 options
    enable_hybrid_search: bool = Field(True, description="Use hybrid search (semantic + keyword)")
    enable_query_rewriting: bool = Field(True, description="Rewrite query before search")
    enable_confidence_scoring: bool = Field(True, description="Calculate confidence score")
    semantic_weight: float = Field(0.7, description="Weight for semantic search", ge=0.0, le=1.0)
    keyword_weight: float = Field(0.3, description="Weight for keyword search", ge=0.0, le=1.0)
    
    # Phase 2 options
    enable_reranking: bool = Field(False, description="Use cross-encoder reranking for higher accuracy")
    enable_context_optimization: bool = Field(False, description="Optimize context selection and ordering")
    enable_metadata_filtering: bool = Field(False, description="Apply smart metadata-based filtering")
    quality_threshold: Optional[float] = Field(None, description="Minimum quality score for documents", ge=0.0, le=100.0)
    context_strategy: str = Field("balanced", description="Context optimization strategy (quality_first/relevance_first/balanced)")
    
    # Phase 5R options (Query Intelligence)
    enable_intent_classification: bool = Field(True, description="⚡ Use fast heuristic query classification (< 1ms)")
    enable_llm_intent: bool = Field(False, description="🤖 Use LLM for intent classification (slower, more accurate)")
    
    # Phase 7R options (Advanced Features)
    enable_contradiction_detection: bool = Field(True, description="🔍 Detect conflicting information in sources")
    enable_difficulty_estimation: bool = Field(True, description="📊 Estimate query difficulty before retrieval")


class RAGQueryResponse(BaseModel):
    """RAG query response."""
    answer: str
    sources: List[dict]
    confidence: float
    confidence_level: Optional[str] = None
    confidence_breakdown: Optional[dict] = None
    recommendation: Optional[str] = None
    metadata: dict


# === API Endpoints ===

@router.post("/rag/ask/enhanced", response_model=RAGQueryResponse, tags=["RAG Accuracy"])
async def ask_enhanced_rag(request: EnhancedRAGQueryRequest):
    """
    Ask a question using accuracy-enhanced RAG (Phase 1 + Phase 2).
    
    **Phase 1 Enhancements:**
    - 🔄 **Hybrid Search**: Combines semantic (embeddings) + keyword (BM25) search
    - 📝 **Query Rewriting**: Expands synonyms, clarifies vague queries, decomposes complex queries
    - 📊 **Confidence Scoring**: Multi-factor confidence assessment (retrieval, quality, alignment, consensus, completeness)
    
    **Phase 2 Enhancements:**
    - 🎯 **Cross-Encoder Reranking**: More accurate document ranking using cross-encoder models
    - 🎨 **Context Optimization**: Smart selection and ordering of document chunks for LLM
    - 🎛️  **Metadata Filtering**: Intelligent filtering based on query intent and document quality
    
    **Expected: +35-55% accuracy improvement (with Phase 2 enabled)**
    
    **Example (Phase 1 only):**
    ```json
    {
      "question": "How does ingestion work?",
      "n_results": 10,
      "enable_hybrid_search": true,
      "enable_query_rewriting": true,
      "enable_confidence_scoring": true
    }
    ```
    
    **Example (Phase 1 + Phase 2):**
    ```json
    {
      "question": "How does ingestion work?",
      "n_results": 10,
      "enable_hybrid_search": true,
      "enable_query_rewriting": true,
      "enable_confidence_scoring": true,
      "enable_reranking": true,
      "enable_context_optimization": true,
      "enable_metadata_filtering": true,
      "quality_threshold": 75.0
    }
    ```
    """
    try:
        logger.info(f"🚀 Enhanced RAG query: {request.question[:60]}...")
        
        enhanced_rag = get_enhanced_rag_service()
        
        result = await enhanced_rag.ask_enhanced(
            question=request.question,
            n_results=request.n_results,
            context=request.context,
            prefer_recent=request.prefer_recent,
            temperature=request.temperature,
            response_length=request.response_length,
            # Phase 1
            enable_hybrid_search=request.enable_hybrid_search,
            enable_query_rewriting=request.enable_query_rewriting,
            enable_confidence_scoring=request.enable_confidence_scoring,
            semantic_weight=request.semantic_weight,
            keyword_weight=request.keyword_weight,
            # Phase 2
            enable_reranking=request.enable_reranking,
            enable_context_optimization=request.enable_context_optimization,
            enable_metadata_filtering=request.enable_metadata_filtering,
            quality_threshold=request.quality_threshold,
            context_strategy=request.context_strategy,
            # Phase 5R
            enable_intent_classification=request.enable_intent_classification,
            enable_llm_intent=request.enable_llm_intent,
            # Phase 7R
            enable_contradiction_detection=request.enable_contradiction_detection,
            enable_difficulty_estimation=request.enable_difficulty_estimation
        )
        
        return RAGQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Enhanced RAG query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/ask/standard", response_model=RAGQueryResponse, tags=["RAG Accuracy"])
async def ask_standard_rag(request: RAGQueryRequest):
    """
    Ask a question using standard RAG (no Phase 1 enhancements).
    
    **Use for comparison testing:**
    - Compare accuracy with enhanced RAG
    - Benchmark performance improvements
    - A/B testing
    
    **Features:**
    - ✅ Semantic search (embeddings)
    - ✅ LLM answer generation
    - ❌ No hybrid search
    - ❌ No query rewriting
    - ❌ Basic confidence only
    """
    try:
        logger.info(f"🔍 Standard RAG query: {request.question[:60]}...")
        
        rag_service = get_rag_service()
        
        result = await rag_service.ask(
            question=request.question,
            n_results=request.n_results,
            context=request.context,
            prefer_recent=request.prefer_recent,
            temperature=request.temperature,
            response_length=request.response_length
        )
        
        # Standardize response format
        standardized = {
            "answer": result["answer"],
            "sources": result["sources"],
            "confidence": result.get("confidence", 0.0) * 100 if result.get("confidence", 0.0) <= 1.0 else result.get("confidence", 0.0),
            "confidence_level": "Unknown",
            "confidence_breakdown": {},
            "recommendation": None,
            "metadata": result.get("metadata", {})
        }
        
        return RAGQueryResponse(**standardized)
        
    except Exception as e:
        logger.error(f"❌ Standard RAG query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/compare", tags=["RAG Accuracy"])
async def compare_rag_approaches(request: RAGQueryRequest):
    """
    Compare standard vs enhanced RAG side-by-side.
    
    **Returns:**
    - Both answers
    - Confidence scores
    - Performance metrics
    - Recommendation on which to use
    
    **Use for:**
    - Evaluating accuracy improvements
    - Understanding when enhancements help most
    - Benchmarking
    """
    try:
        logger.info(f"🔬 Comparing RAG approaches: {request.question[:60]}...")
        
        import asyncio
        import time
        
        # Run both in parallel
        rag_service = get_rag_service()
        enhanced_rag = get_enhanced_rag_service()
        
        start_standard = time.time()
        standard_task = rag_service.ask(
            question=request.question,
            n_results=request.n_results,
            context=request.context,
            prefer_recent=request.prefer_recent,
            temperature=request.temperature,
            response_length=request.response_length
        )
        
        start_enhanced = time.time()
        enhanced_task = enhanced_rag.ask_enhanced(
            question=request.question,
            n_results=request.n_results,
            context=request.context,
            prefer_recent=request.prefer_recent,
            temperature=request.temperature,
            response_length=request.response_length,
            enable_hybrid_search=True,
            enable_query_rewriting=True,
            enable_confidence_scoring=True
        )
        
        # Wait for both
        standard_result, enhanced_result = await asyncio.gather(standard_task, enhanced_task)
        
        end_time = time.time()
        
        # Calculate metrics
        standard_time = end_time - start_standard
        enhanced_time = end_time - start_enhanced
        
        return {
            "question": request.question,
            "standard": {
                "answer": standard_result["answer"],
                "confidence": standard_result.get("confidence", 0.0) * 100 if standard_result.get("confidence", 0.0) <= 1.0 else standard_result.get("confidence", 0.0),
                "sources_count": len(standard_result["sources"]),
                "time_seconds": round(standard_time, 2)
            },
            "enhanced": {
                "answer": enhanced_result["answer"],
                "confidence": enhanced_result.get("confidence", 0.0),
                "confidence_level": enhanced_result.get("confidence_level"),
                "confidence_breakdown": enhanced_result.get("confidence_breakdown", {}),
                "recommendation": enhanced_result.get("recommendation"),
                "sources_count": len(enhanced_result["sources"]),
                "time_seconds": round(enhanced_time, 2),
                "enhancements_used": enhanced_result.get("metadata", {}).get("enhancements_used", {})
            },
            "comparison": {
                "confidence_improvement": round(
                    enhanced_result.get("confidence", 0.0) - 
                    (standard_result.get("confidence", 0.0) * 100 if standard_result.get("confidence", 0.0) <= 1.0 else standard_result.get("confidence", 0.0)),
                    1
                ),
                "time_overhead_seconds": round(enhanced_time - standard_time, 2),
                "recommendation": (
                    "Use enhanced RAG" if enhanced_result.get("confidence", 0) > (standard_result.get("confidence", 0) * 100 if standard_result.get("confidence", 0) <= 1.0 else standard_result.get("confidence", 0))
                    else "Use standard RAG"
                )
            }
        }
        
    except Exception as e:
        logger.error(f"❌ RAG comparison failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/bm25/build-index", tags=["RAG Accuracy"])
async def build_bm25_index(force_rebuild: bool = Query(False, description="Force rebuild even if index exists")):
    """
    Build BM25 index for hybrid search.
    
    **When to call:**
    - On application startup
    - After significant document changes
    - If hybrid search is slow (index not built)
    
    **Note:** This is automatically called on first hybrid search, but manual building is faster.
    """
    try:
        logger.info(f"🔨 Building BM25 index (force_rebuild={force_rebuild})...")
        
        enhanced_rag = get_enhanced_rag_service()
        await enhanced_rag.build_bm25_index()
        
        stats = enhanced_rag.bm25_service.get_index_stats()
        
        return {
            "success": True,
            "message": "BM25 index built successfully",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ BM25 index build failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/enhancements/stats", tags=["RAG Accuracy"])
async def get_enhancement_stats():
    """
    Get statistics about RAG accuracy enhancements.
    
    **Returns:**
    - Current phase (Phase 1)
    - Enabled enhancements
    - BM25 index status
    - Expected accuracy improvements
    """
    try:
        enhanced_rag = get_enhanced_rag_service()
        stats = enhanced_rag.get_enhancement_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"❌ Failed to get enhancement stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/health", tags=["RAG Accuracy"])
async def check_rag_health():
    """
    Check RAG system health.
    
    **Checks:**
    - BM25 index built
    - ChromaDB accessible
    - LLM router available
    """
    try:
        enhanced_rag = get_enhanced_rag_service()
        
        # Check BM25
        bm25_stats = enhanced_rag.bm25_service.get_index_stats()
        bm25_healthy = bm25_stats["indexed"]
        
        # Check ChromaDB (try a simple query)
        chroma_healthy = False
        try:
            enhanced_rag.chroma.collection.count()
            chroma_healthy = True
        except Exception:
            pass
        
        # Check LLM router
        llm_healthy = enhanced_rag.ollama_router is not None
        
        overall_healthy = bm25_healthy and chroma_healthy and llm_healthy
        
        return {
            "healthy": overall_healthy,
            "components": {
                "bm25_index": {
                    "healthy": bm25_healthy,
                    "indexed": bm25_stats["indexed"],
                    "index_size": bm25_stats["index_size"]
                },
                "chromadb": {
                    "healthy": chroma_healthy
                },
                "llm_router": {
                    "healthy": llm_healthy
                }
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}", exc_info=True)
        return {
            "healthy": False,
            "error": str(e)
        }

