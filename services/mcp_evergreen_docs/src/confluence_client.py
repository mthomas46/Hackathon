"""Confluence API client for Evergreen Documentation."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
import httpx
import base64
import json


@dataclass
class ConfluencePage:
    """Represents a Confluence page."""
    page_id: str
    title: str
    space_key: str
    content: str
    version: int
    created_at: datetime
    updated_at: datetime
    author: str
    url: str
    labels: List[str]
    metadata: Dict[str, Any]


@dataclass
class ConfluenceSpace:
    """Represents a Confluence space."""
    space_key: str
    name: str
    description: str
    homepage_id: str
    url: str


class ConfluenceAPIError(Exception):
    """Confluence API error."""
    pass


class ConfluenceClient:
    """
    Confluence API client for bi-directional sync.
    
    Provides:
    - Page CRUD operations
    - Content search
    - Version management
    - Space operations
    - Label management
    """
    
    def __init__(
        self,
        base_url: str,
        username: str,
        api_token: str,
        timeout: int = 30
    ):
        """
        Initialize Confluence client.
        
        Args:
            base_url: Confluence base URL (e.g., https://company.atlassian.net/wiki)
            username: Confluence username/email
            api_token: Confluence API token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        
        # Create basic auth header
        credentials = f"{username}:{api_token}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
    
    async def get_page(
        self,
        page_id: str,
        expand: Optional[List[str]] = None
    ) -> ConfluencePage:
        """
        Get a Confluence page by ID.
        
        Args:
            page_id: Page ID
            expand: Optional list of fields to expand (body.storage, version, etc.)
        
        Returns:
            ConfluencePage object
        
        Raises:
            ConfluenceAPIError: If page not found or API error
        """
        expand_params = ",".join(expand) if expand else "body.storage,version,history"
        
        response = await self.client.get(
            f"{self.base_url}/rest/api/content/{page_id}",
            params={"expand": expand_params}
        )
        
        if response.status_code == 404:
            raise ConfluenceAPIError(f"Page not found: {page_id}")
        elif response.status_code != 200:
            raise ConfluenceAPIError(
                f"Failed to get page: {response.status_code} - {response.text}"
            )
        
        data = response.json()
        return self._parse_page(data)
    
    async def get_page_by_title(
        self,
        space_key: str,
        title: str
    ) -> Optional[ConfluencePage]:
        """
        Get a page by title within a space.
        
        Args:
            space_key: Space key
            title: Page title
        
        Returns:
            ConfluencePage if found, None otherwise
        """
        response = await self.client.get(
            f"{self.base_url}/rest/api/content",
            params={
                "spaceKey": space_key,
                "title": title,
                "expand": "body.storage,version,history"
            }
        )
        
        if response.status_code != 200:
            raise ConfluenceAPIError(
                f"Failed to search pages: {response.status_code} - {response.text}"
            )
        
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            return None
        
        return self._parse_page(results[0])
    
    async def create_page(
        self,
        space_key: str,
        title: str,
        content: str,
        parent_id: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> ConfluencePage:
        """
        Create a new Confluence page.
        
        Args:
            space_key: Space key
            title: Page title
            content: Page content (HTML/storage format)
            parent_id: Optional parent page ID
            labels: Optional list of labels
        
        Returns:
            Created ConfluencePage
        """
        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }
        
        if parent_id:
            payload["ancestors"] = [{"id": parent_id}]
        
        response = await self.client.post(
            f"{self.base_url}/rest/api/content",
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            raise ConfluenceAPIError(
                f"Failed to create page: {response.status_code} - {response.text}"
            )
        
        page_data = response.json()
        page = self._parse_page(page_data)
        
        # Add labels if provided
        if labels:
            await self.add_labels(page.page_id, labels)
        
        return page
    
    async def update_page(
        self,
        page_id: str,
        title: str,
        content: str,
        version: int,
        message: Optional[str] = None
    ) -> ConfluencePage:
        """
        Update an existing Confluence page.
        
        Args:
            page_id: Page ID
            title: New page title
            content: New content
            version: Current version number (will be incremented)
            message: Optional version message
        
        Returns:
            Updated ConfluencePage
        """
        payload = {
            "type": "page",
            "title": title,
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            },
            "version": {
                "number": version + 1
            }
        }
        
        if message:
            payload["version"]["message"] = message
        
        response = await self.client.put(
            f"{self.base_url}/rest/api/content/{page_id}",
            json=payload
        )
        
        if response.status_code != 200:
            raise ConfluenceAPIError(
                f"Failed to update page: {response.status_code} - {response.text}"
            )
        
        return self._parse_page(response.json())
    
    async def delete_page(self, page_id: str) -> bool:
        """
        Delete a Confluence page.
        
        Args:
            page_id: Page ID
        
        Returns:
            True if deleted successfully
        """
        response = await self.client.delete(
            f"{self.base_url}/rest/api/content/{page_id}"
        )
        
        if response.status_code == 404:
            return False  # Already deleted
        elif response.status_code != 204:
            raise ConfluenceAPIError(
                f"Failed to delete page: {response.status_code} - {response.text}"
            )
        
        return True
    
    async def search_pages(
        self,
        cql: str,
        limit: int = 25
    ) -> List[ConfluencePage]:
        """
        Search pages using CQL (Confluence Query Language).
        
        Args:
            cql: CQL query string
            limit: Maximum results
        
        Returns:
            List of matching pages
        """
        response = await self.client.get(
            f"{self.base_url}/rest/api/content/search",
            params={
                "cql": cql,
                "limit": limit,
                "expand": "body.storage,version,history"
            }
        )
        
        if response.status_code != 200:
            raise ConfluenceAPIError(
                f"Failed to search: {response.status_code} - {response.text}"
            )
        
        data = response.json()
        return [self._parse_page(page) for page in data.get("results", [])]
    
    async def get_space(self, space_key: str) -> ConfluenceSpace:
        """
        Get space information.
        
        Args:
            space_key: Space key
        
        Returns:
            ConfluenceSpace object
        """
        response = await self.client.get(
            f"{self.base_url}/rest/api/space/{space_key}",
            params={"expand": "homepage,description.plain"}
        )
        
        if response.status_code == 404:
            raise ConfluenceAPIError(f"Space not found: {space_key}")
        elif response.status_code != 200:
            raise ConfluenceAPIError(
                f"Failed to get space: {response.status_code} - {response.text}"
            )
        
        data = response.json()
        return ConfluenceSpace(
            space_key=data["key"],
            name=data["name"],
            description=data.get("description", {}).get("plain", {}).get("value", ""),
            homepage_id=data.get("homepage", {}).get("id", ""),
            url=f"{self.base_url}{data['_links']['webui']}"
        )
    
    async def get_pages_in_space(
        self,
        space_key: str,
        limit: int = 100
    ) -> List[ConfluencePage]:
        """
        Get all pages in a space.
        
        Args:
            space_key: Space key
            limit: Maximum results per request
        
        Returns:
            List of pages in the space
        """
        pages = []
        start = 0
        
        while True:
            response = await self.client.get(
                f"{self.base_url}/rest/api/content",
                params={
                    "spaceKey": space_key,
                    "type": "page",
                    "limit": limit,
                    "start": start,
                    "expand": "body.storage,version,history"
                }
            )
            
            if response.status_code != 200:
                raise ConfluenceAPIError(
                    f"Failed to get pages: {response.status_code} - {response.text}"
                )
            
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                break
            
            pages.extend([self._parse_page(page) for page in results])
            
            # Check if there are more pages
            if len(results) < limit:
                break
            
            start += limit
        
        return pages
    
    async def add_labels(
        self,
        page_id: str,
        labels: List[str]
    ) -> bool:
        """
        Add labels to a page.
        
        Args:
            page_id: Page ID
            labels: List of label names
        
        Returns:
            True if successful
        """
        payload = [{"name": label} for label in labels]
        
        response = await self.client.post(
            f"{self.base_url}/rest/api/content/{page_id}/label",
            json=payload
        )
        
        if response.status_code not in [200, 201]:
            raise ConfluenceAPIError(
                f"Failed to add labels: {response.status_code} - {response.text}"
            )
        
        return True
    
    async def get_page_labels(self, page_id: str) -> List[str]:
        """
        Get labels for a page.
        
        Args:
            page_id: Page ID
        
        Returns:
            List of label names
        """
        response = await self.client.get(
            f"{self.base_url}/rest/api/content/{page_id}/label"
        )
        
        if response.status_code != 200:
            raise ConfluenceAPIError(
                f"Failed to get labels: {response.status_code} - {response.text}"
            )
        
        data = response.json()
        return [label["name"] for label in data.get("results", [])]
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _parse_page(self, data: Dict[str, Any]) -> ConfluencePage:
        """
        Parse Confluence API page data.
        
        Args:
            data: Raw API response data
        
        Returns:
            ConfluencePage object
        """
        # Extract content
        content = ""
        if "body" in data and "storage" in data["body"]:
            content = data["body"]["storage"]["value"]
        
        # Extract version
        version = data.get("version", {}).get("number", 1)
        
        # Extract history
        history = data.get("history", {})
        created_at = history.get("createdDate", datetime.now().isoformat())
        created_by = history.get("createdBy", {}).get("displayName", "Unknown")
        
        # Extract latest version info
        version_info = data.get("version", {})
        updated_at = version_info.get("when", created_at)
        updated_by = version_info.get("by", {}).get("displayName", created_by)
        
        # Extract labels (if available)
        labels = []
        if "metadata" in data and "labels" in data["metadata"]:
            labels = [
                label["name"] 
                for label in data["metadata"]["labels"].get("results", [])
            ]
        
        return ConfluencePage(
            page_id=data["id"],
            title=data["title"],
            space_key=data["space"]["key"],
            content=content,
            version=version,
            created_at=datetime.fromisoformat(created_at.replace("Z", "+00:00")),
            updated_at=datetime.fromisoformat(updated_at.replace("Z", "+00:00")),
            author=updated_by,
            url=f"{self.base_url}{data['_links']['webui']}",
            labels=labels,
            metadata={
                "type": data["type"],
                "status": data["status"],
                "created_by": created_by
            }
        )

