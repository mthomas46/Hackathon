"""Enhanced Dependency Injection Container - Enterprise DI with Ecosystem Integration.

This module provides a comprehensive dependency injection container that follows
existing ecosystem patterns from services/shared/core/di/ while adding
simulation-specific enhancements for enterprise-grade service management.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Type, TypeVar, Union
from datetime import datetime
import inspect
import weakref
import threading

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

# Import shared DI patterns (with fallbacks)
try:
    from core.di.services import IServiceProvider
    from core.di.container import Container
except ImportError:
    class IServiceProvider:
        def register_services(self) -> None: pass

    class Container:
        def resolve(self, service_name: str) -> Any: pass

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.execution.simulation_execution_engine import SimulationExecutionEngine
from simulation.infrastructure.health.simulation_health import (
    get_simulation_health_checker,
    get_simulation_health_endpoint
)

# Import health endpoints from the main health module
try:
    from simulation.infrastructure.health import create_simulation_health_endpoints
except ImportError:
    def create_simulation_health_endpoints():
        """Mock health endpoints function."""
        pass
from simulation.infrastructure.monitoring.simulation_monitoring import get_simulation_monitoring_service
from simulation.infrastructure.utilities.simulation_utilities import (
    get_simulation_validator,
    get_simulation_formatter,
    get_simulation_cache,
    get_simulation_task_manager,
    get_simulation_error_handler,
    get_simulation_retry_manager,
    get_simulation_performance_tracker
)
from simulation.infrastructure.repositories.in_memory_repositories import (
    get_project_repository,
    get_timeline_repository,
    get_team_repository,
    get_simulation_repository
)
from simulation.domain.services.simulation_domain_service import get_simulation_domain_service
from simulation.application.services.simulation_application_service import SimulationApplicationService

T = TypeVar('T')


class EnhancedSimulationServiceProvider(IServiceProvider):
    """Enhanced service provider for project-simulation dependencies with comprehensive service management."""

    def __init__(self):
        self._container = Container()
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._service_metadata: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.logger = get_simulation_logger()

    def register_services(self) -> None:
        """Register all simulation services with enhanced metadata tracking."""
        with self._lock:
            # Infrastructure services
            self._register_infrastructure_services()

            # Domain services
            self._register_domain_services()

            # Application services
            self._register_application_services()

            # Utility services
            self._register_utility_services()

            # External service integrations
            self._register_external_services()

            self.logger.info("All simulation services registered successfully")

    def _register_infrastructure_services(self) -> None:
        """Register infrastructure services with enhanced monitoring."""
        # Core logging
        self._singletons["logger"] = get_simulation_logger()
        self._service_metadata["logger"] = {"type": "infrastructure", "tags": ["core", "logging"]}

        # Enhanced health monitoring
        self._singletons["health_checker"] = get_simulation_health_checker()
        self._service_metadata["health_checker"] = {"type": "infrastructure", "tags": ["health", "monitoring", "core"]}

        self._singletons["health_endpoint"] = get_simulation_health_endpoint()
        self._service_metadata["health_endpoint"] = {"type": "infrastructure", "tags": ["health", "api", "monitoring"]}

        # Comprehensive monitoring
        self._singletons["monitoring_service"] = get_simulation_monitoring_service()
        self._service_metadata["monitoring_service"] = {"type": "infrastructure", "tags": ["monitoring", "metrics", "core"]}

        # Repository layer
        self._singletons["project_repository"] = get_project_repository()
        self._service_metadata["project_repository"] = {"type": "infrastructure", "tags": ["repository", "data", "project"]}

        self._singletons["timeline_repository"] = get_timeline_repository()
        self._service_metadata["timeline_repository"] = {"type": "infrastructure", "tags": ["repository", "data", "timeline"]}

        self._singletons["team_repository"] = get_team_repository()
        self._service_metadata["team_repository"] = {"type": "infrastructure", "tags": ["repository", "data", "team"]}

        # Use SQLite repository for persistence
        from .repositories.sqlite_repositories import get_sqlite_simulation_repository
        self._singletons["simulation_repository"] = get_sqlite_simulation_repository()
        self._service_metadata["simulation_repository"] = {"type": "infrastructure", "tags": ["repository", "data", "simulation"]}

    def _register_domain_services(self) -> None:
        """Register domain services with dependency injection."""
        # Enhanced domain service
        self._singletons["domain_service"] = get_simulation_domain_service()
        self._service_metadata["domain_service"] = {"type": "domain", "tags": ["domain", "business_logic", "core"]}

    def _register_application_services(self) -> None:
        """Register application services with comprehensive dependencies."""
        # Simulation Application Service with enhanced dependencies
        def create_simulation_app_service():
            return SimulationApplicationService(
                domain_service=self.get_service("domain_service"),
                project_repository=self.get_service("project_repository"),
                timeline_repository=self.get_service("timeline_repository"),
                team_repository=self.get_service("team_repository"),
                simulation_repository=self.get_service("simulation_repository"),
                monitoring_service=self.get_service("monitoring_service"),
                logger=self.get_service("logger")
            )

        self._factories["simulation_application_service"] = create_simulation_app_service
        self._service_metadata["simulation_application_service"] = {"type": "application", "tags": ["application", "orchestration", "core"]}

        # Core Simulation Execution Engine
        def create_simulation_execution_engine():
            from .content.content_generation_pipeline import ContentGenerationPipeline
            from .clients.ecosystem_clients import get_ecosystem_service_registry
            from .workflows.workflow_orchestrator import SimulationWorkflowOrchestrator

            return SimulationExecutionEngine(
                content_pipeline=ContentGenerationPipeline(),
                ecosystem_clients=get_ecosystem_service_registry(),
                workflow_orchestrator=SimulationWorkflowOrchestrator(),
                logger=self.get_service("logger"),
                monitoring_service=self.get_service("monitoring_service"),
                simulation_repository=self.get_service("simulation_repository"),
                project_repository=self.get_service("project_repository"),
                timeline_repository=self.get_service("timeline_repository"),
                team_repository=self.get_service("team_repository")
            )

        self._factories["simulation_execution_engine"] = create_simulation_execution_engine
        self._service_metadata["simulation_execution_engine"] = {"type": "infrastructure", "tags": ["execution", "simulation", "core"]}

    def _register_utility_services(self) -> None:
        """Register utility services for validation, formatting, and resilience."""
        # Data validation
        self._singletons["validator"] = get_simulation_validator()
        self._service_metadata["validator"] = {"type": "utility", "tags": ["validation", "data", "quality"]}

        # Data formatting
        self._singletons["formatter"] = get_simulation_formatter()
        self._service_metadata["formatter"] = {"type": "utility", "tags": ["formatting", "presentation", "data"]}

        # Caching
        self._singletons["cache"] = get_simulation_cache()
        self._service_metadata["cache"] = {"type": "utility", "tags": ["caching", "performance", "infrastructure"]}

        # Async task management
        self._singletons["task_manager"] = get_simulation_task_manager()
        self._service_metadata["task_manager"] = {"type": "utility", "tags": ["async", "tasks", "concurrency"]}

        # Error handling
        self._singletons["error_handler"] = get_simulation_error_handler()
        self._service_metadata["error_handler"] = {"type": "utility", "tags": ["error", "resilience", "handling"]}

        # Retry management
        self._singletons["retry_manager"] = get_simulation_retry_manager()
        self._service_metadata["retry_manager"] = {"type": "utility", "tags": ["retry", "resilience", "reliability"]}

        # Performance tracking
        self._singletons["performance_tracker"] = get_simulation_performance_tracker()
        self._service_metadata["performance_tracker"] = {"type": "utility", "tags": ["performance", "monitoring", "metrics"]}

    def _register_external_services(self) -> None:
        """Register external service integrations."""
        # Document generation service (mock-data-generator integration)
        self._factories["document_generation_service"] = self._create_document_generation_service
        self._service_metadata["document_generation_service"] = {"type": "external", "tags": ["external", "documents", "generation"]}

        # Workflow execution service (orchestrator integration)
        self._factories["workflow_execution_service"] = self._create_workflow_execution_service
        self._service_metadata["workflow_execution_service"] = {"type": "external", "tags": ["external", "workflow", "orchestration"]}

    def _create_document_generation_service(self):
        """Create document generation service with mock-data-generator integration."""
        # Enhanced document generation service with ecosystem integration
        class EnhancedDocumentGenerationService:
            def __init__(self, cache_manager=None, retry_manager=None):
                self.cache = cache_manager or get_simulation_cache()
                self.retry_manager = retry_manager or get_simulation_retry_manager()
                self.logger = get_simulation_logger()

            async def generate_project_documents(self, project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
                """Generate project documents using enhanced mock-data-generator integration."""
                try:
                    # Use cache if available
                    cache_key = f"docs:project:{hash(str(project_config))}"
                    cached_result = self.cache.get(cache_key)
                    if cached_result:
                        return cached_result

                    # Generate documents with retry logic
                    documents = await self._generate_with_retry(project_config)

                    # Cache the result
                    self.cache.set(cache_key, documents, ttl=3600)  # 1 hour TTL

                    return documents

                except Exception as e:
                    self.logger.error("Document generation failed", error=str(e))
                    return []

            async def _generate_with_retry(self, project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
                """Generate documents with retry logic."""
                async def generate_attempt():
                    # This would integrate with mock-data-generator service
                    # For now, return enhanced mock data
                    return [
                        {
                            "id": f"req_{project_config.get('id', 'unknown')}",
                            "type": "project_requirements",
                            "title": f"{project_config.get('name', 'Project')} Requirements",
                            "content": f"Requirements for {project_config.get('name', 'the project')}",
                            "quality_score": 0.85,
                            "metadata": {"phase": "planning", "complexity": project_config.get('complexity', 'medium')}
                        },
                        {
                            "id": f"arch_{project_config.get('id', 'unknown')}",
                            "type": "architecture_diagram",
                            "title": f"{project_config.get('name', 'Project')} Architecture",
                            "content": "System architecture documentation",
                            "quality_score": 0.92,
                            "metadata": {"phase": "design", "complexity": project_config.get('complexity', 'medium')}
                        }
                    ]

                return await self.retry_manager.execute_with_simulation_retry(
                    "document_generation", generate_attempt
                )

            async def generate_phase_documents(self, project_config: Dict[str, Any], phase_name: str) -> List[Dict[str, Any]]:
                """Generate phase-specific documents."""
                try:
                    phase_docs = [
                        {
                            "id": f"{phase_name.lower()}_{project_config.get('id', 'unknown')}",
                            "type": f"{phase_name.lower()}_documentation",
                            "title": f"{phase_name} Phase Documentation",
                            "content": f"Documentation for {phase_name} phase",
                            "quality_score": 0.88,
                            "metadata": {"phase": phase_name, "complexity": project_config.get('complexity', 'medium')}
                        }
                    ]

                    return phase_docs

                except Exception as e:
                    self.logger.error("Phase document generation failed", error=str(e))
                    return []

        return EnhancedDocumentGenerationService(
            cache_manager=self.get_service("cache"),
            retry_manager=self.get_service("retry_manager")
        )

    def _create_workflow_execution_service(self):
        """Create workflow execution service with orchestrator integration."""
        # Enhanced workflow execution service
        class EnhancedWorkflowExecutionService:
            def __init__(self, task_manager=None, monitoring_service=None, logger=None):
                self.task_manager = task_manager or get_simulation_task_manager()
                self.monitoring = monitoring_service or get_simulation_monitoring_service()
                self.logger = logger or get_simulation_logger()

            async def execute_document_analysis_workflow(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
                """Execute document analysis workflow with comprehensive tracking."""
                start_time = datetime.now()

                try:
                    # Track workflow execution
                    self.monitoring.record_simulation_event("workflow_started", "analysis_workflow")

                    # Execute analysis tasks in parallel
                    analysis_tasks = []
                    for doc in documents:
                        task = self.task_manager.run_simulation_task(
                            f"analyze_{doc.get('id', 'unknown')}",
                            self._analyze_document(doc)
                        )
                        analysis_tasks.append(task)

                    results = await asyncio.gather(*analysis_tasks, return_exceptions=True)

                    # Process results
                    successful_analyses = [r for r in results if not isinstance(r, Exception)]
                    failed_analyses = [r for r in results if isinstance(r, Exception)]

                    execution_time = (datetime.now() - start_time).total_seconds()

                    result = {
                        "success": len(failed_analyses) == 0,
                        "execution_time": execution_time,
                        "documents_analyzed": len(successful_analyses),
                        "analysis_results": successful_analyses,
                        "errors": [str(e) for e in failed_analyses]
                    }

                    # Track completion
                    self.monitoring.record_simulation_event(
                        "workflow_completed",
                        "analysis_workflow",
                        duration_seconds=execution_time,
                        success=result["success"]
                    )

                    return result

                except Exception as e:
                    self.logger.error("Document analysis workflow failed", error=str(e))
                    return {
                        "success": False,
                        "execution_time": (datetime.now() - start_time).total_seconds(),
                        "error": str(e)
                    }

            async def execute_team_dynamics_workflow(self, team_config: Dict[str, Any]) -> Dict[str, Any]:
                """Execute team dynamics analysis workflow."""
                start_time = datetime.now()

                try:
                    # Track workflow execution
                    self.monitoring.record_simulation_event("workflow_started", "team_dynamics_workflow")

                    # Analyze team composition and dynamics
                    analysis_result = await self._analyze_team_dynamics(team_config)

                    execution_time = (datetime.now() - start_time).total_seconds()

                    result = {
                        "success": True,
                        "execution_time": execution_time,
                        "team_analysis": analysis_result
                    }

                    # Track completion
                    self.monitoring.record_simulation_event(
                        "workflow_completed",
                        "team_dynamics_workflow",
                        duration_seconds=execution_time,
                        success=True
                    )

                    return result

                except Exception as e:
                    self.logger.error("Team dynamics workflow failed", error=str(e))
                    return {
                        "success": False,
                        "execution_time": (datetime.now() - start_time).total_seconds(),
                        "error": str(e)
                    }

            async def _analyze_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
                """Analyze a single document."""
                # Simulate document analysis
                await asyncio.sleep(0.1)  # Simulate processing time

                return {
                    "document_id": document.get("id"),
                    "quality_score": document.get("quality_score", 0.8),
                    "insights": ["Document analysis completed"],
                    "recommendations": ["Review content for completeness"]
                }

            async def _analyze_team_dynamics(self, team_config: Dict[str, Any]) -> Dict[str, Any]:
                """Analyze team dynamics."""
                # Simulate team analysis
                await asyncio.sleep(0.05)  # Simulate processing time

                return {
                    "team_size": len(team_config.get("members", [])),
                    "skill_distribution": "balanced",
                    "collaboration_score": 0.85,
                    "recommendations": ["Team composition is optimal"]
                }

        return EnhancedWorkflowExecutionService(
            task_manager=self.get_service("task_manager"),
            monitoring_service=self.get_service("monitoring_service"),
            logger=self.get_service("logger")
        )

    def get_service(self, service_name: str) -> Any:
        """Get a service instance with enhanced error handling."""
        with self._lock:
            # Check singletons first
            if service_name in self._singletons:
                return self._singletons[service_name]

            # Check factories
            if service_name in self._factories:
                try:
                    instance = self._factories[service_name]()
                    self.logger.debug(f"Created service instance: {service_name}")
                    return instance
                except Exception as e:
                    self.logger.error(f"Failed to create service {service_name}", error=str(e))
                    raise

            # Check legacy services
            if service_name in self._services:
                try:
                    return self._services[service_name]()
                except Exception as e:
                    self.logger.error(f"Failed to create legacy service {service_name}", error=str(e))
                    raise

            raise ValueError(f"Service '{service_name}' not registered")

    def has_service(self, service_name: str) -> bool:
        """Check if a service is registered."""
        return (service_name in self._singletons or
                service_name in self._factories or
                service_name in self._services)

    def get_all_services(self) -> Dict[str, Any]:
        """Get all registered services with metadata."""
        all_services = {}
        service_names = set()
        service_names.update(self._singletons.keys())
        service_names.update(self._factories.keys())
        service_names.update(self._services.keys())

        for service_name in service_names:
            try:
                all_services[service_name] = {
                    "instance": self.get_service(service_name),
                    "metadata": self._service_metadata.get(service_name, {})
                }
            except Exception as e:
                self.logger.warning(f"Could not instantiate service {service_name}", error=str(e))
                all_services[service_name] = {
                    "instance": None,
                    "metadata": self._service_metadata.get(service_name, {}),
                    "error": str(e)
                }

        return all_services

    def get_service_metadata(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific service."""
        return self._service_metadata.get(service_name)

    def get_services_by_type(self, service_type: str) -> List[str]:
        """Get all services of a specific type."""
        return [name for name, metadata in self._service_metadata.items()
                if metadata.get("type") == service_type]

    def get_services_by_tag(self, tag: str) -> List[str]:
        """Get all services with a specific tag."""
        return [name for name, metadata in self._service_metadata.items()
                if tag in metadata.get("tags", [])]

    def get_service_health_status(self) -> Dict[str, Any]:
        """Get health status of all services."""
        health_status = {}
        for service_name in self.get_registered_services():
            try:
                service = self.get_service(service_name)
                # Simple health check - service is healthy if it can be instantiated
                health_status[service_name] = {
                    "healthy": True,
                    "metadata": self._service_metadata.get(service_name, {})
                }
            except Exception as e:
                health_status[service_name] = {
                    "healthy": False,
                    "error": str(e),
                    "metadata": self._service_metadata.get(service_name, {})
                }

        return health_status

    def get_registered_services(self) -> List[str]:
        """Get list of all registered service names."""
        services = set()
        services.update(self._singletons.keys())
        services.update(self._factories.keys())
        services.update(self._services.keys())
        return sorted(list(services))


