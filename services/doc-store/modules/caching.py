# ============================================================================
# CACHING MODULE
# ============================================================================
"""
High-performance caching layer for Doc Store service.

Provides multi-level caching with Redis integration, intelligent cache invalidation,
performance monitoring, and adaptive caching strategies.
"""

import json
import hashlib
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    REDIS_AVAILABLE = False

from services.shared.utilities import utc_now


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    ttl: int
    created_at: datetime
    hits: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class CacheStats:
    """Cache performance statistics."""
    total_entries: int = 0
    total_hits: int = 0
    total_misses: int = 0
    hit_rate: float = 0.0
    total_size_bytes: int = 0
    evictions: int = 0
    connections: int = 0
    avg_response_time_ms: float = 0.0


class DocStoreCache:
    """High-performance caching layer for doc-store operations."""

    def __init__(self, redis_url: Optional[str] = None, max_memory_mb: int = 100):
        self.redis_url = redis_url or "redis://localhost:6379"
        self.max_memory_mb = max_memory_mb
        self.redis_client = None
        self.local_cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()
        self.cache_prefix = "docstore:cache:"
        self.monitoring_enabled = True
        self.response_times: List[float] = []

    async def initialize(self) -> bool:
        """Initialize the cache system."""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = aioredis.from_url(self.redis_url)
                # Configure Redis for caching
                await self.redis_client.config_set('maxmemory', f'{self.max_memory_mb}mb')
                await self.redis_client.config_set('maxmemory-policy', 'allkeys-lru')
                self.stats.connections = 1
                return True
            except Exception:
                self.redis_client = None
                return False
        return False

    async def close(self):
        """Close cache connections."""
        if self.redis_client:
            await self.redis_client.aclose()
            self.redis_client = None
            self.stats.connections = 0

    def _generate_cache_key(self, operation: str, params: Dict[str, Any]) -> str:
        """Generate a deterministic cache key."""
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True, default=str)
        key_content = f"{operation}:{sorted_params}"
        key_hash = hashlib.md5(key_content.encode()).hexdigest()[:16]
        return f"{self.cache_prefix}{operation}:{key_hash}"

    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate memory size of cached value."""
        if isinstance(value, (dict, list)):
            return len(json.dumps(value).encode('utf-8'))
        elif isinstance(value, str):
            return len(value.encode('utf-8'))
        else:
            return len(str(value).encode('utf-8'))

    async def get(self, operation: str, params: Dict[str, Any], tags: Optional[List[str]] = None) -> Optional[Any]:
        """Get cached value with performance monitoring."""
        start_time = time.time()
        cache_key = self._generate_cache_key(operation, params)

        try:
            # Try Redis first
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    # Update access time and hit count
                    await self.redis_client.hincrby(f"{cache_key}:meta", "hits", 1)
                    await self.redis_client.hset(f"{cache_key}:meta", "last_accessed", utc_now().isoformat())

                    self.stats.total_hits += 1
                    response_time = (time.time() - start_time) * 1000
                    self.response_times.append(response_time)

                    return json.loads(cached_data)

            # Try local cache
            if cache_key in self.local_cache:
                entry = self.local_cache[cache_key]
                if utc_now() < entry.created_at + timedelta(seconds=entry.ttl):
                    entry.hits += 1
                    entry.last_accessed = utc_now()

                    self.stats.total_hits += 1
                    response_time = (time.time() - start_time) * 1000
                    self.response_times.append(response_time)

                    return entry.value

            self.stats.total_misses += 1
            return None

        except Exception:
            self.stats.total_misses += 1
            return None

    async def set(self, operation: str, params: Dict[str, Any], value: Any,
                  ttl: int = 300, tags: Optional[List[str]] = None) -> bool:
        """Set cached value with metadata."""
        try:
            cache_key = self._generate_cache_key(operation, params)
            serialized_value = json.dumps(value, default=str)
            size_bytes = len(serialized_value.encode('utf-8'))

            # Store in Redis
            if self.redis_client:
                # Store value
                await self.redis_client.setex(cache_key, ttl, serialized_value)

                # Store metadata
                meta_key = f"{cache_key}:meta"
                await self.redis_client.hset(meta_key, mapping={
                    "operation": operation,
                    "params": json.dumps(params),
                    "ttl": ttl,
                    "created_at": utc_now().isoformat(),
                    "hits": 0,
                    "size_bytes": size_bytes,
                    "tags": json.dumps(tags or [])
                })
                await self.redis_client.expire(meta_key, ttl)

                # Add to tag index
                if tags:
                    for tag in tags:
                        await self.redis_client.sadd(f"{self.cache_prefix}tag:{tag}", cache_key)
                        await self.redis_client.expire(f"{self.cache_prefix}tag:{tag}", ttl)

            # Store in local cache as backup
            self.local_cache[cache_key] = CacheEntry(
                key=cache_key,
                value=value,
                ttl=ttl,
                created_at=utc_now(),
                size_bytes=size_bytes,
                tags=tags or []
            )

            # Update stats
            self.stats.total_entries = len(self.local_cache)
            self.stats.total_size_bytes = sum(entry.size_bytes for entry in self.local_cache.values())

            return True

        except Exception:
            return False

    async def invalidate(self, operation: Optional[str] = None, tags: Optional[List[str]] = None) -> int:
        """Invalidate cache entries by operation or tags."""
        try:
            invalidated = 0

            if tags and self.redis_client:
                # Invalidate by tags
                for tag in tags:
                    tag_key = f"{self.cache_prefix}tag:{tag}"
                    cache_keys = await self.redis_client.smembers(tag_key)
                    if cache_keys:
                        # Delete cache entries
                        await self.redis_client.delete(*cache_keys)
                        # Delete metadata
                        meta_keys = [f"{key}:meta" for key in cache_keys]
                        await self.redis_client.delete(*meta_keys)
                        # Delete tag index
                        await self.redis_client.delete(tag_key)
                        invalidated += len(cache_keys)

            elif operation and self.redis_client:
                # Invalidate by operation pattern
                pattern = f"{self.cache_prefix}{operation}:*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    await self.redis_client.delete(*keys)
                    invalidated += len(keys)

            # Clear local cache
            if operation:
                keys_to_remove = [k for k in self.local_cache.keys() if operation in k]
                for key in keys_to_remove:
                    del self.local_cache[key]
                invalidated += len(keys_to_remove)
            elif tags:
                keys_to_remove = []
                for key, entry in self.local_cache.items():
                    if any(tag in entry.tags for tag in tags):
                        keys_to_remove.append(key)
                for key in keys_to_remove:
                    del self.local_cache[key]
                invalidated += len(keys_to_remove)
            else:
                invalidated += len(self.local_cache)
                self.local_cache.clear()

            return invalidated

        except Exception:
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        try:
            redis_stats = {}
            if self.redis_client:
                info = await self.redis_client.info()
                redis_stats = {
                    "redis_used_memory": info.get("used_memory", 0),
                    "redis_total_connections": info.get("total_connections_received", 0),
                    "redis_connected_clients": info.get("connected_clients", 0),
                    "redis_keys_count": await self.redis_client.dbsize()
                }

            # Calculate hit rate
            total_requests = self.stats.total_hits + self.stats.total_misses
            hit_rate = (self.stats.total_hits / total_requests * 100) if total_requests > 0 else 0

            # Calculate average response time
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0

            # Keep only last 100 response times
            self.response_times = self.response_times[-100:]

            return {
                "cache_enabled": self.redis_client is not None,
                "local_cache_entries": len(self.local_cache),
                "total_hits": self.stats.total_hits,
                "total_misses": self.stats.total_misses,
                "hit_rate_percent": round(hit_rate, 2),
                "total_size_bytes": self.stats.total_size_bytes,
                "evictions": self.stats.evictions,
                "avg_response_time_ms": round(avg_response_time, 2),
                "redis_stats": redis_stats,
                "uptime_seconds": (utc_now() - datetime.fromisoformat("2024-01-01T00:00:00")).total_seconds()
            }

        except Exception as e:
            return {"error": str(e)}

    async def warmup_cache(self) -> Dict[str, Any]:
        """Warm up cache with frequently accessed data."""
        try:
            # This would be implemented to preload commonly accessed data
            # For now, return placeholder
            return {
                "status": "warmup_placeholder",
                "message": "Cache warmup not yet implemented - would preload analytics, search facets, etc."
            }
        except Exception as e:
            return {"error": str(e)}

    async def optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache performance and memory usage."""
        try:
            optimizations = []

            # Clean expired local cache entries
            expired_keys = []
            now = utc_now()
            for key, entry in self.local_cache.items():
                if now > entry.created_at + timedelta(seconds=entry.ttl):
                    expired_keys.append(key)

            for key in expired_keys:
                del self.local_cache[key]

            if expired_keys:
                optimizations.append(f"Cleaned {len(expired_keys)} expired local cache entries")

            # Redis optimizations would go here
            if self.redis_client:
                # Trigger Redis memory optimization
                await self.redis_client.memory_purge()
                optimizations.append("Triggered Redis memory optimization")

            return {
                "optimizations_applied": optimizations,
                "local_cache_entries_after": len(self.local_cache)
            }

        except Exception as e:
            return {"error": str(e)}


# Global cache instance
docstore_cache = DocStoreCache()
