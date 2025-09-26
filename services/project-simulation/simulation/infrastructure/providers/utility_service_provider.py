"""Utility Service Provider - Utility and helper services."""

import threading
from typing import Any, Dict


class UtilityServiceProvider:
    """Provides utility services for the simulation system."""

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._lock = threading.RLock()

    def register_utility_services(self, container: Any) -> None:
        """Register all utility services."""
        with self._lock:
            # Document generation service
            container.register_singleton("document_generation_service", self._create_document_generation_service())
            self._services["document_generation_service"] = container.resolve("document_generation_service")

    def _create_document_generation_service(self) -> Any:
        """Create document generation service instance."""
        # Implementation would go here
        return object()  # Placeholder

    def get_service(self, service_name: str) -> Any:
        """Get a registered service."""
        return self._services.get(service_name)
