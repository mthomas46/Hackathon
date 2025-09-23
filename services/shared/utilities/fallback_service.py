"""Comprehensive Fallback Service for graceful degradation and service resilience.

Provides multiple layers of fallback mechanisms:
- External API fallbacks with circuit breaker integration
- Database failover and read-only mode fallbacks
- Cache-based data fallbacks for frequently accessed data
- Service degradation strategies with feature toggles
- Stale-while-revalidate patterns for improved user experience
"""

import asyncio
import hashlib
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)
T = TypeVar("T")


class FallbackStrategy(Enum):
    """Strategies for fallback behavior."""

    CACHE_FIRST = "cache_first"  # Try cache first, fallback to source
    SOURCE_FIRST = "source_first"  # Try source first, fallback to cache
    STALE_WHILE_REVALIDATE = "stale_while_revalidate"  # Serve stale data while refreshing
    DEGRADED_MODE = "degraded_mode"  # Limited functionality mode
    STATIC_FALLBACK = "static_fallback"  # Return static/default data


class FallbackPriority(Enum):
    """Priority levels for fallback execution."""

    CRITICAL = 1  # Must work, system breaking without it
    HIGH = 2  # Important but system can limp along
    MEDIUM = 3  # Nice to have, degrades user experience
    LOW = 4  # Optional, purely for enhancement


@dataclass
class FallbackResult:
    """Result of a fallback operation."""

    success: bool
    data: Any = None
    source: str = "unknown"  # cache, primary, secondary, static
    timestamp: float = field(default_factory=time.time)
    ttl_seconds: Optional[float] = None
    degraded: bool = False
    error: Optional[str] = None


@dataclass
class CacheEntry:
    """Cache entry with metadata."""

    data: Any
    timestamp: float
    ttl_seconds: float
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    etag: Optional[str] = None


class CacheFallback:
    """Cache-based fallback for data persistence."""

    def __init__(self, max_size: int = 1000, default_ttl: float = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Get data from cache if available and not expired."""
        with self._lock:
            entry = self._cache.get(key)
            if entry and not self._is_expired(entry):
                entry.access_count += 1
                entry.last_accessed = time.time()
                return entry.data
            elif entry and self._is_expired(entry):
                # Remove expired entry
                del self._cache[key]
        return None

    def set(self, key: str, data: Any, ttl_seconds: Optional[float] = None, etag: Optional[str] = None) -> None:
        """Store data in cache."""
        with self._lock:
            # Evict if at capacity (simple LRU-like eviction)
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            ttl = ttl_seconds or self.default_ttl
            entry = CacheEntry(data=data, timestamp=time.time(), ttl_seconds=ttl, etag=etag)
            self._cache[key] = entry

    def invalidate(self, key: str) -> bool:
        """Invalidate a cache entry."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
        return False

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if self._is_expired(entry))
            total_accesses = sum(entry.access_count for entry in self._cache.values())

            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries,
                "total_accesses": total_accesses,
                "hit_rate": total_accesses / max(1, sum(entry.access_count + 1 for entry in self._cache.values())),
            }

    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        return time.time() - entry.timestamp > entry.ttl_seconds

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find entry with oldest last_accessed time
        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].last_accessed)
        del self._cache[oldest_key]


