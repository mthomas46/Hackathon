"""
RAG (Retrieval Augmented Generation) services.

Provides intelligent question answering with LLM-based synthesis.
Includes multi-pass query processing for complex queries.
Includes context-aware RAG for hierarchical filtering (Week 3).
Includes accuracy-enhanced RAG with Phase 1 improvements (hybrid search, query rewriting, confidence scoring).
"""

from .rag_service import RAGService, get_rag_service
from .multi_pass_query import MultiPassQueryService, get_multi_pass_service
from .context_aware_rag import ContextAwareRAG, get_context_aware_rag
from .temporal_rag_service import TemporalRAGService
from .accuracy_enhanced_rag import AccuracyEnhancedRAG, get_enhanced_rag_service
from .hybrid_search import HybridSearchService, get_hybrid_search_service
from .bm25_search import BM25SearchService, get_bm25_service
from .query_rewriter import QueryRewriter, get_query_rewriter
from .confidence_scorer import ConfidenceScorer, get_confidence_scorer
from .reranker import RerankerService, get_reranker_service
from .context_optimizer import ContextOptimizer, get_context_optimizer
from .metadata_filter import MetadataFilter, get_metadata_filter

__all__ = [
    "RAGService",
    "get_rag_service",
    "MultiPassQueryService",
    "get_multi_pass_service",
    "ContextAwareRAG",
    "get_context_aware_rag",
    "TemporalRAGService",
    # Phase 1 Accuracy Enhancements
    "AccuracyEnhancedRAG",
    "get_enhanced_rag_service",
    "HybridSearchService",
    "get_hybrid_search_service",
    "BM25SearchService",
    "get_bm25_service",
    "QueryRewriter",
    "get_query_rewriter",
    "ConfidenceScorer",
    "get_confidence_scorer",
    # Phase 2 Accuracy Enhancements
    "RerankerService",
    "get_reranker_service",
    "ContextOptimizer",
    "get_context_optimizer",
    "MetadataFilter",
    "get_metadata_filter"
]

