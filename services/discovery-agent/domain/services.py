"""Domain Services for Service Discovery.

This module contains domain services that implement the core business logic
for service discovery operations.
"""

import importlib.util
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from .exceptions import (
    DiscoveryError,
    ServiceDiscoveryError,
    InvalidOpenApiSpecError,
    ServiceNotFoundError,
    EndpointDiscoveryError,
    NetworkTimeoutError,
    UnsupportedApiVersionError,
    MalformedUrlError,
)
from . import entities
from .value_objects import DiscoverySpec, EndpointMetadata, ServiceMetadata, HttpMethod, ApiPath
# TODO: Import repositories when needed
# from .repositories import ServiceRepository, EndpointRepository
# Temporary workaround for import issues
import sys
from pathlib import Path
current_file = Path(__file__)
domain_dir = current_file.parent
repos_file = domain_dir / "repositories.py"
if repos_file.exists():
    spec = importlib.util.spec_from_file_location("repositories", repos_file)
    if spec and spec.loader:
        repos_module = importlib.util.module_from_spec(spec)
        sys.modules["repositories"] = repos_module
        spec.loader.exec_module(repos_module)
        ServiceRepository = repos_module.ServiceRepository
        EndpointRepository = repos_module.EndpointRepository
else:
    # Fallback
    ServiceRepository = object
    EndpointRepository = object


logger = logging.getLogger(__name__)


class EndpointAnalyzer:
    """Domain service for analyzing and extracting endpoint information."""

    def analyze_openapi_spec(self, spec: Dict[str, Any]) -> tuple[ServiceMetadata, List[Dict[str, Any]]]:
        """Analyze OpenAPI specification and extract service and endpoint data.

        Args:
            spec: OpenAPI specification dictionary

        Returns:
            Tuple of (service_metadata, endpoints_data)

        Raises:
            ValidationError: If spec is invalid
        """
        try:
            # Extract service metadata
            info = spec.get("info", {})
            service_metadata = ServiceMetadata.from_openapi_info(info)

            # Extract endpoints
            endpoints_data = []
            paths = spec.get("paths", {})

            for path, methods in paths.items():
                for method, operation in methods.items():
                    if isinstance(operation, dict):
                        endpoint_data = self._extract_endpoint_data(path, method, operation)
                        endpoints_data.append(endpoint_data)

            return service_metadata, endpoints_data

        except Exception as e:
            raise InvalidOpenApiSpecError(f"Failed to analyze OpenAPI spec: {e}") from e

    def _extract_endpoint_data(self, path: str, method: str, operation: Dict[str, Any]) -> Dict[str, Any]:
        """Extract endpoint data from OpenAPI operation."""
        return {
            "path": path,
            "method": method.upper(),
            "summary": operation.get("summary"),
            "description": operation.get("description"),
            "parameters": operation.get("parameters", []),
            "responses": operation.get("responses", {}),
            "tags": operation.get("tags", []),
            "operation_id": operation.get("operationId"),
            "deprecated": operation.get("deprecated", False),
        }


class DiscoveryService:
    """Core domain service for service discovery operations."""

    def __init__(
        self,
        service_repository: ServiceRepository,
        endpoint_analyzer: EndpointAnalyzer
    ):
        self.service_repository = service_repository
        self.endpoint_analyzer = endpoint_analyzer
        self.logger = logging.getLogger(self.__class__.__name__)

    async def discover_service(
        self,
        name: str,
        base_url: str,
        discovery_spec: Optional[DiscoverySpec] = None
    ) -> DiscoveryResult:
        """Discover a service and its endpoints.

        Args:
            name: Service name
            base_url: Base URL of the service
            discovery_spec: Optional discovery specification

        Returns:
            DiscoveryResult with the discovered service or error
        """
        try:
            # Check if service already exists
            existing_service = await self.service_repository.find_by_name(name)
            if existing_service:
                # Update existing service
                service = existing_service
                service.base_url = base_url
            else:
                # Create new service
                service = entities.Service(
                    name=name,
                    base_url=base_url
                )

            # Perform discovery
            if discovery_spec:
                await self._perform_discovery(service, discovery_spec)
            else:
                # Try to discover automatically
                await self._perform_auto_discovery(service)

            # Save the service
            saved_service = await self.service_repository.save(service)

            return DiscoveryResult(
                service=saved_service,
                success=True
            )

        except Exception as e:
            self.logger.error(f"Service discovery failed for {name}: {e}")
            return DiscoveryResult(
                service=entities.Service(name=name, base_url=base_url, status="error"),
                success=False,
                error_message=str(e)
            )

    async def _perform_discovery(self, service: entities.Service, discovery_spec: DiscoverySpec) -> None:
        """Perform discovery using the provided specification."""
        if discovery_spec.has_content:
            # Use inline content
            spec_data = discovery_spec.content
        elif discovery_spec.has_url:
            # Fetch from URL
            spec_data = await self._fetch_openapi_spec(discovery_spec.url)
        else:
            raise ValidationError("Discovery spec must have content or URL")

        # Analyze the spec
        service_metadata, endpoints_data = self.endpoint_analyzer.analyze_openapi_spec(spec_data)

        # Update service metadata
        service.openapi_url = discovery_spec.url
        service.version = service_metadata.version
        service.description = service_metadata.description

        # Add endpoints
        for endpoint_data in endpoints_data:
            endpoint = Endpoint(
                path=endpoint_data["path"],
                method=endpoint_data["method"],
                summary=endpoint_data.get("summary"),
                description=endpoint_data.get("description"),
                parameters=endpoint_data.get("parameters", []),
                responses=endpoint_data.get("responses", {}),
                tags=endpoint_data.get("tags", [])
            )
            service.add_endpoint(endpoint)

        service.status = "active"

    async def _perform_auto_discovery(self, service: entities.Service) -> None:
        """Attempt automatic discovery of service endpoints."""
        # Try common OpenAPI endpoints
        openapi_urls = [
            urljoin(service.base_url, "/openapi.json"),
            urljoin(service.base_url, "/swagger.json"),
            urljoin(service.base_url, "/docs/openapi.json"),
        ]

        for openapi_url in openapi_urls:
            try:
                spec_data = await self._fetch_openapi_spec(openapi_url)
                discovery_spec = DiscoverySpec(url=openapi_url, content=spec_data)
                await self._perform_discovery(service, discovery_spec)
                return  # Success
            except Exception:
                continue  # Try next URL

        # If no OpenAPI found, mark as discovered but with no endpoints
        service.status = "discovered"
        self.logger.warning(f"No OpenAPI specification found for service {service.name}")

    async def _fetch_openapi_spec(self, url: str) -> Dict[str, Any]:
        """Fetch OpenAPI specification from URL."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def get_service(self, service_id: str) -> Optional[entities.Service]:
        """Get service by ID."""
        return await self.service_repository.find_by_id(service_id)

    async def get_service_by_name(self, name: str) -> Optional[entities.Service]:
        """Get service by name."""
        return await self.service_repository.find_by_name(name)

    async def list_services(self) -> List[entities.Service]:
        """List all discovered services."""
        return await self.service_repository.find_all()

    async def list_active_services(self) -> List[entities.Service]:
        """List all active services."""
        return await self.service_repository.find_active_services()

    async def remove_service(self, service_id: str) -> bool:
        """Remove a service."""
        return await self.service_repository.delete(service_id)

    async def get_endpoints_for_service(self, service_id: str) -> List[Endpoint]:
        """Get all endpoints for a service."""
        service = await self.service_repository.find_by_id(service_id)
        return service.endpoints if service else []
