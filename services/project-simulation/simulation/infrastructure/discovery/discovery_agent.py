"""
Discovery agent for service registration and health checking.
Following DDD infrastructure patterns with clean separation of concerns.
"""

import httpx
from typing import List, Optional
import time
from datetime import datetime

from simulation.domain.entities.discovery import (
    ServiceRegistration,
    ServiceEndpoint,
    HealthStatus,
    EndpointValidation,
    DiscoveryResult
)


class DiscoveryAgent:
    """Agent responsible for service discovery, registration, and health monitoring."""

    def __init__(self, registry, http_client: Optional[httpx.AsyncClient] = None):
        self.registry = registry
        self.http_client = http_client or httpx.AsyncClient(timeout=10.0)

    async def register_simulation_service(self, service_name: str, base_url: str) -> ServiceRegistration:
        """Register the project simulation service with all its endpoints."""
        endpoints = self._get_simulation_service_endpoints()

        registration = ServiceRegistration(
            service_name=service_name,
            base_url=base_url,
            endpoints=endpoints,
            version="1.0.0",
            health_check_url=f"{base_url}/health"
        )

        self.registry.register_service(registration)
        return registration

    async def discover_service_health(self, service_url: str) -> HealthStatus:
        """Discover and validate service health."""
        try:
            start_time = time.time()
            response = await self.http_client.get(f"{service_url}/health")
            response_time = int((time.time() - start_time) * 1000)

            if response.status_code == 200:
                health_data = response.json()
                return HealthStatus(
                    is_healthy=True,
                    version=health_data.get("version"),
                    uptime_seconds=health_data.get("uptime"),
                    endpoints=health_data.get("endpoints", [])
                )
            else:
                return HealthStatus(
                    is_healthy=False,
                    error_message=f"Health check failed with status {response.status_code}"
                )

        except Exception as e:
            return HealthStatus(
                is_healthy=False,
                error_message=str(e)
            )

    async def update_service_endpoints(self, service_name: str, new_endpoints: List[ServiceEndpoint]) -> bool:
        """Update the endpoints for an existing service."""
        existing_service = self.registry.get_service(service_name)
        if not existing_service:
            return False

        updated_registration = ServiceRegistration(
            service_name=existing_service.service_name,
            base_url=existing_service.base_url,
            endpoints=new_endpoints,
            version=existing_service.version,
            health_check_url=existing_service.health_check_url,
            registered_at=existing_service.registered_at,
            is_active=existing_service.is_active
        )

        return self.registry.update_service(service_name, updated_registration)

    async def validate_endpoints(self, base_url: str, endpoints: List[ServiceEndpoint]) -> List[EndpointValidation]:
        """Validate that endpoints are accessible."""
        validations = []

        for endpoint in endpoints:
            validation = await self._validate_single_endpoint(base_url, endpoint)
            validations.append(validation)

        return validations

    async def discover_service_with_fallback(self, service_name: str) -> Optional[DiscoveryResult]:
        """Discover a service with fallback mechanisms."""
        # Try primary registry first
        service = self.registry.get_service(service_name)
        if service:
            return DiscoveryResult(
                service_name=service_name,
                base_url=service.base_url,
                status="found",
                registration=service
            )

        # Try fallback discovery
        try:
            fallback_result = await self._fallback_discovery(service_name)
            if fallback_result:
                return DiscoveryResult(
                    service_name=service_name,
                    base_url=fallback_result.get("base_url"),
                    status="found",
                    registration=None
                )
        except Exception as e:
            return DiscoveryResult(
                service_name=service_name,
                status="error",
                error_message=str(e)
            )

        return DiscoveryResult(service_name=service_name, status="not_found")

    def _get_simulation_service_endpoints(self) -> List[ServiceEndpoint]:
        """Get all endpoints for the project simulation service."""
        return [
            ServiceEndpoint(
                path="/api/v1/simulations",
                method="POST",
                description="Create new simulation"
            ),
            ServiceEndpoint(
                path="/api/v1/simulations/{simulation_id}",
                method="GET",
                description="Get simulation details"
            ),
            ServiceEndpoint(
                path="/api/v1/simulations/{simulation_id}/execute",
                method="POST",
                description="Execute simulation"
            ),
            ServiceEndpoint(
                path="/api/v1/simulations/{simulation_id}/cancel",
                method="POST",
                description="Cancel simulation"
            ),
            ServiceEndpoint(
                path="/api/v1/interpreter/simulate",
                method="POST",
                description="Create simulation from interpreter query"
            ),
            ServiceEndpoint(
                path="/api/v1/interpreter/mock-data",
                method="POST",
                description="Generate mock data for interpreter"
            ),
            ServiceEndpoint(
                path="/api/v1/interpreter/analyze",
                method="POST",
                description="Perform analysis using simulation infrastructure"
            ),
            ServiceEndpoint(
                path="/api/v1/interpreter/capabilities",
                method="GET",
                description="Get interpreter capabilities"
            ),
            ServiceEndpoint(
                path="/api/v1/health",
                method="GET",
                description="Health check endpoint"
            ),
            ServiceEndpoint(
                path="/api/v1/service-discovery",
                method="GET",
                description="Service discovery information"
            )
        ]

    async def _validate_single_endpoint(self, base_url: str, endpoint: ServiceEndpoint) -> EndpointValidation:
        """Validate a single endpoint."""
        try:
            start_time = time.time()
            url = f"{base_url}{endpoint.path}"

            if endpoint.method.upper() == "GET":
                response = await self.http_client.get(url)
            elif endpoint.method.upper() == "POST":
                response = await self.http_client.post(url, json={})
            else:
                return EndpointValidation(
                    endpoint=endpoint,
                    is_accessible=False,
                    error_message=f"Unsupported method: {endpoint.method}"
                )

            response_time = int((time.time() - start_time) * 1000)

            return EndpointValidation(
                endpoint=endpoint,
                is_accessible=response.status_code < 500,
                response_time_ms=response_time,
                status_code=response.status_code
            )

        except Exception as e:
            return EndpointValidation(
                endpoint=endpoint,
                is_accessible=False,
                error_message=str(e)
            )

    async def _fallback_discovery(self, service_name: str) -> Optional[dict]:
        """Fallback service discovery mechanism."""
        try:
            # Try to discover via external discovery service
            discovery_url = f"http://discovery-agent:8080/api/v1/services/{service_name}"
            response = await self.http_client.get(discovery_url)

            if response.status_code == 200:
                return response.json()

        except Exception:
            pass

        return None
