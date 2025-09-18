"""Service Registry Repository Implementation"""

from typing import List, Optional
from threading import Lock

from ...domain.service_registry import Service, ServiceId
from .interfaces import ServiceRepositoryInterface


class InMemoryServiceRepository(ServiceRepositoryInterface):
    """In-memory implementation of service repository."""

    def __init__(self):
        self._services: dict[str, Service] = {}
        self._lock = Lock()

    def save_service(self, service: Service) -> bool:
        """Save a service."""
        with self._lock:
            self._services[service.service_id.value] = service
            return True

    def get_service(self, service_id: ServiceId) -> Optional[Service]:
        """Get a service by ID."""
        with self._lock:
            return self._services.get(service_id.value)

    def list_services(self) -> List[Service]:
        """List all services."""
        with self._lock:
            return list(self._services.values())

    def delete_service(self, service_id: ServiceId) -> bool:
        """Delete a service."""
        with self._lock:
            if service_id.value in self._services:
                del self._services[service_id.value]
                return True
            return False

    def update_service(self, service: Service) -> bool:
        """Update a service."""
        with self._lock:
            self._services[service.service_id.value] = service
            return True
