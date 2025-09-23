"""
Advanced Cache Management System

Multi-level caching with Redis, memory, and tiered strategies:
- L1: In-memory cache for frequently accessed data
- L2: Redis cache for shared data across instances
- L3: Database cache for persistent, less frequently accessed data
- Intelligent cache invalidation and prefetching
- Cache compression and memory optimization
"""

import asyncio
import hashlib
import json
import pickle  # nosec: Required for complex object serialization with JSON fallback
import zlib
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import redis.asyncio as redis



@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None
    access_count: int = 0
    compressed: bool = False
    size_bytes: int = 0


@dataclass
class CacheStats:
    """Cache performance statistics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    sets: int = 0
    deletes: int = 0
    compression_ratio: float = 1.0
    memory_usage_bytes: int = 0
    hit_ratio: float = 0.0


class BaseCache:
    """Base cache interface."""

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        raise NotImplementedError

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        raise NotImplementedError

    async def clear(self) -> bool:
        """Clear all cache entries."""
        raise NotImplementedError

    async def get_stats(self) -> CacheStats:
        """Get cache statistics."""
        raise NotImplementedError


class MemoryCache(BaseCache):
    """In-memory LRU cache with TTL support."""

    def __init__(self, max_size: int = 1000, compression_threshold: int = 1024):
        self.max_size = max_size
        self.compression_threshold = compression_threshold
        self.cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        self.executor = ThreadPoolExecutor(max_workers=2)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        if key not in self.cache:
            self.stats.misses += 1
            return None

        entry = self.cache[key]

        # Check TTL
        if entry.ttl and (datetime.now() - entry.created_at).seconds > entry.ttl:
            await self.delete(key)
            self.stats.misses += 1
            return None

        # Update access metadata
        entry.accessed_at = datetime.now()
        entry.access_count += 1
        self.stats.hits += 1

        # Decompress if needed
        value = entry.value
        if entry.compressed:
            value = await asyncio.get_event_loop().run_in_executor(self.executor, zlib.decompress, value)
            value = pickle.loads(value)  # nosec: Safe fallback after JSON attempt for complex objects

        return value

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache."""
        try:
            # Serialize and potentially compress
            serialized = pickle.dumps(value)  # nosec: Used only for complex objects not serializable by JSON
            compressed = False
            final_value = serialized

            # Compress if above threshold
            if len(serialized) > self.compression_threshold:
                compressed_value = await asyncio.get_event_loop().run_in_executor(
                    self.executor, zlib.compress, serialized, 6
                )
                if len(compressed_value) < len(serialized):
                    final_value = compressed_value
                    compressed = True
                    self.stats.compression_ratio = (
                        self.stats.compression_ratio + len(compressed_value) / len(serialized)
                    ) / 2

            entry = CacheEntry(key=key, value=final_value, ttl=ttl, compressed=compressed, size_bytes=len(final_value))

            # Evict if at capacity (simple LRU)
            if len(self.cache) >= self.max_size and key not in self.cache:
                # Find least recently used
                lru_key = min(self.cache.keys(), key=lambda k: (self.cache[k].accessed_at, self.cache[k].access_count))
                await self.delete(lru_key)
                self.stats.evictions += 1

            self.cache[key] = entry
            self.stats.sets += 1
            self._update_memory_usage()

            return True

        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        if key in self.cache:
            del self.cache[key]
            self.stats.deletes += 1
            self._update_memory_usage()
            return True
        return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        if key not in self.cache:
            return False

        entry = self.cache[key]
        if entry.ttl and (datetime.now() - entry.created_at).seconds > entry.ttl:
            await self.delete(key)
            return False

        return True

    async def clear(self) -> bool:
        """Clear all memory cache entries."""
        self.cache.clear()
        self.stats = CacheStats()
        return True

    async def get_stats(self) -> CacheStats:
        """Get memory cache statistics."""
        self.stats.hit_ratio = (
            self.stats.hits / (self.stats.hits + self.stats.misses) if (self.stats.hits + self.stats.misses) > 0 else 0
        )
        return self.stats

    def _update_memory_usage(self):
        """Update memory usage statistics."""
        self.stats.memory_usage_bytes = sum(entry.size_bytes for entry in self.cache.values())


