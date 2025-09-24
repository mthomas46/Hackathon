"""Service Registration Domain Service using standardized BaseService"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from services.shared.utilities import BaseService

from ..entities.service import Service
from ..value_objects.service_capability import ServiceCapability
from ..value_objects.service_endpoint import ServiceEndpoint
from ..value_objects.service_id import ServiceId


class ServiceRegistrationService(BaseService[Service]):
    """Domain service for registering and managing service instances."""

    def __init__(self):
        """Initialize the registration service."""
        self._registered_services: Dict[str, Service] = {}

    def _validate_entity(self, entity: Service) -> None:
        """Validate service entity using standardized validation."""
        if not entity.name or not entity.name.strip():
            raise ValueError("Service name cannot be empty")
        if not entity.service_id or not entity.service_id.value:
            raise ValueError("Service ID cannot be empty")
        if not entity.category or not entity.category.strip():
            raise ValueError("Service category cannot be empty")

    async def _create_entity_from_data(
        self, entity_id: str, data: Dict[str, Any]
    ) -> Service:
        """Create service entity from data using standardized factory pattern."""
        from ..factories.service_factory import ServiceFactory

        return ServiceFactory.create_service(
            service_id=data.get("service_id", entity_id),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=data.get("category", ""),
            base_url=data.get("base_url"),
            openapi_url=data.get("openapi_url"),
            capabilities=data.get("capabilities", []),
            endpoints=data.get("endpoints", []),
            metadata=data.get("metadata", {}),
        )

    def register_service(
        self,
        service_id: ServiceId,
        name: str,
        description: str,
        category: str,
        base_url: Optional[str] = None,
        openapi_url: Optional[str] = None,
        capabilities: Optional[list[str]] = None,
        endpoints: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Service:
        """Register a new service instance."""
        # Check if service already exists
        if service_id.value in self._registered_services:
            # Update existing service
            existing_service = self._registered_services[service_id.value]
            existing_service.update_metadata(metadata or {})
            existing_service.update_status("healthy")
            return existing_service

        # Create new service
        service = Service(
            service_id=service_id,
            name=name,
            description=description,
            category=category,
            base_url=base_url,
            openapi_url=openapi_url,
            metadata=metadata,
        )

        # Add capabilities
        if capabilities:
            for cap_name in capabilities:
                capability = ServiceCapability(cap_name)
                service.add_capability(capability)

        # Add endpoints
        if endpoints:
            for endpoint_str in endpoints:
                # Parse endpoint string (e.g., "GET /health - Health check")
                if " - " in endpoint_str:
                    endpoint_part, description = endpoint_str.split(" - ", 1)
                    if " " in endpoint_part:
                        method, path = endpoint_part.split(" ", 1)
                        endpoint = ServiceEndpoint(method, path, description)
                        service.add_endpoint(endpoint)

        service.update_status("healthy")
        self._registered_services[service_id.value] = service

        return service

    def unregister_service(self, service_id: ServiceId) -> bool:
        """Unregister a service."""
        if service_id.value in self._registered_services:
            del self._registered_services[service_id.value]
            return True
        return False

    def update_service_status(self, service_id: ServiceId, status: str) -> bool:
        """Update the status of a registered service."""
        service = self._registered_services.get(service_id.value)
        if service:
            service.update_status(status)
            return True
        return False

    def get_registered_service(self, service_id: ServiceId) -> Optional[Service]:
        """Get a registered service instance."""
        return self._registered_services.get(service_id.value)

    def get_all_registered_services(self) -> list[Service]:
        """Get all registered service instances."""
        return list(self._registered_services.values())

    def heartbeat_service(self, service_id: ServiceId) -> bool:
        """Update the last seen timestamp for a service (heartbeat)."""
        service = self._registered_services.get(service_id.value)
        if service:
            service.update_status(service.status)  # This updates last_seen
            return True
        return False

    def cleanup_stale_services(self, max_age_minutes: int = 30) -> list[ServiceId]:
        """Remove services that haven't been seen recently."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        stale_services = []

        services_to_remove = []
        for service_id_str, service in self._registered_services.items():
            if service.last_seen < cutoff_time:
                stale_services.append(service.service_id)
                services_to_remove.append(service_id_str)

        # Remove stale services
        for service_id_str in services_to_remove:
            del self._registered_services[service_id_str]

        return stale_services

    def get_service_count(self) -> int:
        """Get the total number of registered services."""
        return len(self._registered_services)

    def is_service_registered(self, service_id: ServiceId) -> bool:
        """Check if a service is registered."""
        return service_id.value in self._registered_services
