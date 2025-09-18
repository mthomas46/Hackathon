"""Dependency Injection Container - Infrastructure Setup.

This module provides dependency injection container following existing
ecosystem patterns from services/shared/core/di/.
"""

from typing import Dict, Any, Optional
import sys
from pathlib import Path

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))
from core.di.services import IServiceProvider
from core.di.container import Container

from .logging import get_simulation_logger
from .health import get_simulation_health_manager
from .repositories.in_memory_repositories import (
    get_project_repository,
    get_timeline_repository,
    get_team_repository,
    get_simulation_repository
)
from ..domain.services.project_simulation_service import ProjectSimulationService
from ..application.services.simulation_application_service import SimulationApplicationService


class SimulationServiceProvider(IServiceProvider):
    """Service provider for project-simulation dependencies."""

    def __init__(self):
        self._container = Container()
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}

    def register_services(self) -> None:
        """Register all simulation services."""
        # Infrastructure services
        self._register_infrastructure_services()

        # Domain services
        self._register_domain_services()

        # Application services
        self._register_application_services()

    def _register_infrastructure_services(self) -> None:
        """Register infrastructure services."""
        # Logging
        self._singletons["logger"] = get_simulation_logger()

        # Health monitoring
        self._singletons["health_manager"] = get_simulation_health_manager()

        # Repositories
        self._singletons["project_repository"] = get_project_repository()
        self._singletons["timeline_repository"] = get_timeline_repository()
        self._singletons["team_repository"] = get_team_repository()
        self._singletons["simulation_repository"] = get_simulation_repository()

    def _register_domain_services(self) -> None:
        """Register domain services."""
        # Project Simulation Service
        self._services["project_simulation_service"] = lambda: ProjectSimulationService(
            project_repository=self.get_service("project_repository"),
            timeline_repository=self.get_service("timeline_repository"),
            team_repository=self.get_service("team_repository"),
            simulation_repository=self.get_service("simulation_repository"),
            document_generation_service=self._create_document_generation_service(),
            workflow_execution_service=self._create_workflow_execution_service()
        )

    def _register_application_services(self) -> None:
        """Register application services."""
        # Simulation Application Service
        self._services["simulation_application_service"] = lambda: SimulationApplicationService(
            project_simulation_service=self.get_service("project_simulation_service"),
            logger=self.get_service("logger")
        )

    def _create_document_generation_service(self):
        """Create document generation service."""
        # Placeholder - will be implemented with mock-data-generator integration
        class MockDocumentGenerationService:
            async def generate_project_documents(self, project):
                return [{"type": "requirements", "title": f"{project.name} Requirements"}]

            async def generate_phase_documents(self, project, phase_name):
                return [{"type": "design", "title": f"{phase_name} Design Document"}]

        return MockDocumentGenerationService()

    def _create_workflow_execution_service(self):
        """Create workflow execution service."""
        # Placeholder - will be implemented with orchestrator integration
        class MockWorkflowExecutionService:
            async def execute_document_analysis_workflow(self, documents):
                return {"success": True, "execution_time": 1.5}

            async def execute_team_dynamics_workflow(self, team):
                return {"success": True, "execution_time": 0.8}

        return MockWorkflowExecutionService()

    def get_service(self, service_name: str) -> Any:
        """Get a service instance."""
        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]

        # Check services
        if service_name in self._services:
            return self._services[service_name]()

        raise ValueError(f"Service '{service_name}' not registered")

    def has_service(self, service_name: str) -> bool:
        """Check if a service is registered."""
        return service_name in self._singletons or service_name in self._services

    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services."""
        all_services = dict(self._singletons)
        for service_name in self._services:
            if service_name not in all_services:
                try:
                    all_services[service_name] = self.get_service(service_name)
                except:
                    pass  # Skip services that can't be instantiated
        return all_services


class SimulationContainer(Container):
    """Container specifically for project-simulation service."""

    def __init__(self):
        super().__init__()
        self._provider = SimulationServiceProvider()
        self._provider.register_services()

    def resolve(self, service_name: str) -> Any:
        """Resolve a service by name."""
        return self._provider.get_service(service_name)

    def has_service(self, service_name: str) -> bool:
        """Check if service is available."""
        return self._provider.has_service(service_name)

    @property
    def logger(self):
        """Get logger service."""
        return self.resolve("logger")

    @property
    def health_manager(self):
        """Get health manager."""
        return self.resolve("health_manager")

    @property
    def project_repository(self):
        """Get project repository."""
        return self.resolve("project_repository")

    @property
    def simulation_application_service(self):
        """Get simulation application service."""
        return self.resolve("simulation_application_service")

    @property
    def project_simulation_service(self):
        """Get project simulation domain service."""
        return self.resolve("project_simulation_service")


# Global container instance
_simulation_container: Optional[SimulationContainer] = None


def get_simulation_container() -> SimulationContainer:
    """Get the global simulation container instance."""
    global _simulation_container
    if _simulation_container is None:
        _simulation_container = SimulationContainer()
    return _simulation_container


def get_service(service_name: str) -> Any:
    """Get a service from the global container."""
    return get_simulation_container().resolve(service_name)


# Convenience functions for commonly used services
def get_logger():
    """Get logger service."""
    return get_simulation_container().logger

def get_health_manager():
    """Get health manager."""
    return get_simulation_container().health_manager

def get_application_service():
    """Get simulation application service."""
    return get_simulation_container().simulation_application_service


__all__ = [
    'SimulationServiceProvider',
    'SimulationContainer',
    'get_simulation_container',
    'get_service',
    'get_logger',
    'get_health_manager',
    'get_application_service'
]
