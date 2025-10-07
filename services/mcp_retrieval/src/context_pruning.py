"""
Context Pruning System for Token Budget Management.

Implements intelligent context pruning with multiple strategies:
- Relevance: Keep most relevant items
- Recency: Keep most recent items
- Hybrid: Balance relevance and recency
- Importance: Keep most important items
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class PruningStrategy(Enum):
    """Pruning strategy options."""
    RELEVANCE = "relevance"
    RECENCY = "recency"
    HYBRID = "hybrid"
    IMPORTANCE = "importance"


@dataclass
class ContextItem:
    """A single context item to be pruned."""
    content: str
    timestamp: datetime
    relevance_score: float  # 0.0 to 1.0
    importance_score: float  # 0.0 to 1.0
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate context item fields."""
        if not 0.0 <= self.relevance_score <= 1.0:
            raise ValueError(f"Relevance score must be between 0 and 1, got {self.relevance_score}")
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError(f"Importance score must be between 0 and 1, got {self.importance_score}")
        if self.token_count < 0:
            raise ValueError(f"Token count must be non-negative, got {self.token_count}")


@dataclass
class PrunedContext:
    """Result of context pruning."""
    items: List[ContextItem]
    token_count: int
    pruning_ratio: float  # Ratio of kept tokens to original tokens
    strategy: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# Context Pruner
# ============================================================================

