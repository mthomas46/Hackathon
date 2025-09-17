"""Application Caching Service - Multi-level caching with TTL support."""

import asyncio
import json
import hashlib
from typing import Any, Dict, Optional, List, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import threading
from collections import OrderedDict

from .application_service import ApplicationService, ServiceContext


class CacheEntry:
    """Cache entry with TTL support."""

    def __init__(self, value: Any, ttl_seconds: Optional[int] = None):
        """Initialize cache entry."""
        self.value = value
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl_seconds is None:
            return False

        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    def access(self) -> None:
        """Record access."""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'ttl_seconds': self.ttl_seconds,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        entry = cls(data['value'], data['ttl_seconds'])
        entry.created_at = datetime.fromisoformat(data['created_at'])
        entry.access_count = data.get('access_count', 0)
        entry.last_accessed = datetime.fromisoformat(data['last_accessed'])
        return entry


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from cache."""
        pass

    @abstractmethod
    async def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        pass

    @abstractmethod
    async def size(self) -> int:
        """Get cache size."""
        pass

    @abstractmethod
    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get cache keys."""
        pass


class InMemoryCacheBackend(CacheBackend):
    """In-memory cache backend using LRU eviction."""

    def __init__(self, max_size: int = 1000):
        """Initialize in-memory cache."""
        self.max_size = max_size
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]

                if entry.is_expired():
                    del self.cache[key]
                    return None

                entry.access()
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return entry.value

            return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache."""
        async with self.lock:
            # Remove if exists
            if key in self.cache:
                del self.cache[key]

            # Add new entry
            entry = CacheEntry(value, ttl_seconds)
            self.cache[key] = entry
            self.cache.move_to_end(key)

            # Evict if over capacity
            if len(self.cache) > self.max_size:
                self.cache.popitem(last=False)  # Remove least recently used

    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    async def clear(self) -> None:
        """Clear all values from cache."""
        async with self.lock:
            self.cache.clear()

    async def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if entry.is_expired():
                    del self.cache[key]
                    return False
                return True
            return False

    async def size(self) -> int:
        """Get cache size."""
        async with self.lock:
            # Clean expired entries
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.cache[key]

            return len(self.cache)

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get cache keys."""
        async with self.lock:
            # Clean expired entries
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.cache[key]

            all_keys = list(self.cache.keys())

            if pattern:
                import re
                regex = re.compile(pattern.replace('*', '.*'))
                return [k for k in all_keys if regex.match(k)]

            return all_keys


