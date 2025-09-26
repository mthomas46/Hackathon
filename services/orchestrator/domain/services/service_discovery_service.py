"""Service discovery domain service."""

from typing import List, Optional

from ..entities.service import Service
from ..repositories.service_repository import ServiceRepository
from ..value_objects.service_id import ServiceId
from ..value_objects.service_status import ServiceStatus


class ServiceDiscoveryService:
    """Domain service for service discovery and health management."""

    def __init__(self, service_repository: ServiceRepository):
        self.service_repository = service_repository

    async def register_service(
        self,
        name: str,
        endpoint: str,
        metadata: Optional[dict] = None
    ) -> Service:
        """Register a new service."""
        service_id = ServiceId.generate()
        service = Service(
            id=service_id,
            name=name,
            status=ServiceStatus.REGISTERED,
            endpoint=endpoint,
            metadata=metadata or {}
        )

        service.validate()
        await self.service_repository.save(service)

        return service

    async def unregister_service(self, service_id: ServiceId) -> None:
        """Unregister a service."""
        await self.service_repository.delete(service_id)

    async def update_service_health(
        self,
        service_id: ServiceId,
        healthy: bool
    ) -> Optional[Service]:
        """Update service health status."""
        service = await self.service_repository.find_by_id(service_id)
        if not service:
            return None

        service.update_health_status(healthy)
        await self.service_repository.save(service)

        return service

    async def discover_service(self, name: str) -> Optional[Service]:
        """Discover a service by name."""
        return await self.service_repository.find_by_name(name)

    async def get_service(self, service_id: ServiceId) -> Optional[Service]:
        """Get a service by ID."""
        return await self.service_repository.find_by_id(service_id)

    async def get_healthy_services(self) -> List[Service]:
        """Get all healthy services."""
        services = await self.service_repository.find_all()
        return [s for s in services if s.is_healthy()]

    async def get_services_by_status(self, status: ServiceStatus) -> List[Service]:
        """Get services by status."""
        return await self.service_repository.find_by_status(status)

    async def get_all_services(self) -> List[Service]:
        """Get all registered services."""
        return await self.service_repository.find_all()
