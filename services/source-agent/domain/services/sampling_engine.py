"""
Intelligent Sampling Engine
===========================

Provides AI-powered document sampling strategies to reduce data volume
while maintaining maximum information value for planning insights.
"""

import os
import random
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import hashlib
from collections import Counter
import asyncio


class SamplingStrategy(Enum):
    """Available sampling strategies."""
    RANDOM = "random"
    STRATIFIED = "stratified"
    IMPORTANCE_BASED = "importance_based"
    TEMPORAL = "temporal"
    DIVERSITY_BASED = "diversity_based"


@dataclass
class SamplingConfig:
    """Configuration for sampling."""
    strategy: SamplingStrategy
    target_count: Optional[int] = None
    target_percentage: Optional[float] = None
    min_samples_per_strata: int = 2
    diversity_threshold: float = 0.3
    recency_weight: float = 0.5


@dataclass
class SamplingResult:
    """Result of a sampling operation."""
    sampled_items: List[Any]
    original_count: int
    sampled_count: int
    reduction_percentage: float
    strategy_used: SamplingStrategy
    metadata: Dict[str, Any]


class SamplingEngine:
    """
    Intelligent sampling engine for document processing.
    
    Provides:
    - Multiple sampling strategies
    - AI-powered relevance scoring
    - Deduplication
    - Context-aware sampling
    - Stratification support
    """
    
    def __init__(self, log_client=None):
        """
        Initialize sampling engine.
        
        Args:
            log_client: Optional log collector client
        """
        self.log_client = log_client
        self._cache = {}
    
    async def sample(
        self,
        items: List[Any],
        config: SamplingConfig,
        key_extractor: Optional[Callable[[Any], str]] = None,
        strata_extractor: Optional[Callable[[Any], str]] = None,
        importance_scorer: Optional[Callable[[Any], float]] = None
    ) -> SamplingResult:
        """
        Sample items using the specified strategy.
        
        Args:
            items: List of items to sample
            config: Sampling configuration
            key_extractor: Function to extract unique key from item
            strata_extractor: Function to extract strata from item (for stratified sampling)
            importance_scorer: Function to score item importance (for importance-based sampling)
            
        Returns:
            SamplingResult with sampled items and metadata
        """
        if not items:
            return SamplingResult(
                sampled_items=[],
                original_count=0,
                sampled_count=0,
                reduction_percentage=0.0,
                strategy_used=config.strategy,
                metadata={}
            )
        
        # Deduplicate first
        deduplicated = self._deduplicate(items, key_extractor)
        
        # Determine target count
        target_count = self._calculate_target_count(len(deduplicated), config)
        
        # Apply sampling strategy
        if config.strategy == SamplingStrategy.RANDOM:
            sampled = self._random_sampling(deduplicated, target_count)
            metadata = {"method": "random"}
            
        elif config.strategy == SamplingStrategy.STRATIFIED:
            if strata_extractor is None:
                raise ValueError("strata_extractor required for stratified sampling")
            sampled, metadata = self._stratified_sampling(
                deduplicated, target_count, strata_extractor, config
            )
            
        elif config.strategy == SamplingStrategy.IMPORTANCE_BASED:
            if importance_scorer is None:
                raise ValueError("importance_scorer required for importance-based sampling")
            sampled, metadata = self._importance_based_sampling(
                deduplicated, target_count, importance_scorer
            )
            
        elif config.strategy == SamplingStrategy.TEMPORAL:
            sampled, metadata = self._temporal_sampling(deduplicated, target_count, config)
            
        elif config.strategy == SamplingStrategy.DIVERSITY_BASED:
            sampled, metadata = self._diversity_based_sampling(
                deduplicated, target_count, key_extractor, config
            )
        else:
            raise ValueError(f"Unknown sampling strategy: {config.strategy}")
        
        # Calculate reduction
        reduction_percentage = (1 - len(sampled) / len(items)) * 100 if items else 0.0
        
        if self.log_client:
            await self.log_client.log_business_event(
                "sampling_completed",
                {
                    "strategy": config.strategy.value,
                    "original_count": len(items),
                    "sampled_count": len(sampled),
                    "reduction_percentage": reduction_percentage
                }
            )
        
        return SamplingResult(
            sampled_items=sampled,
            original_count=len(items),
            sampled_count=len(sampled),
            reduction_percentage=round(reduction_percentage, 2),
            strategy_used=config.strategy,
            metadata=metadata
        )
    
    def _deduplicate(
        self,
        items: List[Any],
        key_extractor: Optional[Callable[[Any], str]] = None
    ) -> List[Any]:
        """Remove duplicate items based on key."""
        if key_extractor is None:
            # Default: use hash of string representation
            key_extractor = lambda x: hashlib.md5(str(x).encode()).hexdigest()
        
        seen = set()
        deduplicated = []
        
        for item in items:
            key = key_extractor(item)
            if key not in seen:
                seen.add(key)
                deduplicated.append(item)
        
        return deduplicated
    
    def _calculate_target_count(
        self,
        total_count: int,
        config: SamplingConfig
    ) -> int:
        """Calculate target sample count from config."""
        if config.target_count is not None:
            return min(config.target_count, total_count)
        elif config.target_percentage is not None:
            return max(1, int(total_count * config.target_percentage))
        else:
            # Default: 30% sampling
            return max(1, int(total_count * 0.3))
    
    def _random_sampling(
        self,
        items: List[Any],
        target_count: int
    ) -> List[Any]:
        """Perform random sampling."""
        if target_count >= len(items):
            return items
        return random.sample(items, target_count)
    
    def _stratified_sampling(
        self,
        items: List[Any],
        target_count: int,
        strata_extractor: Callable[[Any], str],
        config: SamplingConfig
    ) -> tuple[List[Any], Dict[str, Any]]:
        """Perform stratified sampling to maintain representation across strata."""
        # Group by strata
        strata = {}
        for item in items:
            stratum = strata_extractor(item)
            if stratum not in strata:
                strata[stratum] = []
            strata[stratum].append(item)
        
        # Calculate samples per stratum
        total_items = len(items)
        samples_per_stratum = {}
        
        for stratum, stratum_items in strata.items():
            proportion = len(stratum_items) / total_items
            sample_count = max(
                config.min_samples_per_strata,
                int(target_count * proportion)
            )
            samples_per_stratum[stratum] = min(sample_count, len(stratum_items))
        
        # Adjust if we're over target
        total_samples = sum(samples_per_stratum.values())
        if total_samples > target_count:
            # Scale down proportionally
            scale_factor = target_count / total_samples
            samples_per_stratum = {
                s: max(config.min_samples_per_strata, int(c * scale_factor))
                for s, c in samples_per_stratum.items()
            }
        
        # Sample from each stratum
        sampled = []
        for stratum, stratum_items in strata.items():
            sample_count = samples_per_stratum[stratum]
            if sample_count >= len(stratum_items):
                sampled.extend(stratum_items)
            else:
                sampled.extend(random.sample(stratum_items, sample_count))
        
        metadata = {
            "strata_count": len(strata),
            "samples_per_stratum": samples_per_stratum
        }
        
        return sampled, metadata
    
    def _importance_based_sampling(
        self,
        items: List[Any],
        target_count: int,
        importance_scorer: Callable[[Any], float]
    ) -> tuple[List[Any], Dict[str, Any]]:
        """Sample based on importance scores (top-k)."""
        # Score all items
        scored_items = [(item, importance_scorer(item)) for item in items]
        
        # Sort by score (descending)
        scored_items.sort(key=lambda x: x[1], reverse=True)
        
        # Take top k
        sampled = [item for item, _ in scored_items[:target_count]]
        
        # Calculate score statistics
        scores = [score for _, score in scored_items[:target_count]]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        min_score = min(scores) if scores else 0.0
        max_score = max(scores) if scores else 0.0
        
        metadata = {
            "avg_importance_score": round(avg_score, 2),
            "min_importance_score": round(min_score, 2),
            "max_importance_score": round(max_score, 2)
        }
        
        return sampled, metadata
    
    def _temporal_sampling(
        self,
        items: List[Any],
        target_count: int,
        config: SamplingConfig
    ) -> tuple[List[Any], Dict[str, Any]]:
        """Sample with bias toward recent items."""
        # Assume items have a 'updated' or 'created' attribute
        # For items without timestamp, assign low priority
        
        def get_timestamp(item):
            """Extract timestamp from item."""
            for attr in ['updated', 'created', 'timestamp', 'date']:
                if hasattr(item, attr):
                    ts = getattr(item, attr)
                    if ts:
                        return ts.timestamp() if hasattr(ts, 'timestamp') else 0
            return 0
        
        # Score by recency
        max_timestamp = max((get_timestamp(item) for item in items), default=1)
        
        def temporal_score(item):
            """Calculate temporal score (0-1, higher = more recent)."""
            ts = get_timestamp(item)
            if max_timestamp == 0:
                return 0.5
            return (ts / max_timestamp) * config.recency_weight + (1 - config.recency_weight) * 0.5
        
        # Use importance-based sampling with temporal scores
        return self._importance_based_sampling(items, target_count, temporal_score)
    
    def _diversity_based_sampling(
        self,
        items: List[Any],
        target_count: int,
        key_extractor: Optional[Callable[[Any], str]],
        config: SamplingConfig
    ) -> tuple[List[Any], Dict[str, Any]]:
        """Sample to maximize diversity."""
        if target_count >= len(items):
            return items, {"diversity_method": "all_items"}
        
        # Extract features for diversity calculation
        def get_features(item):
            """Extract feature set from item."""
            features = set()
            
            # Use attributes as features
            if hasattr(item, 'labels'):
                features.update(item.labels)
            if hasattr(item, 'issue_type'):
                features.add(item.issue_type)
            if hasattr(item, 'status'):
                features.add(item.status)
            if hasattr(item, 'priority'):
                features.add(item.priority)
            if hasattr(item, 'content_type'):
                features.add(item.content_type)
            
            # Extract words from title/summary
            for attr in ['title', 'summary']:
                if hasattr(item, attr):
                    text = getattr(item, attr)
                    if text:
                        words = text.lower().split()[:5]  # First 5 words
                        features.update(words)
            
            return features
        
        # Start with a random item
        sampled = [random.choice(items)]
        remaining = [item for item in items if item != sampled[0]]
        
        # Greedily add most diverse items
        while len(sampled) < target_count and remaining:
            # Calculate diversity score for each remaining item
            diversity_scores = []
            
            for candidate in remaining:
                candidate_features = get_features(candidate)
                
                # Calculate average distance to sampled items
                distances = []
                for selected in sampled:
                    selected_features = get_features(selected)
                    
                    # Jaccard distance
                    intersection = len(candidate_features & selected_features)
                    union = len(candidate_features | selected_features)
                    distance = 1 - (intersection / union if union > 0 else 0)
                    distances.append(distance)
                
                avg_distance = sum(distances) / len(distances) if distances else 0
                diversity_scores.append((candidate, avg_distance))
            
            # Select item with highest average distance
            diversity_scores.sort(key=lambda x: x[1], reverse=True)
            best_candidate = diversity_scores[0][0]
            
            sampled.append(best_candidate)
            remaining.remove(best_candidate)
        
        # Calculate diversity metrics
        all_features = set()
        for item in sampled:
            all_features.update(get_features(item))
        
        metadata = {
            "diversity_method": "greedy_max_distance",
            "unique_features": len(all_features),
            "avg_features_per_item": round(len(all_features) / len(sampled), 2) if sampled else 0
        }
        
        return sampled, metadata
    
    async def recommend_strategy(
        self,
        items: List[Any],
        target_reduction: float = 0.7
    ) -> SamplingStrategy:
        """
        Recommend best sampling strategy based on data characteristics.
        
        Args:
            items: Items to be sampled
            target_reduction: Target reduction percentage (0-1)
            
        Returns:
            Recommended SamplingStrategy
        """
        if not items:
            return SamplingStrategy.RANDOM
        
        # Analyze data characteristics
        has_strata = any(hasattr(item, attr) for attr in ['status', 'issue_type', 'content_type'] for item in items[:10])
        has_timestamp = any(hasattr(item, attr) for attr in ['updated', 'created', 'timestamp'] for item in items[:10])
        has_features = any(hasattr(item, attr) for attr in ['labels', 'title', 'summary'] for item in items[:10])
        
        # Small datasets: take all or random
        if len(items) < 20:
            return SamplingStrategy.RANDOM
        
        # If we have clear strata, use stratified
        if has_strata:
            return SamplingStrategy.STRATIFIED
        
        # If we have timestamps and want recent data, use temporal
        if has_timestamp and target_reduction < 0.8:
            return SamplingStrategy.TEMPORAL
        
        # If we have rich features, use diversity
        if has_features:
            return SamplingStrategy.DIVERSITY_BASED
        
        # Default to random
        return SamplingStrategy.RANDOM

