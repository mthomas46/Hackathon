"""Cache Manager - Advanced caching strategies and implementations."""

import asyncio
import threading
import json
import pickle
from typing import Dict, Any, Optional, Union, List, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
import hashlib
import lru

from ..di.services import ILoggerService, ICacheService
from ..logging.logger import get_logger

T = TypeVar('T')


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    tags: List[str] = field(default_factory=list)

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return self.expires_at is not None and datetime.now(timezone.utc) > self.expires_at

    def access(self) -> None:
        """Record access to this entry."""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)

    def calculate_size(self) -> int:
        """Calculate approximate size of the entry in bytes."""
        try:
            # Rough size calculation
            value_size = len(pickle.dumps(self.value))
            metadata_size = len(pickle.dumps({
                'key': self.key,
                'created_at': self.created_at,
                'expires_at': self.expires_at,
                'access_count': self.access_count,
                'last_accessed': self.last_accessed,
                'tags': self.tags
            }))
            return value_size + metadata_size
        except Exception:
            return 1024  # Default size estimate


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass

    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache implementation with LRU eviction."""

    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None) -> None:
        """Initialize memory cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.RLock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired():
                    await self.delete(key)
                    return None

                entry.access()
                self._hits += 1
                return entry.value
            else:
                self._misses += 1
                return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache."""
        with self._lock:
            # Calculate TTL
            expires_at = None
            if ttl or self._default_ttl:
                ttl_seconds = ttl or self._default_ttl
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=datetime.now(timezone.utc),
                expires_at=expires_at
            )
            entry.calculate_size()

            # Check if we need to evict
            if key not in self._cache and len(self._cache) >= self._max_size:
                await self._evict_lru()

            self._cache[key] = entry

    async def delete(self, key: str) -> None:
        """Delete value from memory cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry.is_expired():
                    await self.delete(key)
                    return False
                return True
            return False

    async def clear(self) -> None:
        """Clear all memory cache entries."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

    async def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        if not self._cache:
            return

        # Find entry with oldest access time
        oldest_key = None
        oldest_time = datetime.now(timezone.utc)

        for key, entry in self._cache.items():
            if entry.last_accessed and entry.last_accessed < oldest_time:
                oldest_time = entry.last_accessed
                oldest_key = key
            elif entry.last_accessed is None and entry.created_at < oldest_time:
                oldest_time = entry.created_at
                oldest_key = key

        if oldest_key:
            del self._cache[oldest_key]
            self._evictions += 1

    async def get_stats(self) -> Dict[str, Any]:
        """Get memory cache statistics."""
        with self._lock:
            total_size = sum(entry.size_bytes for entry in self._cache.values())

            return {
                "entries": len(self._cache),
                "max_size": self._max_size,
                "total_size_bytes": total_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0,
                "evictions": self._evictions,
                "default_ttl": self._default_ttl
            }


class RedisCache(CacheBackend):
    """Redis cache implementation."""

    def __init__(self,
                 host: str = "localhost",
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 default_ttl: Optional[int] = None,
                 key_prefix: str = "cache:") -> None:
        """Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password
            default_ttl: Default TTL in seconds
            key_prefix: Key prefix for namespacing
        """
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._default_ttl = default_ttl
        self._key_prefix = key_prefix
        self._redis = None
        self._lock = threading.RLock()

        # Initialize Redis connection
        self._init_redis()

    def _init_redis(self) -> None:
        """Initialize Redis connection."""
        try:
            import redis.asyncio as aioredis
            self._redis = aioredis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                password=self._password,
                decode_responses=False  # Keep as bytes for pickle
            )
        except ImportError:
            # Redis not available
            pass

    def _make_key(self, key: str) -> str:
        """Make prefixed cache key."""
        return f"{self._key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self._redis:
            return None

        try:
            cache_key = self._make_key(key)
            value_bytes = await self._redis.get(cache_key)
            if value_bytes:
                return pickle.loads(value_bytes)
        except Exception:
            pass  # Cache miss or error

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis cache."""
        if not self._redis:
            return

        try:
            cache_key = self._make_key(key)
            value_bytes = pickle.dumps(value)
            ttl_seconds = ttl or self._default_ttl

            if ttl_seconds:
                await self._redis.setex(cache_key, ttl_seconds, value_bytes)
            else:
                await self._redis.set(cache_key, value_bytes)
        except Exception:
            pass  # Ignore cache errors

    async def delete(self, key: str) -> None:
        """Delete value from Redis cache."""
        if not self._redis:
            return

        try:
            cache_key = self._make_key(key)
            await self._redis.delete(cache_key)
        except Exception:
            pass  # Ignore cache errors

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        if not self._redis:
            return False

        try:
            cache_key = self._make_key(key)
            return await self._redis.exists(cache_key) > 0
        except Exception:
            return False

    async def clear(self) -> None:
        """Clear all Redis cache entries with our prefix."""
        if not self._redis:
            return

        try:
            # Find all keys with our prefix
            pattern = f"{self._key_prefix}*"
            keys = await self._redis.keys(pattern)
            if keys:
                await self._redis.delete(*keys)
        except Exception:
            pass  # Ignore cache errors

    async def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self._redis:
            return {"error": "Redis not available"}

        try:
            info = await self._redis.info()
            return {
                "redis_connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "key_prefix": self._key_prefix,
                "default_ttl": self._default_ttl
            }
        except Exception as e:
            return {"error": str(e)}


