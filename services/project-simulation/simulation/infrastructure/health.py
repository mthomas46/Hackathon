"""Health Infrastructure - Reuse Shared Health Monitoring.

This module provides health monitoring infrastructure for the project-simulation service
by reusing the shared health components from services/shared/.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import from shared infrastructure
shared_path = Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"
sys.path.insert(0, str(shared_path))

try:
    from monitoring.health import (
        HealthManager,
        HealthStatus,
        SystemHealth,
        DependencyHealth,
        register_health_endpoints
    )
except ImportError:
    # Create mock classes for testing
    class HealthManager:
        def __init__(self, *args, **kwargs):
            pass

    class HealthStatus:
        pass

    class SystemHealth:
        pass

    class DependencyHealth:
        pass

    def register_health_endpoints(*args, **kwargs):
        pass

from ..domain.value_objects import ECOSYSTEM_SERVICES


class SimulationHealthManager(HealthManager):
    """Health manager specifically for project-simulation service."""

    def __init__(self):
        """Initialize simulation health manager."""
        super().__init__(
            service_name="project-simulation",
            version="1.0.0"
        )

        # Add simulation-specific health checks
        self.add_health_check(
            name="domain_models_loaded",
            description="Domain models and aggregates are properly loaded"
        )

        self.add_health_check(
            name="infrastructure_ready",
            description="Infrastructure adapters and repositories are ready"
        )

        self.add_health_check(
            name="ecosystem_integration",
            description="Integration with ecosystem services is functional"
        )

    async def basic_health(self) -> HealthStatus:
        """Enhanced basic health check for simulation service."""
        # Get base health from parent
        health_status = await super().basic_health()

        # Add simulation-specific health indicators
        try:
            # Check if domain models can be imported
            from ..domain.entities.project import Project
            from ..domain.entities.simulation import Simulation
            health_status.models_loaded = True
        except ImportError:
            health_status.models_loaded = False
            health_status.status = "unhealthy"

        # Check infrastructure readiness
        try:
            # Check if infrastructure components are available
            from .repositories.in_memory_repositories import InMemoryProjectRepository
            health_status.api_connected = True  # Using as infrastructure readiness indicator
        except ImportError:
            health_status.api_connected = False

        # Check ecosystem service integration
        ecosystem_healthy = await self._check_ecosystem_services()
        health_status.llm_connected = ecosystem_healthy  # Using as ecosystem integration indicator

        return health_status

    async def _check_ecosystem_services(self) -> bool:
        """Check if critical ecosystem services are available."""
        critical_services = [
            "doc_store",
            "mock_data_generator",
            "orchestrator"
        ]

        healthy_count = 0
        for service_name in critical_services:
            service_info = next(
                (s for s in ECOSYSTEM_SERVICES if s.name == service_name),
                None
            )
            if service_info:
                try:
                    dep_health = await self.dependency_health(
                        service_name,
                        f"http://{service_info.endpoint.url.replace('http://', '')}{service_info.health_check_endpoint}"
                    )
                    if dep_health.status == "healthy":
                        healthy_count += 1
                except:
                    pass

        # Consider ecosystem healthy if at least 2 out of 3 critical services are available
        return healthy_count >= 2

    async def simulation_health(self) -> Dict[str, Any]:
        """Get comprehensive simulation service health."""
        basic_health = await self.basic_health()
        system_health = await self.system_health()
        custom_checks = await self.run_custom_checks()

        return {
            "service_health": basic_health.dict(),
            "system_health": system_health.dict(),
            "custom_checks": custom_checks,
            "simulation_specific": {
                "domain_models_loaded": basic_health.models_loaded,
                "infrastructure_ready": basic_health.api_connected,
                "ecosystem_integration": basic_health.llm_connected,
                "critical_services": await self._get_critical_services_status()
            }
        }

    async def _get_critical_services_status(self) -> Dict[str, DependencyHealth]:
        """Get status of critical ecosystem services."""
        critical_services = ["doc_store", "mock_data_generator", "orchestrator"]
        status = {}

        for service_name in critical_services:
            service_info = next(
                (s for s in ECOSYSTEM_SERVICES if s.name == service_name),
                None
            )
            if service_info:
                try:
                    health = await self.dependency_health(
                        service_name,
                        f"http://{service_info.endpoint.url.replace('http://', '')}{service_info.health_check_endpoint}"
                    )
                    status[service_name] = health
                except Exception as e:
                    status[service_name] = DependencyHealth(
                        name=service_name,
                        status="unknown",
                        error=str(e)
                    )

        return status


# Global health manager instance
_simulation_health_manager: Optional[SimulationHealthManager] = None


def get_simulation_health_manager() -> SimulationHealthManager:
    """Get the global simulation health manager instance."""
    global _simulation_health_manager
    if _simulation_health_manager is None:
        _simulation_health_manager = SimulationHealthManager()
    return _simulation_health_manager


def create_simulation_health_endpoints():
    """Create health endpoints for simulation service."""
    health_manager = get_simulation_health_manager()

    async def health():
        """Basic health check endpoint."""
        return await health_manager.basic_health()

    async def health_detailed():
        """Detailed health check endpoint."""
        return await health_manager.simulation_health()

    async def health_system():
        """System-wide health check endpoint."""
        return await health_manager.system_health()

    return {
        "health": health,
        "health_detailed": health_detailed,
        "health_system": health_system
    }


# Re-export key health utilities
__all__ = [
    'SimulationHealthManager',
    'get_simulation_health_manager',
    'create_simulation_health_endpoints'
]
