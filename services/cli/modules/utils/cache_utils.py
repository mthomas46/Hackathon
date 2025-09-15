"""Cache utilities for CLI operations."""

from typing import Dict, Any, Optional
import time


class CacheManager:
    """Manager for CLI caching operations."""

    def __init__(self, cache: Optional[Dict[str, Any]] = None, default_ttl: int = 300):
        self.cache = cache or {}
        self.default_ttl = default_ttl

    async def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self.cache:
            item = self.cache[key]
            if time.time() - item.get('timestamp', 0) < item.get('ttl', self.default_ttl):
                return item['data']
            else:
                # Remove expired item
                del self.cache[key]
        return None

    async def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """Set cached value with TTL."""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'ttl': ttl or self.default_ttl
        }

    async def invalidate(self, pattern: Optional[str] = None):
        """Invalidate cache entries matching pattern."""
        if pattern:
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
        else:
            self.cache.clear()

    async def cleanup_expired(self):
        """Remove all expired cache entries."""
        current_time = time.time()
        expired_keys = []

        for key, item in self.cache.items():
            if current_time - item.get('timestamp', 0) >= item.get('ttl', self.default_ttl):
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]

    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        expired_entries = 0
        current_time = time.time()

        for item in self.cache.values():
            if current_time - item.get('timestamp', 0) >= item.get('ttl', self.default_ttl):
                expired_entries += 1

        return {
            'total_entries': total_entries,
            'active_entries': total_entries - expired_entries,
            'expired_entries': expired_entries
        }
