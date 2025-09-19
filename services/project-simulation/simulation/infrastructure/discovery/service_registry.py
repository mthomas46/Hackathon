"""
Service registry for managing service registrations.
Following DDD infrastructure patterns with clean separation of concerns.
"""

from typing import Dict, List, Optional
from threading import Lock
from datetime import datetime

from simulation.domain.entities.discovery import ServiceRegistration


class ServiceRegistry:
    """In-memory service registry for managing service registrations."""

    def __init__(self):
        self._services: Dict[str, ServiceRegistration] = {}
        self._lock = Lock()

    def register_service(self, registration: ServiceRegistration) -> None:
        """Register a service in the registry."""
        with self._lock:
            self._services[registration.service_name] = registration

    def get_service(self, service_name: str) -> Optional[ServiceRegistration]:
        """Get a service registration by name."""
        with self._lock:
            return self._services.get(service_name)

    def update_service(self, service_name: str, updated_registration: ServiceRegistration) -> bool:
        """Update an existing service registration."""
        with self._lock:
            if service_name in self._services:
                self._services[service_name] = updated_registration
                return True
            return False

    def unregister_service(self, service_name: str) -> bool:
        """Remove a service from the registry."""
        with self._lock:
            if service_name in self._services:
                del self._services[service_name]
                return True
            return False

    def list_services(self) -> List[ServiceRegistration]:
        """List all registered services."""
        with self._lock:
            return list(self._services.values())

    def get_services_by_pattern(self, pattern: str) -> List[ServiceRegistration]:
        """Get services whose names match the given pattern."""
        with self._lock:
            return [
                service for service in self._services.values()
                if pattern.lower() in service.service_name.lower()
            ]

    def clear_all(self) -> None:
        """Clear all service registrations (for testing)."""
        with self._lock:
            self._services.clear()

    def get_service_count(self) -> int:
        """Get the total number of registered services."""
        with self._lock:
            return len(self._services)
