"""Orchestrator Service Client for external service communication."""

from typing import Dict, Any, Optional
import asyncio
from services.shared.integrations.clients.clients import ServiceClients


class OrchestratorServiceClient:
    """Service client for orchestrator external communications."""

    def __init__(self, timeout: int = 30):
        self.client = ServiceClients(timeout=timeout)

    async def call_service(
        self,
        service_name: str,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Call an external service endpoint."""
        # This is a simplified implementation - in practice, you'd resolve
        # service URLs from a registry or configuration
        service_urls = {
            "reporting": "http://reporting:5030",
            "doc_store": "http://doc-store:5020",
            "analysis_service": "http://analysis-service:5010",
            # Add other services as needed
        }

        base_url = service_urls.get(service_name)
        if not base_url:
            raise ValueError(f"Unknown service: {service_name}")

        url = f"{base_url}{endpoint}"

        if method.upper() == "GET":
            return await self.client.get_json(url, headers=headers)
        elif method.upper() == "POST":
            return await self.client.post_json(url, data or {}, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