class ServiceFallback:
    """Fallback configuration for a specific service or operation."""

    def __init__(
        self,
        name: str,
        primary_func: Callable[[], Awaitable[T]],
        fallback_funcs: List[Callable[[], Awaitable[T]]],
        strategy: FallbackStrategy = FallbackStrategy.SOURCE_FIRST,
        priority: FallbackPriority = FallbackPriority.MEDIUM,
        cache_fallback: Optional[CacheFallback] = None,
        cache_key_func: Optional[Callable[[], str]] = None,
    ):
        self.name = name
        self.primary_func = primary_func
        self.fallback_funcs = fallback_funcs
        self.strategy = strategy
        self.priority = priority
        self.cache_fallback = cache_fallback
        self.cache_key_func = cache_key_func or (lambda: f"fallback:{name}")

    async def execute(self) -> FallbackResult:
        """Execute with fallback logic."""
        start_time = time.time()

        if self.strategy == FallbackStrategy.CACHE_FIRST:
            return await self._cache_first_fallback()
        elif self.strategy == FallbackStrategy.STALE_WHILE_REVALIDATE:
            return await self._stale_while_revalidate()
        else:  # SOURCE_FIRST or other strategies
            return await self._source_first_fallback()

    async def _cache_first_fallback(self) -> FallbackResult:
        """Try cache first, then fallbacks."""
        cache_key = self.cache_key_func()

        # Try cache first
        if self.cache_fallback:
            cached_data = self.cache_fallback.get(cache_key)
            if cached_data is not None:
                return FallbackResult(success=True, data=cached_data, source="cache", degraded=False)

        # Cache miss, try primary then fallbacks
        return await self._try_sources(cache_key)

    async def _source_first_fallback(self) -> FallbackResult:
        """Try primary first, then fallbacks."""
        cache_key = self.cache_key_func() if self.cache_fallback else None
        return await self._try_sources(cache_key)

    async def _stale_while_revalidate(self) -> FallbackResult:
        """Serve stale data while revalidating in background."""
        cache_key = self.cache_key_func()

        # Get stale data
        stale_data = None
        if self.cache_fallback:
            stale_data = self.cache_fallback.get(cache_key)

        # Start background revalidation
        asyncio.create_task(self._background_revalidate(cache_key))

        # Return stale data if available
        if stale_data is not None:
            return FallbackResult(success=True, data=stale_data, source="cache_stale", degraded=True)

        # No stale data, try sources
        return await self._try_sources(cache_key)

    async def _try_sources(self, cache_key: Optional[str] = None) -> FallbackResult:
        """Try primary source then fallbacks."""
        sources = [self.primary_func] + self.fallback_funcs

        for i, source_func in enumerate(sources):
            try:
                data = await source_func()
                source_type = "primary" if i == 0 else f"fallback_{i}"

                # Cache successful result if cache is available
                if cache_key and self.cache_fallback and i == 0:  # Only cache primary results
                    self.cache_fallback.set(cache_key, data)

                return FallbackResult(
                    success=True, data=data, source=source_type, degraded=i > 0  # Any fallback is considered degraded
                )

            except Exception as e:
                error_msg = f"{source_func.__name__ if hasattr(source_func, '__name__') else f'source_{i}'}: {str(e)}"
                logger.warning(f"Fallback source failed for {self.name}: {error_msg}")

                # Continue to next source
                continue

        # All sources failed
        return FallbackResult(success=False, error="All fallback sources failed", degraded=True)

    async def _background_revalidate(self, cache_key: str) -> None:
        """Background revalidation for stale-while-revalidate."""
        try:
            # Try to refresh cache
            result = await self._try_sources(cache_key)
            if result.success and self.cache_fallback:
                # Update cache with fresh data
                self.cache_fallback.set(cache_key, result.data)
                logger.debug(f"Background revalidation successful for {self.name}")
        except Exception as e:
            logger.error(f"Background revalidation failed for {self.name}: {e}")


