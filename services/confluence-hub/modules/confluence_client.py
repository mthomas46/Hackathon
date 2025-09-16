"""Confluence API client for interacting with Confluence REST API."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Client for interacting with Confluence API."""
    
    def __init__(self, base_url: str, username: str, api_token: str, is_cloud: bool = True):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.api_token = api_token
        self.is_cloud = is_cloud
        self.timeout = httpx.Timeout(30.0)
        
    def _get_api_endpoint(self) -> str:
        """Get API endpoint based on Confluence type."""
        return f"{self.base_url}/wiki/rest/api" if self.is_cloud else f"{self.base_url}/rest/api"
    
    def _get_auth(self) -> tuple:
        """Get authentication tuple."""
        return (self.username, self.api_token)
    
    async def test_connectivity(self) -> bool:
        """Test connection to Confluence."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                endpoint = f"{self._get_api_endpoint()}/user/current"
                response = await client.get(endpoint, auth=self._get_auth())
                
                if response.status_code == 200:
                    user_data = response.json()
                    display_name = user_data.get('displayName', 'Unknown')
                    logger.info(f"Connected to Confluence as user: {display_name}")
                    return True
                elif response.status_code == 404:
                    # Try alternative endpoint for older versions
                    endpoint = f"{self._get_api_endpoint()}/content?limit=1"
                    response = await client.get(endpoint, auth=self._get_auth())
                    if response.status_code == 200:
                        logger.info("Connected to Confluence (legacy endpoint)")
                        return True
                
                logger.error(f"Confluence connectivity test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Confluence connectivity test error: {str(e)}")
            return False
    
    async def get_page_by_id(self, page_id: str, expand: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get a specific page by ID."""
        if expand is None:
            expand = ['space', 'version', 'ancestors', 'children.page', 'body.storage']
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                expand_param = ','.join(expand)
                endpoint = f"{self._get_api_endpoint()}/content/{page_id}?expand={expand_param}"
                response = await client.get(endpoint, auth=self._get_auth())
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching page {page_id}: {str(e)}")
            raise
    
    async def search_pages_by_title(self, title: str, space_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for pages by title."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                cql = f'title = "{title}" AND type = page'
                if space_key:
                    cql += f' AND space = "{space_key}"'
                
                params = {
                    'cql': cql,
                    'expand': 'space,version',
                    'limit': 50
                }
                
                endpoint = f"{self._get_api_endpoint()}/content/search"
                response = await client.get(endpoint, params=params, auth=self._get_auth())
                response.raise_for_status()
                return response.json().get('results', [])
        except Exception as e:
            logger.error(f"Error searching for page '{title}': {str(e)}")
            raise
    
    async def get_child_pages(self, page_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get direct child pages of a page."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {
                    'expand': 'space,version,ancestors',
                    'limit': limit
                }
                
                endpoint = f"{self._get_api_endpoint()}/content/{page_id}/child/page"
                response = await client.get(endpoint, params=params, auth=self._get_auth())
                response.raise_for_status()
                return response.json().get('results', [])
        except Exception as e:
            logger.error(f"Error fetching child pages for {page_id}: {str(e)}")
            raise
    
    async def get_all_descendant_pages(
        self, 
        page_id: str, 
        max_depth: int = 10, 
        current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """Recursively get all descendant pages."""
        if current_depth >= max_depth:
            logger.warning(f"Maximum depth {max_depth} reached for page {page_id}")
            return []
        
        child_pages = await self.get_child_pages(page_id)
        all_descendants = list(child_pages)
        
        # Recursively get children of each child page
        for child_page in child_pages:
            try:
                grandchildren = await self.get_all_descendant_pages(
                    child_page['id'], max_depth, current_depth + 1
                )
                all_descendants.extend(grandchildren)
            except Exception as e:
                page_title = child_page.get('title', 'Unknown')
                page_id = child_page['id']
                logger.warning(f"Error fetching descendants for page {page_title} ({page_id}): {str(e)}")
        
        return all_descendants