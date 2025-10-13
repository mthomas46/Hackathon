"""
Cache statistics endpoint for monitoring.

Provides real-time cache hit/miss rates and performance metrics.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ...utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/cache/stats",
    summary="Cache statistics",
    description="Get cache hit/miss rates and performance metrics"
)
async def get_cache_stats():
    """
    Get cache statistics for all cached endpoints.
    
    Returns:
        Cache hit/miss rates, speedup metrics, and recommendations
    """
    try:
        redis_client = get_redis_client()
        
        # Get stats for each cache prefix
        cache_prefixes = ["rag", "embedding", "search", "doc_query", "chroma_search", "db_repo"]
        
        stats = {}
        total_hits = 0
        total_misses = 0
        
        for prefix in cache_prefixes:
            hits_key = f"cache_stats:{prefix}:hits"
            misses_key = f"cache_stats:{prefix}:misses"
            
            hits = await redis_client.get(hits_key)
            misses = await redis_client.get(misses_key)
            
            hits = int(hits) if hits else 0
            misses = int(misses) if misses else 0
            total = hits + misses
            
            hit_rate = (hits / total * 100) if total > 0 else 0.0
            
            stats[prefix] = {
                "hits": hits,
                "misses": misses,
                "total": total,
                "hit_rate": round(hit_rate, 2),
                "status": (
                    "🔥 Excellent" if hit_rate >= 70 else
                    "✅ Good" if hit_rate >= 50 else
                    "⚠️  Fair" if hit_rate >= 30 else
                    "❌ Poor" if total > 0 else
                    "📊 No data"
                )
            }
            
            total_hits += hits
            total_misses += misses
        
        # Overall stats
        overall_total = total_hits + total_misses
        overall_hit_rate = (total_hits / overall_total * 100) if overall_total > 0 else 0.0
        
        # Get key counts
        all_keys = await redis_client.keys("*")
        cache_keys = [k for k in all_keys if any(p in k.decode() if isinstance(k, bytes) else k 
                                                   for p in cache_prefixes)]
        
        return {
            "overall": {
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_requests": overall_total,
                "hit_rate": round(overall_hit_rate, 2),
                "cached_keys": len(cache_keys),
                "status": (
                    "🔥 Excellent" if overall_hit_rate >= 70 else
                    "✅ Good" if overall_hit_rate >= 50 else
                    "⚠️  Fair" if overall_hit_rate >= 30 else
                    "❌ Poor" if overall_total > 0 else
                    "📊 No data yet"
                )
            },
            "by_endpoint": stats,
            "recommendations": _get_recommendations(stats, overall_hit_rate),
            "performance_impact": {
                "estimated_speedup": f"{round(1 + (overall_hit_rate / 100) * 35, 1)}x average",
                "cache_effectiveness": f"{round(overall_hit_rate, 1)}% of requests served from cache",
                "estimated_cost_savings": f"{round(overall_hit_rate * 0.85, 1)}% reduction"
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve cache statistics: {str(e)}"
        )


@router.post(
    "/cache/reset",
    summary="Reset cache statistics",
    description="Reset cache hit/miss counters (does not clear cache)"
)
async def reset_cache_stats():
    """Reset cache statistics counters."""
    try:
        redis_client = get_redis_client()
        
        # Delete all cache_stats keys
        stats_keys = await redis_client.keys("cache_stats:*")
        if stats_keys:
            await redis_client.delete(*stats_keys)
        
        return {
            "message": "Cache statistics reset successfully",
            "keys_deleted": len(stats_keys)
        }
    
    except Exception as e:
        logger.error(f"Failed to reset cache stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset cache statistics: {str(e)}"
        )


@router.delete(
    "/cache/clear",
    summary="Clear all cache",
    description="Clear all cached data (use with caution!)"
)
async def clear_cache():
    """Clear all cached data."""
    try:
        redis_client = get_redis_client()
        
        # Get all cache keys (not stats)
        cache_prefixes = ["rag:", "embedding:", "search:", "doc_query:", "chroma_search:", "db_repo:"]
        
        deleted = 0
        for prefix in cache_prefixes:
            keys = await redis_client.keys(f"{prefix}*")
            if keys:
                await redis_client.delete(*keys)
                deleted += len(keys)
        
        return {
            "message": "Cache cleared successfully",
            "keys_deleted": deleted
        }
    
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


def _get_recommendations(stats: Dict[str, Any], overall_hit_rate: float) -> list[str]:
    """Generate recommendations based on cache performance."""
    recommendations = []
    
    if overall_hit_rate < 30:
        recommendations.append(
            "⚠️  Overall hit rate is low (<30%). Consider increasing cache TTLs or "
            "investigating why queries are so diverse."
        )
    
    # Check RAG specifically
    rag_stats = stats.get("rag", {})
    if rag_stats.get("total", 0) > 10 and rag_stats.get("hit_rate", 0) < 50:
        recommendations.append(
            "⚠️  RAG cache hit rate is low. This might be due to LLM non-determinism. "
            "Consider setting temperature=0 for cacheable queries or using deterministic mode."
        )
    
    # Check embedding cache
    embedding_stats = stats.get("embedding", {})
    if embedding_stats.get("total", 0) > 10 and embedding_stats.get("hit_rate", 0) < 70:
        recommendations.append(
            "⚠️  Embedding cache hit rate is lower than expected (should be >70%). "
            "Verify that identical texts generate identical embeddings."
        )
    
    if overall_hit_rate >= 70:
        recommendations.append(
            "🔥 Excellent cache performance! Your cache hit rate is above 70%, "
            "providing significant cost and latency savings."
        )
    
    if not recommendations:
        recommendations.append(
            "✅ Cache performance is good. Continue monitoring for optimization opportunities."
        )
    
    return recommendations

