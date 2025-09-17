"""Shared utilities for Memory Agent service modules.

This module contains common utilities used across all memory-agent modules
to eliminate code duplication and ensure consistency.
"""

import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta

# Import shared utilities
from services.shared.utilities import utc_now, generate_id
from services.shared.monitoring.logging import fire_and_forget
from services.shared.core.responses.responses import create_success_response, create_error_response
from services.shared.utilities.error_handling import ServiceException
from services.shared.core.constants_new import ErrorCodes, ServiceNames
from services.shared.core.models.models import MemoryItem

# Global configuration for memory agent
_MEMORY_MAX_ITEMS = int(os.environ.get("MEMORY_MAX_ITEMS", "1000"))
_MEMORY_TTL_SECONDS = int(os.environ.get("MEMORY_TTL_SECONDS", "3600"))
_REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")

def get_memory_max_items() -> int:
    """Get maximum memory items configuration."""
    return _MEMORY_MAX_ITEMS

def get_memory_ttl_seconds() -> int:
    """Get memory TTL configuration in seconds."""
    return _MEMORY_TTL_SECONDS

def get_redis_url() -> str:
    """Get Redis URL configuration."""
    return _REDIS_URL

def handle_memory_agent_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for memory-agent operations.

    Logs the error and returns a standardized error response.
    """
    fire_and_forget("error", f"Memory-agent {operation} error: {error}", ServiceNames.MEMORY_AGENT, context)
    return create_error_response(
        f"Failed to {operation}",
        error_code=ErrorCodes.INTERNAL_ERROR,
        details={"error": str(error), **context}
    )

def create_memory_agent_success_response(operation: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response for memory-agent operations.

    Returns a consistent success response format.
    """
    return create_success_response(f"Memory {operation} successful", data, **context)

def build_memory_agent_context(operation: str, item_count: Optional[int] = None, **additional) -> Dict[str, Any]:
    """Build context dictionary for memory-agent operations.

    Provides consistent context for logging and responses.
    """
    context = {
        "operation": operation,
        "service": "memory-agent"
    }

    if item_count is not None:
        context["item_count"] = item_count

    context.update(additional)
    return context

def create_memory_item(key: str, value: Any, item_type: str = "general", ttl_seconds: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> MemoryItem:
    """Create a memory item with standardized fields and TTL management."""
    expires_at = None
    if ttl_seconds:
        expires_at = utc_now() + timedelta(seconds=ttl_seconds)

    return MemoryItem(
        id=f"mem:{item_type}:{generate_id()}",
        key=key,
        value=value,
        type=item_type,
        created_at=utc_now(),
        expires_at=expires_at,
        metadata=metadata or {"source": "memory-agent"}
    )

def serialize_memory_value(value: Any) -> str:
    """Serialize memory value to string format."""
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)

def deserialize_memory_value(value: str) -> Any:
    """Deserialize memory value from string format."""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

def build_memory_filter_query(memory_type: Optional[str] = None, key_pattern: Optional[str] = None) -> str:
    """Build SQL-like filter query for memory items."""
    conditions = []
    if memory_type:
        conditions.append(f"type = '{memory_type}'")
    if key_pattern:
        conditions.append(f"key LIKE '{key_pattern}'")
    return " AND ".join(conditions) if conditions else "1=1"

def is_memory_item_expired(item: MemoryItem, ttl_seconds: int = _MEMORY_TTL_SECONDS) -> bool:
    """Check if a memory item has expired."""
    now = utc_now()

    if item.expires_at:
        return item.expires_at < now

    # If no explicit expires_at, infer by created_at + TTL
    if hasattr(item, "created_at") and item.created_at:
        expiry = item.created_at + timedelta(seconds=ttl_seconds)
        return expiry < now

    return False

def cleanup_expired_memory_items(memory_list: List[MemoryItem], ttl_seconds: int = _MEMORY_TTL_SECONDS) -> List[MemoryItem]:
    """Clean up expired memory items from a list."""
    fresh_items = []
    for item in memory_list:
        if not is_memory_item_expired(item, ttl_seconds):
            fresh_items.append(item)
    return fresh_items

def get_memory_stats_summary(memory_list: List[MemoryItem], max_items: int = _MEMORY_MAX_ITEMS, ttl_seconds: int = _MEMORY_TTL_SECONDS) -> Dict[str, Any]:
    """Get comprehensive memory statistics summary."""
    now = utc_now()
    active_items = len(memory_list)

    # Count by type
    type_counts = {}
    for item in memory_list:
        type_counts[item.type] = type_counts.get(item.type, 0) + 1

    # Count expired items
    expired_count = sum(1 for item in memory_list if is_memory_item_expired(item, ttl_seconds))

    return {
        "total_items": len(memory_list),
        "active_items": active_items,
        "expired_items": expired_count,
        "max_capacity": max_items,
        "utilization_percent": (active_items / max_items) * 100 if max_items > 0 else 0,
        "type_breakdown": type_counts,
        "ttl_seconds": ttl_seconds,
        "healthy": active_items <= max_items
    }

def validate_memory_item(item: MemoryItem) -> None:
    """Validate memory item fields."""
    if not item.key:
        raise ServiceException(
            "Memory item key is required",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={"field": "key"}
        )

    if not item.data:
        raise ServiceException(
            "Memory item data is required",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={"field": "data"}
        )

    if not item.type:
        raise ServiceException(
            "Memory item type is required",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={"field": "type"}
        )

def extract_endpoint_from_text(text: str) -> List[str]:
    """Extract API endpoints from text content."""
    endpoints = []
    if not text:
        return endpoints

    for token in text.split():
        if token.startswith("/") and len(token) > 1:
            endpoint = token.strip(",.;:()[]{}")
            if endpoint not in endpoints:
                endpoints.append(endpoint)

    return endpoints
