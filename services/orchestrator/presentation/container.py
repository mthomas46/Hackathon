"""Dependency Injection Container for Presentation Layer"""

from typing import Optional
import threading


class OrchestratorContainer:
    """Dependency injection container for the orchestrator service."""

    _instance: Optional['OrchestratorContainer'] = None
    _lock = threading.Lock()

    def __init__(self):
        """Initialize the container with all dependencies."""
        self._initialized = False

    def _initialize_dependencies(self):
        """Initialize all dependencies lazily."""
        if self._initialized:
            return

        # Infrastructure layer
        from ..infrastructure.persistence.in_memory import InMemoryWorkflowRepository, InMemoryWorkflowExecutionRepository
        from ..infrastructure.persistence.service_registry_repository import InMemoryServiceRepository
        from ..infrastructure.external_services.service_client import OrchestratorServiceClient

        self.workflow_repository = InMemoryWorkflowRepository()
        self.execution_repository = InMemoryWorkflowExecutionRepository()
        self.service_repository = InMemoryServiceRepository()
        self.service_client = OrchestratorServiceClient()

        # Domain services (static definitions for now)
        from ..domain.service_registry.services import ServiceDiscoveryService, ServiceRegistrationService
        from ..domain.health_monitoring.services import HealthCheckService, SystemMonitoringService
        from ..domain.workflow_management.services.workflow_executor import WorkflowExecutor
        from ..modules.services import _get_service_definitions

        self.service_discovery_service = ServiceDiscoveryService(_get_service_definitions())
        self.service_registration_service = ServiceRegistrationService()
        self.health_check_service = HealthCheckService()
        self.system_monitoring_service = SystemMonitoringService(self.health_check_service)
        self.workflow_executor = WorkflowExecutor()

        # Application layer - Workflow Management
        from ..application.workflow_management.use_cases import (
            CreateWorkflowUseCase, ExecuteWorkflowUseCase, GetWorkflowUseCase,
            ListWorkflowsUseCase, ListWorkflowExecutionsUseCase, GetWorkflowExecutionUseCase
        )

        self.create_workflow_use_case = CreateWorkflowUseCase(self.workflow_repository)
        self.execute_workflow_use_case = ExecuteWorkflowUseCase(
            self.workflow_repository,
            self.execution_repository,
            self.workflow_executor
        )
        self.get_workflow_use_case = GetWorkflowUseCase(self.workflow_repository)
        self.list_workflows_use_case = ListWorkflowsUseCase(self.workflow_repository)
        self.list_workflow_executions_use_case = ListWorkflowExecutionsUseCase(self.execution_repository)
        self.get_workflow_execution_use_case = GetWorkflowExecutionUseCase(self.execution_repository)

        # Application layer - Service Registry
        from ..application.service_registry.use_cases import (
            RegisterServiceUseCase, UnregisterServiceUseCase, GetServiceUseCase, ListServicesUseCase
        )

        self.register_service_use_case = RegisterServiceUseCase(self.service_registration_service)
        self.unregister_service_use_case = UnregisterServiceUseCase(self.service_registration_service)
        self.get_service_use_case = GetServiceUseCase(
            self.service_discovery_service,
            self.service_registration_service
        )
        self.list_services_use_case = ListServicesUseCase(
            self.service_discovery_service,
            self.service_registration_service
        )

        # Application layer - Health Monitoring
        from ..application.health_monitoring.use_cases import (
            CheckSystemHealthUseCase, CheckServiceHealthUseCase, GetSystemHealthUseCase,
            GetServiceHealthUseCase, GetSystemInfoUseCase, GetSystemMetricsUseCase,
            GetSystemConfigUseCase, CheckSystemReadinessUseCase, ListWorkflowsUseCase as HealthListWorkflowsUseCase
        )

        self.check_system_health_use_case = CheckSystemHealthUseCase(self.system_monitoring_service)
        self.check_service_health_use_case = CheckServiceHealthUseCase(self.health_check_service)
        self.get_system_health_use_case = GetSystemHealthUseCase(self.system_monitoring_service)
        self.get_service_health_use_case = GetServiceHealthUseCase(self.system_monitoring_service)
        self.get_system_info_use_case = GetSystemInfoUseCase(self.system_monitoring_service)
        self.get_system_metrics_use_case = GetSystemMetricsUseCase(self.system_monitoring_service)
        self.get_system_config_use_case = GetSystemConfigUseCase(self.system_monitoring_service)
        self.check_system_readiness_use_case = CheckSystemReadinessUseCase(self.system_monitoring_service)
        self.health_list_workflows_use_case = HealthListWorkflowsUseCase()

        self._initialized = True

    @classmethod
    def get_instance(cls) -> 'OrchestratorContainer':
        """Get singleton instance of the container."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def __getattr__(self, name):
        """Lazy initialization of dependencies."""
        if not self._initialized:
            self._initialize_dependencies()
        return getattr(self, name)


def get_container() -> OrchestratorContainer:
    """Get the global container instance."""
    return OrchestratorContainer.get_instance()
