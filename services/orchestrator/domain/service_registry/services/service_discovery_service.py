"""Service Discovery Domain Service"""

from typing import List, Optional, Dict, Any

from ..entities.service import Service
from ..value_objects.service_id import ServiceId
from ..value_objects.service_capability import ServiceCapability
from ..value_objects.service_endpoint import ServiceEndpoint


class ServiceDiscoveryService:
    """Domain service for discovering and querying services."""

    def __init__(self, service_definitions: Dict[str, Dict[str, Any]]):
        """Initialize with static service definitions."""
        self._service_definitions = service_definitions

    def get_all_services(self) -> List[Service]:
        """Get all available services in the ecosystem."""
        services = []

        for service_name, definition in self._service_definitions.items():
            service_id = ServiceId(service_name)
            service = Service(
                service_id=service_id,
                name=definition["name"],
                description=definition["description"],
                category=definition["category"]
            )

            # Add capabilities
            for cap_name in definition["capabilities"]:
                capability = ServiceCapability(cap_name)
                service.add_capability(capability)

            # Add endpoints (parse from endpoint strings)
            for endpoint_str in definition["endpoints"]:
                if " - " in endpoint_str:
                    endpoint_part, description = endpoint_str.split(" - ", 1)
                    if " " in endpoint_part:
                        method, path = endpoint_part.split(" ", 1)
                        endpoint = ServiceEndpoint(method, path, description)
                        service.add_endpoint(endpoint)

            services.append(service)

        return services

    def get_service_by_id(self, service_id: ServiceId) -> Optional[Service]:
        """Get a service by its ID."""
        services = self.get_all_services()
        return next((s for s in services if s.service_id == service_id), None)

    def find_services_by_category(self, category: str) -> List[Service]:
        """Find services by category."""
        services = self.get_all_services()
        return [s for s in services if s.category == category]

    def find_services_by_capability(self, capability_name: str) -> List[Service]:
        """Find services that have a specific capability."""
        services = self.get_all_services()
        return [s for s in services if s.has_capability(capability_name)]

    def find_service_for_endpoint(self, method: str, path: str) -> Optional[Service]:
        """Find which service handles a specific endpoint."""
        services = self.get_all_services()

        for service in services:
            for endpoint in service.endpoints:
                if endpoint.method == method.upper() and endpoint.path == path:
                    return service

        return None

    def get_service_capabilities_summary(self) -> Dict[str, List[str]]:
        """Get a summary of all capabilities by service."""
        services = self.get_all_services()
        summary = {}

        for service in services:
            summary[service.name] = [cap.name for cap in service.capabilities]

        return summary

    def get_service_categories(self) -> List[str]:
        """Get all unique service categories."""
        services = self.get_all_services()
        categories = set(s.category for s in services)
        return sorted(list(categories))

    def validate_service_exists(self, service_id: ServiceId) -> bool:
        """Validate that a service exists in the registry."""
        return self.get_service_by_id(service_id) is not None

    def get_service_health_endpoint(self, service_id: ServiceId) -> Optional[str]:
        """Get the health check endpoint for a service."""
        service = self.get_service_by_id(service_id)
        if not service:
            return None

        # Look for health endpoints
        health_endpoints = [ep for ep in service.endpoints if 'health' in ep.path.lower()]
        if health_endpoints:
            return f"{service.base_url or ''}{health_endpoints[0].path}"

        return None
