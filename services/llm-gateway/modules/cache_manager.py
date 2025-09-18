"""Cache Manager Module for LLM Gateway Service.

Provides intelligent caching for LLM responses to improve performance and reduce costs.
Supports TTL-based expiration, pattern-based cache clearing, and cache analytics.
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional, List
import asyncio

from services.shared.config import get_config_value
from services.shared.logging import fire_and_forget
from services.shared.constants_new import ServiceNames


class CacheEntry:
    """Represents a cached response entry."""

    def __init__(self, key: str, response: str, ttl: int = 3600):
        self.key = key
        self.response = response
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = time.time()

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl

    def get_remaining_ttl(self) -> int:
        """Get remaining TTL in seconds."""
        elapsed = time.time() - self.created_at
        return max(0, int(self.ttl - elapsed))

    def access(self):
        """Mark entry as accessed."""
        self.access_count += 1
        self.last_accessed = time.time()


class CacheManager:
    """Intelligent cache manager for LLM responses."""

    def __init__(self):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = int(get_config_value("CACHE_MAX_SIZE", "1000", section="cache"))
        self.default_ttl = int(get_config_value("CACHE_DEFAULT_TTL", "3600", section="cache"))
        self.cleanup_interval = int(get_config_value("CACHE_CLEANUP_INTERVAL", "300", section="cache"))

        # Start background cleanup task if event loop is available
        try:
            asyncio.get_running_loop()
            asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No event loop running (e.g., in tests), skip background task
            pass

    def generate_cache_key(self, request) -> str:
        """Generate a unique cache key for the request."""
        # Handle both dict and object inputs
        if isinstance(request, dict):
            key_components = {
                "prompt": request.get('prompt', ''),
                "provider": request.get('provider', ''),
                "model": request.get('model', ''),
                "context": request.get('context', ''),
                "temperature": request.get('temperature', 0.7),
                "max_tokens": request.get('max_tokens', 1024)
            }
        else:
            # Handle object inputs
            key_components = {
                "prompt": getattr(request, 'prompt', ''),
                "provider": getattr(request, 'provider', ''),
                "model": getattr(request, 'model', ''),
                "context": getattr(request, 'context', ''),
                "temperature": getattr(request, 'temperature', 0.7),
                "max_tokens": getattr(request, 'max_tokens', 1024)
            }

        # Create a stable hash
        key_string = json.dumps(key_components, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()

    async def get_cached_response(self, key: str) -> Optional[str]:
        """Retrieve cached response if available and not expired."""
        if key not in self.cache:
            return None

        entry = self.cache[key]

        if entry.is_expired():
            # Remove expired entry
            del self.cache[key]
            return None

        # Mark as accessed
        entry.access()

        fire_and_forget(
            "llm_gateway_cache_hit",
            f"Cache hit for key: {key[:8]}...",
            ServiceNames.LLM_GATEWAY,
            {
                "cache_key_prefix": key[:8],
                "access_count": entry.access_count,
                "age_seconds": int(time.time() - entry.created_at)
            }
        )

        return entry.response

    async def cache_response(self, key: str, response: str, ttl: Optional[int] = None):
        """Cache a response."""
        if ttl is None:
            ttl = self.default_ttl

        # Check cache size limit
        if len(self.cache) >= self.max_size:
            await self._evict_oldest()

        entry = CacheEntry(key, response, ttl)
        self.cache[key] = entry

        fire_and_for_get(
            "llm_gateway_cache_store",
            f"Cached response for key: {key[:8]}...",
            ServiceNames.LLM_GATEWAY,
            {
                "cache_key_prefix": key[:8],
                "response_length": len(response),
                "ttl_seconds": ttl
            }
        )

    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries, optionally matching a pattern."""
        if pattern is None:
            # Clear all cache
            cleared_count = len(self.cache)
            self.cache.clear()

            fire_and_forget(
                "llm_gateway_cache_cleared_all",
                f"Cleared all cache entries: {cleared_count}",
                ServiceNames.LLM_GATEWAY,
                {"cleared_count": cleared_count}
            )

            return cleared_count

        else:
            # Clear entries matching pattern
            keys_to_remove = []
            for key in self.cache.keys():
                if pattern in key:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.cache[key]

            cleared_count = len(keys_to_remove)

            fire_and_forget(
                "llm_gateway_cache_cleared_pattern",
                f"Cleared cache entries matching '{pattern}': {cleared_count}",
                ServiceNames.LLM_GATEWAY,
                {
                    "pattern": pattern,
                    "cleared_count": cleared_count
                }
            )

            return cleared_count

    async def clear_expired(self) -> int:
        """Clear all expired cache entries."""
        expired_keys = []
        for key, entry in self.cache.items():
            if entry.is_expired():
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            fire_and_forget(
                "llm_gateway_cache_expired_cleared",
                f"Cleared expired cache entries: {len(expired_keys)}",
                ServiceNames.LLM_GATEWAY,
                {"cleared_count": len(expired_keys)}
            )

        return len(expired_keys)

    async def clear_all(self) -> int:
        """Clear all cache entries."""
        return await self.clear_cache()

    async def _evict_oldest(self):
        """Evict the oldest cache entries when cache is full."""
        if not self.cache:
            return

        # Find entries sorted by last access time (oldest first)
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed
        )

        # Remove oldest 10% of entries
        entries_to_remove = max(1, len(sorted_entries) // 10)

        removed_keys = []
        for i in range(entries_to_remove):
            key, _ = sorted_entries[i]
            del self.cache[key]
            removed_keys.append(key)

        fire_and_forget(
            "llm_gateway_cache_eviction",
            f"Evicted {len(removed_keys)} oldest cache entries",
            ServiceNames.LLM_GATEWAY,
            {"evicted_count": len(removed_keys)}
        )

    async def _periodic_cleanup(self):
        """Periodically clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.clear_expired()
            except Exception as e:
                fire_and_forget(
                    "llm_gateway_cache_cleanup_error",
                    f"Cache cleanup error: {str(e)}",
                    ServiceNames.LLM_GATEWAY,
                    {"error": str(e)}
                )

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {
                "total_entries": 0,
                "total_size_bytes": 0,
                "oldest_entry_age": 0,
                "newest_entry_age": 0,
                "average_access_count": 0.0,
                "hit_rate_estimate": 0.0
            }

        total_size = sum(len(entry.response.encode('utf-8')) for entry in self.cache.values())
        current_time = time.time()

        oldest_entry = min(self.cache.values(), key=lambda x: x.created_at)
        newest_entry = max(self.cache.values(), key=lambda x: x.created_at)

        oldest_age = current_time - oldest_entry.created_at
        newest_age = current_time - newest_entry.created_at

        total_accesses = sum(entry.access_count for entry in self.cache.values())
        average_accesses = total_accesses / len(self.cache) if self.cache else 0

        return {
            "total_entries": len(self.cache),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_entry_age_seconds": int(oldest_age),
            "newest_entry_age_seconds": int(newest_age),
            "average_access_count": round(average_accesses, 2),
            "max_size": self.max_size,
            "utilization_percent": round((len(self.cache) / self.max_size) * 100, 2)
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get cache health status."""
        try:
            stats = self.get_cache_stats()
            expired_count = await self.clear_expired()

            return {
                "status": "healthy",
                "stats": stats,
                "expired_entries_cleared": expired_count,
                "last_cleanup": time.time()
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "stats": {},
                "expired_entries_cleared": 0
            }

    async def preload_cache(self, requests: List[Dict[str, Any]]):
        """Preload cache with common requests."""
        preloaded_count = 0

        for request_data in requests:
            try:
                # Create a mock request object
                class MockRequest:
                    def __init__(self, data):
                        for key, value in data.items():
                            setattr(self, key, value)

                mock_request = MockRequest(request_data)
                cache_key = self.generate_cache_key(mock_request)

                # Check if already cached
                if cache_key not in self.cache:
                    # Simulate caching a response
                    mock_response = f"Cached response for: {request_data.get('prompt', '')[:50]}..."
                    await self.cache_response(cache_key, mock_response, ttl=7200)  # 2 hours
                    preloaded_count += 1

            except Exception as e:
                fire_and_forget(
                    "llm_gateway_cache_preload_error",
                    f"Cache preload error: {str(e)}",
                    ServiceNames.LLM_GATEWAY,
                    {"error": str(e)}
                )

        fire_and_forget(
            "llm_gateway_cache_preloaded",
            f"Preloaded {preloaded_count} cache entries",
            ServiceNames.LLM_GATEWAY,
            {"preloaded_count": preloaded_count}
        )

        return preloaded_count