class EnhancedSimulationContainer(Container):
    """Enhanced container for project-simulation service with enterprise features."""

    def __init__(self):
        super().__init__()
        self._provider = EnhancedSimulationServiceProvider()
        self._provider.register_services()
        self.logger = get_simulation_logger()

    def resolve(self, service_name: str) -> Any:
        """Resolve a service by name with enhanced error handling."""
        try:
            return self._provider.get_service(service_name)
        except Exception as e:
            self.logger.error(f"Failed to resolve service {service_name}", error=str(e))
            raise

    def has_service(self, service_name: str) -> bool:
        """Check if service is available."""
        return self._provider.has_service(service_name)

    def get_service_info(self, service_name: str) -> Dict[str, Any]:
        """Get comprehensive information about a service."""
        return {
            "available": self.has_service(service_name),
            "metadata": self._provider.get_service_metadata(service_name),
            "instance": None  # Don't instantiate unless requested
        }

    def get_services_summary(self) -> Dict[str, Any]:
        """Get comprehensive services summary."""
        all_services = self._provider.get_all_services()
        registered_services = self._provider.get_registered_services()

        summary = {
            "total_services": len(registered_services),
            "services_by_type": {},
            "services_by_tag": {},
            "healthy_services": 0,
            "unhealthy_services": 0,
            "service_details": {}
        }

        # Categorize services
        for service_name in registered_services:
            metadata = self._provider.get_service_metadata(service_name) or {}
            service_type = metadata.get("type", "unknown")
            tags = metadata.get("tags", [])

            # Count by type
            summary["services_by_type"][service_type] = summary["services_by_type"].get(service_type, 0) + 1

            # Count by tags
            for tag in tags:
                summary["services_by_tag"][tag] = summary["services_by_tag"].get(tag, 0) + 1

            # Service details
            summary["service_details"][service_name] = {
                "type": service_type,
                "tags": tags,
                "healthy": all_services.get(service_name, {}).get("instance") is not None
            }

            if summary["service_details"][service_name]["healthy"]:
                summary["healthy_services"] += 1
            else:
                summary["unhealthy_services"] += 1

        return summary

    # Enhanced property accessors with error handling
    @property
    def logger(self):
        """Get logger service."""
        # Return stored logger if available, otherwise resolve from provider
        if hasattr(self, '_logger'):
            return self._logger
        return self.resolve("logger")

    @logger.setter
    def logger(self, value):
        """Set logger service."""
        # Store logger directly as an attribute for easy access
        self._logger = value

    @property
    def health_checker(self):
        """Get health checker service."""
        return self.resolve("health_checker")

    @property
    def health_endpoint(self):
        """Get health endpoint service."""
        return self.resolve("health_endpoint")

    @property
    def monitoring_service(self):
        """Get monitoring service."""
        return self.resolve("monitoring_service")

    @property
    def project_repository(self):
        """Get project repository."""
        return self.resolve("project_repository")

    @property
    def simulation_application_service(self):
        """Get simulation application service."""
        return self.resolve("simulation_application_service")

    @property
    def domain_service(self):
        """Get domain service."""
        return self.resolve("domain_service")

    # Utility services
    @property
    def validator(self):
        """Get data validator service."""
        return self.resolve("validator")

    @property
    def formatter(self):
        """Get data formatter service."""
        return self.resolve("formatter")

    @property
    def cache(self):
        """Get cache manager service."""
        return self.resolve("cache")

    @property
    def task_manager(self):
        """Get async task manager service."""
        return self.resolve("task_manager")

    @property
    def error_handler(self):
        """Get error handler service."""
        return self.resolve("error_handler")

    @property
    def retry_manager(self):
        """Get retry manager service."""
        return self.resolve("retry_manager")

    @property
    def performance_tracker(self):
        """Get performance tracker service."""
        return self.resolve("performance_tracker")

    # External service integrations
    @property
    def document_generation_service(self):
        """Get document generation service."""
        return self.resolve("document_generation_service")

    @property
    def workflow_execution_service(self):
        """Get workflow execution service."""
        return self.resolve("workflow_execution_service")


