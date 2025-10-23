"""
Cache Service

High-level caching service wrapping multi-level cache infrastructure.
Provides a clean interface for tests and application code.
"""

import logging
from typing import Any, Optional, Dict
import json

from ...services.ingestion.smart_cache import MultiLevelCache
from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class CacheService:
    """
    High-level caching service.
    
    Provides:
    - Multi-level caching (L1: memory, L2: Redis)
    - Automatic fallback on failures
    - Statistics tracking
    - TTL management
    
    Wraps existing MultiLevelCache infrastructure.
    """
    
    def __init__(
        self,
        prefix: str = "app_cache",
        l1_size: int = 1000,
        l1_ttl: int = 300,
        l2_ttl: int = 3600
    ):
        """
        Initialize cache service.
        
        Args:
            prefix: Cache key prefix
            l1_size: L1 cache size
            l1_ttl: L1 TTL in seconds
            l2_ttl: L2 TTL in seconds
        """
        self.cache = MultiLevelCache(
            prefix=prefix,
            l1_max_size=l1_size,
            l1_ttl=l1_ttl,
            l2_ttl=l2_ttl
        )
        self.redis_client = get_redis_client()
        logger.info(f"CacheService initialized: {prefix}")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None
        """
        try:
            return await self.cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
        
        Returns:
            True if successful
        """
        try:
            await self.cache.set(key, value, ttl=ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if deleted
        """
        try:
            await self.cache.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """
        Clear all cache entries.
        
        Returns:
            True if successful
        """
        try:
            await self.cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            return await self.cache.get_stats()
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {
                "error": str(e),
                "l1_size": 0,
                "l2_hits": 0,
                "l2_misses": 0
            }
    
    async def warm(self, keys_values: Dict[str, Any]) -> int:
        """
        Warm cache with multiple key-value pairs.
        
        Args:
            keys_values: Dictionary of keys and values
        
        Returns:
            Number of keys successfully cached
        """
        count = 0
        for key, value in keys_values.items():
            if await self.set(key, value):
                count += 1
        
        logger.info(f"Cache warmed: {count}/{len(keys_values)} keys")
        return count
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if exists
        """
        value = await self.get(key)
        return value is not None
    
    async def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """
        Get multiple keys from cache.
        
        Args:
            keys: List of cache keys
        
        Returns:
            Dictionary of key-value pairs (only existing keys)
        """
        result = {}
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        return result
    
    async def set_many(self, keys_values: Dict[str, Any], ttl: Optional[int] = None) -> int:
        """
        Set multiple keys in cache.
        
        Args:
            keys_values: Dictionary of keys and values
            ttl: Optional TTL for all keys
        
        Returns:
            Number of keys successfully set
        """
        count = 0
        for key, value in keys_values.items():
            if await self.set(key, value, ttl=ttl):
                count += 1
        return count


# Singleton instance
_cache_service: Optional[CacheService] = None


def get_cache_service(
    prefix: str = "app_cache",
    **kwargs
) -> CacheService:
    """
    Get singleton cache service.
    
    Args:
        prefix: Cache key prefix
        **kwargs: Additional cache configuration
    
    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None or _cache_service.cache.prefix != prefix:
        _cache_service = CacheService(prefix=prefix, **kwargs)
    return _cache_service

