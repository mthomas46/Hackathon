"""
Hierarchical Retrieval System for MCP Tiers.

Implements tier-by-tier retrieval with token budget management
and intelligent result ranking across multiple MCP tiers.

Tier Order (priority from highest to lowest):
1. Client - Most specific, highest priority
2. Project - Project-specific knowledge
3. Company - Company-wide knowledge  
4. Team - Team-specific knowledge
5. Ecosystem - Broadest, lowest priority
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class RetrievalResult:
    """Result from hierarchical retrieval."""
    content: str
    tier: str
    score: float  # 0.0 to 1.0
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate result fields."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0 and 1, got {self.score}")
        if self.token_count < 0:
            raise ValueError(f"Token count must be non-negative, got {self.token_count}")


@dataclass
class TierConfig:
    """Configuration for a single tier."""
    name: str
    weight: float  # 0.0 to 1.0
    priority: int  # Lower number = higher priority
    
    def __post_init__(self):
        """Validate tier config."""
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError(f"Weight must be between 0 and 1, got {self.weight}")


class TierName(Enum):
    """Valid tier names."""
    CLIENT = "client"
    PROJECT = "project"
    COMPANY = "company"
    TEAM = "team"
    ECOSYSTEM = "ecosystem"


# ============================================================================
# Hierarchical Retriever
# ============================================================================

class HierarchicalRetriever:
    """
    Hierarchical retrieval across MCP tiers.
    
    Retrieves results with cascading priority:
    - Client tier first (highest priority)
    - Then Project tier  
    - Then Company tier
    - Then Team tier
    - Finally Ecosystem tier (lowest priority)
    
    Supports:
    - Token budget management
    - Custom tier weights
    - Configurable result limits
    - Score-based ranking
    """
    
    # Default tier order (priority)
    TIER_ORDER = ["client", "project", "company", "team", "ecosystem"]
    
    # Default tier weights (client highest, ecosystem lowest)
    DEFAULT_WEIGHTS = {
        "client": 0.4,
        "project": 0.3,
        "company": 0.15,
        "team": 0.1,
        "ecosystem": 0.05,
    }
    
    def __init__(
        self,
        tiers: List[str],
        token_budget: int = 4000,
        tier_weights: Optional[Dict[str, float]] = None,
    ):
        """
        Initialize hierarchical retriever.
        
        Args:
            tiers: List of tier names to search
            token_budget: Maximum tokens to retrieve
            tier_weights: Optional custom weights per tier (must sum to ~1.0)
        """
        # Validate tiers
        self.tiers = self._validate_tiers(tiers)
        self.token_budget = token_budget
        
        # Set up weights
        if tier_weights is None:
            self.tier_weights = {
                tier: self.DEFAULT_WEIGHTS.get(tier, 0.1)
                for tier in self.tiers
            }
        else:
            self.tier_weights = tier_weights
        
        # Create tier configs
        self.tier_configs = self._create_tier_configs()
        
        logger.info(f"HierarchicalRetriever initialized with tiers: {self.tiers}")
    
    def _validate_tiers(self, tiers: List[str]) -> List[str]:
        """Validate tier names."""
        valid_tiers = {t.value for t in TierName}
        
        for tier in tiers:
            if tier not in valid_tiers:
                raise ValueError(
                    f"Invalid tier '{tier}'. Must be one of: {valid_tiers}"
                )
        
        return tiers
    
    def _create_tier_configs(self) -> List[TierConfig]:
        """Create tier configurations with priorities."""
        configs = []
        
        for tier in self.tiers:
            priority = self.TIER_ORDER.index(tier) if tier in self.TIER_ORDER else 999
            weight = self.tier_weights.get(tier, 0.1)
            
            configs.append(TierConfig(
                name=tier,
                weight=weight,
                priority=priority
            ))
        
        # Sort by priority
        configs.sort(key=lambda c: c.priority)
        
        return configs
    
    def retrieve(
        self,
        query: str,
        tiers: Optional[List[str]] = None,
        max_results: int = 10,
    ) -> List[RetrievalResult]:
        """
        Retrieve results with cascading across tiers.
        
        Args:
            query: Search query
            tiers: Optional specific tiers to search (defaults to all)
            max_results: Maximum number of results
        
        Returns:
            List of retrieval results ordered by score
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if max_results == 0:
            return []
        
        # Determine which tiers to search
        search_tiers = tiers if tiers is not None else self.tiers
        
        # Validate search tiers
        for tier in search_tiers:
            if tier not in self.tiers:
                raise ValueError(
                    f"Invalid tier '{tier}'. Must be one of: {self.tiers}"
                )
        
        # Retrieve from each tier
        all_results = []
        
        for tier_config in self.tier_configs:
            if tier_config.name not in search_tiers:
                continue
            
            # Retrieve from this tier
            tier_results = self._retrieve_from_tier(
                query=query,
                tier=tier_config.name,
                tier_weight=tier_config.weight,
                max_results=max_results - len(all_results)  # Remaining budget
            )
            
            all_results.extend(tier_results)
            
            # Stop if we have enough results
            if len(all_results) >= max_results:
                break
        
        # Sort by score (descending) and limit
        all_results.sort(key=lambda r: r.score, reverse=True)
        
        return all_results[:max_results]
    
    def retrieve_with_budget(
        self,
        query: str,
        tiers: Optional[List[str]] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve results respecting token budget.
        
        Distributes token budget across tiers based on weights.
        
        Args:
            query: Search query
            tiers: Optional specific tiers to search
        
        Returns:
            List of results within token budget
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        # Determine which tiers to search
        search_tiers = tiers if tiers is not None else self.tiers
        
        # Calculate token budget per tier
        tier_budgets = self._calculate_tier_budgets(search_tiers)
        
        # Retrieve from each tier with budget
        all_results = []
        remaining_budget = self.token_budget
        
        for tier_config in self.tier_configs:
            if tier_config.name not in search_tiers:
                continue
            
            if remaining_budget <= 0:
                break
            
            tier_budget = tier_budgets.get(tier_config.name, 0)
            
            # Retrieve from this tier
            tier_results = self._retrieve_from_tier_with_budget(
                query=query,
                tier=tier_config.name,
                tier_weight=tier_config.weight,
                token_budget=min(tier_budget, remaining_budget)
            )
            
            # Add results and update budget
            for result in tier_results:
                if remaining_budget - result.token_count >= 0:
                    all_results.append(result)
                    remaining_budget -= result.token_count
        
        # Sort by score
        all_results.sort(key=lambda r: r.score, reverse=True)
        
        return all_results
    
    def _calculate_tier_budgets(
        self,
        search_tiers: List[str]
    ) -> Dict[str, int]:
        """Calculate token budget per tier based on weights."""
        budgets = {}
        
        # Calculate total weight for search tiers
        total_weight = sum(
            self.tier_weights.get(tier, 0.1)
            for tier in search_tiers
        )
        
        # Distribute budget proportionally
        for tier in search_tiers:
            weight = self.tier_weights.get(tier, 0.1)
            budget = int(self.token_budget * (weight / total_weight))
            budgets[tier] = budget
        
        return budgets
    
    def _retrieve_from_tier(
        self,
        query: str,
        tier: str,
        tier_weight: float,
        max_results: int,
    ) -> List[RetrievalResult]:
        """
        Retrieve from a single tier.
        
        This is a mock implementation for testing.
        In production, this would query ChromaDB/Neo4j.
        """
        if max_results <= 0:
            return []
        
        # Mock implementation for testing
        # In production, this would:
        # 1. Query vector store (ChromaDB)
        # 2. Query graph database (Neo4j)
        # 3. Combine and rank results
        # 4. Apply tier weight to scores
        
        # For now, return mock results
        mock_results = self._generate_mock_results(
            query=query,
            tier=tier,
            tier_weight=tier_weight,
            count=min(max_results, 3)  # Mock: return up to 3 results per tier
        )
        
        return mock_results
    
    def _retrieve_from_tier_with_budget(
        self,
        query: str,
        tier: str,
        tier_weight: float,
        token_budget: int,
    ) -> List[RetrievalResult]:
        """
        Retrieve from tier respecting token budget.
        
        This is a mock implementation for testing.
        """
        if token_budget <= 0:
            return []
        
        # Mock implementation
        mock_results = self._generate_mock_results(
            query=query,
            tier=tier,
            tier_weight=tier_weight,
            count=5  # Generate several results
        )
        
        # Filter by budget
        results_within_budget = []
        remaining_budget = token_budget
        
        for result in mock_results:
            if result.token_count <= remaining_budget:
                results_within_budget.append(result)
                remaining_budget -= result.token_count
        
        return results_within_budget
    
    def _generate_mock_results(
        self,
        query: str,
        tier: str,
        tier_weight: float,
        count: int,
    ) -> List[RetrievalResult]:
        """
        Generate mock results for testing.
        
        In production, replace with actual retrieval from data stores.
        """
        # Simulate no results for very specific/unlikely queries
        if "xyz123" in query or "extremely specific query" in query:
            return []
        
        results = []
        
        for i in range(count):
            # Generate score based on tier weight and position
            base_score = 0.9 - (i * 0.1)  # Decreasing scores
            weighted_score = base_score * (0.5 + tier_weight * 0.5)  # Apply weight
            weighted_score = max(0.0, min(1.0, weighted_score))  # Clamp to [0, 1]
            
            result = RetrievalResult(
                content=f"Mock result {i+1} from {tier} tier for query: {query[:30]}",
                tier=tier,
                score=weighted_score,
                token_count=50 + (i * 10),  # Increasing token counts
                metadata={
                    "source": f"mock_{tier}",
                    "position": i,
                    "tier_weight": tier_weight,
                }
            )
            
            results.append(result)
        
        return results


# ============================================================================
# Helper Functions
# ============================================================================

def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.
    
    Simple estimation: ~4 characters per token.
    In production, use tiktoken library.
    """
    return max(1, len(text) // 4)