# Maintain backward compatibility
SimulationServiceProvider = EnhancedSimulationServiceProvider
SimulationContainer = EnhancedSimulationContainer


# Global container instance
_simulation_container: Optional[EnhancedSimulationContainer] = None
_container_lock = threading.Lock()


def get_simulation_container() -> EnhancedSimulationContainer:
    """Get the global simulation container instance with thread safety."""
    global _simulation_container
    if _simulation_container is None:
        with _container_lock:
            if _simulation_container is None:
                _simulation_container = EnhancedSimulationContainer()
    return _simulation_container


def get_service(service_name: str) -> Any:
    """Get a service from the global container with error handling."""
    try:
        return get_simulation_container().resolve(service_name)
    except Exception as e:
        logger = get_simulation_logger()
        logger.error(f"Failed to get service {service_name}", error=str(e))
        raise


# Enhanced convenience functions
def get_logger():
    """Get logger service."""
    return get_simulation_container().logger

def get_health_checker():
    """Get health checker service."""
    return get_simulation_container().health_checker

def get_health_endpoint():
    """Get health endpoint service."""
    return get_simulation_container().health_endpoint

def get_monitoring_service():
    """Get monitoring service."""
    return get_simulation_container().monitoring_service

def get_application_service():
    """Get simulation application service."""
    return get_simulation_container().simulation_application_service

