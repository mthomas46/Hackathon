"""
Cache Monitoring API Routes

Provides real-time monitoring of cache performance and hit rates.
Tracks Phase 1 + 2 + 3 caching improvements.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cache", tags=["cache-monitoring"])


class CacheMetrics(BaseModel):
    """Cache performance metrics."""
    redis_hit_rate: float
    redis_hits: int
    redis_misses: int
    redis_used_memory: str
    redis_connected_clients: int
    cache_keys_by_prefix: Dict[str, int]


@router.get("/metrics", response_model=Dict[str, Any])
async def get_cache_metrics():
    """
    Get comprehensive cache metrics.
    
    Includes:
    - Redis hit/miss rates
    - Memory usage
    - Cache key distribution
    - Performance indicators
    
    Returns:
        Dict with cache metrics
    """
    try:
        from ...utils.redis_client import get_redis_client as get_cache_client
        
        cache_client = get_cache_client()
        if not cache_client:
            raise HTTPException(status_code=503, detail="Cache client not available")
        
        # ⚡ FINAL FIX: Properly handle async Redis client
        # The client attribute is async redis.Redis, need to await ALL calls
        try:
            if hasattr(cache_client, 'client') and cache_client.client:
                # Always await - redis-py async client always returns coroutines
                info_result = cache_client.client.info()
                
                # Check if it's a coroutine and await it
                import inspect
                if inspect.iscoroutine(info_result):
                    info = await info_result
                    logger.debug("✅ Got Redis INFO from cache_client.client (async)")
                else:
                    info = info_result
                    logger.debug("✅ Got Redis INFO from cache_client.client (sync)")
            else:
                raise AttributeError("No client attribute")
        except Exception as e:
            # Fallback: return basic metrics without Redis INFO
            logger.warning(f"Redis client info() failed ({e}), returning fallback metrics")
            return {
                "status": "limited",
                "message": f"Cache client available but detailed metrics unavailable: {str(e)}",
                "redis": {
                    "available": True,
                    "detailed_metrics": False
                },
                "fallback_metrics": {
                    "cache_enabled": True,
                    "note": "Using fallback metrics - core caching still works"
                },
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
        
        # Calculate hit rate
        hits = int(info.get("keyspace_hits", 0))
        misses = int(info.get("keyspace_misses", 0))
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        # Get all keys grouped by prefix
        try:
            if hasattr(cache_client, 'client') and cache_client.client:
                # Call keys() and check if result is coroutine
                keys_result = cache_client.client.keys("*")
                import inspect
                if inspect.iscoroutine(keys_result):
                    keys = await keys_result
                else:
                    keys = keys_result
                logger.debug(f"✅ Got {len(keys)} keys from Redis")
            else:
                # Use wrapper's async method
                keys = await cache_client.keys("*")
                logger.debug(f"✅ Got {len(keys)} keys from Redis (wrapper)")
        except Exception as e:
            logger.warning(f"Failed to get keys: {e}")
            keys = []
        key_distribution = {}
        for key in keys:
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            prefix = key.split(':')[0] if ':' in key else 'other'
            key_distribution[prefix] = key_distribution.get(prefix, 0) + 1
        
        # Phase-specific metrics
        phase_metrics = {
            "phase1_answer_cache": key_distribution.get("rag_answer_enhanced_v1", 0) + key_distribution.get("rag_answer_v2", 0),
            "phase3a_document_cache": key_distribution.get("enriched_doc", 0),
            "phase3b_bm25_index_cache": key_distribution.get("bm25_index_serialized", 0),
            "embedding_cache": key_distribution.get("embedding", 0),
            "chroma_search_cache": key_distribution.get("chroma_search", 0),
            "query_rewrite_cache": key_distribution.get("query_rewrite", 0),
            "bm25_search_cache": key_distribution.get("bm25_search", 0),
            "bm25_corpus_cache": key_distribution.get("bm25_corpus", 0)
        }
        
        return {
            "redis": {
                "hit_rate": round(hit_rate, 2),
                "hits": hits,
                "misses": misses,
                "total_requests": total,
                "used_memory": info.get("used_memory_human", "unknown"),
                "used_memory_peak": info.get("used_memory_peak_human", "unknown"),
                "connected_clients": int(info.get("connected_clients", 0)),
                "total_keys": len(keys),
                "uptime_seconds": int(info.get("uptime_in_seconds", 0))
            },
            "key_distribution": key_distribution,
            "phase_metrics": phase_metrics,
            "performance_indicators": {
                "cache_efficiency": "high" if hit_rate > 70 else "medium" if hit_rate > 40 else "low",
                "answer_cache_active": phase_metrics["phase1_answer_cache"] > 0,
                "document_cache_active": phase_metrics["phase3a_document_cache"] > 0,
                "bm25_cache_active": phase_metrics["phase3b_bm25_index_cache"] > 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get cache metrics: {str(e)}")


@router.get("/hit-rate", response_model=Dict[str, Any])
async def get_cache_hit_rate():
    """
    Get simplified cache hit rate.
    
    Returns:
        Hit rate percentage and basic stats
    """
    try:
        from ...utils.redis_client import get_redis_client
        
        cache_client = get_redis_client()
        if not cache_client:
            raise HTTPException(status_code=503, detail="Cache client not available")
        
        info = cache_client.info()
        
        hits = int(info.get("keyspace_hits", 0))
        misses = int(info.get("keyspace_misses", 0))
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0
        
        return {
            "hit_rate": round(hit_rate, 2),
            "hits": hits,
            "misses": misses,
            "total_requests": total,
            "status": "healthy" if hit_rate > 40 else "needs_improvement"
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache hit rate: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get hit rate: {str(e)}")


@router.post("/clear", response_model=Dict[str, str])
async def clear_cache(prefix: str = None):
    """
    Clear cache keys (optionally by prefix).
    
    Args:
        prefix: Optional prefix to clear specific cache keys
        
    Returns:
        Status message
    """
    try:
        from ...utils.redis_client import get_redis_client as get_cache_client
        
        cache_client = get_cache_client()
        if not cache_client:
            raise HTTPException(status_code=503, detail="Cache client not available")
        
        if prefix:
            # Clear keys with specific prefix
            try:
                if hasattr(cache_client, 'client') and cache_client.client:
                    import inspect
                    if inspect.iscoroutinefunction(cache_client.client.keys):
                        keys = await cache_client.client.keys(f"{prefix}:*")
                        if keys:
                            if inspect.iscoroutinefunction(cache_client.client.delete):
                                await cache_client.client.delete(*keys)
                            else:
                                cache_client.client.delete(*keys)
                    else:
                        keys = cache_client.client.keys(f"{prefix}:*")
                        if keys:
                            cache_client.client.delete(*keys)
                else:
                    keys = await cache_client.keys(f"{prefix}:*")
                    if keys:
                        await cache_client.delete(*keys)
                
                if keys:
                    logger.info(f"Cleared {len(keys)} cache keys with prefix '{prefix}'")
                    return {"status": "success", "message": f"Cleared {len(keys)} keys with prefix '{prefix}'"}
                else:
                    return {"status": "success", "message": f"No keys found with prefix '{prefix}'"}
            except Exception as e:
                logger.error(f"Failed to clear keys with prefix '{prefix}': {e}")
                raise HTTPException(status_code=500, detail=f"Failed to clear keys: {str(e)}")
        else:
            # Clear all keys
            try:
                if hasattr(cache_client, 'client') and cache_client.client:
                    import inspect
                    if inspect.iscoroutinefunction(cache_client.client.flushall):
                        await cache_client.client.flushall()
                    else:
                        cache_client.client.flushall()
                else:
                    # Use wrapper method if available
                    if hasattr(cache_client, 'flushall'):
                        await cache_client.flushall()
                logger.warning("Cleared ALL cache keys")
                return {"status": "success", "message": "Cleared all cache keys"}
            except Exception as e:
                logger.error(f"Failed to flush cache: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to flush cache: {str(e)}")
            
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/keys/{prefix}", response_model=Dict[str, Any])
async def get_cache_keys_by_prefix(prefix: str):
    """
    Get all cache keys with a specific prefix.
    
    Args:
        prefix: Cache key prefix (e.g., 'enriched_doc', 'bm25_index_serialized')
        
    Returns:
        List of keys and their TTLs
    """
    try:
        from ...utils.redis_client import get_redis_client as get_cache_client
        
        cache_client = get_cache_client()
        if not cache_client:
            raise HTTPException(status_code=503, detail="Cache client not available")
        
        keys = cache_client.keys(f"{prefix}:*")
        
        key_info = []
        for key in keys[:50]:  # Limit to 50 keys
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            
            try:
                if hasattr(cache_client, 'client') and cache_client.client:
                    import inspect
                    if inspect.iscoroutinefunction(cache_client.client.ttl):
                        ttl = await cache_client.client.ttl(key)
                    else:
                        ttl = cache_client.client.ttl(key)
                else:
                    ttl = -1  # Default if not available
            except:
                ttl = -1  # Default on error
            key_info.append({
                "key": key,
                "ttl_seconds": ttl if ttl > 0 else None,
                "expires": ttl > 0
            })
        
        return {
            "prefix": prefix,
            "total_keys": len(keys),
            "keys_shown": len(key_info),
            "keys": key_info
        }
        
    except Exception as e:
        logger.error(f"Failed to get cache keys: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get keys: {str(e)}")

