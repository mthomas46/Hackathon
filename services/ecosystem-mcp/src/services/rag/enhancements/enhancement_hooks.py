"""
Enhancement Hooks

Defines hooks for customizing enhancement pipeline behavior.
Allows different RAG types to inject custom logic at key points.
"""

from dataclasses import dataclass
from typing import Optional, Callable, Awaitable, List, Dict, Any


@dataclass
class EnhancementHooks:
    """
    Hooks for customizing enhancement pipeline behavior.
    
    Allows RAG types to inject custom logic at specific points:
    1. Pre-retrieval: Build custom filters (temporal, context, etc.)
    2. Custom retrieval: Replace default retrieval entirely
    3. Post-retrieval: Process documents after retrieval
    4. Custom generation: Replace default answer generation
    
    Example (Temporal RAG):
        hooks = EnhancementHooks(
            pre_retrieval_filter=lambda ctx: {
                "git_date": {"$lte": as_of_date.timestamp()}
            },
            retrieval_fn=custom_temporal_retrieval
        )
    """
    
    # Pre-retrieval: Build custom filters
    # Input: QueryContext
    # Output: Dict of filters to merge with metadata filters
    pre_retrieval_filter: Optional[Callable[
        [Any],  # QueryContext
        Awaitable[Dict[str, Any]]
    ]] = None
    
    # Custom retrieval: Replace default retrieval
    # Input: QueryContext, filters dict, n_results
    # Output: List of documents
    retrieval_fn: Optional[Callable[
        [Any, Dict[str, Any], int],  # QueryContext, filters, n_results
        Awaitable[List[Dict[str, Any]]]
    ]] = None
    
    # Post-retrieval: Custom document processing
    # Input: Documents, QueryContext
    # Output: Processed documents
    post_retrieval_processor: Optional[Callable[
        [List[Dict[str, Any]], Any],  # documents, QueryContext
        Awaitable[List[Dict[str, Any]]]
    ]] = None
    
    # Custom generation: Replace default answer generation
    # Input: Query, documents, QueryContext
    # Output: Generated answer string
    generation_fn: Optional[Callable[
        [str, List[Dict[str, Any]], Any],  # query, documents, QueryContext
        Awaitable[str]
    ]] = None
    
    def has_custom_retrieval(self) -> bool:
        """Check if custom retrieval is defined."""
        return self.retrieval_fn is not None
    
    def has_custom_generation(self) -> bool:
        """Check if custom generation is defined."""
        return self.generation_fn is not None
    
    def has_pre_retrieval_filter(self) -> bool:
        """Check if pre-retrieval filter is defined."""
        return self.pre_retrieval_filter is not None
    
    def has_post_retrieval_processor(self) -> bool:
        """Check if post-retrieval processor is defined."""
        return self.post_retrieval_processor is not None

