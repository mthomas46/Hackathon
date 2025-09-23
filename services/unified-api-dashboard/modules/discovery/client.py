"""
Discovery Client - API Service Discovery and Registration
"""

import logging
from typing import Any, Dict, List

import httpx

logger = logging.getLogger(__name__)


class DiscoveryClient:
    """Client for service discovery operations."""

    def __init__(self, base_url: str = "http://localhost:5045"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def discover_services(self) -> List[Dict[str, Any]]:
        """Discover all available services."""
        try:
            response = await self.client.get(f"{self.base_url}/services")
            response.raise_for_status()
            data = response.json()
            return data.get("services", [])
        except Exception as e:
            logger.error(f"Service discovery failed: {e}")
            return []

    async def scan_network(self) -> Dict[str, Any]:
        """Trigger a network scan for services."""
        try:
            response = await self.client.post(f"{self.base_url}/scan")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Network scan failed: {e}")
            return {"error": str(e)}

    async def register_service(self, service_info: Dict[str, Any]) -> bool:
        """Register a new service."""
        try:
            response = await self.client.post(f"{self.base_url}/register", json=service_info)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Service registration failed: {e}")
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
