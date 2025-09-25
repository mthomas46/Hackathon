"""Cache Manager Core - Main cache management functionality."""

import asyncio
import hashlib
import pickle  # nosec: Required for controlled cache serialization
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TypeVar

from ...di.services import ICacheService, ILoggerService
from ...logging.logger import get_logger
from .cache_backend import CacheBackend
from .memory_cache import MemoryCache
from .redis_cache import RedisCache

T = TypeVar("T")


class CacheManager(ICacheService):
    """Advanced cache manager with multiple backends and strategies."""

    def __init__(
        self,
        primary_backend: Optional[CacheBackend] = None,
        secondary_backend: Optional[CacheBackend] = None,
        logger: Optional[ILoggerService] = None,
    ) -> None:
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
            "read_operations": 0,
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
        return hashlib.sha256(key_string.encode()).hexdigest()


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
