"""Service Discovery - Ecosystem Service Discovery and Registration.

This module implements service discovery patterns following the discovery_agent
service architecture, providing automatic service location, health monitoring,
and dynamic service registration for the simulation service ecosystem integration.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import asyncio
import threading
import json
import weakref

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger

# Import shared discovery patterns (with fallbacks)
try:
    from shared.discovery.registry import ServiceRegistry, ServiceInstance
    from shared.discovery.health import ServiceHealthChecker
    from shared.discovery.client import DiscoveryClient
except ImportError:
    # Fallback implementations
    from dataclasses import dataclass
    from enum import Enum

    class ServiceStatus(str, Enum):
        UP = "up"
        DOWN = "down"
        UNKNOWN = "unknown"

    @dataclass
    class ServiceInstance:
        service_id: str
        service_name: str
        address: str
        port: int
        status: ServiceStatus
        metadata: Dict[str, Any]
        registered_at: datetime
        last_heartbeat: datetime

    class ServiceRegistry:
        def __init__(self):
            self.services: Dict[str, List[ServiceInstance]] = {}

        def register(self, instance: ServiceInstance):
            if instance.service_name not in self.services:
                self.services[instance.service_name] = []
            self.services[instance.service_name].append(instance)

        def deregister(self, service_id: str):
            for service_list in self.services.values():
                service_list[:] = [s for s in service_list if s.service_id != service_id]

        def get_instances(self, service_name: str) -> List[ServiceInstance]:
            return self.services.get(service_name, [])

        def get_all_services(self) -> Dict[str, List[ServiceInstance]]:
            return self.services.copy()

    class ServiceHealthChecker:
        def __init__(self, registry: ServiceRegistry):
            self.registry = registry

        async def check_health(self, instance: ServiceInstance) -> ServiceStatus:
            # Simplified health check
            return ServiceStatus.UP

    class DiscoveryClient:
        def __init__(self, registry: ServiceRegistry):
            self.registry = registry

        def discover_service(self, service_name: str) -> Optional[ServiceInstance]:
            instances = self.registry.get_instances(service_name)
            if instances:
                # Return first healthy instance
                return instances[0]
            return None


class SimulationServiceDiscovery:
    """Advanced service discovery for simulation ecosystem integration."""

    def __init__(self):
        """Initialize service discovery with enterprise features."""
        self.logger = get_simulation_logger()
        self._lock = threading.RLock()

        # Core discovery components
        self.registry = ServiceRegistry()
        self.health_checker = ServiceHealthChecker(self.registry)
        self.discovery_client = DiscoveryClient(self.registry)

        # Service tracking
        self._service_endpoints: Dict[str, str] = {}
        self._service_metadata: Dict[str, Dict[str, Any]] = {}
        self._service_dependencies: Dict[str, Set[str]] = {}

        # Health monitoring
        self._health_status: Dict[str, ServiceStatus] = {}
        self._health_timestamps: Dict[str, datetime] = {}

        # Auto-discovery configuration
        self._auto_discovery_enabled = True
        self._discovery_interval = 30  # seconds
        self._health_check_interval = 15  # seconds

        # Background tasks
        self._discovery_thread: Optional[threading.Thread] = None
        self._health_thread: Optional[threading.Thread] = None
        self._running = False

        # Initialize with known ecosystem services
        self._initialize_ecosystem_services()

        self.logger.info("Simulation service discovery initialized")

    def _initialize_ecosystem_services(self):
        """Initialize with known ecosystem services."""
        ecosystem_services = {
            "mock_data_generator": {
                "default_url": "http://localhost:5002",
                "description": "Document and data generation service",
                "dependencies": []
            },
            "doc_store": {
                "default_url": "http://localhost:5003",
                "description": "Document storage and retrieval service",
                "dependencies": []
            },
            "analysis_service": {
                "default_url": "http://localhost:5004",
                "description": "Content analysis and quality assessment",
                "dependencies": ["doc_store"]
            },
            "llm_gateway": {
                "default_url": "http://localhost:5005",
                "description": "AI language model gateway",
                "dependencies": []
            },
            "prompt_store": {
                "default_url": "http://localhost:5006",
                "description": "Prompt management and versioning",
                "dependencies": []
            },
            "orchestrator": {
                "default_url": "http://localhost:5007",
                "description": "Workflow orchestration service",
                "dependencies": ["doc_store", "analysis_service"]
            },
            "log_collector": {
                "default_url": "http://localhost:5008",
                "description": "Centralized logging service",
                "dependencies": []
            },
            "notification_service": {
                "default_url": "http://localhost:5009",
                "description": "Event notification service",
                "dependencies": []
            },
            "source_agent": {
                "default_url": "http://localhost:5010",
                "description": "Code analysis and documentation",
                "dependencies": []
            },
            "code_analyzer": {
                "default_url": "http://localhost:5011",
                "description": "Advanced code analysis",
                "dependencies": ["source_agent"]
            },
            "github_mcp": {
                "default_url": "http://localhost:5012",
                "description": "GitHub integration service",
                "dependencies": []
            },
            "bedrock_proxy": {
                "default_url": "http://localhost:5013",
                "description": "AWS AI services proxy",
                "dependencies": []
            },
            "summarizer_hub": {
                "default_url": "http://localhost:5014",
                "description": "Content summarization service",
                "dependencies": ["analysis_service"]
            },
            "architecture_digitizer": {
                "default_url": "http://localhost:5015",
                "description": "Architecture diagram generation",
                "dependencies": []
            },
            "interpreter": {
                "default_url": "http://localhost:5016",
                "description": "Cross-document analysis and insights",
                "dependencies": ["doc_store", "analysis_service"]
            },
            "memory_agent": {
                "default_url": "http://localhost:5017",
                "description": "Context and conversation management",
                "dependencies": []
            },
            "secure_analyzer": {
                "default_url": "http://localhost:5018",
                "description": "Security analysis and compliance",
                "dependencies": ["code_analyzer"]
            },
            "cli": {
                "default_url": "http://localhost:5019",
                "description": "Command-line interface service",
                "dependencies": []
            },
            "ollama": {
                "default_url": "http://localhost:5020",
                "description": "Local LLM inference service",
                "dependencies": []
            },
            "frontend": {
                "default_url": "http://localhost:3000",
                "description": "Web frontend application",
                "dependencies": ["doc_store", "analysis_service"]
            },
            "discovery_agent": {
                "default_url": "http://localhost:5021",
                "description": "Service discovery and registration",
                "dependencies": []
            }
        }

        for service_name, config in ecosystem_services.items():
            self._service_endpoints[service_name] = config["default_url"]
            self._service_metadata[service_name] = {
                "description": config["description"],
                "default_url": config["default_url"],
                "auto_discovered": False
            }
            self._service_dependencies[service_name] = set(config["dependencies"])

            # Register with discovery registry
            instance = ServiceInstance(
                service_id=f"{service_name}_default",
                service_name=service_name,
                address=config["default_url"].replace("http://", "").split(":")[0],
                port=int(config["default_url"].split(":")[-1]),
                status=ServiceStatus.UNKNOWN,
                metadata={"description": config["description"]},
                registered_at=datetime.now(),
                last_heartbeat=datetime.now()
            )
            self.registry.register(instance)

    def start_discovery(self):
        """Start the service discovery and health monitoring."""
        if self._running:
            return

        self._running = True

        # Start background threads
        self._discovery_thread = threading.Thread(target=self._discovery_worker, daemon=True)
        self._health_thread = threading.Thread(target=self._health_worker, daemon=True)

        self._discovery_thread.start()
        self._health_thread.start()

        self.logger.info("Service discovery started")

    def stop_discovery(self):
        """Stop the service discovery and health monitoring."""
        if not self._running:
            return

        self._running = False

        if self._discovery_thread:
            self._discovery_thread.join(timeout=5)
        if self._health_thread:
            self._health_thread.join(timeout=5)

        self.logger.info("Service discovery stopped")

    def discover_service(self, service_name: str) -> Optional[ServiceInstance]:
        """Discover a service instance."""
        return self.discovery_client.discover_service(service_name)

    def get_service_url(self, service_name: str) -> Optional[str]:
        """Get the URL for a service."""
        instance = self.discover_service(service_name)
        if instance:
            return f"http://{instance.address}:{instance.port}"
        return self._service_endpoints.get(service_name)

    def get_service_health(self, service_name: str) -> Dict[str, Any]:
        """Get health information for a service."""
        status = self._health_status.get(service_name, ServiceStatus.UNKNOWN)
        last_check = self._health_timestamps.get(service_name, datetime.now())

        return {
            "service_name": service_name,
            "status": status,
            "last_check": last_check,
            "is_healthy": status == ServiceStatus.UP,
            "metadata": self._service_metadata.get(service_name, {})
        }

    def get_service_dependencies(self, service_name: str) -> Set[str]:
        """Get dependencies for a service."""
        return self._service_dependencies.get(service_name, set())

    def get_ecosystem_health_overview(self) -> Dict[str, Any]:
        """Get comprehensive ecosystem health overview."""
        total_services = len(self._service_endpoints)
        healthy_services = sum(1 for status in self._health_status.values() if status == ServiceStatus.UP)
        unhealthy_services = sum(1 for status in self._health_status.values() if status == ServiceStatus.DOWN)

        health_percentage = (healthy_services / total_services * 100) if total_services > 0 else 0

        # Service health breakdown
        service_health = {}
        for service_name in self._service_endpoints.keys():
            service_health[service_name] = self.get_service_health(service_name)

        return {
            "timestamp": datetime.now(),
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": unhealthy_services,
            "unknown_services": total_services - healthy_services - unhealthy_services,
            "health_percentage": health_percentage,
            "overall_status": self._calculate_overall_status(health_percentage),
            "service_health": service_health,
            "dependency_graph": self._build_dependency_graph()
        }

    def register_simulation_service(self, service_name: str, url: str, metadata: Dict[str, Any] = None):
        """Register the simulation service itself."""
        with self._lock:
            instance = ServiceInstance(
                service_id=f"simulation_{service_name}",
                service_name=service_name,
                address=url.replace("http://", "").split(":")[0],
                port=int(url.split(":")[-1]),
                status=ServiceStatus.UP,
                metadata=metadata or {},
                registered_at=datetime.now(),
                last_heartbeat=datetime.now()
            )
            self.registry.register(instance)
            self._service_endpoints[service_name] = url
            self._service_metadata[service_name] = metadata or {}
            self._health_status[service_name] = ServiceStatus.UP

            self.logger.info("Simulation service registered", service_name=service_name, url=url)

    def _discovery_worker(self):
        """Background worker for service discovery."""
        while self._running:
            try:
                self._perform_discovery()
                asyncio.run(self._async_sleep(self._discovery_interval))
            except Exception as e:
                self.logger.error("Error in discovery worker", error=str(e))
                asyncio.run(self._async_sleep(5))

    def _health_worker(self):
        """Background worker for health checking."""
        while self._running:
            try:
                asyncio.run(self._perform_health_checks())
                asyncio.run(self._async_sleep(self._health_check_interval))
            except Exception as e:
                self.logger.error("Error in health worker", error=str(e))
                asyncio.run(self._async_sleep(5))

    async def _async_sleep(self, seconds: float):
        """Async sleep helper."""
        await asyncio.sleep(seconds)

    def _perform_discovery(self):
        """Perform service discovery."""
        # In a real implementation, this would query service registries,
        # check DNS, or use other discovery mechanisms
        pass

    async def _perform_health_checks(self):
        """Perform health checks on all registered services."""
        for service_name in list(self._service_endpoints.keys()):
            try:
                instances = self.registry.get_instances(service_name)
                if instances:
                    instance = instances[0]
                    status = await self.health_checker.check_health(instance)
                    self._health_status[service_name] = status
                    self._health_timestamps[service_name] = datetime.now()

                    # Update instance status
                    instance.status = status
                    instance.last_heartbeat = datetime.now()

            except Exception as e:
                self.logger.warning("Health check failed", service=service_name, error=str(e))
                self._health_status[service_name] = ServiceStatus.DOWN
                self._health_timestamps[service_name] = datetime.now()

    def _calculate_overall_status(self, health_percentage: float) -> str:
        """Calculate overall ecosystem status."""
        if health_percentage >= 95:
            return "excellent"
        elif health_percentage >= 80:
            return "good"
        elif health_percentage >= 60:
            return "degraded"
        else:
            return "critical"

    def _build_dependency_graph(self) -> Dict[str, Any]:
        """Build service dependency graph."""
        graph = {}
        for service_name, dependencies in self._service_dependencies.items():
            graph[service_name] = {
                "dependencies": list(dependencies),
                "dependents": []
            }

        # Build reverse dependencies
        for service_name, deps in self._service_dependencies.items():
            for dep in deps:
                if dep in graph:
                    graph[dep]["dependents"].append(service_name)

        return graph


# Global discovery instance
_simulation_discovery: Optional[SimulationServiceDiscovery] = None
_discovery_lock = threading.Lock()


def get_simulation_service_discovery() -> SimulationServiceDiscovery:
    """Get the global simulation service discovery instance."""
    global _simulation_discovery
    if _simulation_discovery is None:
        with _discovery_lock:
            if _simulation_discovery is None:
                _simulation_discovery = SimulationServiceDiscovery()
    return _simulation_discovery


def discover_service(service_name: str) -> Optional[ServiceInstance]:
    """Discover a service instance."""
    return get_simulation_service_discovery().discover_service(service_name)


def get_service_url(service_name: str) -> Optional[str]:
    """Get the URL for a service."""
    return get_simulation_service_discovery().get_service_url(service_name)


def get_ecosystem_health() -> Dict[str, Any]:
    """Get ecosystem health overview."""
    return get_simulation_service_discovery().get_ecosystem_health_overview()


__all__ = [
    'SimulationServiceDiscovery',
    'get_simulation_service_discovery',
    'discover_service',
    'get_service_url',
    'get_ecosystem_health'
]
