"""
RAG (Retrieval Augmented Generation) services.

Provides intelligent question answering with LLM-based synthesis.
Includes multi-pass query processing for complex queries.
Includes context-aware RAG for hierarchical filtering (Week 3).
"""

from .rag_service import RAGService, get_rag_service
from .multi_pass_query import MultiPassQueryService, get_multi_pass_service
from .context_aware_rag import ContextAwareRAG, get_context_aware_rag
from .temporal_rag_service import TemporalRAGService

__all__ = [
    "RAGService",
    "get_rag_service",
    "MultiPassQueryService",
    "get_multi_pass_service",
    "ContextAwareRAG",
    "get_context_aware_rag",
    "TemporalRAGService"
]

