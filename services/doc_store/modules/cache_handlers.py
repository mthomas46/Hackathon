# ============================================================================
# CACHE HANDLERS MODULE
# ============================================================================
"""
Cache management handlers for Doc Store service.

Provides endpoints for cache monitoring, management, and optimization.
"""

from typing import Dict, Any, Optional, List
from .caching import docstore_cache
from .shared_utils import (
    build_doc_store_context,
    create_doc_store_success_response,
    handle_doc_store_error
)
from .models import CacheStatsResponse, CacheInvalidationRequest


class CacheHandlers:
    """Handles cache management operations."""

    @staticmethod
    async def handle_get_cache_stats() -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        try:
            stats = await docstore_cache.get_stats()

            context = build_doc_store_context("cache_stats_retrieval")
            return create_doc_store_success_response("cache statistics retrieved", stats, **context)

        except Exception as e:
            context = build_doc_store_context("cache_stats_retrieval")
            return handle_doc_store_error("retrieve cache statistics", e, **context)

    @staticmethod
    async def handle_invalidate_cache(tags: Optional[List[str]] = None, operation: Optional[str] = None) -> Dict[str, Any]:
        """Invalidate cache entries."""
        try:
            invalidated_count = await docstore_cache.invalidate(operation=operation, tags=tags)

            context = build_doc_store_context(
                "cache_invalidation",
                invalidated_count=invalidated_count,
                tags=tags,
                operation=operation
            )
            return create_doc_store_success_response(
                "cache entries invalidated",
                {"invalidated_count": invalidated_count, "tags": tags, "operation": operation},
                **context
            )

        except Exception as e:
            context = build_doc_store_context("cache_invalidation")
            return handle_doc_store_error("invalidate cache", e, **context)

    @staticmethod
    async def handle_warmup_cache() -> Dict[str, Any]:
        """Warm up the cache with frequently accessed data."""
        try:
            result = await docstore_cache.warmup_cache()

            context = build_doc_store_context("cache_warmup")
            return create_doc_store_success_response("cache warmup completed", result, **context)

        except Exception as e:
            context = build_doc_store_context("cache_warmup")
            return handle_doc_store_error("warmup cache", e, **context)

    @staticmethod
    async def handle_optimize_cache() -> Dict[str, Any]:
        """Optimize cache performance and memory usage."""
        try:
            result = await docstore_cache.optimize_cache()

            context = build_doc_store_context("cache_optimization")
            return create_doc_store_success_response("cache optimization completed", result, **context)

        except Exception as e:
            context = build_doc_store_context("cache_optimization")
            return handle_doc_store_error("optimize cache", e, **context)
