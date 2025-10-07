"""Base HTTP client for all backend services."""

import httpx
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager


logger = logging.getLogger(__name__)


class BaseClient:
    """Base HTTP client with common functionality."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        """
        Initialize the base client.
        
        Args:
            base_url: Base URL for the service
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @asynccontextmanager
    async def _request(self, method: str, endpoint: str, **kwargs):
        """
        Make an HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for httpx request
            
        Yields:
            Response object
        """
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            yield response
        except httpx.TimeoutException:
            logger.error(f"Request timeout: {method} {url}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {method} {url}")
            raise
        except Exception as e:
            logger.error(f"Request failed: {method} {url} - {str(e)}")
            raise
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response JSON data
        """
        async with self._request("GET", endpoint, params=params) as response:
            return response.json()
    
    async def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None, data: Optional[Any] = None) -> Dict[str, Any]:
        """
        Make a POST request.
        
        Args:
            endpoint: API endpoint
            json: JSON body
            data: Form data
            
        Returns:
            Response JSON data
        """
        async with self._request("POST", endpoint, json=json, data=data) as response:
            return response.json()
    
    async def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a PUT request.
        
        Args:
            endpoint: API endpoint
            json: JSON body
            
        Returns:
            Response JSON data
        """
        async with self._request("PUT", endpoint, json=json) as response:
            return response.json()
    
    async def delete(self, endpoint: str) -> Dict[str, Any]:
        """
        Make a DELETE request.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Response JSON data
        """
        async with self._request("DELETE", endpoint) as response:
            return response.json()
    
    async def health_check(self) -> bool:
        """
        Check if the service is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.get("/health")
            return response.get("status") == "healthy"
        except Exception:
            return False
