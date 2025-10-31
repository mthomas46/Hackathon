"""
Query Context

Holds enriched query state throughout the enhancement pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class QueryContext:
    """
    Enriched query context maintained throughout enhancement pipeline.
    
    Holds all query-related state and metadata collected during processing.
    Passed through all pipeline stages to maintain context.
    """
    
    # Original query
    original_query: str
    
    # Rewritten query (if query rewriting enabled)
    rewritten_query: Optional[str] = None
    
    # Query variants (for parallel search)
    query_variants: List[str] = field(default_factory=list)
    
    # Query intent (if intent classification enabled)
    intent: Optional[Dict[str, Any]] = None
    
    # Query difficulty (if difficulty estimation enabled)
    difficulty: Optional[Dict[str, Any]] = None
    
    # Adaptive parameters (from intent/difficulty)
    adaptive_n_results: Optional[int] = None
    adaptive_strategy: Optional[str] = None
    adaptive_enable_reranking: Optional[bool] = None
    
    # Metadata filters (built from config + hooks)
    metadata_filters: Dict[str, Any] = field(default_factory=dict)
    
    # Custom data (for RAG type-specific state)
    custom_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "original_query": self.original_query,
            "rewritten_query": self.rewritten_query,
            "query_variants": self.query_variants,
            "intent": self.intent,
            "difficulty": self.difficulty,
            "adaptive_n_results": self.adaptive_n_results,
            "adaptive_strategy": self.adaptive_strategy,
            "adaptive_enable_reranking": self.adaptive_enable_reranking,
            "metadata_filters": self.metadata_filters,
            "custom_data": self.custom_data
        }
    
    def get_primary_query(self) -> str:
        """Get the primary query to use (rewritten if available, else original)."""
        return self.rewritten_query or self.original_query
    
    def get_n_results(self, default: int) -> int:
        """Get adaptive n_results if set, else default."""
        return self.adaptive_n_results if self.adaptive_n_results is not None else default
    
    def get_strategy(self, default: str) -> str:
        """Get adaptive strategy if set, else default."""
        return self.adaptive_strategy or default
    
    def should_enable_reranking(self, default: bool) -> bool:
        """Get adaptive reranking if set, else default."""
        return self.adaptive_enable_reranking if self.adaptive_enable_reranking is not None else default

