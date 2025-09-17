"""
Orchestrator Service - Domain Driven Design Architecture

Central control plane for the LLM Documentation Ecosystem following DDD principles.
Organized into bounded contexts with clear separation of concerns.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from typing import Optional

# Add parent directory to path for proper imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Shared utilities
from services.shared.health import register_health_endpoints
from services.shared.error_handling import register_exception_handlers
from services.shared.constants_new import ServiceNames
from services.shared.utilities import setup_common_middleware, attach_self_register

# Infrastructure components
from .infrastructure.persistence.in_memory import InMemoryWorkflowRepository, InMemoryWorkflowExecutionRepository
from .infrastructure.persistence.service_registry_repository import InMemoryServiceRepository
from .infrastructure.external_services.service_client import OrchestratorServiceClient

# Domain services (with static service definitions)
from .domain.service_registry.services import ServiceDiscoveryService, ServiceRegistrationService
from .domain.health_monitoring.services import HealthCheckService, SystemMonitoringService
from .modules.services import _get_service_definitions

# Application layer
from .application.workflow_management.use_cases import (
    CreateWorkflowUseCase, ExecuteWorkflowUseCase, GetWorkflowUseCase, ListWorkflowsUseCase
)
from .application.workflow_management.queries import ListWorkflowsQuery
from .application.service_registry.use_cases import (
    RegisterServiceUseCase, UnregisterServiceUseCase, GetServiceUseCase, ListServicesUseCase
)
from .application.health_monitoring.use_cases import (
    CheckSystemHealthUseCase, CheckServiceHealthUseCase, GetSystemHealthUseCase,
    GetServiceHealthUseCase, GetSystemInfoUseCase, GetSystemMetricsUseCase,
    GetSystemConfigUseCase, CheckSystemReadinessUseCase, ListWorkflowsUseCase as HealthListWorkflowsUseCase
)

# Presentation layer (API routes) - Optional for now
try:
    from .presentation.api.workflow_management.routes import router as workflow_router
except ImportError:
    workflow_router = None

try:
    from .presentation.api.health.routes import router as health_router
except ImportError:
    health_router = None

try:
    from .presentation.api.infrastructure.routes import router as infrastructure_router
except ImportError:
    infrastructure_router = None

# Service configuration
SERVICE_TITLE = "Orchestrator"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5099

# ============================================================================
# APPLICATION COMPOSITION - Dependency Injection Container
# ============================================================================

class OrchestratorContainer:
    """Dependency injection container for orchestrator service."""

    def __init__(self):
        # Infrastructure layer
        self.workflow_repository = InMemoryWorkflowRepository()
        self.execution_repository = InMemoryWorkflowExecutionRepository()
        self.service_repository = InMemoryServiceRepository()
        self.service_client = OrchestratorServiceClient()

        # Domain services
        self.service_discovery_service = ServiceDiscoveryService(_get_service_definitions())
        self.service_registration_service = ServiceRegistrationService()
        self.health_check_service = HealthCheckService()
        self.system_monitoring_service = SystemMonitoringService(self.health_check_service)

        # Application layer - Workflow Management
        from .domain.workflow_management.services.workflow_executor import WorkflowExecutor
        self.workflow_executor = WorkflowExecutor()

        self.create_workflow_use_case = CreateWorkflowUseCase(self.workflow_repository)
        self.execute_workflow_use_case = ExecuteWorkflowUseCase(
            self.workflow_repository,
            self.execution_repository,
            self.workflow_executor
        )
        self.get_workflow_use_case = GetWorkflowUseCase(self.workflow_repository)
        self.list_workflows_use_case = ListWorkflowsUseCase(self.workflow_repository)

        # Application layer - Service Registry
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
        self.check_system_health_use_case = CheckSystemHealthUseCase(self.system_monitoring_service)
        self.check_service_health_use_case = CheckServiceHealthUseCase(self.health_check_service)
        self.get_system_health_use_case = GetSystemHealthUseCase(self.system_monitoring_service)
        self.get_service_health_use_case = GetServiceHealthUseCase(self.system_monitoring_service)
        self.get_system_info_use_case = GetSystemInfoUseCase(self.system_monitoring_service)
        self.get_system_metrics_use_case = GetSystemMetricsUseCase(self.system_monitoring_service)
        self.get_system_config_use_case = GetSystemConfigUseCase(self.system_monitoring_service)
        self.check_system_readiness_use_case = CheckSystemReadinessUseCase(self.system_monitoring_service)
        self.health_list_workflows_use_case = HealthListWorkflowsUseCase()


# Global container instance
container = OrchestratorContainer()

# ============================================================================
# FASTAPI APPLICATION - Focused on composition and startup
# ============================================================================

app = FastAPI(
    title=SERVICE_TITLE,
    description="Central control plane and coordination service for the LLM Documentation Ecosystem",
    version=SERVICE_VERSION
)

# Use common middleware setup to reduce duplication across services
setup_common_middleware(app, ServiceNames.ORCHESTRATOR)

# Install error handlers and health endpoints
register_exception_handlers(app)
register_health_endpoints(app, ServiceNames.ORCHESTRATOR, SERVICE_VERSION)


@app.on_event("startup")
async def startup_event():
    """Handle orchestrator startup events."""
    print("🚀 Orchestrator service starting up...")

    # Initialize core components
    print("🔧 Initializing core components...")
    # Add initialization logic here as needed

    print("🎉 Orchestrator service startup complete!")


@app.on_event("shutdown")
async def shutdown_event():
    """Handle orchestrator shutdown events."""
    print("🛑 Orchestrator service shutting down...")

    # Add cleanup logic here as needed

    print("🏁 Orchestrator shutdown completed")
# ============================================================================
# API ROUTE REGISTRATION - Clean separation by bounded contexts
# ============================================================================

# Register API routes by bounded context (DDD-based)
try:
    from .presentation.api.workflow_management import router as workflow_router
    app.include_router(workflow_router, prefix="/api/v1/workflows", tags=["Workflow Management"])
except ImportError:
    print("⚠️  Workflow Management routes not available")

try:
    from .presentation.api.health_monitoring import router as health_router
    app.include_router(health_router, prefix="/api/v1/health", tags=["Health & Monitoring"])
except ImportError:
    print("⚠️  Health Monitoring routes not available")

try:
    from .presentation.api.infrastructure import router as infrastructure_router
    app.include_router(infrastructure_router, prefix="/api/v1/infrastructure", tags=["Infrastructure"])
except ImportError:
    print("⚠️  Infrastructure routes not available")

# Legacy route support (to be migrated)
@app.get("/workflows")
async def list_workflows():
    """List all available workflow configurations and capabilities."""
    query = ListWorkflowsQuery()
    result = await container.list_workflows_use_case.execute(query)
    return {"workflows": [w.to_dict() for w in result]}


if __name__ == "__main__":
    """Run the Orchestrator service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