class CacheManager(ICacheService):
    """Advanced cache manager with multiple backends and strategies."""

    def __init__(self,
                 primary_backend: Optional[CacheBackend] = None,
                 secondary_backend: Optional[CacheBackend] = None,
                 logger: Optional[ILoggerService] = None) -> None:
        """Initialize cache manager.

        Args:
            primary_backend: Primary cache backend (fast, small)
            secondary_backend: Secondary cache backend (slower, larger)
            logger: Logger service for cache operations
        """
        self._primary = primary_backend or MemoryCache(max_size=1000)
        self._secondary = secondary_backend
        self._logger = logger or get_logger()
        self._lock = threading.RLock()

        # Cache configuration
        self._enable_write_through = True
        self._enable_read_through = True

        # Statistics
        self._stats = {
            "primary_hits": 0,
            "primary_misses": 0,
            "secondary_hits": 0,
            "secondary_misses": 0,
            "write_operations": 0,
            "read_operations": 0
        }

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback strategy."""
        with self._lock:
            self._stats["read_operations"] += 1

            # Try primary cache first
            value = await self._primary.get(key)
            if value is not None:
                self._stats["primary_hits"] += 1
                return value

            self._stats["primary_misses"] += 1

            # Try secondary cache if available
            if self._secondary:
                value = await self._secondary.get(key)
                if value is not None:
                    self._stats["secondary_hits"] += 1
                    # Populate primary cache for faster future access
                    if self._enable_read_through:
                        await self._primary.set(key, value)
                    return value

                self._stats["secondary_misses"] += 1

            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with write-through strategy."""
        with self._lock:
            self._stats["write_operations"] += 1

            # Write to primary cache
            await self._primary.set(key, value, ttl)

            # Write to secondary cache if enabled
            if self._secondary and self._enable_write_through:
                await self._secondary.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        """Delete value from cache."""
        with self._lock:
            await self._primary.delete(key)
            if self._secondary:
                await self._secondary.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            # Check primary first
            if await self._primary.exists(key):
                return True

            # Check secondary if available
            if self._secondary:
                return await self._secondary.exists(key)

            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            stats = dict(self._stats)

            # Add backend statistics
            primary_stats = asyncio.run(self._primary.get_stats())
            stats["primary_backend"] = primary_stats

            if self._secondary:
                secondary_stats = asyncio.run(self._secondary.get_stats())
                stats["secondary_backend"] = secondary_stats

            return stats

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            asyncio.run(self._primary.clear())
            if self._secondary:
                asyncio.run(self._secondary.clear())

            # Reset statistics
            for key in self._stats:
                self._stats[key] = 0

    def set_write_through(self, enabled: bool) -> None:
        """Enable or disable write-through caching."""
        self._enable_write_through = enabled

    def set_read_through(self, enabled: bool) -> None:
        """Enable or disable read-through caching."""
        self._enable_read_through = enabled

    def create_key(self, *args, **kwargs) -> str:
        """Create a cache key from arguments."""
        # Sort kwargs for consistent key generation
        sorted_kwargs = sorted(kwargs.items())

        # Create key string
        key_parts = [str(arg) for arg in args] + [f"{k}:{v}" for k, v in sorted_kwargs]

        # Hash for consistent length
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


# Convenience functions
def get_cache_key(*args, **kwargs) -> str:
    """Generate a cache key from arguments."""
    return get_cache_manager().create_key(*args, **kwargs)


async def get_cached_value(key: str) -> Optional[Any]:
    """Get value from cache."""
    return await get_cache_manager().get(key)


async def set_cached_value(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Set value in cache."""
    await get_cache_manager().set(key, value, ttl)


async def invalidate_cache(key: str) -> None:
    """Invalidate cache entry."""
    await get_cache_manager().delete(key)
