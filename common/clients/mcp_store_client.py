"""
HTTP client for MCP Store service.

Provides methods for managing MCP packages, versions, and marketplace features.
"""

import logging
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime

from common.http_client import ServiceHTTPClient

logger = logging.getLogger(__name__)


class MCPStoreClient:
    """
    Client for interacting with MCP Store service.
    
    Enables other services to:
    - Manage MCP packages and versions
    - Upload and download packages
    - Search and discover packages
    - Access marketplace features
    - Export and import packages
    """
    
    def __init__(self, base_url: str = "http://localhost:5648"):
        """
        Initialize MCP Store client.
        
        Args:
            base_url: Base URL of MCP Store service
        """
        self.client = ServiceHTTPClient(
            base_url=base_url,
            service_name="mcp-store",
            timeout=60,  # Longer timeout for uploads/downloads
            max_retries=3,
        )
        logger.info(f"MCPStoreClient initialized for {base_url}")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.close()
    
    async def health_check(self) -> bool:
        """
        Check if MCP Store is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return await self.client.health_check()
    
    # ========================================================================
    # Package Management
    # ========================================================================
    
    async def create_package(
        self,
        name: str,
        description: str,
        owner_id: str,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new MCP package.
        
        Args:
            name: Package name (unique)
            description: Package description
            owner_id: Owner/author ID
            tags: Package tags
            categories: Package categories
            metadata: Additional metadata
        
        Returns:
            Created package data
        """
        try:
            payload = {
                "name": name,
                "description": description,
                "owner_id": owner_id,
            }
            
            if tags:
                payload["tags"] = tags
            if categories:
                payload["categories"] = categories
            if metadata:
                payload["metadata"] = metadata
            
            result = await self.client.post("/api/v1/packages", json=payload)
            
            logger.info(f"Created package: {name}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to create package {name}: {e}")
            raise
    
    async def get_package(self, package_id: str) -> Optional[Dict[str, Any]]:
        """
        Get package by ID.
        
        Args:
            package_id: Package ID
        
        Returns:
            Package data or None if not found
        """
        try:
            return await self.client.get(f"/api/v1/packages/{package_id}")
        except Exception as e:
            logger.warning(f"Failed to get package {package_id}: {e}")
            return None
    
    async def get_package_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get package by name.
        
        Args:
            name: Package name
        
        Returns:
            Package data or None if not found
        """
        try:
            result = await self.search_packages(query=name, limit=1)
            if result and len(result) > 0:
                # Return exact match if found
                for pkg in result:
                    if pkg.get("name") == name:
                        return pkg
            return None
        except Exception as e:
            logger.warning(f"Failed to get package by name {name}: {e}")
            return None
    
    async def list_packages(
        self,
        limit: int = 50,
        offset: int = 0,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List packages.
        
        Args:
            limit: Maximum number of packages
            offset: Pagination offset
            status: Filter by status (draft/published/deprecated/archived)
        
        Returns:
            List of packages
        """
        try:
            params = {"limit": limit, "offset": offset}
            if status:
                params["status"] = status
            
            result = await self.client.get("/api/v1/packages", params=params)
            return result.get("packages", [])
        except Exception as e:
            logger.warning(f"Failed to list packages: {e}")
            return []
    
    async def update_package(
        self,
        package_id: str,
        **updates
    ) -> Dict[str, Any]:
        """
        Update package metadata.
        
        Args:
            package_id: Package ID
            **updates: Fields to update
        
        Returns:
            Updated package data
        """
        try:
            result = await self.client.put(f"/api/v1/packages/{package_id}", json=updates)
            logger.info(f"Updated package {package_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to update package {package_id}: {e}")
            raise
    
    async def delete_package(self, package_id: str) -> bool:
        """
        Delete package.
        
        Args:
            package_id: Package ID
        
        Returns:
            True if deleted successfully
        """
        try:
            await self.client.delete(f"/api/v1/packages/{package_id}")
            logger.info(f"Deleted package {package_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete package {package_id}: {e}")
            return False
    
    # ========================================================================
    # Version Management
    # ========================================================================
    
    async def upload_version(
        self,
        package_id: str,
        version: str,
        file_data: bytes,
        changelog: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Upload a new package version.
        
        Args:
            package_id: Package ID
            version: Version string (e.g., "1.0.0")
            file_data: Package file data (.mcp file)
            changelog: Version changelog
            metadata: Additional metadata
        
        Returns:
            Uploaded version data
        """
        try:
            # Note: Actual implementation would use multipart/form-data
            # This is a simplified version
            payload = {
                "version": version,
                "file_data": file_data.hex(),  # Simplified - would be multipart in reality
            }
            
            if changelog:
                payload["changelog"] = changelog
            if metadata:
                payload["metadata"] = metadata
            
            result = await self.client.post(
                f"/api/v1/packages/{package_id}/versions",
                json=payload
            )
            
            logger.info(f"Uploaded version {version} for package {package_id}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to upload version {version} for package {package_id}: {e}")
            raise
    
    async def get_version(
        self,
        package_id: str,
        version: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get version details.
        
        Args:
            package_id: Package ID
            version: Version string
        
        Returns:
            Version data or None if not found
        """
        try:
            return await self.client.get(f"/api/v1/packages/{package_id}/versions/{version}")
        except Exception as e:
            logger.warning(f"Failed to get version {version} for package {package_id}: {e}")
            return None
    
    async def list_versions(
        self,
        package_id: str,
    ) -> List[Dict[str, Any]]:
        """
        List all versions of a package.
        
        Args:
            package_id: Package ID
        
        Returns:
            List of versions
        """
        try:
            result = await self.client.get(f"/api/v1/packages/{package_id}/versions")
            return result.get("versions", [])
        except Exception as e:
            logger.warning(f"Failed to list versions for package {package_id}: {e}")
            return []
    
    async def download_version(
        self,
        package_id: str,
        version: str,
    ) -> Optional[bytes]:
        """
        Download a package version.
        
        Args:
            package_id: Package ID
            version: Version string
        
        Returns:
            Package file data or None if failed
        """
        try:
            result = await self.client.get(
                f"/api/v1/packages/{package_id}/versions/{version}/download"
            )
            # In reality, this would return binary data
            # This is simplified
            return result.get("file_data", b"")
        except Exception as e:
            logger.error(f"Failed to download version {version} for package {package_id}: {e}")
            return None
    
    # ========================================================================
    # Search & Discovery
    # ========================================================================
    
    async def search_packages(
        self,
        query: str,
        limit: int = 20,
        tags: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search packages.
        
        Args:
            query: Search query
            limit: Maximum results
            tags: Filter by tags
            categories: Filter by categories
        
        Returns:
            List of matching packages
        """
        try:
            params = {"query": query, "limit": limit}
            if tags:
                params["tags"] = ",".join(tags)
            if categories:
                params["categories"] = ",".join(categories)
            
            result = await self.client.get("/api/v1/search", params=params)
            return result.get("results", [])
        except Exception as e:
            logger.warning(f"Failed to search packages with query '{query}': {e}")
            return []
    
    # ========================================================================
    # Marketplace Features
    # ========================================================================
    
    async def star_package(self, package_id: str, user_id: str) -> bool:
        """
        Star a package.
        
        Args:
            package_id: Package ID
            user_id: User ID
        
        Returns:
            True if starred successfully
        """
        try:
            await self.client.post(
                f"/api/v1/packages/{package_id}/star",
                json={"user_id": user_id}
            )
            logger.info(f"User {user_id} starred package {package_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to star package {package_id}: {e}")
            return False
    
    async def unstar_package(self, package_id: str, user_id: str) -> bool:
        """
        Unstar a package.
        
        Args:
            package_id: Package ID
            user_id: User ID
        
        Returns:
            True if unstarred successfully
        """
        try:
            await self.client.delete(f"/api/v1/packages/{package_id}/star?user_id={user_id}")
            logger.info(f"User {user_id} unstarred package {package_id}")
            return True
        except Exception as e:
            logger.warning(f"Failed to unstar package {package_id}: {e}")
            return False
    
    async def get_trending_packages(
        self,
        time_window_days: int = 7,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get trending packages.
        
        Args:
            time_window_days: Time window in days
            limit: Maximum results
        
        Returns:
            List of trending packages
        """
        try:
            params = {"days": time_window_days, "limit": limit}
            result = await self.client.get("/api/v1/marketplace/trending", params=params)
            return result.get("packages", [])
        except Exception as e:
            logger.warning(f"Failed to get trending packages: {e}")
            return []
    
    async def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get popular tags.
        
        Args:
            limit: Maximum tags
        
        Returns:
            List of tags with counts
        """
        try:
            params = {"limit": limit}
            result = await self.client.get("/api/v1/marketplace/popular-tags", params=params)
            return result.get("tags", [])
        except Exception as e:
            logger.warning(f"Failed to get popular tags: {e}")
            return []
    
    async def get_marketplace_stats(self) -> Dict[str, Any]:
        """
        Get marketplace statistics.
        
        Returns:
            Marketplace stats (total packages, downloads, etc.)
        """
        try:
            return await self.client.get("/api/v1/marketplace/stats")
        except Exception as e:
            logger.warning(f"Failed to get marketplace stats: {e}")
            return {}
    
    # ========================================================================
    # Export/Import
    # ========================================================================
    
    async def export_package(
        self,
        package_id: str,
        version: Optional[str] = None,
        include_all_versions: bool = False,
    ) -> Optional[bytes]:
        """
        Export package as .mcp file.
        
        Args:
            package_id: Package ID
            version: Specific version (optional)
            include_all_versions: Export all versions
        
        Returns:
            .mcp file data or None if failed
        """
        try:
            params = {}
            if version:
                params["version"] = version
            if include_all_versions:
                params["all_versions"] = "true"
            
            result = await self.client.post(
                f"/api/v1/packages/{package_id}/export",
                json=params
            )
            
            logger.info(f"Exported package {package_id}")
            
            # In reality, this would return binary data
            return result.get("file_data", b"")
        except Exception as e:
            logger.error(f"Failed to export package {package_id}: {e}")
            return None
    
    async def import_package(self, file_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Import package from .mcp file.
        
        Args:
            file_data: .mcp file data
        
        Returns:
            Imported package data or None if failed
        """
        try:
            # In reality, this would use multipart/form-data
            payload = {"file_data": file_data.hex()}
            
            result = await self.client.post("/api/v1/import", json=payload)
            
            logger.info(f"Imported package: {result.get('package_id')}")
            
            return result
        except Exception as e:
            logger.error(f"Failed to import package: {e}")
            return None

