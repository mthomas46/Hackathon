"""Service repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.service import Service
from ..value_objects.service_id import ServiceId
from ..value_objects.service_status import ServiceStatus


class ServiceRepository(ABC):
    """Abstract repository for service persistence."""

    @abstractmethod
    async def save(self, service: Service) -> None:
        """Save a service."""
        pass

    @abstractmethod
    async def find_by_id(self, service_id: ServiceId) -> Optional[Service]:
        """Find a service by ID."""
        pass

    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Service]:
        """Find a service by name."""
        pass

    @abstractmethod
    async def find_by_status(self, status: ServiceStatus) -> List[Service]:
        """Find services by status."""
        pass

    @abstractmethod
    async def find_all(self) -> List[Service]:
        """Find all services."""
        pass

    @abstractmethod
    async def delete(self, service_id: ServiceId) -> None:
        """Delete a service by ID."""
        pass
