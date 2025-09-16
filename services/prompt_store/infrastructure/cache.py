"""Cache infrastructure for Prompt Store service.

Provides Redis and local caching capabilities for prompts and analytics.
"""

import time
import json
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from services.shared.utilities import utc_now

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    aioredis = None
    REDIS_AVAILABLE = False


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    created_at: datetime
    ttl: int
    hits: int = 0
    last_accessed: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class CacheStats:
    """Cache statistics."""
    total_hits: int = 0
    total_misses: int = 0
    total_size_bytes: int = 0
    evictions: int = 0


class PromptStoreCache:
    """Multi-level cache with Redis and local fallback for prompt store."""

    def __init__(self, redis_url: Optional[str] = None, max_local_entries: int = 1000):
        self.redis_url = redis_url or "redis://localhost:6379"
        self.redis_client = None
        self.local_cache: Dict[str, CacheEntry] = {}
        self.max_local_entries = max_local_entries
        self.stats = CacheStats()
        self.response_times: List[float] = []

    async def initialize(self) -> None:
        """Initialize Redis connection if available."""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = aioredis.from_url(self.redis_url)
                await self.redis_client.ping()
                print("✅ Redis cache initialized")
            except Exception as e:
                print(f"⚠️  Redis connection failed, using local cache only: {e}")
                self.redis_client = None

    async def close(self) -> None:
        """Close cache connections."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        start_time = time.time()

        # Try Redis first
        if self.redis_client:
            try:
                value = await self.redis_client.get(f"prompt_store:{key}")
                if value:
                    self.stats.total_hits += 1
                    self.response_times.append(time.time() - start_time)
                    return json.loads(value)
            except Exception:
                pass

        # Try local cache
        if key in self.local_cache:
            entry = self.local_cache[key]
            if self._is_expired(entry):
                del self.local_cache[key]
                self.stats.total_misses += 1
            else:
                entry.hits += 1
                entry.last_accessed = utc_now()
                self.stats.total_hits += 1
                self.response_times.append(time.time() - start_time)
                return entry.value

        self.stats.total_misses += 1
        self.response_times.append(time.time() - start_time)
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600, tags: Optional[List[str]] = None) -> bool:
        """Set value in cache."""
        entry = CacheEntry(
            value=value,
            created_at=utc_now(),
            ttl=ttl,
            tags=tags or []
        )

        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.setex(f"prompt_store:{key}", ttl, json.dumps(value))
                return True
            except Exception:
                pass

        # Use local cache
        if len(self.local_cache) >= self.max_local_entries:
            self._evict_oldest()

        self.local_cache[key] = entry
        return True

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        deleted = False

        # Try Redis first
        if self.redis_client:
            try:
                await self.redis_client.delete(f"prompt_store:{key}")
                deleted = True
            except Exception:
                pass

        # Remove from local cache
        if key in self.local_cache:
            del self.local_cache[key]
            deleted = True

        return deleted

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern."""
        invalidated = 0

        # Try Redis first
        if self.redis_client:
            try:
                keys = await self.redis_client.keys(f"prompt_store:{pattern}")
                if keys:
                    await self.redis_client.delete(*keys)
                    invalidated = len(keys)
            except Exception:
                pass

        # Remove from local cache
        keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.local_cache[key]
            invalidated += 1

        return invalidated

    async def clear(self) -> None:
        """Clear all cache entries."""
        # Clear Redis
        if self.redis_client:
            try:
                keys = await self.redis_client.keys("prompt_store:*")
                if keys:
                    await self.redis_client.delete(*keys)
            except Exception:
                pass

        # Clear local cache
        self.local_cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats.total_hits + self.stats.total_misses
        hit_ratio = self.stats.total_hits / total_requests if total_requests > 0 else 0

        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0

        return {
            "total_hits": self.stats.total_hits,
            "total_misses": self.stats.total_misses,
            "hit_ratio": hit_ratio,
            "total_size_bytes": self._calculate_size(),
            "evictions": self.stats.evictions,
            "local_cache_entries": len(self.local_cache),
            "avg_response_time_ms": avg_response_time * 1000,
            "redis_available": self.redis_client is not None
        }

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        return (utc_now() - entry.created_at).total_seconds() > entry.ttl

    def _evict_oldest(self) -> None:
        """Evict oldest cache entry."""
        if not self.local_cache:
            return

        oldest_key = min(self.local_cache.keys(),
                        key=lambda k: self.local_cache[k].last_accessed or self.local_cache[k].created_at)

        if oldest_key:
            del self.local_cache[oldest_key]
            self.stats.evictions += 1

    def _calculate_size(self) -> int:
        """Calculate approximate size of local cache."""
        try:
            return sum(len(json.dumps(entry.value)) for entry in self.local_cache.values())
        except Exception:
            return 0

    async def warmup_prompts(self, prompt_ids: List[str]) -> int:
        """Warm up cache with frequently used prompts."""
        warmed = 0
        for prompt_id in prompt_ids:
            # This would be implemented to load prompts into cache
            # For now, just track the operation
            warmed += 1
        return warmed

    async def warmup_analytics(self) -> bool:
        """Warm up analytics cache."""
        # This would pre-calculate and cache analytics data
        return True


# Global cache instance
prompt_store_cache = PromptStoreCache()