class DegradationStrategy:
    """Strategy for graceful service degradation."""

    def __init__(self, name: str):
        self.name = name
        self._features: Dict[str, bool] = {}
        self._degradation_levels: Dict[str, List[str]] = {}
        self._current_level: str = "normal"

    def add_feature_toggle(self, feature: str, enabled: bool = True) -> None:
        """Add a feature that can be toggled during degradation."""
        self._features[feature] = enabled

    def add_degradation_level(self, level: str, disabled_features: List[str]) -> None:
        """Add a degradation level with features to disable."""
        self._degradation_levels[level] = disabled_features

    def set_degradation_level(self, level: str) -> None:
        """Set the current degradation level."""
        if level not in self._degradation_levels:
            logger.warning(f"Unknown degradation level: {level}")
            return

        self._current_level = level

        # Disable features for this level
        for feature in self._degradation_levels[level]:
            self._features[feature] = False

        logger.info(f"Service {self.name} degraded to level: {level}")

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is currently enabled."""
        return self._features.get(feature, True)

    def get_status(self) -> Dict[str, Any]:
        """Get current degradation status."""
        return {
            "current_level": self._current_level,
            "features": dict(self._features),
            "available_levels": list(self._degradation_levels.keys()),
        }


class FallbackService:
    """Centralized fallback service for the ecosystem."""

    def __init__(self):
        self._fallbacks: Dict[str, ServiceFallback] = {}
        self._degradation_strategies: Dict[str, DegradationStrategy] = {}
        self._global_cache = CacheFallback(max_size=5000, default_ttl=600)  # 10 minutes default
        self._alert_callbacks: List[Callable[[str, str, Dict[str, Any]], None]] = []

    def register_fallback(
        self,
        name: str,
        primary_func: Callable[[], Awaitable[T]],
        fallback_funcs: List[Callable[[], Awaitable[T]]],
        strategy: FallbackStrategy = FallbackStrategy.SOURCE_FIRST,
        priority: FallbackPriority = FallbackPriority.MEDIUM,
        use_global_cache: bool = True,
    ) -> None:
        """Register a fallback configuration."""
        cache = self._global_cache if use_global_cache else CacheFallback()
        cache_key_func = lambda: f"fallback:{name}"

        fallback = ServiceFallback(
            name=name,
            primary_func=primary_func,
            fallback_funcs=fallback_funcs,
            strategy=strategy,
            priority=priority,
            cache_fallback=cache,
            cache_key_func=cache_key_func,
        )

        self._fallbacks[name] = fallback
        logger.info(f"Registered fallback: {name} with strategy {strategy.value}")

    def register_degradation_strategy(self, service_name: str) -> DegradationStrategy:
        """Register a degradation strategy for a service."""
        if service_name not in self._degradation_strategies:
            self._degradation_strategies[service_name] = DegradationStrategy(service_name)

        return self._degradation_strategies[service_name]

    async def execute_with_fallback(self, name: str) -> FallbackResult:
        """Execute a registered fallback."""
        if name not in self._fallbacks:
            return FallbackResult(success=False, error=f"Fallback '{name}' not registered")

        try:
            result = await self._fallbacks[name].execute()

            # Alert on fallback usage
            if result.degraded:
                await self._trigger_alert(
                    "degraded_fallback", {"fallback_name": name, "source": result.source, "error": result.error}
                )

            return result

        except Exception as e:
            logger.error(f"Fallback execution failed for {name}: {e}")
            return FallbackResult(success=False, error=str(e))

    def invalidate_cache(self, fallback_name: Optional[str] = None, key: Optional[str] = None) -> None:
        """Invalidate cache entries."""
        if fallback_name and fallback_name in self._fallbacks:
            cache_key = self._fallbacks[fallback_name].cache_key_func()
            if self._fallbacks[fallback_name].cache_fallback:
                self._fallbacks[fallback_name].cache_fallback.invalidate(cache_key)
        elif key:
            self._global_cache.invalidate(key)
        else:
            # Clear all caches
            self._global_cache.clear()
            for fallback in self._fallbacks.values():
                if fallback.cache_fallback:
                    fallback.cache_fallback.clear()

    def set_degradation_level(self, service_name: str, level: str) -> None:
        """Set degradation level for a service."""
        if service_name in self._degradation_strategies:
            self._degradation_strategies[service_name].set_degradation_level(level)
        else:
            logger.warning(f"No degradation strategy registered for {service_name}")

    def is_feature_enabled(self, service_name: str, feature: str) -> bool:
        """Check if a feature is enabled for a service."""
        strategy = self._degradation_strategies.get(service_name)
        if strategy:
            return strategy.is_feature_enabled(feature)
        return True  # Default to enabled if no strategy

    def add_alert_callback(self, callback: Callable[[str, str, Dict[str, Any]], None]) -> None:
        """Add callback for fallback alerts."""
        self._alert_callbacks.append(callback)

    async def _trigger_alert(self, alert_type: str, data: Dict[str, Any]) -> None:
        """Trigger alert callbacks."""
        for callback in self._alert_callbacks:
            try:
                await callback(alert_type, self.__class__.__name__, data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def get_fallback_stats(self) -> Dict[str, Any]:
        """Get fallback statistics."""
        stats = {
            "total_fallbacks": len(self._fallbacks),
            "cache_stats": self._global_cache.get_stats(),
            "degradation_strategies": len(self._degradation_strategies),
        }

        # Add per-fallback stats
        fallback_stats = {}
        for name, fallback in self._fallbacks.items():
            cache_stats = {}
            if fallback.cache_fallback:
                cache_stats = fallback.cache_fallback.get_stats()

            fallback_stats[name] = {
                "strategy": fallback.strategy.value,
                "priority": fallback.priority.value,
                "fallback_count": len(fallback.fallback_funcs),
                "cache_stats": cache_stats,
            }

        stats["fallbacks"] = fallback_stats
        return stats

    def get_degradation_status(self) -> Dict[str, Any]:
        """Get degradation status for all services."""
        return {service_name: strategy.get_status() for service_name, strategy in self._degradation_strategies.items()}


# Global instance
_fallback_service: Optional[FallbackService] = None


def get_fallback_service() -> FallbackService:
    """Get the global fallback service instance."""
    global _fallback_service
    if _fallback_service is None:
        _fallback_service = FallbackService()
    return _fallback_service


# Convenience functions
async def execute_with_fallback(name: str) -> FallbackResult:
    """Convenience function to execute fallback."""
    service = get_fallback_service()
    return await service.execute_with_fallback(name)


def register_fallback(
    name: str,
    primary_func: Callable[[], Awaitable[T]],
    fallback_funcs: List[Callable[[], Awaitable[T]]],
    strategy: FallbackStrategy = FallbackStrategy.SOURCE_FIRST,
    priority: FallbackPriority = FallbackPriority.MEDIUM,
) -> None:
    """Convenience function to register fallback."""
    service = get_fallback_service()
    service.register_fallback(name, primary_func, fallback_funcs, strategy, priority)


def set_service_degradation(service_name: str, level: str) -> None:
    """Convenience function to set service degradation level."""
    service = get_fallback_service()
    service.set_degradation_level(service_name, level)
