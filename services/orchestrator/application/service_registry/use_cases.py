"""Use Cases for Service Registry"""

from typing import Optional, List
from abc import ABC, abstractmethod

from .commands import *
from .queries import *
from ...domain.service_registry import (
    Service, ServiceId, ServiceDiscoveryService, ServiceRegistrationService
)
from ...shared.domain import DomainResult


class UseCase(ABC):
    """Base class for all use cases."""

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """Execute the use case."""
        pass


class RegisterServiceUseCase(UseCase):
    """Use case for registering services."""

    def __init__(self, registration_service: ServiceRegistrationService):
        self.registration_service = registration_service

    async def execute(self, command: RegisterServiceCommand) -> DomainResult[Service]:
        """Execute the register service use case."""
        try:
            service = self.registration_service.register_service(
                service_id=command.service_id,
                name=command.name,
                description=command.description,
                category=command.category,
                base_url=command.base_url,
                openapi_url=command.openapi_url,
                capabilities=command.capabilities,
                endpoints=command.endpoints,
                metadata=command.metadata
            )
            return DomainResult.success_result(service, "Service registered successfully")
        except Exception as e:
            return DomainResult.single_error(f"Failed to register service: {str(e)}")


class UnregisterServiceUseCase(UseCase):
    """Use case for unregistering services."""

    def __init__(self, registration_service: ServiceRegistrationService):
        self.registration_service = registration_service

    async def execute(self, command: UnregisterServiceCommand) -> DomainResult[bool]:
        """Execute the unregister service use case."""
        try:
            success = self.registration_service.unregister_service(command.service_id)
            if success:
                return DomainResult.success_result(True, "Service unregistered successfully")
            else:
                return DomainResult.single_error("Service not found")
        except Exception as e:
            return DomainResult.single_error(f"Failed to unregister service: {str(e)}")


class UpdateServiceStatusUseCase(UseCase):
    """Use case for updating service status."""

    def __init__(self, registration_service: ServiceRegistrationService):
        self.registration_service = registration_service

    async def execute(self, command: UpdateServiceStatusCommand) -> DomainResult[bool]:
        """Execute the update service status use case."""
        try:
            success = self.registration_service.update_service_status(
                command.service_id,
                command.status
            )
            if success:
                return DomainResult.success_result(True, "Service status updated successfully")
            else:
                return DomainResult.single_error("Service not found")
        except Exception as e:
            return DomainResult.single_error(f"Failed to update service status: {str(e)}")


class GetServiceUseCase(UseCase):
    """Use case for getting a service."""

    def __init__(self, discovery_service: ServiceDiscoveryService, registration_service: ServiceRegistrationService):
        self.discovery_service = discovery_service
        self.registration_service = registration_service

    async def execute(self, query: GetServiceQuery) -> DomainResult[Optional[Service]]:
        """Execute the get service use case."""
        try:
            # First check registered services
            service = self.registration_service.get_registered_service(query.service_id)
            if service:
                return DomainResult.success_result(service)

            # Then check static service definitions
            service = self.discovery_service.get_service_by_id(query.service_id)
            return DomainResult.success_result(service)
        except Exception as e:
            return DomainResult.single_error(f"Failed to get service: {str(e)}")


class ListServicesUseCase(UseCase):
    """Use case for listing services."""

    def __init__(self, discovery_service: ServiceDiscoveryService, registration_service: ServiceRegistrationService):
        self.discovery_service = discovery_service
        self.registration_service = registration_service

    async def execute(self, query: ListServicesQuery) -> DomainResult[List[Service]]:
        """Execute the list services use case."""
        try:
            services = []

            # Get static service definitions
            static_services = self.discovery_service.get_all_services()

            # Apply filters to static services
            if query.category_filter:
                static_services = [s for s in static_services if s.category == query.category_filter]

            if query.capability_filter:
                static_services = [s for s in static_services if s.has_capability(query.capability_filter)]

            services.extend(static_services)

            # Get registered service instances
            registered_services = self.registration_service.get_all_registered_services()

            # Apply filters to registered services
            if query.category_filter:
                registered_services = [s for s in registered_services if s.category == query.category_filter]

            if query.capability_filter:
                registered_services = [s for s in registered_services if s.has_capability(query.capability_filter)]

            if query.status_filter:
                registered_services = [s for s in registered_services if s.status == query.status_filter]

            services.extend(registered_services)

            # Remove duplicates (registered services override static definitions)
            seen_ids = set()
            unique_services = []
            for service in services:
                if service.service_id.value not in seen_ids:
                    unique_services.append(service)
                    seen_ids.add(service.service_id.value)

            # Apply pagination
            start = query.offset
            end = start + query.limit
            paginated_services = unique_services[start:end]

            return DomainResult.success_result(paginated_services)
        except Exception as e:
            return DomainResult.single_error(f"Failed to list services: {str(e)}")


class GetServiceCategoriesUseCase(UseCase):
    """Use case for getting service categories."""

    def __init__(self, discovery_service: ServiceDiscoveryService):
        self.discovery_service = discovery_service

    async def execute(self, query: GetServiceCategoriesQuery) -> DomainResult[List[str]]:
        """Execute the get service categories use case."""
        try:
            categories = self.discovery_service.get_service_categories()
            return DomainResult.success_result(categories)
        except Exception as e:
            return DomainResult.single_error(f"Failed to get service categories: {str(e)}")


class GetServiceCapabilitiesUseCase(UseCase):
    """Use case for getting service capabilities."""

    def __init__(self, discovery_service: ServiceDiscoveryService):
        self.discovery_service = discovery_service

    async def execute(self, query: GetServiceCapabilitiesQuery) -> DomainResult[dict]:
        """Execute the get service capabilities use case."""
        try:
            capabilities = self.discovery_service.get_service_capabilities_summary()
            return DomainResult.success_result(capabilities)
        except Exception as e:
            return DomainResult.single_error(f"Failed to get service capabilities: {str(e)}")
