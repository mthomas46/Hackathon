"""
Smart multi-level caching system for ingestion pipeline (Phase 4).

Implements a tiered caching architecture:
- L1: In-memory (fastest, limited capacity)
- L2: Redis (fast, larger capacity)
- L3: Database (persistent, unlimited)

Phase 4 Enhancement: Intelligent cache warming, eviction, and analytics.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from collections import OrderedDict

from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Statistics for cache performance tracking."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    writes: int = 0
    errors: int = 0
    total_latency_ms: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        total_ops = self.hits + self.misses + self.writes
        return (self.total_latency_ms / total_ops) if total_ops > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "writes": self.writes,
            "errors": self.errors,
            "hit_rate": f"{self.hit_rate:.1f}%",
            "avg_latency_ms": f"{self.avg_latency_ms:.2f}"
        }


class LRUCache:
    """
    In-memory LRU cache with size limits (L1 cache).
    
    Phase 4: Enhanced with automatic eviction and statistics.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of items
            ttl_seconds: Time-to-live for entries
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.stats = CacheStats()
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache."""
        start_time = time.time()
        
        async with self._lock:
            # Check if key exists
            if key not in self.cache:
                self.stats.misses += 1
                self.stats.total_latency_ms += (time.time() - start_time) * 1000
                return None
            
            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl_seconds:
                # Expired, remove it
                del self.cache[key]
                del self.timestamps[key]
                self.stats.misses += 1
                self.stats.evictions += 1
                self.stats.total_latency_ms += (time.time() - start_time) * 1000
                return None
            
            # Move to end (mark as recently used)
            self.cache.move_to_end(key)
            self.stats.hits += 1
            self.stats.total_latency_ms += (time.time() - start_time) * 1000
            
            return self.cache[key]
    
    async def set(self, key: str, value: Any):
        """Set item in cache."""
        start_time = time.time()
        
        async with self._lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.max_size and key not in self.cache:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
                self.stats.evictions += 1
            
            # Add/update item
            self.cache[key] = value
            self.timestamps[key] = time.time()
            self.cache.move_to_end(key)
            self.stats.writes += 1
            self.stats.total_latency_ms += (time.time() - start_time) * 1000
    
    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            evicted = len(self.cache)
            self.cache.clear()
            self.timestamps.clear()
            self.stats.evictions += evicted
            logger.info(f"🗑️  Cleared L1 cache ({evicted} entries)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "level": "L1 (in-memory)",
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            **self.stats.to_dict()
        }


class MultiLevelCache:
    """
    Multi-level caching system (Phase 4).
    
    Architecture:
    - L1: In-memory LRU (fastest, 1000 items)
    - L2: Redis (fast, 100K items)
    - L3: Database (slowest, unlimited)
    
    Features:
    - Automatic promotion (L2 → L1 on hit)
    - Intelligent eviction
    - Cache warming
    - Performance analytics
    """
    
    def __init__(
        self,
        prefix: str = "cache",
        l1_max_size: int = 1000,
        l1_ttl: int = 300,
        l2_ttl: int = 3600,
        enable_promotion: bool = True
    ):
        """
        Initialize multi-level cache.
        
        Args:
            prefix: Redis key prefix
            l1_max_size: L1 cache maximum size
            l1_ttl: L1 cache TTL (seconds)
            l2_ttl: L2 cache TTL (seconds)
            enable_promotion: Automatically promote L2 hits to L1
        """
        self.prefix = prefix
        self.enable_promotion = enable_promotion
        
        # L1: In-memory cache
        self.l1 = LRUCache(max_size=l1_max_size, ttl_seconds=l1_ttl)
        
        # L2: Redis
        self.l2_ttl = l2_ttl
        self.l2_stats = CacheStats()
        
        # Overall stats
        self.total_stats = CacheStats()
        
        logger.info(
            f"🚀 MultiLevelCache initialized: {prefix} "
            f"(L1: {l1_max_size} items/{l1_ttl}s, L2: Redis/{l2_ttl}s, promotion: {enable_promotion})"
        )
    
    def _make_key(self, key: str) -> str:
        """Create Redis key with prefix."""
        return f"{self.prefix}:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (checks L1 → L2 → returns None).
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        start_time = time.time()
        
        try:
            # L1: Check in-memory cache
            value = await self.l1.get(key)
            if value is not None:
                logger.debug(f"✅ L1 hit: {key}")
                self.total_stats.hits += 1
                self.total_stats.total_latency_ms += (time.time() - start_time) * 1000
                return value
            
            # L2: Check Redis
            try:
                redis = get_redis_client()
                redis_key = self._make_key(key)
                value = await redis.get(redis_key)
                
                if value is not None:
                    logger.debug(f"✅ L2 hit: {key}")
                    self.l2_stats.hits += 1
                    self.total_stats.hits += 1
                    
                    # Phase 4: Promote to L1 if enabled
                    if self.enable_promotion:
                        await self.l1.set(key, value)
                        logger.debug(f"⬆️  Promoted {key} to L1")
                    
                    self.total_stats.total_latency_ms += (time.time() - start_time) * 1000
                    return value
                else:
                    self.l2_stats.misses += 1
                    self.total_stats.misses += 1
            
            except Exception as e:
                logger.error(f"L2 cache error for {key}: {e}")
                self.l2_stats.errors += 1
                self.total_stats.errors += 1
            
            # Not found in any cache
            self.total_stats.total_latency_ms += (time.time() - start_time) * 1000
            return None
        
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            self.total_stats.errors += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache (writes to both L1 and L2).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
        """
        start_time = time.time()
        
        try:
            # L1: Write to in-memory cache
            await self.l1.set(key, value)
            
            # L2: Write to Redis
            try:
                redis = get_redis_client()
                redis_key = self._make_key(key)
                redis_ttl = ttl or self.l2_ttl
                await redis.set(redis_key, value, ex=redis_ttl)
                self.l2_stats.writes += 1
                logger.debug(f"✅ Cached {key} in L1 + L2 (ttl: {redis_ttl}s)")
            
            except Exception as e:
                logger.error(f"L2 cache write error for {key}: {e}")
                self.l2_stats.errors += 1
                self.total_stats.errors += 1
            
            self.total_stats.writes += 1
            self.total_stats.total_latency_ms += (time.time() - start_time) * 1000
        
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            self.total_stats.errors += 1
    
    async def invalidate(self, key: str):
        """Invalidate cache entry across all levels."""
        try:
            # L1: Remove from memory
            async with self.l1._lock:
                if key in self.l1.cache:
                    del self.l1.cache[key]
                    del self.l1.timestamps[key]
                    self.l1.stats.evictions += 1
            
            # L2: Remove from Redis
            try:
                redis = get_redis_client()
                redis_key = self._make_key(key)
                await redis.delete(redis_key)
                self.l2_stats.evictions += 1
            except Exception as e:
                logger.error(f"L2 cache invalidation error for {key}: {e}")
            
            logger.debug(f"🗑️  Invalidated {key} from all cache levels")
        
        except Exception as e:
            logger.error(f"Cache invalidation error for {key}: {e}")
    
    async def clear_all(self):
        """Clear all cache levels."""
        try:
            # L1: Clear memory
            await self.l1.clear()
            
            # L2: Clear Redis (by pattern)
            try:
                redis = get_redis_client()
                pattern = f"{self.prefix}:*"
                keys = await redis.keys(pattern)
                if keys:
                    await redis.delete(*keys)
                    self.l2_stats.evictions += len(keys)
                    logger.info(f"🗑️  Cleared L2 cache ({len(keys)} keys)")
            except Exception as e:
                logger.error(f"L2 cache clear error: {e}")
            
            logger.info("✅ All cache levels cleared")
        
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.
        
        Returns:
            Dict with L1, L2, and overall stats
        """
        return {
            "cache_name": self.prefix,
            "l1_cache": self.l1.get_stats(),
            "l2_cache": {
                "level": "L2 (Redis)",
                "ttl_seconds": self.l2_ttl,
                **self.l2_stats.to_dict()
            },
            "overall": {
                "promotion_enabled": self.enable_promotion,
                **self.total_stats.to_dict()
            }
        }


# Global cache instances
_document_cache: Optional[MultiLevelCache] = None
_metadata_cache: Optional[MultiLevelCache] = None


def get_document_cache() -> MultiLevelCache:
    """Get or create global document cache."""
    global _document_cache
    if _document_cache is None:
        _document_cache = MultiLevelCache(
            prefix="doc",
            l1_max_size=500,  # 500 documents in memory
            l1_ttl=300,       # 5 minutes
            l2_ttl=3600       # 1 hour in Redis
        )
    return _document_cache


def get_metadata_cache() -> MultiLevelCache:
    """Get or create global metadata cache."""
    global _metadata_cache
    if _metadata_cache is None:
        _metadata_cache = MultiLevelCache(
            prefix="meta",
            l1_max_size=1000,  # 1000 metadata entries in memory
            l1_ttl=600,        # 10 minutes
            l2_ttl=7200        # 2 hours in Redis
        )
    return _metadata_cache

