"""Streamlined Dependency Injection Container - Modular DI with separated concerns.

This module provides a clean dependency injection container that delegates
service registration to focused provider classes, following the Single
Responsibility Principle and making the codebase much more maintainable.
"""

import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional

# Import from shared infrastructure
sys.path.append(
    str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared")
)

# Import shared DI patterns (with fallbacks)
try:
    from core.di.container import Container
    from core.di.services import IServiceProvider
except ImportError:
    class IServiceProvider:
        def register_services(self) -> None:
            pass

    class Container:
        def __init__(self):
            self._services: Dict[str, Any] = {}
            self._singletons: Dict[str, Any] = {}
            self._factories: Dict[str, Any] = {}

        def register_singleton(self, name: str, instance: Any) -> None:
            self._singletons[name] = instance

        def resolve(self, name: str) -> Any:
            return self._singletons.get(name) or self._services.get(name)

# Import focused service providers
from .providers.application_service_provider import ApplicationServiceProvider
from .providers.domain_service_provider import DomainServiceProvider
from .providers.external_service_provider import ExternalServiceProvider
from .providers.infrastructure_service_provider import InfrastructureServiceProvider
from .providers.utility_service_provider import UtilityServiceProvider


class SimulationServiceProvider(IServiceProvider):
    """Orchestrator service provider that coordinates focused providers."""

    def __init__(self):
        self._container = Container()
        self._lock = threading.RLock()

        # Initialize focused providers
        self._infrastructure_provider = InfrastructureServiceProvider()
        self._domain_provider = DomainServiceProvider()
        self._application_provider = ApplicationServiceProvider()
        self._utility_provider = UtilityServiceProvider()
        self._external_provider = ExternalServiceProvider()

    def register_services(self) -> None:
        """Register all services through focused providers."""
        with self._lock:
            # Register services through each focused provider
            self._infrastructure_provider.register_infrastructure_services(self._container)
            self._domain_provider.register_domain_services(self._container)
            self._application_provider.register_application_services(self._container)
            self._utility_provider.register_utility_services(self._container)
            self._external_provider.register_external_services(self._container)

    def get_service(self, service_name: str) -> Any:
        """Get a service from any of the providers."""
        # Try each provider in order
        service = self._infrastructure_provider.get_service(service_name)
        if service:
            return service

        service = self._domain_provider.get_service(service_name)
        if service:
            return service

        service = self._application_provider.get_service(service_name)
        if service:
            return service

        service = self._utility_provider.get_service(service_name)
        if service:
            return service

        service = self._external_provider.get_service(service_name)
        if service:
            return service

        # Fallback to container resolution
        return self._container.resolve(service_name)


class SimulationContainer(Container):
    """Enhanced container with simulation-specific features."""

    def __init__(self):
        super().__init__()
        self._service_provider = SimulationServiceProvider()
        self._service_provider.register_services()

    def resolve(self, service_name: str) -> Any:
        """Resolve a service by name."""
        return self._service_provider.get_service(service_name)


# Global container instance
_container_instance: Optional[SimulationContainer] = None
_container_lock = threading.Lock()


def get_simulation_container() -> SimulationContainer:
    """Get the global simulation container instance."""
    global _container_instance
    if _container_instance is None:
        with _container_lock:
            if _container_instance is None:
                _container_instance = SimulationContainer()
    return _container_instance


def get_service(service_name: str) -> Any:
    """Get a service from the global container."""
    return get_simulation_container().resolve(service_name)


# Convenience functions for commonly used services
def get_logger():
    """Get the logger service."""
    return get_service("logger")


def get_health_checker():
    """Get the health checker service."""
    return get_service("health_checker")


def get_health_endpoint():
    """Get the health endpoint service."""
    return get_service("health_endpoint")


def get_monitoring_service():
    """Get the monitoring service."""
    return get_service("monitoring_service")


def get_application_service():
    """Get the application service."""
    return get_service("application_service")


def get_domain_service():
    """Get the domain service."""
    return get_service("domain_service")


def get_validator():
    """Get the validator service."""
    return get_service("validator")


def get_formatter():
    """Get the formatter service."""
    return get_service("formatter")


def get_cache():
    """Get the cache service."""
    return get_service("cache")


def get_task_manager():
    """Get the task manager."""
    return get_service("task_manager")


def get_error_handler():
    """Get the error handler."""
    return get_service("error_handler")


def get_retry_manager():
    """Get the retry manager."""
    return get_service("retry_manager")


def get_performance_tracker():
    """Get the performance tracker."""
    return get_service("performance_tracker")


def get_document_generation_service():
    """Get the document generation service."""
    return get_service("document_generation_service")


def get_workflow_execution_service():
    """Get the workflow execution service."""
    return get_service("workflow_execution_service")
