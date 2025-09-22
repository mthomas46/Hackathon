"""Prompt Store Client - Client for Prompt Store Service.

This module provides a client for interacting with the Prompt Store service,
enabling browsing, creation, and management of prompts by category and tags.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
from infrastructure.config.config import get_config


class PromptStoreClient:
    """Client for interacting with the Prompt Store service."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0):
        """Initialize the prompt store client.

        Args:
            base_url: Base URL of the Prompt Store service
            timeout: Request timeout in seconds
        """
        self.config = get_config()
        self.base_url = base_url or self.config.prompt_service.base_url
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

    async def list_prompts(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        lifecycle_status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List prompts with optional filtering."""
        try:
            params = {"limit": limit, "offset": offset}
            if category:
                params["category"] = category
            if tags:
                params["tags"] = ",".join(tags)
            if lifecycle_status:
                params["lifecycle_status"] = lifecycle_status

            response = await self.client.get("/api/v1/prompts", params=params)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to list prompts: {e}")
            return {"success": False, "error": str(e), "prompts": []}

    async def create_prompt(
        self,
        name: str,
        category: str,
        content: str,
        description: str = "",
        variables: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new prompt."""
        try:
            request_data = {
                "name": name,
                "category": category,
                "content": content,
                "description": description,
                "variables": variables or [],
                "tags": tags or [],
            }

            response = await self.client.post("/api/v1/prompts", json=request_data)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to create prompt: {e}")
            return {"success": False, "error": str(e)}

    async def get_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """Get a specific prompt by ID."""
        try:
            response = await self.client.get(f"/api/v1/prompts/{prompt_id}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get prompt {prompt_id}: {e}")
            return {"success": False, "error": str(e)}

    async def update_prompt(self, prompt_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing prompt."""
        try:
            response = await self.client.put(f"/api/v1/prompts/{prompt_id}", json=updates)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to update prompt {prompt_id}: {e}")
            return {"success": False, "error": str(e)}

    async def delete_prompt(self, prompt_id: str) -> Dict[str, Any]:
        """Delete a prompt."""
        try:
            response = await self.client.delete(f"/api/v1/prompts/{prompt_id}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to delete prompt {prompt_id}: {e}")
            return {"success": False, "error": str(e)}

    async def fork_prompt(self, prompt_id: str, name: str) -> Dict[str, Any]:
        """Fork an existing prompt."""
        try:
            request_data = {"name": name}
            response = await self.client.post(f"/api/v1/prompts/{prompt_id}/fork", json=request_data)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to fork prompt {prompt_id}: {e}")
            return {"success": False, "error": str(e)}

    async def search_prompts(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Search prompts with advanced filters."""
        try:
            response = await self.client.post("/api/v1/prompts/search", json=query)
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to search prompts: {e}")
            return {"success": False, "error": str(e), "results": []}

    async def get_categories(self) -> List[str]:
        """Get all available prompt categories."""
        try:
            # Get all prompts and extract categories
            result = await self.list_prompts(limit=1000)
            if result.get("success"):
                prompts = result.get("prompts", [])
                categories = list(set(p.get("category") for p in prompts if p.get("category")))
                return sorted(categories)
            return []
        except Exception as e:
            self.logger.error(f"Failed to get categories: {e}")
            return []

    async def get_tags(self) -> List[str]:
        """Get all available prompt tags."""
        try:
            # Get all prompts and extract tags
            result = await self.list_prompts(limit=1000)
            if result.get("success"):
                prompts = result.get("prompts", [])
                all_tags = []
                for p in prompts:
                    all_tags.extend(p.get("tags", []))
                return sorted(list(set(all_tags)))
            return []
        except Exception as e:
            self.logger.error(f"Failed to get tags: {e}")
            return []

    async def get_prompts_by_category(self, category: str) -> Dict[str, Any]:
        """Get prompts by category."""
        try:
            response = await self.client.get(f"/api/v1/prompts/category/{category}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get prompts by category {category}: {e}")
            return {"success": False, "error": str(e), "prompts": []}

    async def get_prompts_by_tag(self, tag: str) -> Dict[str, Any]:
        """Get prompts by tag."""
        try:
            response = await self.client.get(f"/api/v1/prompts/tags/{tag}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get prompts by tag {tag}: {e}")
            return {"success": False, "error": str(e), "prompts": []}

    async def get_prompt_drift(self, prompt_id: str) -> Dict[str, Any]:
        """Check prompt drift for a specific prompt."""
        try:
            response = await self.client.get(f"/api/v1/prompts/{prompt_id}/drift")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get prompt drift for {prompt_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_prompt_suggestions(self, prompt_id: str) -> Dict[str, Any]:
        """Get suggestions for improving a prompt."""
        try:
            response = await self.client.get(f"/api/v1/prompts/{prompt_id}/suggestions")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get suggestions for {prompt_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary for prompts."""
        try:
            response = await self.client.get("/api/v1/analytics/summary")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get analytics summary: {e}")
            return {"success": False, "error": str(e)}

    async def get_prompt_analytics(self, prompt_id: str) -> Dict[str, Any]:
        """Get analytics for a specific prompt."""
        try:
            response = await self.client.get(f"/api/v1/analytics/prompts/{prompt_id}")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get analytics for {prompt_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_usage_analytics(self) -> Dict[str, Any]:
        """Get usage analytics."""
        try:
            response = await self.client.get("/api/v1/analytics/usage")
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get usage analytics: {e}")
            return {"success": False, "error": str(e)}

    def format_prompt_for_display(self, prompt: Dict[str, Any]) -> Dict[str, Any]:
        """Format a prompt for display in the dashboard."""
        return {
            "id": prompt.get("id", ""),
            "name": prompt.get("name", ""),
            "category": prompt.get("category", ""),
            "description": prompt.get("description", ""),
            "content_preview": (
                prompt.get("content", "")[:200] + "..."
                if len(prompt.get("content", "")) > 200
                else prompt.get("content", "")
            ),
            "variables": prompt.get("variables", []),
            "tags": prompt.get("tags", []),
            "is_active": prompt.get("is_active", True),
            "is_template": prompt.get("is_template", False),
            "lifecycle_status": prompt.get("lifecycle_status", "draft"),
            "created_by": prompt.get("created_by", ""),
            "created_at": prompt.get("created_at", ""),
            "updated_at": prompt.get("updated_at", ""),
            "version": prompt.get("version", 1),
            "performance_score": prompt.get("performance_score", 0.0),
            "usage_count": prompt.get("usage_count", 0),
            "content_full": prompt.get("content", ""),
        }
