"""
Cache decorator for expensive operations.

Uses Redis for distributed caching with TTL support.
"""

import json
import hashlib
import logging
from functools import wraps
from typing import Any, Callable, Optional
import inspect

from ..utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Cache metrics (will be exposed via Prometheus)
CACHE_HITS = 0
CACHE_MISSES = 0


def cache(
    ttl: int = 3600,
    key_prefix: str = "cache",
    key_fn: Optional[Callable] = None
):
    """
    Cache decorator using Redis with TTL support.
    
    Caches function results in Redis with automatic serialization/deserialization.
    Supports both sync and async functions.
    
    Args:
        ttl: Time to live in seconds (default: 1 hour)
        key_prefix: Prefix for cache key (default: "cache")
        key_fn: Custom function to generate cache key from args/kwargs
    
    Usage:
        @cache(ttl=3600, key_prefix="embedding")
        async def generate_embedding(text: str) -> List[float]:
            ...
    
    Cache Key Format:
        {key_prefix}:{function_name}:{hash_of_args}
    
    Example:
        embedding:generate_embedding:a3b2c1d4e5
    
    Notes:
        - Only works with JSON-serializable return values
        - Arguments must be JSON-serializable for key generation
        - Cache misses and hits are logged and tracked
    """
    def decorator(func: Callable) -> Callable:
        # Detect if function is async
        is_async = inspect.iscoroutinefunction(func)
        
        if is_async:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                global CACHE_HITS, CACHE_MISSES
                
                redis = get_redis_client()
                
                # Generate cache key
                if key_fn:
                    cache_key = f"{key_prefix}:{key_fn(*args, **kwargs)}"
                else:
                    # Default: hash of function name + args/kwargs
                    # Filter out non-serializable args (like Request objects)
                    serializable_args = []
                    for arg in args:
                        try:
                            json.dumps(arg)
                            serializable_args.append(arg)
                        except (TypeError, ValueError):
                            # Skip non-serializable args
                            pass
                    
                    serializable_kwargs = {}
                    for k, v in kwargs.items():
                        try:
                            json.dumps(v)
                            serializable_kwargs[k] = v
                        except (TypeError, ValueError):
                            # Skip non-serializable kwargs
                            pass
                    
                    key_data = json.dumps({
                        "args": serializable_args,
                        "kwargs": serializable_kwargs
                    }, sort_keys=True)
                    key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
                    cache_key = f"{key_prefix}:{func.__name__}:{key_hash}"
                
                # Try cache first
                try:
                    cached = await redis.get(cache_key)
                    if cached:
                        CACHE_HITS += 1
                        logger.debug(f"Cache HIT: {cache_key}")
                        return json.loads(cached)
                except Exception as e:
                    logger.warning(f"Cache read error for {cache_key}: {e}")
                    # Continue to compute if cache fails
                
                # Cache miss - compute result
                CACHE_MISSES += 1
                logger.debug(f"Cache MISS: {cache_key}")
                result = await func(*args, **kwargs)
                
                # Store in cache (best effort)
                try:
                    serialized = json.dumps(result)
                    await redis.set(cache_key, serialized, ex=ttl)
                    logger.debug(f"Cached result for {cache_key} (TTL: {ttl}s)")
                except (TypeError, ValueError) as e:
                    logger.warning(f"Cannot cache result for {cache_key}: {e}")
                except Exception as e:
                    logger.error(f"Cache write error for {cache_key}: {e}")
                
                return result
            
            return async_wrapper
        
        else:
            # Sync wrapper (for future use)
            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                global CACHE_HITS, CACHE_MISSES
                
                # For sync functions, we need to use sync Redis operations
                # For now, just pass through
                logger.warning(f"Cache decorator used on sync function {func.__name__}, skipping cache")
                return func(*args, **kwargs)
            
            return sync_wrapper
    
    return decorator


def get_cache_stats() -> dict:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache hits, misses, and hit rate
    """
    total = CACHE_HITS + CACHE_MISSES
    hit_rate = (CACHE_HITS / total * 100) if total > 0 else 0
    
    return {
        "cache_hits": CACHE_HITS,
        "cache_misses": CACHE_MISSES,
        "total_requests": total,
        "hit_rate_percent": round(hit_rate, 2)
    }


async def clear_cache_prefix(prefix: str) -> int:
    """
    Clear all cache keys matching a prefix.
    
    Args:
        prefix: Cache key prefix to clear (e.g., "embedding:")
    
    Returns:
        Number of keys deleted
    """
    redis = get_redis_client()
    pattern = f"{prefix}:*"
    
    # Note: This is a simplified version. Production should use SCAN for large datasets
    keys = await redis.keys(pattern)
    if keys:
        deleted = await redis.delete(*keys)
        logger.info(f"Cleared {deleted} cache keys matching {pattern}")
        return deleted
    
    return 0


async def clear_all_cache() -> int:
    """
    Clear ALL cache (use with caution).
    
    Returns:
        Number of keys deleted
    """
    redis = get_redis_client()
    
    # Get all cache keys
    keys = await redis.keys("cache:*")
    if keys:
        deleted = await redis.delete(*keys)
        logger.info(f"Cleared ALL cache: {deleted} keys deleted")
        return deleted
    
    return 0

