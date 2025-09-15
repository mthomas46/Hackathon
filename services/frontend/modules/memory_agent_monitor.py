"""Memory Agent monitoring infrastructure for Frontend service.

Provides visualization and monitoring capabilities for memory agent
service operational context and event summary storage.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from services.shared.utilities import utc_now
from .shared_utils import get_memory_agent_url, get_frontend_clients


class MemoryAgentMonitor:
    """Monitor for memory agent service operational context and event storage."""

    def __init__(self):
        self._memory_items = []
        self._cache_ttl = 30  # Cache for 30 seconds

    def is_cache_fresh(self, cache_key: str) -> bool:
        """Check if cache is still fresh."""
        cache_time = getattr(self, f"_{cache_key}_updated", None)
        if not cache_time:
            return False
        return (utc_now() - cache_time).total_seconds() < self._cache_ttl

    async def get_memory_status(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get comprehensive memory agent service status."""
        if not force_refresh and self.is_cache_fresh("status"):
            return getattr(self, "_status_cache", {})

        try:
            clients = get_frontend_clients()
            memory_url = get_memory_agent_url()

            # Get health status
            health_response = await clients.get_json(f"{memory_url}/health")

            status_data = {
                "health": health_response,
                "memory_stats": self._calculate_memory_stats(),
                "recent_items": self._memory_items[-10:] if self._memory_items else [],  # Last 10 items
                "last_updated": utc_now().isoformat()
            }

            self._status_cache = status_data
            self._status_updated = utc_now()

            return status_data

        except Exception as e:
            return {
                "error": str(e),
                "health": {},
                "memory_stats": {},
                "recent_items": [],
                "last_updated": utc_now().isoformat()
            }

    async def list_memory_items(self, type: Optional[str] = None, key: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Get memory items with filtering."""
        try:
            clients = get_frontend_clients()
            memory_url = get_memory_agent_url()

            # Build query parameters
            params = {"limit": limit}
            if type:
                params["type"] = type
            if key:
                params["key"] = key

            # Build URL with query parameters
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            url = f"{memory_url}/memory/list?{query_string}"

            response = await clients.get_json(url)

            if response.get("success") and "items" in response:
                items = response["items"]
                # Cache the items for monitoring
                self._memory_items.extend(items[-20:])  # Keep last 20 items
                if len(self._memory_items) > 100:  # Limit cache size
                    self._memory_items = self._memory_items[-100:]
                return items

            return []

        except Exception as e:
            return []

    async def store_memory_item(self, item_type: str, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Store a memory item and cache the result."""
        try:
            clients = get_frontend_clients()
            memory_url = get_memory_agent_url()

            memory_item = {
                "type": item_type,
                "key": key,
                "value": value,
                "metadata": metadata or {},
                "timestamp": utc_now().isoformat()
            }

            payload = {"item": memory_item}

            response = await clients.post_json(f"{memory_url}/memory/put", payload)

            if response.get("success"):
                # Cache the stored item
                stored_item = {
                    "id": f"memory_{utc_now().isoformat()}",
                    "type": item_type,
                    "key": key,
                    "value": str(value)[:200] + "..." if len(str(value)) > 200 else str(value),
                    "metadata": metadata,
                    "timestamp": utc_now().isoformat(),
                    "response": response
                }

                self._memory_items.insert(0, stored_item)  # Add to front
                # Keep only last 100 items
                if len(self._memory_items) > 100:
                    self._memory_items = self._memory_items[:100]

                return {
                    "success": True,
                    "item_id": stored_item["id"],
                    "response": response
                }

            return {
                "success": False,
                "error": "Failed to store memory item",
                "response": response
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }

    def _calculate_memory_stats(self) -> Dict[str, Any]:
        """Calculate statistics from cached memory items."""
        if not self._memory_items:
            return {
                "total_items_cached": 0,
                "unique_types": 0,
                "most_common_type": None
            }

        total = len(self._memory_items)

        # Count types
        type_counts = {}
        for item in self._memory_items:
            item_type = item.get("type", "unknown")
            type_counts[item_type] = type_counts.get(item_type, 0) + 1

        most_common_type = max(type_counts.items(), key=lambda x: x[1]) if type_counts else None

        return {
            "total_items_cached": total,
            "unique_types": len(type_counts),
            "most_common_type": most_common_type[0] if most_common_type else None,
            "type_distribution": type_counts
        }

    def get_memory_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent memory items."""
        return self._memory_items[:limit]


# Global instance
memory_agent_monitor = MemoryAgentMonitor()