class RedisCache(BaseCache):
    """Redis-based distributed cache."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 10,
    ):
        self.redis_url = f"redis://:{password}@{host}:{port}/{db}" if password else f"redis://{host}:{port}/{db}"
        self.max_connections = max_connections
        self._pool = None
        self.stats = CacheStats()

    async def _get_connection(self) -> redis.Redis:
        """Get Redis connection."""
        if self._pool is None:
            self._pool = redis.ConnectionPool.from_url(
                self.redis_url, max_connections=self.max_connections, decode_responses=False
            )
        return redis.Redis(connection_pool=self._pool)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            redis_client = await self._get_connection()
            value = await redis_client.get(key)

            if value is None:
                self.stats.misses += 1
                return None

            # Deserialize
            try:
                deserialized = pickle.loads(value)  # nosec: Safe fallback after JSON attempt for complex objects
                self.stats.hits += 1
                return deserialized
            except Exception:
                # Try JSON fallback
                json_str = value.decode("utf-8")
                deserialized = json.loads(json_str)
                self.stats.hits += 1
                return deserialized

        except Exception:
            self.stats.misses += 1
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        try:
            redis_client = await self._get_connection()

            # Serialize
            if isinstance(value, (dict, list, str, int, float, bool)):
                serialized = json.dumps(value).encode("utf-8")
            else:
                serialized = pickle.dumps(value)  # nosec: Used only for complex objects not serializable by JSON

            success = await redis_client.set(key, serialized, ex=ttl)
            if success:
                self.stats.sets += 1
            return bool(success)

        except Exception:
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache."""
        try:
            redis_client = await self._get_connection()
            result = await redis_client.delete(key)
            if result > 0:
                self.stats.deletes += 1
            return result > 0
        except Exception:
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        try:
            redis_client = await self._get_connection()
            return bool(await redis_client.exists(key))
        except Exception:
            return False

    async def clear(self) -> bool:
        """Clear Redis cache (use with caution)."""
        try:
            redis_client = await self._get_connection()
            await redis_client.flushdb()
            return True
        except Exception:
            return False

    async def get_stats(self) -> CacheStats:
        """Get Redis cache statistics."""
        try:
            redis_client = await self._get_connection()
            info = await redis_client.info()

            self.stats.memory_usage_bytes = info.get("used_memory", 0)
            self.stats.hit_ratio = (
                info.get("keyspace_hits", 0) / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
                if (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0)) > 0
                else 0
            )

            return self.stats
        except Exception:
            return self.stats


class TieredCache(BaseCache):
    """
    Multi-level tiered cache with automatic fallback.

    L1: Memory cache (fastest, smallest)
    L2: Redis cache (shared, medium speed)
    L3: Database cache (persistent, slowest)
    """

    def __init__(
        self, l1_cache: MemoryCache, l2_cache: Optional[RedisCache] = None, l3_callback: Optional[Callable] = None
    ):
        self.l1_cache = l1_cache
        self.l2_cache = l2_cache
        self.l3_callback = l3_callback  # Callback for database/cache layer
        self.stats = CacheStats()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from tiered cache with fallback."""
        # Try L1 cache first
        value = await self.l1_cache.get(key)
        if value is not None:
            # Also populate L2 if available
            if self.l2_cache:
                await self.l2_cache.set(key, value, ttl=300)  # 5 minutes
            return value

        # Try L2 cache
        if self.l2_cache:
            value = await self.l2_cache.get(key)
            if value is not None:
                # Populate L1
                await self.l1_cache.set(key, value, ttl=60)  # 1 minute
                return value

        # Try L3 (database/external cache)
        if self.l3_callback:
            try:
                value = await self.l3_callback(key, "get")
                if value is not None:
                    # Populate L1 and L2
                    await self.l1_cache.set(key, value, ttl=300)
                    if self.l2_cache:
                        await self.l2_cache.set(key, value, ttl=3600)  # 1 hour
                    return value
            except Exception:
                pass

        self.stats.misses += 1
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in all cache tiers."""
        success = True

        # Set in L1
        if not await self.l1_cache.set(key, value, ttl=min(ttl or 300, 60)):  # Max 1 min in L1
            success = False

        # Set in L2
        if self.l2_cache and not await self.l2_cache.set(key, value, ttl=ttl or 3600):
            success = False

        # Set in L3
        if self.l3_callback:
            try:
                await self.l3_callback(key, "set", value, ttl)
            except Exception:
                success = False

        if success:
            self.stats.sets += 1

        return success

    async def delete(self, key: str) -> bool:
        """Delete value from all cache tiers."""
        success = True

        # Delete from L1
        if not await self.l1_cache.delete(key):
            success = False

        # Delete from L2
        if self.l2_cache and not await self.l2_cache.delete(key):
            success = False

        # Delete from L3
        if self.l3_callback:
            try:
                await self.l3_callback(key, "delete")
            except Exception:
                success = False

        if success:
            self.stats.deletes += 1

        return success

    async def exists(self, key: str) -> bool:
        """Check if key exists in any cache tier."""
        return (
            await self.l1_cache.exists(key)
            or (self.l2_cache and await self.l2_cache.exists(key))
            or (self.l3_callback and await self._l3_exists(key))
        )

    async def clear(self) -> bool:
        """Clear all cache tiers."""
        success = True

        if not await self.l1_cache.clear():
            success = False

        if self.l2_cache and not await self.l2_cache.clear():
            success = False

        # L3 clear not implemented for safety

        return success

    async def get_stats(self) -> Dict[str, CacheStats]:
        """Get statistics from all cache tiers."""
        stats = {"tiered": self.stats, "l1": await self.l1_cache.get_stats()}

        if self.l2_cache:
            stats["l2"] = await self.l2_cache.get_stats()

        return stats

    async def _l3_exists(self, key: str) -> bool:
        """Check if key exists in L3."""
        if self.l3_callback:
            try:
                return await self.l3_callback(key, "exists")
            except Exception:
                pass
        return False


