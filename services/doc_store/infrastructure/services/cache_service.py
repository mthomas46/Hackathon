"""Cache service for Doc Store infrastructure.

Provides caching operations and management.
"""

from typing import Any, Dict, Optional
import time
from ..adapters.database_adapter import DatabaseAdapter


class CacheService:
    """Service for managing document caching operations."""

    def __init__(self, db_adapter: DatabaseAdapter, cache_ttl: int = 3600):
        """Initialize cache service.

        Args:
            db_adapter: Database adapter for persistence
            cache_ttl: Default time-to-live for cache entries in seconds
        """
        self.db_adapter = db_adapter
        self.cache_ttl = cache_ttl

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value if exists and not expired, None otherwise
        """
        try:
            result = self.db_adapter.execute_query(
                "SELECT value, expires_at FROM cache WHERE key = ?",
                (key,)
            )

            if result and result[0]["expires_at"] > time.time():
                return result[0]["value"]

            # Remove expired entry
            if result:
                self.delete(key)

        except Exception:
            # Cache miss on error
            pass

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Store a value in cache.

        Args:
            key: Cache key
            value: Value to store
            ttl: Time-to-live in seconds (uses default if not provided)

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            expires_at = time.time() + (ttl or self.cache_ttl)

            # Upsert operation
            self.db_adapter.execute_write("""
                INSERT OR REPLACE INTO cache (key, value, expires_at, created_at)
                VALUES (?, ?, ?, ?)
            """, (key, str(value), expires_at, time.time()))

            return True

        except Exception:
            return False

    def delete(self, key: str) -> bool:
        """Remove a value from cache.

        Args:
            key: Cache key to remove

        Returns:
            True if removed successfully, False otherwise
        """
        try:
            self.db_adapter.execute_write(
                "DELETE FROM cache WHERE key = ?",
                (key,)
            )
            return True
        except Exception:
            return False

    def clear(self) -> bool:
        """Clear all cache entries.

        Returns:
            True if cleared successfully, False otherwise
        """
        try:
            self.db_adapter.execute_write("DELETE FROM cache")
            return True
        except Exception:
            return False

    def cleanup_expired(self) -> int:
        """Remove expired cache entries.

        Returns:
            Number of entries removed
        """
        try:
            result = self.db_adapter.execute_write(
                "DELETE FROM cache WHERE expires_at <= ?",
                (time.time(),)
            )
            return result
        except Exception:
            return 0

    def health_check(self) -> Dict[str, Any]:
        """Perform cache health check.

        Returns:
            Health status dictionary
        """
        try:
            # Test basic operations
            test_key = "__health_check__"
            self.set(test_key, "test_value", ttl=60)

            retrieved = self.get(test_key)
            success = retrieved == "test_value"

            self.delete(test_key)

            return {
                "status": "healthy" if success else "unhealthy",
                "cache_operations": success,
                "database_connected": True
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_connected": False
            }
