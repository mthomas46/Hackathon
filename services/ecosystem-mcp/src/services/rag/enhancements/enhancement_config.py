"""
Enhancement Configuration

Defines configuration options for the enhancement pipeline with presets
optimized for different RAG query types.
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class EnhancementConfig:
    """
    Configuration for RAG enhancement pipeline.
    
    Controls which enhancements are enabled and their parameters.
    Includes presets optimized for different query scenarios.
    """
    
    # ===== Phase 1: Core Enhancements =====
    enable_hybrid_search: bool = True
    enable_query_rewriting: bool = True
    enable_confidence_scoring: bool = True
    semantic_weight: float = 0.7
    keyword_weight: float = 0.3
    
    # ===== Phase 2: Advanced Enhancements =====
    enable_reranking: bool = False
    enable_context_optimization: bool = False
    enable_metadata_filtering: bool = False
    quality_threshold: Optional[float] = None
    context_strategy: str = "balanced"  # quality_first, relevance_first, balanced
    
    # ===== Phase 5R: Query Intelligence =====
    enable_intent_classification: bool = True
    enable_llm_intent: bool = False  # Opt-in (slower but more accurate)
    
    # ===== Phase 7R: Advanced Features =====
    enable_contradiction_detection: bool = True
    enable_difficulty_estimation: bool = True
    
    # ===== Audit Phase 2: Performance =====
    use_unified_analyzer: bool = True  # Combined difficulty + intent analysis
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "EnhancementConfig":
        """Create from dictionary."""
        return cls(**config_dict)
    
    # ===== Configuration Presets =====
    
    @classmethod
    def default(cls) -> "EnhancementConfig":
        """
        Balanced defaults for general-purpose RAG queries.
        
        Good balance of quality and speed.
        Recommended for most queries.
        """
        return cls(
            # Phase 1: Core features enabled
            enable_hybrid_search=True,
            enable_query_rewriting=True,
            enable_confidence_scoring=True,
            semantic_weight=0.7,
            keyword_weight=0.3,
            
            # Phase 2: Context optimization only
            enable_reranking=False,  # Off by default (expensive)
            enable_context_optimization=True,
            enable_metadata_filtering=True,
            quality_threshold=None,  # No hard threshold
            context_strategy="balanced",
            
            # Phase 5R: Fast intent classification
            enable_intent_classification=True,
            enable_llm_intent=False,
            
            # Phase 7R: All enabled
            enable_contradiction_detection=True,
            enable_difficulty_estimation=True,
            
            # Audit: Unified analyzer
            use_unified_analyzer=True
        )
    
    @classmethod
    def temporal_default(cls) -> "EnhancementConfig":
        """
        Optimized for temporal RAG queries.
        
        Temporal filtering is the primary mechanism,
        so some enhancements are adjusted:
        - Skip intent classification (temporal queries are explicit)
        - Skip difficulty estimation (not needed)
        - Enable hybrid search (better coverage)
        - Enable query rewriting (expand date references)
        """
        return cls(
            # Phase 1: Core features
            enable_hybrid_search=True,
            enable_query_rewriting=True,
            enable_confidence_scoring=True,
            semantic_weight=0.7,
            keyword_weight=0.3,
            
            # Phase 2: Skip reranking (temporal filter is primary)
            enable_reranking=False,
            enable_context_optimization=True,
            enable_metadata_filtering=True,
            quality_threshold=None,
            context_strategy="balanced",
            
            # Phase 5R: Skip (temporal queries explicit)
            enable_intent_classification=False,
            enable_llm_intent=False,
            
            # Phase 7R: Skip difficulty (not needed for temporal)
            enable_contradiction_detection=True,
            enable_difficulty_estimation=False,
            
            # Audit: Skip unified (not needed)
            use_unified_analyzer=False
        )
    
    @classmethod
    def context_aware_default(cls) -> "EnhancementConfig":
        """
        Optimized for context-aware RAG queries.
        
        Context filtering is the primary mechanism,
        so metadata filtering is disabled.
        Reranking is beneficial for hierarchical filtering.
        """
        return cls(
            # Phase 1: All core features
            enable_hybrid_search=True,
            enable_query_rewriting=True,
            enable_confidence_scoring=True,
            semantic_weight=0.7,
            keyword_weight=0.3,
            
            # Phase 2: Enable reranking (good for hierarchical filtering)
            enable_reranking=True,
            enable_context_optimization=True,
            enable_metadata_filtering=False,  # Context filters are primary
            quality_threshold=None,
            context_strategy="relevance_first",  # Context already filtered
            
            # Phase 5R: All enabled
            enable_intent_classification=True,
            enable_llm_intent=False,
            
            # Phase 7R: All enabled
            enable_contradiction_detection=True,
            enable_difficulty_estimation=True,
            
            # Audit: Unified analyzer
            use_unified_analyzer=True
        )
    
    @classmethod
    def multipass_default(cls) -> "EnhancementConfig":
        """
        Optimized for multi-pass RAG queries (N×M calls).
        
        Disables expensive features to keep N×M queries reasonable:
        - Skip query rewriting (questions already specific)
        - Skip reranking (too expensive for N×M)
        - Skip contradiction detection (too expensive)
        - Enable hybrid search (better per-question coverage)
        - Enable context optimization (token management critical)
        """
        return cls(
            # Phase 1: Hybrid + confidence only
            enable_hybrid_search=True,
            enable_query_rewriting=False,  # Questions already specific
            enable_confidence_scoring=True,  # Track per-question
            semantic_weight=0.7,
            keyword_weight=0.3,
            
            # Phase 2: Context opt + metadata filter only
            enable_reranking=False,  # Too expensive for N×M
            enable_context_optimization=True,  # Token management critical
            enable_metadata_filtering=True,  # Quality filter
            quality_threshold=None,
            context_strategy="quality_first",  # Best docs only
            
            # Phase 5R: Skip (questions pre-analyzed)
            enable_intent_classification=False,
            enable_llm_intent=False,
            
            # Phase 7R: Skip expensive features
            enable_contradiction_detection=False,  # Too expensive
            enable_difficulty_estimation=False,  # Questions pre-validated
            
            # Audit: Skip (not needed)
            use_unified_analyzer=False
        )
    
    @classmethod
    def fast(cls) -> "EnhancementConfig":
        """
        Fast configuration for latency-sensitive queries.
        
        Minimizes processing time by enabling only core features:
        - Hybrid search (essential)
        - Skip everything else
        
        Use when speed is critical and quality can be lower.
        """
        return cls(
            # Phase 1: Hybrid only
            enable_hybrid_search=True,
            enable_query_rewriting=False,
            enable_confidence_scoring=False,
            semantic_weight=0.7,
            keyword_weight=0.3,
            
            # Phase 2: All disabled
            enable_reranking=False,
            enable_context_optimization=False,
            enable_metadata_filtering=False,
            quality_threshold=None,
            context_strategy="balanced",
            
            # Phase 5R: All disabled
            enable_intent_classification=False,
            enable_llm_intent=False,
            
            # Phase 7R: All disabled
            enable_contradiction_detection=False,
            enable_difficulty_estimation=False,
            
            # Audit: Disabled
            use_unified_analyzer=False
        )
    
    @classmethod
    def max_quality(cls) -> "EnhancementConfig":
        """
        Maximum quality configuration (slow but best results).
        
        Enables ALL enhancements including expensive ones:
        - Reranking enabled
        - LLM intent classification enabled
        - High quality threshold
        - All detection features enabled
        
        Use when answer quality is critical and speed is not a concern.
        """
        return cls(
            # Phase 1: All enabled
            enable_hybrid_search=True,
            enable_query_rewriting=True,
            enable_confidence_scoring=True,
            semantic_weight=0.7,
            keyword_weight=0.3,
            
            # Phase 2: All enabled with high quality
            enable_reranking=True,  # ✅ Enable
            enable_context_optimization=True,
            enable_metadata_filtering=True,
            quality_threshold=60.0,  # High quality only
            context_strategy="balanced",
            
            # Phase 5R: All enabled including LLM
            enable_intent_classification=True,
            enable_llm_intent=True,  # ✅ Use LLM for best intent
            
            # Phase 7R: All enabled
            enable_contradiction_detection=True,
            enable_difficulty_estimation=True,
            
            # Audit: Unified analyzer
            use_unified_analyzer=True
        )
    
    @classmethod
    def minimal(cls) -> "EnhancementConfig":
        """
        Minimal enhancements (nearly same as standard RAG).
        
        Only enables hybrid search to improve retrieval.
        Everything else disabled.
        
        Use for testing or when standard RAG behavior is desired
        but with better document retrieval.
        """
        return cls(
            # Phase 1: Hybrid only
            enable_hybrid_search=True,
            enable_query_rewriting=False,
            enable_confidence_scoring=False,
            semantic_weight=0.7,
            keyword_weight=0.3,
            
            # Phase 2: All disabled
            enable_reranking=False,
            enable_context_optimization=False,
            enable_metadata_filtering=False,
            quality_threshold=None,
            context_strategy="balanced",
            
            # Phase 5R: All disabled
            enable_intent_classification=False,
            enable_llm_intent=False,
            
            # Phase 7R: All disabled
            enable_contradiction_detection=False,
            enable_difficulty_estimation=False,
            
            # Audit: Disabled
            use_unified_analyzer=False
        )

