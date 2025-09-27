"""Memory operations for the Memory Agent service.

This module contains all memory management and Redis operations,
extracted from the main memory-agent service to improve maintainability.
"""

import time
from typing import Any, Dict, List, Optional

# Import shared utilities from main service module
from ..modules.shared_utils import (
    cleanup_expired_memory_items,
    get_memory_max_items,
    get_memory_stats_summary,
    get_memory_ttl_seconds,
)

# Import global state from dedicated state module to avoid circular dependencies
from .memory_state import _memory

# Performance optimization: Track last cleanup time to avoid frequent cleanup
_last_cleanup_time = None
_CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes


def _lazy_cleanup_memory():
    """Perform lazy cleanup of expired memory items to improve performance.

    Implements a time-based cleanup strategy that runs periodically rather than
    on every operation. This reduces performance overhead while maintaining
    memory bounds and preventing accumulation of expired items.

    The cleanup interval is configurable and balances memory efficiency
    with performance requirements.
    """
    global _last_cleanup_time

    current_time = time.time()
    if (
        _last_cleanup_time is None
        or current_time - _last_cleanup_time > _CLEANUP_INTERVAL_SECONDS
    ):
        # Time to run cleanup
        ttl_seconds = get_memory_ttl_seconds()
        _memory[:] = cleanup_expired_memory_items(_memory, ttl_seconds)
        _last_cleanup_time = current_time


def put_memory_item(item: Any) -> Dict[str, Any]:
    """Store a memory item with capacity management and automatic cleanup.

    Adds a new item to the memory store while maintaining configured capacity limits.
    Performs lazy cleanup of expired items and enforces maximum item limits by
    removing oldest items when capacity is exceeded.

    Args:
        item: Any object to store in memory

    Returns:
        Dictionary containing operation status and memory statistics

    Note:
        This function modifies the global memory state and should be used carefully
        in multi-threaded environments.
    """
    _memory.append(item)

    # Maintain memory size limits
    max_items = get_memory_max_items()
    if len(_memory) > max_items:
        del _memory[: len(_memory) - max_items]

    return {
        "count": len(_memory),
        "max_items": max_items,
        "utilization_percent": (len(_memory) / max_items) * 100 if max_items > 0 else 0,
    }


def list_memory_items(
    memory_type: Optional[str] = None, key: Optional[str] = None, limit: int = 100
) -> List[Any]:
    """List memory items with filtering, lazy TTL cleanup, and pagination.

    Retrieves memory items from the store with optional filtering by type and key.
    Automatically performs lazy cleanup of expired items to ensure data freshness.
    Supports pagination to limit result size for performance.

    Args:
        memory_type: Optional filter by memory item type
        key: Optional filter by key substring matching
        limit: Maximum number of items to return (0 = no limit)

    Returns:
        List of memory items matching the filter criteria, ordered by recency
        (most recent first)
    """
    # Perform lazy cleanup to improve performance
    _lazy_cleanup_memory()

    # Apply filters
    filtered = _memory
    if memory_type:
        filtered = [m for m in filtered if m.type == memory_type]
    if key:
        filtered = [m for m in filtered if key in m.key]

    # Apply pagination
    return filtered[-limit:] if limit > 0 else filtered


def get_memory_stats() -> Dict[str, Any]:
    """Get comprehensive memory usage statistics with lazy cleanup.

    Provides detailed statistics about memory usage including item counts,
    capacity utilization, TTL settings, and performance metrics.
    Performs lazy cleanup to ensure statistics reflect current state.

    Returns:
        Dictionary containing memory statistics including:
        - total_items: Current number of items in memory
        - max_items: Configured maximum capacity
        - utilization_percent: Current capacity utilization
        - ttl_seconds: Time-to-live setting for items
        - last_cleanup: Timestamp of last cleanup operation
    """
    ttl_seconds = get_memory_ttl_seconds()
    max_items = get_memory_max_items()

    # Perform lazy cleanup to improve performance
    _lazy_cleanup_memory()

    return get_memory_stats_summary(_memory, max_items, ttl_seconds)


def cleanup_expired_items() -> int:
    """Clean up expired memory items and return count of removed items.

    Immediately removes all expired memory items from the store based on
    the configured TTL settings. This is a forced cleanup that runs regardless
    of the lazy cleanup interval.

    Returns:
        Integer count of items that were removed during cleanup

    Note:
        This function performs immediate cleanup and may impact performance
        if called frequently. Consider using lazy cleanup for better performance.
    """
    ttl_seconds = get_memory_ttl_seconds()
    original_count = len(_memory)

    _memory[:] = cleanup_expired_memory_items(_memory, ttl_seconds)
    removed_count = original_count - len(_memory)

    return removed_count
