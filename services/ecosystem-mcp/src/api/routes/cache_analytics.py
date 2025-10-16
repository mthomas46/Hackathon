"""
Cache analytics API endpoints (Phase 4).

Provides visibility into multi-level cache performance.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import logging

from ...services.ingestion.smart_cache import get_document_cache, get_metadata_cache

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/cache/stats",
    summary="Get cache statistics",
    response_description="Multi-level cache performance metrics"
)
async def get_cache_stats() -> Dict[str, Any]:
    """
    Get comprehensive cache statistics for all cache levels.
    
    Returns performance metrics including:
    - Hit/miss rates
    - Cache sizes
    - Latency metrics
    - Eviction counts
    
    Phase 4 Enhancement: Multi-level cache visibility.
    """
    try:
        doc_cache = get_document_cache()
        meta_cache = get_metadata_cache()
        
        return {
            "status": "success",
            "caches": {
                "document_cache": doc_cache.get_stats(),
                "metadata_cache": meta_cache.get_stats()
            },
            "recommendations": _generate_recommendations(doc_cache, meta_cache)
        }
    
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {e}")


@router.post(
    "/cache/clear",
    summary="Clear all caches",
    response_description="Cache clear status"
)
async def clear_all_caches() -> Dict[str, Any]:
    """
    Clear all cache levels (L1 and L2).
    
    Useful for:
    - Testing
    - Forcing fresh data
    - Memory reclamation
    
    Phase 4: Multi-level cache management.
    """
    try:
        doc_cache = get_document_cache()
        meta_cache = get_metadata_cache()
        
        await doc_cache.clear_all()
        await meta_cache.clear_all()
        
        return {
            "status": "success",
            "message": "All caches cleared successfully",
            "caches_cleared": ["document_cache", "metadata_cache"]
        }
    
    except Exception as e:
        logger.error(f"Failed to clear caches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear caches: {e}")


@router.post(
    "/cache/invalidate/{cache_name}/{key}",
    summary="Invalidate specific cache entry",
    response_description="Invalidation status"
)
async def invalidate_cache_entry(cache_name: str, key: str) -> Dict[str, Any]:
    """
    Invalidate a specific cache entry across all levels.
    
    Args:
        cache_name: Cache to invalidate from ("document" or "metadata")
        key: Cache key to invalidate
    
    Phase 4: Granular cache management.
    """
    try:
        if cache_name == "document":
            cache = get_document_cache()
        elif cache_name == "metadata":
            cache = get_metadata_cache()
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid cache name: {cache_name}. Use 'document' or 'metadata'"
            )
        
        await cache.invalidate(key)
        
        return {
            "status": "success",
            "message": f"Cache entry invalidated: {key}",
            "cache": cache_name,
            "key": key
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to invalidate cache entry: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to invalidate: {e}")


def _generate_recommendations(doc_cache, meta_cache) -> list[str]:
    """Generate cache optimization recommendations based on stats."""
    recommendations = []
    
    # Check document cache hit rate
    doc_stats = doc_cache.total_stats
    if doc_stats.hits + doc_stats.misses > 100:  # Enough data
        hit_rate = doc_stats.hit_rate
        
        if hit_rate < 50:
            recommendations.append(
                "📉 Document cache hit rate is low (<50%). "
                "Consider increasing L1 cache size or TTL."
            )
        elif hit_rate > 90:
            recommendations.append(
                "✅ Document cache hit rate is excellent (>90%). "
                "Cache is well-tuned."
            )
    
    # Check metadata cache hit rate
    meta_stats = meta_cache.total_stats
    if meta_stats.hits + meta_stats.misses > 100:
        hit_rate = meta_stats.hit_rate
        
        if hit_rate < 50:
            recommendations.append(
                "📉 Metadata cache hit rate is low (<50%). "
                "Consider increasing L1 cache size or TTL."
            )
    
    # Check eviction rates
    if doc_cache.l1.stats.evictions > doc_cache.l1.max_size * 0.5:
        recommendations.append(
            "⚠️  High eviction rate in document L1 cache. "
            "Consider increasing max_size."
        )
    
    if meta_cache.l1.stats.evictions > meta_cache.l1.max_size * 0.5:
        recommendations.append(
            "⚠️  High eviction rate in metadata L1 cache. "
            "Consider increasing max_size."
        )
    
    # Check error rates
    total_ops = doc_stats.hits + doc_stats.misses + doc_stats.writes
    if total_ops > 0 and (doc_stats.errors / total_ops) > 0.01:  # >1% error rate
        recommendations.append(
            "❌ High error rate in document cache (>1%). "
            "Check Redis connectivity."
        )
    
    if not recommendations:
        recommendations.append(
            "✅ All caches operating within normal parameters."
        )
    
    return recommendations