class ContextPruner:
    """
    Intelligent context pruning with multiple strategies.
    
    Supports four pruning strategies:
    1. RELEVANCE - Keep most relevant items
    2. RECENCY - Keep most recent items
    3. HYBRID - Balance relevance and recency (50/50 weighted)
    4. IMPORTANCE - Keep most important items
    
    All strategies respect strict token budgets.
    """
    
    def __init__(self, strategy: PruningStrategy = PruningStrategy.HYBRID):
        """
        Initialize context pruner.
        
        Args:
            strategy: Pruning strategy to use
        """
        if not isinstance(strategy, PruningStrategy):
            raise ValueError(f"Invalid strategy. Must be PruningStrategy enum, got {strategy}")
        
        self.strategy = strategy
        logger.info(f"ContextPruner initialized with strategy: {strategy.value}")
    
    def set_strategy(self, strategy: PruningStrategy):
        """
        Change pruning strategy.
        
        Args:
            strategy: New pruning strategy
        """
        if not isinstance(strategy, PruningStrategy):
            raise ValueError(f"Invalid strategy. Must be PruningStrategy enum, got {strategy}")
        
        self.strategy = strategy
        logger.info(f"Strategy changed to: {strategy.value}")
    
    def prune(
        self,
        items: List[ContextItem],
        target_tokens: int,
        query: Optional[str] = None,
    ) -> PrunedContext:
        """
        Prune context items to fit within token budget.
        
        Args:
            items: Context items to prune
            target_tokens: Target token budget
            query: Optional query for relevance calculation
        
        Returns:
            Pruned context within token budget
        """
        if target_tokens < 0:
            raise ValueError(f"Target tokens must be non-negative, got {target_tokens}")
        
        if not items:
            return PrunedContext(
                items=[],
                token_count=0,
                pruning_ratio=0.0,
                strategy=self.strategy.value,
                metadata={}
            )
        
        if target_tokens == 0:
            return PrunedContext(
                items=[],
                token_count=0,
                pruning_ratio=0.0,
                strategy=self.strategy.value,
                metadata={"reason": "zero_budget"}
            )
        
        # Calculate original token count
        original_token_count = sum(item.token_count for item in items)
        
        # Apply pruning strategy
        if self.strategy == PruningStrategy.RELEVANCE:
            pruned_items = self._prune_by_relevance(items, target_tokens)
        elif self.strategy == PruningStrategy.RECENCY:
            pruned_items = self._prune_by_recency(items, target_tokens)
        elif self.strategy == PruningStrategy.HYBRID:
            pruned_items = self._prune_hybrid(items, target_tokens, query)
        elif self.strategy == PruningStrategy.IMPORTANCE:
            pruned_items = self._prune_by_importance(items, target_tokens)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
        
        # Calculate final metrics
        final_token_count = sum(item.token_count for item in pruned_items)
        pruning_ratio = final_token_count / original_token_count if original_token_count > 0 else 0.0
        
        return PrunedContext(
            items=pruned_items,
            token_count=final_token_count,
            pruning_ratio=pruning_ratio,
            strategy=self.strategy.value,
            metadata={
                "original_item_count": len(items),
                "pruned_item_count": len(pruned_items),
                "original_token_count": original_token_count,
                "items_removed": len(items) - len(pruned_items),
            }
        )
    
    def _prune_by_relevance(
        self,
        items: List[ContextItem],
        target_tokens: int
    ) -> List[ContextItem]:
        """
        Prune by relevance score (keep highest relevance).
        
        Args:
            items: Context items
            target_tokens: Target token budget
        
        Returns:
            Pruned items ordered by relevance (descending)
        """
        # Sort by relevance (descending)
        sorted_items = sorted(items, key=lambda x: x.relevance_score, reverse=True)
        
        # Select items within budget
        selected_items = []
        current_tokens = 0
        
        for item in sorted_items:
            if current_tokens + item.token_count <= target_tokens:
                selected_items.append(item)
                current_tokens += item.token_count
        
        return selected_items
    
    def _prune_by_recency(
        self,
        items: List[ContextItem],
        target_tokens: int
    ) -> List[ContextItem]:
        """
        Prune by recency (keep most recent).
        
        Args:
            items: Context items
            target_tokens: Target token budget
        
        Returns:
            Pruned items ordered by timestamp (most recent first)
        """
        # Sort by timestamp (most recent first)
        sorted_items = sorted(items, key=lambda x: x.timestamp, reverse=True)
        
        # Select items within budget
        selected_items = []
        current_tokens = 0
        
        for item in sorted_items:
            if current_tokens + item.token_count <= target_tokens:
                selected_items.append(item)
                current_tokens += item.token_count
        
        return selected_items
    
    def _prune_by_importance(
        self,
        items: List[ContextItem],
        target_tokens: int
    ) -> List[ContextItem]:
        """
        Prune by importance score (keep highest importance).
        
        Args:
            items: Context items
            target_tokens: Target token budget
        
        Returns:
            Pruned items ordered by importance (descending)
        """
        # Sort by importance (descending)
        sorted_items = sorted(items, key=lambda x: x.importance_score, reverse=True)
        
        # Select items within budget
        selected_items = []
        current_tokens = 0
        
        for item in sorted_items:
            if current_tokens + item.token_count <= target_tokens:
                selected_items.append(item)
                current_tokens += item.token_count
        
        return selected_items
    
    def _prune_hybrid(
        self,
        items: List[ContextItem],
        target_tokens: int,
        query: Optional[str] = None
    ) -> List[ContextItem]:
        """
        Prune using hybrid strategy (balance relevance and recency).
        
        Combines relevance and recency scores with 50/50 weighting.
        
        Args:
            items: Context items
            target_tokens: Target token budget
            query: Optional query for relevance boost
        
        Returns:
            Pruned items ordered by combined score (descending)
        """
        # Calculate combined scores
        scored_items = []
        
        # Normalize recency scores (more recent = higher score)
        if items:
            timestamps = [item.timestamp for item in items]
            min_time = min(timestamps)
            max_time = max(timestamps)
            time_range = (max_time - min_time).total_seconds()
            
            for item in items:
                # Recency score: 0.0 (oldest) to 1.0 (most recent)
                if time_range > 0:
                    recency_score = (item.timestamp - min_time).total_seconds() / time_range
                else:
                    recency_score = 1.0  # All same time
                
                # Combined score: 50% relevance + 50% recency
                combined_score = (item.relevance_score * 0.5) + (recency_score * 0.5)
                
                scored_items.append((item, combined_score))
        
        # Sort by combined score (descending)
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        # Select items within budget
        selected_items = []
        current_tokens = 0
        
        for item, score in scored_items:
            if current_tokens + item.token_count <= target_tokens:
                selected_items.append(item)
                current_tokens += item.token_count
        
        return selected_items


# ============================================================================
# Helper Functions
# ============================================================================

def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    
    Simple estimation: ~4 characters per token.
    In production, use tiktoken library.
    
    Args:
        text: Text to estimate tokens for
    
    Returns:
        Estimated token count
    """
    return max(1, len(text) // 4)


def create_context_item(
    content: str,
    timestamp: Optional[datetime] = None,
    relevance_score: float = 0.5,
    importance_score: float = 0.5,
    metadata: Optional[Dict[str, Any]] = None
) -> ContextItem:
    """
    Helper to create a context item with automatic token counting.
    
    Args:
        content: Content string
        timestamp: Item timestamp (defaults to now)
        relevance_score: Relevance score 0-1
        importance_score: Importance score 0-1
        metadata: Additional metadata
    
    Returns:
        ContextItem instance
    """
    return ContextItem(
        content=content,
        timestamp=timestamp or datetime.now(),
        relevance_score=relevance_score,
        importance_score=importance_score,
        token_count=estimate_tokens(content),
        metadata=metadata or {}
    )

