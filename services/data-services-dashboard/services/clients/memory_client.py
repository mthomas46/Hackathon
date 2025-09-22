"""Memory Agent Client - Client for Memory Agent Service.

This module provides a client for interacting with the Memory Agent service,
enabling browsing and management of conversation memory and operational context.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from infrastructure.config.config import get_config


class MemoryAgentClient:
    """Client for interacting with the Memory Agent service."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize the memory agent client.

        Args:
            base_url: Base URL of the Memory Agent service
            timeout: Request timeout in seconds
        """
        self.config = get_config()
        self.base_url = base_url or self.config.memory_service.base_url
        self.timeout = timeout

        # HTTP client setup
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Content-Type": "application/json", "User-Agent": "DataServicesDashboard/1.0"},
        )

        # Logging
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check Memory Agent health."""
        try:
            response = await self.client.get("/health")
            return response.json()
        except Exception as e:
            self.logger.error(f"Memory Agent health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def list_memory_items(
        self, type_filter: Optional[str] = None, key_filter: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        """List memory items with optional filtering."""
        try:
            params = {"limit": limit, "offset": offset}
            if type_filter:
                params["type"] = type_filter
            if key_filter:
                params["key"] = key_filter

            response = await self.client.get("/memory/list", params=params)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to list memory items: {e}")
            return {"success": False, "error": str(e), "items": []}

    async def put_memory_item(
        self,
        item_type: str,
        key: Optional[str] = None,
        summary: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Store a new memory item."""
        try:
            request_data = {"type": item_type, "key": key, "summary": summary, "data": data or {}}

            response = await self.client.post("/memory/put", json=request_data)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to store memory item: {e}")
            return {"success": False, "error": str(e)}

    async def search_memory_items(
        self, query: str, type_filter: Optional[str] = None, limit: int = 20
    ) -> Dict[str, Any]:
        """Search memory items by content."""
        try:
            # Since the memory agent doesn't have a search endpoint,
            # we'll get all items and filter client-side
            all_items = await self.list_memory_items(
                type_filter=type_filter, limit=1000  # Get more items for filtering
            )

            if not all_items.get("success", False):
                return all_items

            items = all_items.get("items", [])

            # Simple text search
            query_lower = query.lower()
            filtered_items = []

            for item in items:
                # Search in summary and data
                searchable_text = ""
                if item.get("summary"):
                    searchable_text += item["summary"].lower()
                if item.get("data"):
                    searchable_text += json.dumps(item["data"]).lower()

                if query_lower in searchable_text:
                    filtered_items.append(item)

            return {"success": True, "items": filtered_items[:limit], "total": len(filtered_items), "query": query}

        except Exception as e:
            self.logger.error(f"Failed to search memory items: {e}")
            return {"success": False, "error": str(e), "items": []}

    async def get_memory_types(self) -> List[str]:
        """Get all available memory types."""
        try:
            # Get a sample of items to extract types
            result = await self.list_memory_items(limit=1000)

            if result.get("success"):
                items = result.get("items", [])
                types = list(set(item.get("type") for item in items if item.get("type")))
                return sorted(types)
            else:
                return []
        except Exception as e:
            self.logger.error(f"Failed to get memory types: {e}")
            return []

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        try:
            # Try to get from health endpoint first
            health = await self.health_check()

            # Then get item counts by type
            types = await self.get_memory_types()
            type_counts = {}

            for mem_type in types:
                result = await self.list_memory_items(type_filter=mem_type, limit=1)
                if result.get("success"):
                    # Estimate count (this is not accurate but gives an idea)
                    type_counts[mem_type] = len(result.get("items", []))

            return {
                "health": health,
                "total_types": len(types),
                "types": types,
                "type_counts": type_counts,
                "estimated_total_items": sum(type_counts.values()),
            }

        except Exception as e:
            self.logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}

    def format_memory_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Format a memory item for display."""
        return {
            "id": item.get("id", ""),
            "type": item.get("type", ""),
            "key": item.get("key", ""),
            "summary": item.get("summary", ""),
            "data_preview": (
                str(item.get("data", {}))[:200] + "..."
                if len(str(item.get("data", {}))) > 200
                else str(item.get("data", {}))
            ),
            "created_at": item.get("created_at", ""),
            "expires_at": item.get("expires_at", ""),
            "data_full": item.get("data", {}),
        }
