"""Client for MCP Store API."""

import logging
from typing import List, Dict, Any, Optional

from clients.base_client import BaseClient


logger = logging.getLogger(__name__)


class MCPStoreClient(BaseClient):
    """Client for interacting with MCP Store."""
    
    def __init__(self, base_url: str = "http://localhost:5648"):
        """Initialize the MCP Store client."""
        super().__init__(base_url)
    
    # ==================== Package Management ====================
    
    async def create_package(
        self,
        name: str,
        description: str,
        owner_id: str,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        is_public: bool = False
    ) -> Dict[str, Any]:
        """Create a new MCP package."""
        payload = {
            "name": name,
            "description": description,
            "owner_id": owner_id,
            "tags": tags or [],
            "categories": categories or [],
            "is_public": is_public
        }
        return await self.post("/api/v1/packages", json=payload)
    
    async def get_package(self, package_id: str) -> Dict[str, Any]:
        """Get a package by ID."""
        return await self.get(f"/api/v1/packages/{package_id}")
    
    async def list_packages(
        self,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        is_public: Optional[bool] = None,
        sort_by: str = "created_at",
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List packages with filters."""
        params = {
            "sort_by": sort_by,
            "limit": limit,
            "offset": offset
        }
        if search:
            params["search_query"] = search
        if tags:
            params["tags"] = ",".join(tags)
        if categories:
            params["categories"] = ",".join(categories)
        if is_public is not None:
            params["is_public"] = is_public
        
        return await self.get("/api/v1/packages", params=params)
    
    async def update_package(
        self,
        package_id: str,
        **updates
    ) -> Dict[str, Any]:
        """Update a package."""
        return await self.put(f"/api/v1/packages/{package_id}", json=updates)
    
    async def delete_package(self, package_id: str) -> Dict[str, Any]:
        """Delete a package."""
        return await self.delete(f"/api/v1/packages/{package_id}")
    
    # ==================== Version Management ====================
    
    async def upload_version(
        self,
        package_id: str,
        version_string: str,
        file_data: bytes,
        release_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a new package version."""
        files = {"file": ("package.mcp", file_data, "application/octet-stream")}
        data = {
            "version_string": version_string,
            "release_notes": release_notes or ""
        }
        return await self.post(
            f"/api/v1/packages/{package_id}/versions",
            data=data,
            files=files
        )
    
    async def get_version(self, version_id: str) -> Dict[str, Any]:
        """Get a version by ID."""
        return await self.get(f"/api/v1/versions/{version_id}")
    
    async def list_versions(
        self,
        package_id: str,
        is_active: Optional[bool] = True
    ) -> List[Dict[str, Any]]:
        """List versions for a package."""
        params = {}
        if is_active is not None:
            params["is_active"] = is_active
        return await self.get(f"/api/v1/packages/{package_id}/versions", params=params)
    
    async def download_version(self, version_id: str) -> bytes:
        """Download a package version."""
        # This would return the binary data
        response = await self.get(f"/api/v1/versions/{version_id}/download")
        return response  # Would need special handling for binary data
    
    # ==================== Marketplace ====================
    
    async def star_package(
        self,
        package_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Star a package."""
        return await self.post(
            f"/api/v1/packages/{package_id}/star",
            params={"user_id": user_id}
        )
    
    async def unstar_package(
        self,
        package_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Unstar a package."""
        return await self.delete(
            f"/api/v1/packages/{package_id}/star",
            params={"user_id": user_id}
        )
    
    async def get_trending(
        self,
        days: int = 7,
        sort_by: str = "downloads",
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get trending packages."""
        return await self.get(
            "/api/v1/marketplace/trending",
            params={"days": days, "sort_by": sort_by, "limit": limit}
        )
    
    async def get_popular_tags(self, limit: int = 20) -> Dict[str, Any]:
        """Get popular tags."""
        return await self.get(
            "/api/v1/marketplace/tags/popular",
            params={"limit": limit}
        )
    
    async def get_popular_categories(self, limit: int = 10) -> Dict[str, Any]:
        """Get popular categories."""
        return await self.get(
            "/api/v1/marketplace/categories/popular",
            params={"limit": limit}
        )
    
    async def get_marketplace_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics."""
        return await self.get("/api/v1/marketplace/stats")
    
    # ==================== Export/Import ====================
    
    async def export_package(
        self,
        package_id: str,
        version_id: Optional[str] = None,
        include_all_versions: bool = False
    ) -> bytes:
        """Export a package to .mcp file."""
        params = {"include_all_versions": include_all_versions}
        if version_id:
            params["version_id"] = version_id
        # Would return binary data
        response = await self.post(
            f"/api/v1/packages/{package_id}/export",
            params=params
        )
        return response
    
    async def import_package(
        self,
        file_data: bytes,
        owner_id: str,
        overwrite_existing: bool = False
    ) -> Dict[str, Any]:
        """Import a package from .mcp file."""
        files = {"file": ("package.mcp", file_data, "application/x-tar")}
        data = {
            "owner_id": owner_id,
            "overwrite_existing": overwrite_existing
        }
        return await self.post("/api/v1/packages/import", data=data, files=files)