class RedisCacheBackend(CacheBackend):
    """Redis-based cache backend."""

    def __init__(self, redis_client=None, prefix: str = "cache:"):
        """Initialize Redis cache."""
        self.redis = redis_client
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        """Make Redis key with prefix."""
        return f"{self.prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis."""
        if not self.redis:
            return None

        try:
            redis_key = self._make_key(key)
            data = await self.redis.get(redis_key)

            if data:
                entry_data = json.loads(data)
                entry = CacheEntry.from_dict(entry_data)

                if entry.is_expired():
                    await self.delete(key)
                    return None

                entry.access()
                # Update access info in Redis
                await self.redis.set(redis_key, json.dumps(entry.to_dict()), ex=entry.ttl_seconds)

                return entry.value

        except Exception:
            return None

        return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in Redis."""
        if not self.redis:
            return

        try:
            redis_key = self._make_key(key)
            entry = CacheEntry(value, ttl_seconds)
            data = json.dumps(entry.to_dict())

            if ttl_seconds:
                await self.redis.set(redis_key, data, ex=ttl_seconds)
            else:
                await self.redis.set(redis_key, data)

        except Exception:
            pass  # Fail silently for cache

    async def delete(self, key: str) -> bool:
        """Delete value from Redis."""
        if not self.redis:
            return False

        try:
            redis_key = self._make_key(key)
            result = await self.redis.delete(redis_key)
            return result > 0
        except Exception:
            return False

    async def clear(self) -> None:
        """Clear all values from Redis."""
        if not self.redis:
            return

        try:
            # Use SCAN to find all keys with prefix
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=f"{self.prefix}*")
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            pass

    async def has(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not self.redis:
            return False

        try:
            redis_key = self._make_key(key)
            exists = await self.redis.exists(redis_key)
            if exists:
                # Check if expired
                data = await self.redis.get(redis_key)
                if data:
                    entry_data = json.loads(data)
                    entry = CacheEntry.from_dict(entry_data)
                    if entry.is_expired():
                        await self.delete(key)
                        return False
            return exists > 0
        except Exception:
            return False

    async def size(self) -> int:
        """Get cache size from Redis."""
        if not self.redis:
            return 0

        try:
            # This is approximate since Redis doesn't have a direct size for pattern
            keys = await self.keys()
            return len(keys)
        except Exception:
            return 0

    async def keys(self, pattern: Optional[str] = None) -> List[str]:
        """Get cache keys from Redis."""
        if not self.redis:
            return []

        try:
            search_pattern = f"{self.prefix}*"
            if pattern:
                search_pattern = f"{self.prefix}{pattern}"

            cursor = 0
            all_keys = []

            while True:
                cursor, keys = await self.redis.scan(cursor, match=search_pattern)
                all_keys.extend(keys)
                if cursor == 0:
                    break

            # Remove prefix from keys
            return [key[len(self.prefix):] for key in all_keys]

        except Exception:
            return []


class ApplicationCache:
    """Application cache with multi-level caching support."""

    def __init__(self, backends: List[CacheBackend], default_ttl: int = 300):
        """Initialize application cache."""
        self.backends = backends
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (try all backends)."""
        for backend in self.backends:
            try:
                value = await backend.get(key)
                if value is not None:
                    return value
            except Exception:
                continue  # Try next backend

        return None

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in all backends."""
        ttl = ttl_seconds or self.default_ttl

        for backend in self.backends:
            try:
                await backend.set(key, value, ttl)
            except Exception:
                continue  # Continue with other backends

    async def delete(self, key: str) -> bool:
        """Delete value from all backends."""
        success = False

        for backend in self.backends:
            try:
                if await backend.delete(key):
                    success = True
            except Exception:
                continue

        return success

    async def clear(self) -> None:
        """Clear all backends."""
        for backend in self.backends:
            try:
                await backend.clear()
            except Exception:
                continue

    async def has(self, key: str) -> bool:
        """Check if key exists in any backend."""
        for backend in self.backends:
            try:
                if await backend.has(key):
                    return True
            except Exception:
                continue

        return False

    def make_key(self, *args, **kwargs) -> str:
        """Make cache key from arguments."""
        # Create deterministic key
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))

        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()


class CachingService(ApplicationService):
    """Application caching service with multi-level caching."""

    def __init__(
        self,
        cache_backends: Optional[List[CacheBackend]] = None,
        default_ttl: int = 300,
        cleanup_interval: int = 60
    ):
        """Initialize caching service."""
        super().__init__("caching_service")

        # Initialize cache backends
        if cache_backends is None:
            cache_backends = [InMemoryCacheBackend()]

        self.cache = ApplicationCache(cache_backends, default_ttl)
        self.cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start caching service."""
        await super().start()

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self) -> None:
        """Stop caching service."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        await super().stop()

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of expired cache entries."""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)

                # Cleanup expired entries in memory backends
                for backend in self.cache.backends:
                    if isinstance(backend, InMemoryCacheBackend):
                        # The InMemoryCacheBackend handles cleanup automatically
                        # but we can force a cleanup by checking size
                        size = await backend.size()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cache cleanup: {e}")

    async def get(self, key: str, context: Optional[ServiceContext] = None) -> Optional[Any]:
        """Get value from cache."""
        async with self.operation_context("cache_get", context):
            return await self.cache.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        context: Optional[ServiceContext] = None
    ) -> None:
        """Set value in cache."""
        async with self.operation_context("cache_set", context):
            await self.cache.set(key, value, ttl_seconds)

    async def delete(self, key: str, context: Optional[ServiceContext] = None) -> bool:
        """Delete value from cache."""
        async with self.operation_context("cache_delete", context):
            return await self.cache.delete(key)

    async def clear(self, context: Optional[ServiceContext] = None) -> None:
        """Clear all cache entries."""
        async with self.operation_context("cache_clear", context):
            await self.cache.clear()

    async def cached_operation(
        self,
        operation_key: str,
        operation_func: callable,
        ttl_seconds: Optional[int] = None,
        force_refresh: bool = False,
        context: Optional[ServiceContext] = None
    ) -> Any:
        """Execute operation with caching."""
        # Try to get from cache first
        if not force_refresh:
            cached_result = await self.get(operation_key, context)
            if cached_result is not None:
                self.logger.debug(f"Cache hit for operation: {operation_key}")
                return cached_result

        # Execute operation
        self.logger.debug(f"Cache miss for operation: {operation_key}")
        result = await operation_func()

        # Cache result
        if result is not None:
            await self.set(operation_key, result, ttl_seconds, context)

        return result

    def make_cache_key(self, *args, **kwargs) -> str:
        """Make cache key from arguments."""
        return self.cache.make_key(*args, **kwargs)

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'backends': len(self.cache.backends),
            'default_ttl': self.cache.default_ttl
        }

        for i, backend in enumerate(self.cache.backends):
            try:
                backend_stats = {
                    'type': backend.__class__.__name__,
                    'size': await backend.size()
                }

                if hasattr(backend, 'max_size'):
                    backend_stats['max_size'] = backend.max_size
                    backend_stats['utilization'] = backend_stats['size'] / backend.max_size

                stats[f'backend_{i}'] = backend_stats

            except Exception as e:
                stats[f'backend_{i}'] = {'error': str(e)}

        return stats

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = await super().health_check()

        # Add cache-specific health info
        try:
            cache_stats = await self.get_cache_stats()
            health['cache'] = cache_stats

            # Test cache operations
            test_key = f"health_check_{int(asyncio.get_event_loop().time())}"
            await self.cache.set(test_key, "test_value", ttl_seconds=10)
            test_value = await self.cache.get(test_key)
            await self.cache.delete(test_key)

            health['cache']['test_result'] = test_value == "test_value"

        except Exception as e:
            health['cache'] = {'error': str(e)}

        return health


# Global caching service instance
caching_service = CachingService()

# Create application cache instance
app_cache = caching_service.cache