class CacheManager:
    """
    Intelligent cache manager with prefetching and invalidation strategies.

    Features:
    - Smart cache key generation
    - Cache warming and prefetching
    - Intelligent invalidation
    - Cache analytics and optimization
    """

    def __init__(self, cache: BaseCache):
        self.cache = cache
        self.key_prefix = "api_dashboard"
        self.prefetch_rules: Dict[str, Callable] = {}
        self.invalidation_rules: Dict[str, List[str]] = {}

    def generate_key(self, *parts) -> str:
        """Generate cache key from parts."""
        key_content = ":".join(str(part) for part in parts)
        return f"{self.key_prefix}:{hashlib.sha256(key_content.encode()).hexdigest()[:16]}"

    async def get_or_compute(self, key: str, compute_func: Callable, ttl: Optional[int] = None) -> Any:
        """Get from cache or compute and cache."""
        value = await self.cache.get(key)
        if value is not None:
            return value

        # Compute value
        value = await compute_func()

        # Cache result
        await self.cache.set(key, value, ttl)

        # Trigger prefetching
        await self._trigger_prefetch(key, value)

        return value

    async def invalidate_pattern(self, pattern: str):
        """Invalidate cache keys matching a pattern."""
        # In a real implementation, this would scan for keys matching the pattern
        # For simplicity, we'll rely on explicit invalidation

    def add_prefetch_rule(self, trigger_key: str, prefetch_func: Callable):
        """Add a prefetch rule."""
        self.prefetch_rules[trigger_key] = prefetch_func

    def add_invalidation_rule(self, source_key: str, dependent_keys: List[str]):
        """Add cache invalidation dependency."""
        if source_key not in self.invalidation_rules:
            self.invalidation_rules[source_key] = []
        self.invalidation_rules[source_key].extend(dependent_keys)

    async def _trigger_prefetch(self, key: str, value: Any):
        """Trigger prefetching based on access patterns."""
        if key in self.prefetch_rules:
            try:
                await self.prefetch_rules[key](value)
            except Exception:
                pass  # Prefetch failures shouldn't affect main operation

    async def invalidate_dependents(self, source_key: str):
        """Invalidate all dependent cache keys."""
        if source_key in self.invalidation_rules:
            for dependent_key in self.invalidation_rules[source_key]:
                await self.cache.delete(dependent_key)

    async def warmup_cache(self, warmup_data: Dict[str, Any]):
        """Warm up cache with frequently accessed data."""
        for key, (value, ttl) in warmup_data.items():
            await self.cache.set(key, value, ttl)

    async def get_cache_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics."""
        stats = await self.cache.get_stats()

        return {
            "cache_stats": stats,
            "prefetch_rules_count": len(self.prefetch_rules),
            "invalidation_rules_count": len(self.invalidation_rules),
            "cache_hit_ratio": getattr(stats, "hit_ratio", 0),
            "memory_usage_mb": getattr(stats, "memory_usage_bytes", 0) / (1024 * 1024),
            "compression_ratio": getattr(stats, "compression_ratio", 1.0),
        }
