#!/usr/bin/env python3
"""
Intelligent Caching Framework

This module provides enterprise-grade caching capabilities with intelligent
invalidation, performance monitoring, and workflow-aware optimization.
"""

import asyncio
import hashlib
import json
import time
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import OrderedDict
import psutil
import os

from ..core.constants_new import ServiceNames
from ..monitoring.logging import fire_and_forget


class CacheStrategy(Enum):
    """Cache strategies for different use cases."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    SIZE_BASED = "size_based"  # Size-based eviction
    WORKFLOW_AWARE = "workflow_aware"  # Workflow-specific caching


class CachePriority(Enum):
    """Cache priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    priority: CachePriority = CachePriority.MEDIUM
    workflow_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    ttl_seconds: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    evictions: int = 0
    invalidations: int = 0
    average_response_time: float = 0.0
    memory_usage_bytes: int = 0
    cache_size_items: int = 0
    hit_ratio: float = 0.0


class IntelligentCache:
    """Intelligent caching system with multiple strategies."""

    def __init__(self, service_name: str, max_size_mb: int = 100, default_ttl_hours: int = 24):
        self.service_name = service_name
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_hours * 3600

        # Cache storage
        self.cache: Dict[str, CacheEntry] = {}
        self.lru_order: OrderedDict[str, None] = OrderedDict()
        self.lfu_count: Dict[str, int] = {}

        # Metrics and monitoring
        self.metrics = CacheMetrics()
        self.performance_history: List[Dict[str, Any]] = []
        self.workflow_caches: Dict[str, Dict[str, CacheEntry]] = {}

        # Configuration
        self.eviction_threshold = 0.8  # Evict when 80% full
        self.cleanup_interval = 300  # Cleanup every 5 minutes
        self.metrics_interval = 60  # Update metrics every minute

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None
        self._memory_monitor_task: Optional[asyncio.Task] = None

        # Threading lock for thread safety
        self._lock = threading.RLock()

        # Start background tasks
        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self._periodic_cleanup())
            loop.create_task(self._periodic_metrics_update())
            loop.create_task(self._memory_monitor())
        else:
            # Create new event loop for background tasks
            def start_tasks():
                asyncio.set_event_loop(asyncio.new_event_loop())
                loop = asyncio.get_event_loop()
                loop.create_task(self._periodic_cleanup())
                loop.create_task(self._periodic_metrics_update())
                loop.create_task(self._memory_monitor())
                loop.run_forever()

            thread = threading.Thread(target=start_tasks, daemon=True)
            thread.start()

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None,
                 priority: CachePriority = CachePriority.MEDIUM,
                 workflow_id: Optional[str] = None,
                 dependencies: Optional[List[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set a cache entry with intelligent metadata."""
        with self._lock:
            try:
                start_time = time.time()

                # Calculate entry size
                size_bytes = self._calculate_size(value)

                # Check if we need to evict before adding
                if self._get_total_size() + size_bytes > self.max_size_bytes:
                    await self._evict_entries(size_bytes)

                # Create cache entry
                entry = CacheEntry(
                    key=key,
                    value=value,
                    size_bytes=size_bytes,
                    priority=priority,
                    workflow_id=workflow_id,
                    dependencies=dependencies or [],
                    ttl_seconds=ttl_seconds or self.default_ttl_seconds,
                    metadata=metadata or {}
                )

                # Store in main cache
                self.cache[key] = entry

                # Update workflow-specific cache
                if workflow_id:
                    if workflow_id not in self.workflow_caches:
                        self.workflow_caches[workflow_id] = {}
                    self.workflow_caches[workflow_id][key] = entry

                # Update LRU order
                self._update_lru(key)

                # Update metrics
                self.metrics.cache_size_items = len(self.cache)
                self.metrics.memory_usage_bytes = self._get_total_size()

                response_time = time.time() - start_time
                self._update_response_time(response_time)

                return True

            except Exception as e:
                fire_and_forget("error", f"Cache set failed for key {key}: {e}", self.service_name)
                return False

    async def get(self, key: str, workflow_id: Optional[str] = None) -> Optional[Any]:
        """Get a cache entry with intelligent access tracking."""
        with self._lock:
            try:
                start_time = time.time()
                self.metrics.total_requests += 1

                # Try main cache first
                entry = self.cache.get(key)

                # If not found and workflow specified, try workflow cache
                if not entry and workflow_id and workflow_id in self.workflow_caches:
                    entry = self.workflow_caches[workflow_id].get(key)

                if not entry:
                    self.metrics.cache_misses += 1
                    response_time = time.time() - start_time
                    self._update_response_time(response_time)
                    return None

                # Check TTL
                if entry.ttl_seconds and (datetime.now() - entry.timestamp).seconds > entry.ttl_seconds:
                    await self.invalidate(key)
                    self.metrics.cache_misses += 1
                    response_time = time.time() - start_time
                    self._update_response_time(response_time)
                    return None

                # Update access metadata
                entry.access_count += 1
                entry.last_accessed = datetime.now()

                # Update LRU order
                self._update_lru(key)

                # Update LFU count
                self.lfu_count[key] = self.lfu_count.get(key, 0) + 1

                self.metrics.cache_hits += 1
                response_time = time.time() - start_time
                self._update_response_time(response_time)

                return entry.value

            except Exception as e:
                fire_and_forget("error", f"Cache get failed for key {key}: {e}", self.service_name)
                return None

    async def invalidate(self, key: str, cascade: bool = True) -> bool:
        """Invalidate a cache entry with optional cascade invalidation."""
        with self._lock:
            try:
                if key in self.cache:
                    entry = self.cache[key]

                    # Cascade invalidation - invalidate dependencies
                    if cascade and entry.dependencies:
                        for dep_key in entry.dependencies:
                            await self.invalidate(dep_key, cascade=False)

                    # Remove from main cache
                    del self.cache[key]

                    # Remove from workflow caches
                    for workflow_cache in self.workflow_caches.values():
                        workflow_cache.pop(key, None)

                    # Clean up empty workflow caches
                    self.workflow_caches = {wid: cache for wid, cache in self.workflow_caches.items()
                                          if cache}

                    # Update LRU and LFU tracking
                    self.lru_order.pop(key, None)
                    self.lfu_count.pop(key, None)

                    self.metrics.invalidations += 1
                    self.metrics.cache_size_items = len(self.cache)

                    return True

                return False

            except Exception as e:
                fire_and_forget("error", f"Cache invalidation failed for key {key}: {e}", self.service_name)
                return False

    async def invalidate_workflow(self, workflow_id: str) -> int:
        """Invalidate all entries for a specific workflow."""
        with self._lock:
            if workflow_id not in self.workflow_caches:
                return 0

            workflow_cache = self.workflow_caches[workflow_id]
            invalidated_count = 0

            for key in list(workflow_cache.keys()):
                if await self.invalidate(key, cascade=False):
                    invalidated_count += 1

            # Remove workflow cache entry
            del self.workflow_caches[workflow_id]

            return invalidated_count

    async def get_or_set(self, key: str, fetch_func: Callable[[], Any],
                        ttl_seconds: Optional[int] = None,
                        workflow_id: Optional[str] = None) -> Any:
        """Get from cache or set with fetch function."""
        # Try to get from cache first
        cached_value = await self.get(key, workflow_id)
        if cached_value is not None:
            return cached_value

        # Fetch new value
        try:
            value = await fetch_func()
            await self.set(key, value, ttl_seconds, workflow_id=workflow_id)
            return value
        except Exception as e:
            fire_and_forget("error", f"Fetch function failed for key {key}: {e}", self.service_name)
            raise e

    def _update_lru(self, key: str):
        """Update LRU order for a key."""
        self.lru_order.move_to_end(key)

    def _calculate_size(self, value: Any) -> int:
        """Calculate the size of a value in bytes."""
        try:
            if isinstance(value, (str, bytes)):
                return len(value.encode('utf-8') if isinstance(value, str) else value)
            elif isinstance(value, dict):
                return len(json.dumps(value).encode('utf-8'))
            elif isinstance(value, list):
                return sum(self._calculate_size(item) for item in value)
            else:
                # Estimate size for other types
                return len(str(value).encode('utf-8'))
        except:
            return 1024  # Default estimate

    def _get_total_size(self) -> int:
        """Get total size of all cache entries."""
        return sum(entry.size_bytes for entry in self.cache.values())

    async def _evict_entries(self, required_space: int):
        """Evict entries to make space for new entry."""
        target_size = self.max_size_bytes - required_space

        # LRU eviction as primary strategy
        while self._get_total_size() > target_size and self.cache:
            # Evict least recently used
            lru_key, _ = self.lru_order.popitem(last=False)
            if lru_key in self.cache:
                entry = self.cache[lru_key]
                del self.cache[lru_key]
                self.lfu_count.pop(lru_key, None)

                # Remove from workflow caches
                for workflow_cache in self.workflow_caches.values():
                    workflow_cache.pop(lru_key, None)

                self.metrics.evictions += 1

    def _update_response_time(self, response_time: float):
        """Update average response time."""
        if self.metrics.total_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            # Weighted average
            weight = 0.1
            self.metrics.average_response_time = (
                self.metrics.average_response_time * (1 - weight) +
                response_time * weight
            )

    async def _periodic_cleanup(self):
        """Periodic cleanup of expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                with self._lock:
                    expired_keys = []
                    current_time = datetime.now()

                    for key, entry in self.cache.items():
                        if entry.ttl_seconds and (current_time - entry.timestamp).seconds > entry.ttl_seconds:
                            expired_keys.append(key)

                    # Remove expired entries
                    for key in expired_keys:
                        await self.invalidate(key, cascade=False)

                    if expired_keys:
                        fire_and_forget("info", f"Cleaned up {len(expired_keys)} expired cache entries", self.service_name)

            except Exception as e:
                fire_and_forget("error", f"Periodic cleanup failed: {e}", self.service_name)

    async def _periodic_metrics_update(self):
        """Periodic metrics update."""
        while True:
            try:
                await asyncio.sleep(self.metrics_interval)

                with self._lock:
                    # Calculate hit ratio
                    if self.metrics.total_requests > 0:
                        self.metrics.hit_ratio = self.metrics.cache_hits / self.metrics.total_requests

                    # Store metrics history
                    metrics_snapshot = {
                        "timestamp": datetime.now().isoformat(),
                        "total_requests": self.metrics.total_requests,
                        "cache_hits": self.metrics.cache_hits,
                        "cache_misses": self.metrics.cache_misses,
                        "hit_ratio": self.metrics.hit_ratio,
                        "evictions": self.metrics.evictions,
                        "invalidations": self.metrics.invalidations,
                        "memory_usage_mb": self.metrics.memory_usage_bytes / (1024 * 1024),
                        "cache_size_items": self.metrics.cache_size_items
                    }

                    self.performance_history.append(metrics_snapshot)

                    # Maintain history limit
                    if len(self.performance_history) > 1000:
                        self.performance_history = self.performance_history[-1000:]

            except Exception as e:
                fire_and_forget("error", f"Metrics update failed: {e}", self.service_name)

    async def _memory_monitor(self):
        """Monitor system memory usage."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                memory = psutil.virtual_memory()
                memory_usage_percent = memory.percent

                # If system memory is high, be more aggressive with cache eviction
                if memory_usage_percent > 85:
                    # Reduce cache size
                    target_size = int(self.max_size_bytes * 0.7)  # Reduce to 70%
                    if self._get_total_size() > target_size:
                        await self._evict_entries(self._get_total_size() - target_size)

                    fire_and_forget("warning", f"High memory usage ({memory_usage_percent}%), reduced cache size", self.service_name)

            except Exception as e:
                fire_and_forget("error", f"Memory monitor failed: {e}", self.service_name)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            total_size = self._get_total_size()

            return {
                "service_name": self.service_name,
                "cache_size_items": len(self.cache),
                "total_size_mb": total_size / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "utilization_percent": (total_size / self.max_size_bytes) * 100 if self.max_size_bytes > 0 else 0,
                "workflow_caches_count": len(self.workflow_caches),
                "performance": {
                    "total_requests": self.metrics.total_requests,
                    "cache_hits": self.metrics.cache_hits,
                    "cache_misses": self.metrics.cache_misses,
                    "hit_ratio": self.metrics.hit_ratio,
                    "average_response_time_ms": self.metrics.average_response_time * 1000,
                    "evictions": self.metrics.evictions,
                    "invalidations": self.metrics.invalidations
                },
                "memory_info": {
                    "system_memory_percent": psutil.virtual_memory().percent,
                    "process_memory_mb": psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
                },
                "recent_performance": self.performance_history[-10:] if self.performance_history else []
            }

    def get_workflow_cache_info(self, workflow_id: str) -> Dict[str, Any]:
        """Get information about a specific workflow's cache."""
        with self._lock:
            if workflow_id not in self.workflow_caches:
                return {"workflow_id": workflow_id, "exists": False}

            workflow_cache = self.workflow_caches[workflow_id]
            total_size = sum(entry.size_bytes for entry in workflow_cache.values())

            return {
                "workflow_id": workflow_id,
                "exists": True,
                "entries_count": len(workflow_cache),
                "total_size_mb": total_size / (1024 * 1024),
                "entries": [
                    {
                        "key": entry.key,
                        "size_bytes": entry.size_bytes,
                        "access_count": entry.access_count,
                        "last_accessed": entry.last_accessed.isoformat()
                    }
                    for entry in workflow_cache.values()
                ]
            }

    async def optimize_for_workflow(self, workflow_id: str, priority_keys: List[str]):
        """Optimize cache for a specific workflow."""
        with self._lock:
            # Increase priority for workflow-specific entries
            if workflow_id in self.workflow_caches:
                for key in priority_keys:
                    if key in self.cache:
                        self.cache[key].priority = CachePriority.HIGH
                        if workflow_id in self.workflow_caches and key in self.workflow_caches[workflow_id]:
                            self.workflow_caches[workflow_id][key].priority = CachePriority.HIGH

            fire_and_forget("info", f"Optimized cache for workflow {workflow_id} with {len(priority_keys)} priority keys", self.service_name)

    async def warmup_cache(self, warmup_data: Dict[str, Any]):
        """Warm up cache with predefined data."""
        with self._lock:
            for key, value in warmup_data.items():
                await self.set(key, value, priority=CachePriority.HIGH)

            fire_and_forget("info", f"Warmed up cache with {len(warmup_data)} entries", self.service_name)

    def shutdown(self):
        """Shutdown cache and cleanup resources."""
        # Cancel background tasks
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        if self._metrics_task and not self._metrics_task.done():
            self._metrics_task.cancel()
        if self._memory_monitor_task and not self._memory_monitor_task.done():
            self._memory_monitor_task.cancel()

        # Clear cache
        self.cache.clear()
        self.workflow_caches.clear()
        self.lru_order.clear()
        self.lfu_count.clear()


# Global cache instances for different services
service_caches: Dict[str, IntelligentCache] = {}


def get_service_cache(service_name: str) -> IntelligentCache:
    """Get or create cache instance for a service."""
    if service_name not in service_caches:
        # Configure cache based on service type
        cache_configs = {
            ServiceNames.DOC_STORE: {"max_size_mb": 200, "default_ttl_hours": 48},
            ServiceNames.PROMPT_STORE: {"max_size_mb": 150, "default_ttl_hours": 24},
            ServiceNames.ANALYSIS_SERVICE: {"max_size_mb": 100, "default_ttl_hours": 12},
            ServiceNames.INTERPRETER: {"max_size_mb": 80, "default_ttl_hours": 6},
            ServiceNames.SUMMARIZER_HUB: {"max_size_mb": 120, "default_ttl_hours": 24},
            ServiceNames.SOURCE_AGENT: {"max_size_mb": 150, "default_ttl_hours": 48},
            ServiceNames.DISCOVERY_AGENT: {"max_size_mb": 50, "default_ttl_hours": 12},
        }

        config = cache_configs.get(service_name, {"max_size_mb": 100, "default_ttl_hours": 24})
        service_caches[service_name] = IntelligentCache(service_name, **config)

    return service_caches[service_name]


def get_cache_metrics() -> Dict[str, Any]:
    """Get metrics for all service caches."""
    return {
        service_name: cache.get_cache_stats()
        for service_name, cache in service_caches.items()
    }


async def invalidate_all_caches(workflow_id: Optional[str] = None):
    """Invalidate all caches or caches for a specific workflow."""
    for cache in service_caches.values():
        if workflow_id:
            await cache.invalidate_workflow(workflow_id)
        else:
            # Clear all entries
            for key in list(cache.cache.keys()):
                await cache.invalidate(key, cascade=False)


def shutdown_all_caches():
    """Shutdown all cache instances."""
    for cache in service_caches.values():
        cache.shutdown()
    service_caches.clear()
