"""
Progressive Context Refinement for 5-Tier Hierarchical System.

Progressively refines context by traversing tiers:
1. Start with Client tier (most specific)
2. Add Project context (relevant to task)
3. Add Company context (org policies)
4. Add Team context (team practices)
5. Add Ecosystem context (industry best practices)
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from .tier_manager import TierManager, TierType, QueryResult

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class RefinementStrategy(Enum):
    """Strategy for progressive refinement."""
    BOTTOM_UP = "bottom_up"  # Start from client, move up
    TOP_DOWN = "top_down"    # Start from ecosystem, move down
    BALANCED = "balanced"     # Balance between specific and general


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class RefinementConfig:
    """Configuration for progressive refinement."""
    strategy: RefinementStrategy = RefinementStrategy.BOTTOM_UP
    max_tiers: int = 5
    token_budget: int = 8000
    tier_weights: Dict[TierType, float] = field(default_factory=dict)
    min_relevance: float = 0.3
    
    def __post_init__(self):
        """Initialize default tier weights if not provided."""
        if not self.tier_weights:
            self.tier_weights = {
                TierType.CLIENT: 0.4,
                TierType.PROJECT: 0.3,
                TierType.COMPANY: 0.15,
                TierType.TEAM: 0.1,
                TierType.ECOSYSTEM: 0.05,
            }


@dataclass
class RefinedContext:
    """Result of progressive context refinement."""
    query: str
    strategy: RefinementStrategy
    tiers_used: List[TierType]
    total_tokens: int
    results_by_tier: Dict[TierType, List[QueryResult]]
    refinement_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_all_results(self) -> List[QueryResult]:
        """Get all results across all tiers."""
        all_results = []
        for results in self.results_by_tier.values():
            all_results.extend(results)
        return all_results
    
    def get_tier_summary(self) -> Dict[str, Any]:
        """Get summary of results by tier."""
        return {
            tier_type.value: {
                "count": len(results),
                "tokens": sum(r.token_count for r in results),
                "avg_relevance": sum(r.relevance for r in results) / len(results) if results else 0
            }
            for tier_type, results in self.results_by_tier.items()
        }


# ============================================================================
# Progressive Refiner
# ============================================================================

class ProgressiveRefiner:
    """
    Progressive context refinement across tiers.
    
    Refines context by intelligently combining knowledge from multiple
    tiers, starting with most specific (client) and progressively adding
    broader context (project, company, team, ecosystem).
    """
    
    def __init__(self, tier_manager: TierManager):
        """
        Initialize progressive refiner.
        
        Args:
            tier_manager: TierManager instance
        """
        self.tier_manager = tier_manager
        logger.info("ProgressiveRefiner initialized")
    
    def refine_context(
        self,
        query: str,
        starting_tier_id: str,
        config: Optional[RefinementConfig] = None
    ) -> RefinedContext:
        """
        Refine context progressively across tiers.
        
        Args:
            query: Query to refine context for
            starting_tier_id: Starting tier ID
            config: Refinement configuration
        
        Returns:
            RefinedContext with results from all tiers
        """
        if config is None:
            config = RefinementConfig()
        
        # Get starting tier
        starting_tier = self.tier_manager.get_tier(starting_tier_id)
        if not starting_tier:
            raise ValueError(f"Tier not found: {starting_tier_id}")
        
        # Execute refinement based on strategy
        if config.strategy == RefinementStrategy.BOTTOM_UP:
            return self._refine_bottom_up(query, starting_tier_id, config)
        elif config.strategy == RefinementStrategy.TOP_DOWN:
            return self._refine_top_down(query, starting_tier_id, config)
        else:  # BALANCED
            return self._refine_balanced(query, starting_tier_id, config)
    
    def _refine_bottom_up(
        self,
        query: str,
        starting_tier_id: str,
        config: RefinementConfig
    ) -> RefinedContext:
        """
        Bottom-up refinement: Start specific, add general context.
        
        Strategy:
        1. Start with client tier (most specific)
        2. If more context needed, add project tier
        3. Continue up hierarchy as needed
        4. Prioritize specific over general
        """
        results_by_tier: Dict[TierType, List[QueryResult]] = {}
        tiers_used: List[TierType] = []
        total_tokens = 0
        
        # Start from current tier and move up
        current_tier_id = starting_tier_id
        tiers_searched = 0
        
        while current_tier_id and tiers_searched < config.max_tiers:
            tier = self.tier_manager.get_tier(current_tier_id)
            if not tier:
                break
            
            # Calculate token budget for this tier
            tier_weight = config.tier_weights.get(tier.tier_type, 0.1)
            tier_budget = int(config.token_budget * tier_weight)
            remaining_budget = config.token_budget - total_tokens
            tier_budget = min(tier_budget, remaining_budget)
            
            if tier_budget <= 0:
                break
            
            # Query this tier
            tier_results = self._query_tier(
                tier_id=current_tier_id,
                query=query,
                max_tokens=tier_budget,
                min_relevance=config.min_relevance
            )
            
            if tier_results:
                results_by_tier[tier.tier_type] = tier_results
                tiers_used.append(tier.tier_type)
                total_tokens += sum(r.token_count for r in tier_results)
            
            # Move to parent tier
            current_tier_id = tier.parent_tier_id
            tiers_searched += 1
        
        # Calculate refinement score
        refinement_score = self._calculate_refinement_score(results_by_tier, config)
        
        return RefinedContext(
            query=query,
            strategy=RefinementStrategy.BOTTOM_UP,
            tiers_used=tiers_used,
            total_tokens=total_tokens,
            results_by_tier=results_by_tier,
            refinement_score=refinement_score,
            metadata={"tiers_searched": tiers_searched}
        )
    
    def _refine_top_down(
        self,
        query: str,
        starting_tier_id: str,
        config: RefinementConfig
    ) -> RefinedContext:
        """
        Top-down refinement: Start general, add specific context.
        
        Strategy:
        1. Start with ecosystem tier (most general)
        2. Add company-specific context
        3. Add team/project context
        4. Add client-specific details
        5. Prioritize general principles first
        """
        results_by_tier: Dict[TierType, List[QueryResult]] = {}
        tiers_used: List[TierType] = []
        total_tokens = 0
        
        # Build path from starting tier to root
        tier_path = self._build_tier_path_to_root(starting_tier_id)
        tier_path.reverse()  # Start from root (ecosystem)
        
        for tier_id in tier_path:
            if total_tokens >= config.token_budget:
                break
            
            tier = self.tier_manager.get_tier(tier_id)
            if not tier:
                continue
            
            # Calculate token budget for this tier
            tier_weight = config.tier_weights.get(tier.tier_type, 0.1)
            tier_budget = int(config.token_budget * tier_weight)
            remaining_budget = config.token_budget - total_tokens
            tier_budget = min(tier_budget, remaining_budget)
            
            if tier_budget <= 0:
                break
            
            # Query this tier
            tier_results = self._query_tier(
                tier_id=tier_id,
                query=query,
                max_tokens=tier_budget,
                min_relevance=config.min_relevance
            )
            
            if tier_results:
                results_by_tier[tier.tier_type] = tier_results
                tiers_used.append(tier.tier_type)
                total_tokens += sum(r.token_count for r in tier_results)
        
        # Calculate refinement score
        refinement_score = self._calculate_refinement_score(results_by_tier, config)
        
        return RefinedContext(
            query=query,
            strategy=RefinementStrategy.TOP_DOWN,
            tiers_used=tiers_used,
            total_tokens=total_tokens,
            results_by_tier=results_by_tier,
            refinement_score=refinement_score
        )
    
    def _refine_balanced(
        self,
        query: str,
        starting_tier_id: str,
        config: RefinementConfig
    ) -> RefinedContext:
        """
        Balanced refinement: Combine specific and general context.
        
        Strategy:
        1. Start with starting tier
        2. Alternate between moving up and down
        3. Balance specific details with general principles
        """
        results_by_tier: Dict[TierType, List[QueryResult]] = {}
        tiers_used: List[TierType] = []
        total_tokens = 0
        
        # Get all tiers in path
        tier_path = self._build_tier_path_to_root(starting_tier_id)
        
        # Start from middle and alternate
        current_index = 0
        visited = set()
        
        while current_index < len(tier_path) and total_tokens < config.token_budget:
            tier_id = tier_path[current_index]
            if tier_id in visited:
                current_index += 1
                continue
            
            visited.add(tier_id)
            tier = self.tier_manager.get_tier(tier_id)
            if not tier:
                current_index += 1
                continue
            
            # Calculate token budget for this tier
            tier_weight = config.tier_weights.get(tier.tier_type, 0.1)
            tier_budget = int(config.token_budget * tier_weight)
            remaining_budget = config.token_budget - total_tokens
            tier_budget = min(tier_budget, remaining_budget)
            
            if tier_budget > 0:
                # Query this tier
                tier_results = self._query_tier(
                    tier_id=tier_id,
                    query=query,
                    max_tokens=tier_budget,
                    min_relevance=config.min_relevance
                )
                
                if tier_results:
                    results_by_tier[tier.tier_type] = tier_results
                    tiers_used.append(tier.tier_type)
                    total_tokens += sum(r.token_count for r in tier_results)
            
            current_index += 1
        
        # Calculate refinement score
        refinement_score = self._calculate_refinement_score(results_by_tier, config)
        
        return RefinedContext(
            query=query,
            strategy=RefinementStrategy.BALANCED,
            tiers_used=tiers_used,
            total_tokens=total_tokens,
            results_by_tier=results_by_tier,
            refinement_score=refinement_score
        )
    
    def _query_tier(
        self,
        tier_id: str,
        query: str,
        max_tokens: int,
        min_relevance: float
    ) -> List[QueryResult]:
        """Query a specific tier."""
        # Get tier knowledge
        knowledge_items = self.tier_manager.get_tier_knowledge(tier_id)
        tier = self.tier_manager.get_tier(tier_id)
        
        if not tier:
            return []
        
        results = []
        current_tokens = 0
        
        # Simple relevance-based filtering (in production would use vector search)
        for item in knowledge_items:
            if current_tokens >= max_tokens:
                break
            
            # Check relevance
            if query.lower() in item.content.lower():
                if item.relevance >= min_relevance:
                    if current_tokens + item.token_count <= max_tokens:
                        results.append(QueryResult(
                            tier_id=tier_id,
                            tier_type=tier.tier_type,
                            content=item.content,
                            relevance=item.relevance,
                            token_count=item.token_count,
                            metadata=item.metadata
                        ))
                        current_tokens += item.token_count
        
        # Sort by relevance
        results.sort(key=lambda r: r.relevance, reverse=True)
        
        return results
    
    def _build_tier_path_to_root(self, tier_id: str) -> List[str]:
        """Build path from tier to root."""
        path = []
        current_id = tier_id
        visited = set()
        
        while current_id:
            if current_id in visited:
                break
            
            path.append(current_id)
            visited.add(current_id)
            
            tier = self.tier_manager.get_tier(current_id)
            current_id = tier.parent_tier_id if tier else None
        
        return path
    
    def _calculate_refinement_score(
        self,
        results_by_tier: Dict[TierType, List[QueryResult]],
        config: RefinementConfig
    ) -> float:
        """
        Calculate refinement quality score.
        
        Factors:
        - Number of tiers used
        - Average relevance across tiers
        - Token utilization
        - Tier diversity
        """
        if not results_by_tier:
            return 0.0
        
        # Tier diversity score (0-1)
        tier_diversity = len(results_by_tier) / config.max_tiers
        
        # Average relevance across all results
        all_results = []
        for results in results_by_tier.values():
            all_results.extend(results)
        
        avg_relevance = sum(r.relevance for r in all_results) / len(all_results) if all_results else 0
        
        # Token utilization (0-1)
        total_tokens = sum(sum(r.token_count for r in results) for results in results_by_tier.values())
        token_utilization = total_tokens / config.token_budget if config.token_budget > 0 else 0
        
        # Combined score (weighted average)
        score = (
            tier_diversity * 0.3 +
            avg_relevance * 0.5 +
            token_utilization * 0.2
        )
        
        return min(1.0, max(0.0, score))


# ============================================================================
# Helper Functions
# ============================================================================

def create_default_config(
    strategy: RefinementStrategy = RefinementStrategy.BOTTOM_UP
) -> RefinementConfig:
    """Create default refinement configuration."""
    return RefinementConfig(strategy=strategy)