def get_domain_service():
    """Get domain service."""
    return get_simulation_container().domain_service

# Utility service getters
def get_validator():
    """Get data validator service."""
    return get_simulation_container().validator

def get_formatter():
    """Get data formatter service."""
    return get_simulation_container().formatter

def get_cache():
    """Get cache manager service."""
    return get_simulation_container().cache

def get_task_manager():
    """Get async task manager service."""
    return get_simulation_container().task_manager

def get_error_handler():
    """Get error handler service."""
    return get_simulation_container().error_handler

def get_retry_manager():
    """Get retry manager service."""
    return get_simulation_container().retry_manager

def get_performance_tracker():
    """Get performance tracker service."""
    return get_simulation_container().performance_tracker

# External service getters
def get_document_generation_service():
    """Get document generation service."""
    return get_simulation_container().document_generation_service

def get_workflow_execution_service():
    """Get workflow execution service."""
    return get_simulation_container().workflow_execution_service


# Container diagnostics and health
def get_container_diagnostics() -> Dict[str, Any]:
    """Get comprehensive container diagnostics."""
    container = get_simulation_container()
    return container.get_services_summary()


def get_container_health() -> Dict[str, Any]:
    """Get container health status."""
    container = get_simulation_container()
    return container._provider.get_service_health_status()


