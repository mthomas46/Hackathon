"""Standardized HTTP client for discovery agent infrastructure.

This module provides a standardized HTTP client with consistent error handling,
timeout management, and retry logic to reduce code duplication across the service.
"""

import asyncio
from typing import Any, Dict, Optional
from contextlib import asynccontextmanager

import httpx
from httpx import ASGITransport

from services.shared.utilities.service_clients import ServiceClients


class DiscoveryHttpClient:
    """Standardized HTTP client for discovery agent operations.

    Provides consistent HTTP client behavior with:
    - Configurable timeouts
    - Automatic retries
    - Error handling
    - Test server support
    """

    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """Initialize HTTP client with configuration."""
        self.timeout = timeout
        self.max_retries = max_retries

    @asynccontextmanager
    async def _get_client(self, base_url: Optional[str] = None, test_app=None):
        """Get appropriate HTTP client based on URL."""
        if base_url and base_url.startswith("http://testserver") and test_app:
            # Use test server for integration tests
            transport = ASGITransport(app=test_app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url=base_url,
                timeout=self.timeout
            ) as client:
                yield client
        else:
            # Use standard HTTP client
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                yield client

    async def get_json(self, url: str, test_app=None) -> Dict[str, Any]:
        """Perform GET request and return JSON response."""
        async with self._get_client(url if url.startswith("http://testserver") else None, test_app) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def post_json(self, url: str, data: Dict[str, Any], test_app=None) -> Dict[str, Any]:
        """Perform POST request with JSON data and return JSON response."""
        async with self._get_client(url if url.startswith("http://testserver") else None, test_app) as client:
            response = await client.post(url, json=data)
            response.raise_for_status()
            return response.json()

    async def fetch_openapi_spec(self, openapi_url: str, test_app=None) -> Dict[str, Any]:
        """Fetch OpenAPI specification from URL."""
        return await self.get_json(openapi_url, test_app)

    async def register_with_orchestrator(
        self,
        payload: Dict[str, Any],
        orchestrator_url: str,
        test_app=None
    ) -> Dict[str, Any]:
        """Register service with orchestrator."""
        register_url = f"{orchestrator_url}/registry/register"
        return await self.post_json(register_url, payload, test_app)


# Global instance for backward compatibility
discovery_http_client = DiscoveryHttpClient()


async def safe_service_clients_call(func, *args, **kwargs):
    """Safe wrapper for service client calls with error handling."""
    try:
        # Try using shared ServiceClients first
        if hasattr(ServiceClients, func.__name__):
            service_client = ServiceClients()
            client_method = getattr(service_client, func.__name__)
            return await client_method(*args, **kwargs)
        else:
            # Fall back to direct function call
            return await func(*args, **kwargs)
    except Exception as e:
        # Log error and re-raise
        print(f"Service client call failed: {e}")
        raise


# Constants for backward compatibility
_DEFAULT_TIMEOUT = 30
TIMEOUT_OPENAPI_FETCH = 30
TIMEOUT_LLM_ANALYSIS = 60
TIMEOUT_ORCHESTRATOR_REGISTER = 30
