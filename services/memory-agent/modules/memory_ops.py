"""Memory operations for the Memory Agent service.

This module contains all memory management and Redis operations,
extracted from the main memory-agent service to improve maintainability.
"""

from typing import List, Optional, Any, Dict
import time

# Import shared utilities from main service module
from ..modules.shared_utils import (
    get_memory_max_items,
    get_memory_ttl_seconds,
    cleanup_expired_memory_items,
    get_memory_stats_summary
)

# Import global state from dedicated state module to avoid circular dependencies
from .memory_state import _memory

# Performance optimization: Track last cleanup time to avoid frequent cleanup
_last_cleanup_time = None
_CLEANUP_INTERVAL_SECONDS = 300  # 5 minutes


def _lazy_cleanup_memory():
    """Perform lazy cleanup of expired memory items to improve performance."""
    global _last_cleanup_time

    current_time = time.time()
    if (_last_cleanup_time is None or
        current_time - _last_cleanup_time > _CLEANUP_INTERVAL_SECONDS):
        # Time to run cleanup
        ttl_seconds = get_memory_ttl_seconds()
        _memory[:] = cleanup_expired_memory_items(_memory, ttl_seconds)
        _last_cleanup_time = current_time


def put_memory_item(item: Any) -> Dict[str, Any]:
    """Store a memory item with capacity management."""
    _memory.append(item)

    # Maintain memory size limits
    max_items = get_memory_max_items()
    if len(_memory) > max_items:
        del _memory[: len(_memory) - max_items]

    return {
        "count": len(_memory),
        "max_items": max_items,
        "utilization_percent": (len(_memory) / max_items) * 100 if max_items > 0 else 0
    }


def list_memory_items(memory_type: Optional[str] = None, key: Optional[str] = None, limit: int = 100) -> List[Any]:
    """List memory items with filtering, lazy TTL cleanup, and pagination."""
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
    """Get comprehensive memory usage statistics with lazy cleanup."""
    ttl_seconds = get_memory_ttl_seconds()
    max_items = get_memory_max_items()

    # Perform lazy cleanup to improve performance
    _lazy_cleanup_memory()

    return get_memory_stats_summary(_memory, max_items, ttl_seconds)


def cleanup_expired_items() -> int:
    """Clean up expired memory items and return count of removed items."""
    ttl_seconds = get_memory_ttl_seconds()
    original_count = len(_memory)

    _memory[:] = cleanup_expired_memory_items(_memory, ttl_seconds)
    removed_count = original_count - len(_memory)

    return removed_count