# Dependency injection decorators
def inject_service(*service_names: str):
    """Decorator to inject services into functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            container = get_simulation_container()
            for service_name in service_names:
                if service_name not in kwargs:
                    try:
                        kwargs[service_name] = container.resolve(service_name)
                    except ValueError:
                        pass  # Service not found, continue without injection
            return func(*args, **kwargs)
        return wrapper
    return decorator


def injectable_service(cls):
    """Decorator to make a class injectable with automatic service resolution."""
    original_init = cls.__init__

    def dependency_injecting_init(self, *args, **kwargs):
        container = get_simulation_container()
        # Get constructor signature
        import inspect
        signature = inspect.signature(original_init)
        parameters = signature.parameters

        # Inject services for unbound parameters
        for param_name, param in parameters.items():
            if param_name == 'self':
                continue
            if param_name not in kwargs and param_name not in signature.bind_partial(self, *args).arguments:
                # Try to resolve from container
                if container.has_service(param_name):
                    kwargs[param_name] = container.resolve(param_name)

        return original_init(self, *args, **kwargs)

    cls.__init__ = dependency_injecting_init
    return cls


__all__ = [
    # Core Classes
    'EnhancedSimulationServiceProvider',
    'EnhancedSimulationContainer',

    # Backward Compatibility
    'SimulationServiceProvider',
    'SimulationContainer',

    # Global Functions
    'get_simulation_container',
    'get_service',

    # Service Getters
    'get_logger',
    'get_health_checker',
    'get_health_endpoint',
    'get_monitoring_service',
    'get_application_service',
    'get_domain_service',
    'get_validator',
    'get_formatter',
    'get_cache',
    'get_task_manager',
    'get_error_handler',
    'get_retry_manager',
    'get_performance_tracker',
    'get_document_generation_service',
    'get_workflow_execution_service',

    # Diagnostics
    'get_container_diagnostics',
    'get_container_health',

    # Decorators
    'inject_service',
    'injectable_service'
]
