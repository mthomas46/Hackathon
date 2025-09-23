"""
Discovery Agent Client

Handles communication with the Discovery Agent service for:
- Service registration and discovery
- Health status monitoring
- OpenAPI specification retrieval
- Service metadata management
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

import httpx

from ...config import Config


class DiscoveryClient:
    """Client for interacting with the Discovery Agent."""

    def __init__(self, config: Config):
        self.config = config
        self.base_url = config.discovery_agent_url.rstrip('/')
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        self.client = httpx.AsyncClient(timeout=self.timeout)

    async def get_all_services(self) -> List[Dict[str, Any]]:
        """Get all registered services from Discovery Agent."""
        try:
            response = await self.client.get(f"{self.base_url}/services")
            response.raise_for_status()
            data = response.json()
            return data.get("services", [])
        except Exception as e:
            print(f"Error fetching services: {e}")
            return []

    async def get_service_details(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific service."""
        try:
            response = await self.client.get(f"{self.base_url}/services/{service_name}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching service details for {service_name}: {e}")
            return None

    async def get_openapi_spec(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get OpenAPI specification for a service."""
        try:
            response = await self.client.get(f"{self.base_url}/services/{service_name}/openapi")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching OpenAPI spec for {service_name}: {e}")
            return None

    async def register_service(self, service_info: Dict[str, Any]) -> bool:
        """Register this dashboard service with the Discovery Agent."""
        try:
            registration_data = {
                "name": self.config.service_name,
                "version": self.config.version,
                "url": f"http://localhost:{self.config.api_port}",
                "description": "Unified API Ecosystem Dashboard",
                "health_endpoint": "/health",
                "tags": ["dashboard", "api", "monitoring", "discovery"],
                "metadata": {
                    "type": "dashboard",
                    "capabilities": ["api_discovery", "health_monitoring", "testing", "analytics"],
                    "ports": {
                        "api": self.config.api_port,
                        "dashboard": self.config.streamlit_port
                    }
                }
            }

            response = await self.client.post(
                f"{self.base_url}/services",
                json=registration_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"Error registering service: {e}")
            return False

    async def update_service_health(self, health_status: str) -> bool:
        """Update service health status."""
        try:
            health_data = {
                "status": health_status,
                "timestamp": datetime.now().isoformat(),
                "version": self.config.version
            }

            response = await self.client.put(
                f"{self.base_url}/services/{self.config.service_name}/health",
                json=health_data
            )
            response.raise_for_status()
            return True

        except Exception as e:
            print(f"Error updating health status: {e}")
            return False

    async def discover_service_dependencies(self, service_name: str) -> List[str]:
        """Discover services that the given service depends on."""
        try:
            # This would typically analyze the service's configuration
            # or API calls to determine dependencies
            service_details = await self.get_service_details(service_name)
            if not service_details:
                return []

            # Simple dependency discovery based on service type
            dependencies = []
            service_type = service_details.get("metadata", {}).get("type", "")

            if service_type in ["orchestrator", "interpreter", "doc_store", "prompt_store"]:
                dependencies.extend(["discovery_agent"])

            if service_type in ["bedrock_proxy", "summarizer_hub"]:
                dependencies.extend(["discovery_agent", "doc_store"])

            if service_type == "frontend":
                dependencies.extend(["orchestrator", "doc_store", "prompt_store"])

            return list(set(dependencies))  # Remove duplicates

        except Exception as e:
            print(f"Error discovering dependencies for {service_name}: {e}")
            return []

    async def get_service_topology(self) -> Dict[str, Any]:
        """Get the complete service topology including dependencies."""
        try:
            services = await self.get_all_services()
            topology = {
                "services": {},
                "dependencies": {},
                "last_updated": datetime.now().isoformat()
            }

            for service in services:
                service_name = service.get("name")
                if not service_name:
                    continue

                # Get service dependencies
                dependencies = await self.discover_service_dependencies(service_name)

                topology["services"][service_name] = {
                    "info": service,
                    "dependencies": dependencies
                }

                # Build reverse dependency mapping
                for dep in dependencies:
                    if dep not in topology["dependencies"]:
                        topology["dependencies"][dep] = []
                    topology["dependencies"][dep].append(service_name)

            return topology

        except Exception as e:
            print(f"Error building service topology: {e}")
            return {"services": {}, "dependencies": {}, "error": str(e)}

    async def watch_services(self, callback=None) -> None:
        """Watch for service changes (registration, deregistration, updates)."""
        # This would typically use WebSocket or Server-Sent Events
        # For now, implement periodic polling
        while True:
            try:
                current_services = await self.get_all_services()

                if callback:
                    await callback(current_services)

                await asyncio.sleep(self.config.api_polling_interval)

            except Exception as e:
                print(f"Error in service watching: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def validate_service_contract(self, service_name: str) -> Dict[str, Any]:
        """Validate that a service meets the expected contract."""
        try:
            service_details = await self.get_service_details(service_name)
            if not service_details:
                return {"valid": False, "errors": ["Service not found"]}

            validation_results = {
                "valid": True,
                "checks": [],
                "errors": [],
                "warnings": []
            }

            # Check required fields
            required_fields = ["name", "version", "url"]
            for field in required_fields:
                if field not in service_details:
                    validation_results["errors"].append(f"Missing required field: {field}")
                    validation_results["valid"] = False
                else:
                    validation_results["checks"].append(f"✓ Has {field}")

            # Check URL format
            url = service_details.get("url", "")
            if not url.startswith(("http://", "https://")):
                validation_results["errors"].append("Invalid URL format")
                validation_results["valid"] = False
            else:
                validation_results["checks"].append("✓ Valid URL format")

            # Check health endpoint
            health_endpoint = service_details.get("health_endpoint")
            if health_endpoint:
                validation_results["checks"].append("✓ Has health endpoint")
            else:
                validation_results["warnings"].append("No health endpoint specified")

            # Check tags
            tags = service_details.get("tags", [])
            if tags:
                validation_results["checks"].append(f"✓ Has {len(tags)} tags")
            else:
                validation_results["warnings"].append("No tags specified")

            return validation_results

        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "checks": [],
                "warnings": []
            }

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
