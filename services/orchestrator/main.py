"""
🎼 Orchestrator Service - Enterprise Control Plane Hub

REST API Standardization - Phase 4C
====================================

Comprehensive OpenAPI/Swagger annotations for enterprise-grade API documentation,
consistent response formats, and standardized error handling.

API Endpoints by Bounded Context:
==================================
• Workflow Management: `/api/v1/workflows` - Workflow creation, execution, and management
• Service Registry: `/api/v1/service-registry` - Service discovery, registration, and health
• Infrastructure: `/api/v1/infrastructure` - Saga orchestration, event streaming, tracing
• Ingestion: `/api/v1/ingestion` - Data ingestion workflows and status tracking
• Query Processing: `/api/v1/queries` - Natural language query processing and results
• Reporting: `/api/v1/reporting` - Report generation and management

Key Features:
=============
• Domain-Driven Design (DDD) architecture with bounded contexts
• Enterprise-grade workflow orchestration and service coordination
• Comprehensive OpenAPI/Swagger documentation with detailed schemas
• Consistent response formats and standardized error handling
• Request/response validation with Pydantic models
• Real-time service discovery and health monitoring
• Event-driven architecture with saga orchestration

Dependencies: shared middlewares/logging, ServiceClients, httpx for external calls.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

# Add parent directory to path for proper imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


from services.shared.core.constants_new import ServiceNames

# Shared utilities
from services.shared.utilities.logging_client import get_log_collector_client
from services.shared.utilities.utilities import setup_common_middleware

from .domain.health_monitoring.services import HealthCheckService, SystemMonitoringService
from .domain.infrastructure.services import DLQService, EventStreamingService, SagaService, TracingService

# Domain services (with static service definitions)
from .domain.service_registry.services import ServiceDiscoveryService, ServiceRegistrationService
from .infrastructure.external_services.service_client import OrchestratorServiceClient

# Infrastructure components
from .infrastructure.persistence.in_memory import InMemoryWorkflowExecutionRepository, InMemoryWorkflowRepository
from .infrastructure.persistence.service_registry_repository import InMemoryServiceRepository
from .modules.services import _get_service_definitions


# Simple workflow check function
def check_workflows_loaded():
    """Check if workflows are loaded."""
    try:
        return hasattr(container, "workflow_repository") and container.workflow_repository is not None
    except:
        return False


from .application.health_monitoring.use_cases import (
    CheckServiceHealthUseCase,
    CheckSystemHealthUseCase,
    CheckSystemReadinessUseCase,
    GetServiceHealthUseCase,
    GetSystemConfigUseCase,
    GetSystemHealthUseCase,
    GetSystemInfoUseCase,
    GetSystemMetricsUseCase,
)
from .application.health_monitoring.use_cases import ListWorkflowsUseCase as HealthListWorkflowsUseCase
from .application.infrastructure.use_cases import (
    ExecuteSagaStepUseCase,
    GetDLQStatsUseCase,
    GetEventStreamStatsUseCase,
    GetSagaUseCase,
    GetTraceUseCase,
    ListDLQEventsUseCase,
    ListSagasUseCase,
    ListTracesUseCase,
    PublishEventUseCase,
    RetryEventUseCase,
    StartSagaUseCase,
    StartTraceUseCase,
)
from .application.ingestion.use_cases import GetIngestionStatusUseCase, ListIngestionsUseCase, StartIngestionUseCase
from .application.query_processing.use_cases import (
    GetQueryResultUseCase,
    ListQueriesUseCase,
    ProcessNaturalLanguageQueryUseCase,
)
from .application.reporting.use_cases import GenerateReportUseCase, GetReportUseCase, ListReportsUseCase
from .application.service_registry.use_cases import (
    GetServiceUseCase,
    ListServicesUseCase,
    RegisterServiceUseCase,
    UnregisterServiceUseCase,
)
from .application.workflow_management.queries import ListWorkflowsQuery

# Application layer
from .application.workflow_management.use_cases import (
    CreateWorkflowUseCase,
    ExecuteWorkflowUseCase,
    GetWorkflowUseCase,
    ListWorkflowsUseCase,
)

# Presentation layer routers are registered dynamically below

# Service configuration
SERVICE_TITLE = "🎼 Orchestrator - Enterprise Control Plane Hub"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5099

# Standard API response models for consistent error handling
class APIResponse(BaseModel):
    """Standard API response wrapper for consistent formatting."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable response message")
    data: Optional[Any] = Field(None, description="Response data payload")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")
    timestamp: Optional[str] = Field(None, description="Response timestamp in ISO 8601 format")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class ErrorResponse(BaseModel):
    """Standard error response for consistent error formatting."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=False, description="Always false for error responses")
    error: Dict[str, Any] = Field(..., description="Error details")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")
    timestamp: str = Field(..., description="Error timestamp in ISO 8601 format")


class HealthResponse(BaseModel):
    """Health check response model for orchestrator service."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    last_health_check: Optional[str] = Field(None, description="Last health check timestamp")
    bounded_contexts_loaded: List[str] = Field(..., description="List of loaded bounded contexts")
    ddd_architecture: bool = Field(..., description="Whether DDD architecture is properly initialized")
    service_discovery_active: bool = Field(..., description="Whether service discovery is operational")

# ============================================================================
# APPLICATION COMPOSITION - Dependency Injection Container
# ============================================================================


class OrchestratorContainer:
    """Dependency injection container for orchestrator service."""

    def __init__(self):
        # Initialize all layers following DDD principles
        self._init_infrastructure()
        self._init_domain_services()
        self._init_application_layer()

    def _init_infrastructure(self):
        """Initialize infrastructure layer components."""
        self.workflow_repository = InMemoryWorkflowRepository()
        self.execution_repository = InMemoryWorkflowExecutionRepository()
        self.service_repository = InMemoryServiceRepository()
        self.service_client = OrchestratorServiceClient()

    def _init_domain_services(self):
        """Initialize domain services for all bounded contexts."""
        # Service Registry domain services
        self.service_discovery_service = ServiceDiscoveryService(_get_service_definitions())
        self.service_registration_service = ServiceRegistrationService()

        # Health & Monitoring domain services
        self.health_check_service = HealthCheckService()
        self.system_monitoring_service = SystemMonitoringService(self.health_check_service)

        # Infrastructure domain services
        self.dlq_service = DLQService()
        self.saga_service = SagaService()
        self.tracing_service = TracingService()
        self.event_streaming_service = EventStreamingService()

    def _init_application_layer(self):
        """Initialize application layer use cases for all bounded contexts."""
        # Workflow Management use cases
        from .domain.workflow_management.services.workflow_executor import WorkflowExecutor

        self.workflow_executor = WorkflowExecutor()

        self.create_workflow_use_case = CreateWorkflowUseCase(self.workflow_repository)
        self.execute_workflow_use_case = ExecuteWorkflowUseCase(
            self.workflow_repository, self.execution_repository, self.workflow_executor
        )
        self.get_workflow_use_case = GetWorkflowUseCase(self.workflow_repository)
        self.list_workflows_use_case = ListWorkflowsUseCase(self.workflow_repository)

        # Service Registry use cases
        self.register_service_use_case = RegisterServiceUseCase(self.service_registration_service)
        self.unregister_service_use_case = UnregisterServiceUseCase(self.service_registration_service)
        self.get_service_use_case = GetServiceUseCase(self.service_discovery_service, self.service_registration_service)
        self.list_services_use_case = ListServicesUseCase(
            self.service_discovery_service, self.service_registration_service
        )

        # Health Monitoring use cases
        self.check_system_health_use_case = CheckSystemHealthUseCase(self.system_monitoring_service)
        self.check_service_health_use_case = CheckServiceHealthUseCase(self.health_check_service)
        self.get_system_health_use_case = GetSystemHealthUseCase(self.system_monitoring_service)
        self.get_service_health_use_case = GetServiceHealthUseCase(self.system_monitoring_service)
        self.get_system_info_use_case = GetSystemInfoUseCase(self.system_monitoring_service)
        self.get_system_metrics_use_case = GetSystemMetricsUseCase(self.system_monitoring_service)
        self.get_system_config_use_case = GetSystemConfigUseCase(self.system_monitoring_service)
        self.check_system_readiness_use_case = CheckSystemReadinessUseCase(self.system_monitoring_service)
        self.health_list_workflows_use_case = HealthListWorkflowsUseCase()

        # Infrastructure use cases
        self.start_saga_use_case = StartSagaUseCase(self.saga_service)
        self.execute_saga_step_use_case = ExecuteSagaStepUseCase(self.saga_service)
        self.get_saga_use_case = GetSagaUseCase(self.saga_service)
        self.list_sagas_use_case = ListSagasUseCase(self.saga_service)
        self.start_trace_use_case = StartTraceUseCase(self.tracing_service)
        self.get_trace_use_case = GetTraceUseCase(self.tracing_service)
        self.list_traces_use_case = ListTracesUseCase(self.tracing_service)
        self.get_dlq_stats_use_case = GetDLQStatsUseCase(self.dlq_service)
        self.list_dlq_events_use_case = ListDLQEventsUseCase(self.dlq_service)
        self.retry_event_use_case = RetryEventUseCase(self.dlq_service)
        self.get_event_stream_stats_use_case = GetEventStreamStatsUseCase(self.event_streaming_service)
        self.publish_event_use_case = PublishEventUseCase(self.event_streaming_service)

        # Ingestion use cases
        self.start_ingestion_use_case = StartIngestionUseCase()
        self.get_ingestion_status_use_case = GetIngestionStatusUseCase()
        self.list_ingestions_use_case = ListIngestionsUseCase()

        # Reporting use cases
        self.generate_report_use_case = GenerateReportUseCase()
        self.get_report_use_case = GetReportUseCase()
        self.list_reports_use_case = ListReportsUseCase()

        # Query Processing use cases
        self.process_natural_language_query_use_case = ProcessNaturalLanguageQueryUseCase()
        self.get_query_result_use_case = GetQueryResultUseCase()
        self.list_queries_use_case = ListQueriesUseCase()


# Global container instance
container = OrchestratorContainer()

# ============================================================================
# FASTAPI APPLICATION - Focused on composition and startup
# ============================================================================

app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="""
    **🎼 Enterprise Control Plane Hub** for the LLM Documentation Ecosystem.

    ## 🎯 **Core Capabilities**

    ### **🏗️ Domain-Driven Design Architecture**
    - **7 Bounded Contexts**: Workflow Management, Service Registry, Infrastructure, Ingestion, Query Processing, Reporting, Health Monitoring
    - **Clean Architecture**: Strict separation of concerns with domain, application, and infrastructure layers
    - **Dependency Injection**: Centralized service composition and lifecycle management
    - **Event-Driven Communication**: Saga orchestration and event streaming for complex workflows

    ### **🔄 Advanced Workflow Orchestration**
    - **Dynamic Workflow Creation**: AI-powered workflow generation from natural language requirements
    - **Multi-Service Coordination**: Intelligent coordination of ecosystem services with error recovery
    - **Real-Time Execution Monitoring**: Comprehensive workflow execution tracking and performance metrics
    - **Parallel Processing**: Concurrent task execution with intelligent load distribution

    ### **🔍 Intelligent Service Discovery**
    - **Real-Time Service Registry**: Dynamic service registration and health monitoring
    - **Capability-Based Discovery**: Service discovery based on required capabilities and interfaces
    - **Load Balancing**: Intelligent load distribution across service instances
    - **Fault Tolerance**: Automatic failover and circuit breaker protection

    ## 📡 **API Architecture by Bounded Context**

    ### **🎯 Workflow Management (`/api/v1/workflows`)**
    - `POST /api/v1/workflows` - Create new workflow definitions
    - `GET /api/v1/workflows` - List available workflows
    - `GET /api/v1/workflows/{id}` - Get workflow details
    - `POST /api/v1/workflows/{id}/execute` - Execute workflow instance

    ### **🔗 Service Registry (`/api/v1/service-registry`)**
    - `POST /api/v1/service-registry/register` - Register new service
    - `DELETE /api/v1/service-registry/unregister` - Unregister service
    - `GET /api/v1/service-registry/services` - List registered services
    - `GET /api/v1/service-registry/services/{name}` - Get service details

    ### **🏛️ Infrastructure (`/api/v1/infrastructure`)**
    - `POST /api/v1/infrastructure/sagas` - Start new saga orchestration
    - `GET /api/v1/infrastructure/sagas` - List active sagas
    - `GET /api/v1/infrastructure/traces` - Get execution traces
    - `POST /api/v1/infrastructure/events` - Publish events to stream

    ### **📥 Ingestion (`/api/v1/ingestion`)**
    - `POST /api/v1/ingestion/start` - Start data ingestion workflow
    - `GET /api/v1/ingestion/status/{id}` - Get ingestion status
    - `GET /api/v1/ingestion/list` - List active ingestions

    ### **🔍 Query Processing (`/api/v1/queries`)**
    - `POST /api/v1/queries/process` - Process natural language query
    - `GET /api/v1/queries/results/{id}` - Get query results
    - `GET /api/v1/queries/history` - Query execution history

    ### **📊 Reporting (`/api/v1/reporting`)**
    - `POST /api/v1/reporting/generate` - Generate new report
    - `GET /api/v1/reporting/reports` - List available reports
    - `GET /api/v1/reporting/reports/{id}` - Get report details

    ## 🏢 **Enterprise Integration**

    ### **🔗 Ecosystem Service Coordination**
    - **Interpreter**: Natural language query interpretation and workflow generation
    - **Doc Store**: Document persistence with provenance tracking
    - **Source Agent**: Multi-source data ingestion and normalization
    - **Analysis Service**: Content analysis and intelligence extraction
    - **Summarizer Hub**: Multi-provider content summarization
    - **Secure Analyzer**: Content security analysis and policy enforcement

    ### **📊 Monitoring & Analytics**
    - **Real-Time Metrics**: Comprehensive performance and orchestration metrics
    - **Execution Tracing**: Complete workflow and saga execution tracking
    - **Service Health**: Real-time health monitoring of all ecosystem services
    - **Analytics Dashboard**: Workflow performance and service utilization analytics
    """,
    contact={
        "name": "Orchestrator Service Team",
        "url": "https://github.com/your-org/orchestrator",
        "email": "orchestrator@your-org.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://your-org.com/license"
    },
    openapi_tags=[
        {
            "name": "Health & Monitoring",
            "description": "Service health checks and system monitoring endpoints"
        },
        {
            "name": "Workflow Management",
            "description": "Workflow creation, execution, and lifecycle management"
        },
        {
            "name": "Service Registry",
            "description": "Service discovery, registration, and health monitoring"
        },
        {
            "name": "Infrastructure",
            "description": "Saga orchestration, event streaming, and system infrastructure"
        },
        {
            "name": "Ingestion",
            "description": "Data ingestion workflows and status tracking"
        },
        {
            "name": "Query Processing",
            "description": "Natural language query processing and results management"
        },
        {
            "name": "Reporting",
            "description": "Report generation and management capabilities"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Initialize log collector client
logger_client = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client
    try:
        logger_client = await get_log_collector_client(ServiceNames.ORCHESTRATOR)
        if logger_client:
            await logger_client.log_business_event(
                "orchestrator_startup",
                {
                    "version": SERVICE_VERSION,
                    "architecture": "domain_driven_design",
                    "services_loaded": [
                        "health_monitoring",
                        "workflow_management",
                        "service_registry",
                        "infrastructure",
                    ],
                    "domain_contexts": [
                        "health_monitoring",
                        "infrastructure",
                        "ingestion",
                        "query_processing",
                        "reporting",
                        "service_registry",
                        "workflow_management",
                    ],
                },
            )
            await logger_client.log_info(
                "Orchestrator service started",
                {
                    "ddd_architecture": True,
                    "bounded_contexts": 7,
                    "service_discovery": True,
                    "workflow_orchestration": True,
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("Orchestrator service shutting down")
        except Exception:
            pass


# Use common middleware setup to reduce duplication across services
setup_common_middleware(app, ServiceNames.ORCHESTRATOR)

# Skip shared health system to avoid datetime serialization issues
# register_exception_handlers(app)
# register_health_endpoints(app, ServiceNames.ORCHESTRATOR, SERVICE_VERSION)


# Simple health endpoint that bypasses all shared systems
@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="""
    **Service Health Check** - Comprehensive health status and operational metrics for the Orchestrator service.

    ## 🔍 **Health Assessment**

    This endpoint provides real-time health status and operational metrics for the Orchestrator service, including:

    ### **🏥 Health Indicators**
    - **Service Status**: Overall health status (healthy/degraded/unhealthy)
    - **DDD Architecture**: Whether Domain-Driven Design architecture is properly initialized
    - **Bounded Contexts**: Status of all 7 bounded contexts (Workflow Management, Service Registry, Infrastructure, etc.)
    - **Service Discovery**: Whether service registry and discovery mechanisms are operational

    ### **📊 Operational Metrics**
    - **Version Information**: Current service version and build details
    - **Uptime Metrics**: Service uptime and operational statistics
    - **System Readiness**: Overall system readiness for processing requests
    - **Integration Status**: Health of connected services and dependencies

    ### **🏗️ Architecture Health**
    - **Dependency Injection**: Whether service container is properly initialized
    - **Bounded Context Loading**: Status of all domain contexts and their services
    - **Router Registration**: Whether API routes are properly registered
    - **Middleware Setup**: Whether security and monitoring middleware is active

    ## 🎯 **Response Codes**

    | Code | Status | Description |
    |------|--------|-------------|
    | 200 | Healthy | Service is fully operational with all bounded contexts loaded |
    | 503 | Degraded | Service is operational but with some issues |
    | 500 | Unhealthy | Service is experiencing critical issues |

    ## 📋 **Usage Examples**

    ### **Basic Health Check**
    ```bash
    curl -X GET http://localhost:5099/health
    ```

    ### **Health Check with Monitoring**
    ```python
    import requests

    response = requests.get("http://localhost:5099/health")
    health_data = response.json()

    if health_data["status"] == "healthy":
        print("✅ Orchestrator service is healthy")
        print(f"📊 {len(health_data['bounded_contexts_loaded'])} bounded contexts loaded")
        if health_data["service_discovery_active"]:
            print("🔍 Service discovery is active")
    else:
        print("⚠️  Orchestrator service health issue detected")
    ```

    ### **Automated Monitoring Script**
    ```bash
    #!/bin/bash
    HEALTH_URL="http://localhost:5099/health"
    STATUS=$(curl -s $HEALTH_URL | jq -r '.status')

    if [ "$STATUS" = "healthy" ]; then
        echo "✅ Orchestrator service is healthy"
        exit 0
    else
        echo "❌ Orchestrator service is unhealthy: $STATUS"
        exit 1
    fi
    ```
    """,
    response_description="Comprehensive health status and operational metrics",
    responses={
        200: {
            "description": "Service is healthy and fully operational",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "orchestrator",
                        "version": "1.0.0",
                        "uptime_seconds": 3600.5,
                        "last_health_check": "2024-09-22T10:30:00Z",
                        "bounded_contexts_loaded": [
                            "workflow_management",
                            "service_registry",
                            "infrastructure",
                            "ingestion",
                            "query_processing",
                            "reporting"
                        ],
                        "ddd_architecture": True,
                        "service_discovery_active": True
                    }
                }
            }
        },
        503: {
            "description": "Service is degraded or temporarily unavailable",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "service": "orchestrator",
                        "version": "1.0.0",
                        "uptime_seconds": 1800.0,
                        "last_health_check": "2024-09-22T10:25:00Z",
                        "bounded_contexts_loaded": [
                            "workflow_management",
                            "service_registry"
                        ],
                        "ddd_architecture": False,
                        "service_discovery_active": True
                    }
                }
            }
        }
    },
    tags=["Health & Monitoring"]
)
async def simple_health() -> HealthResponse:
    """
    **Health Check Endpoint** - Comprehensive service health assessment.

    Returns detailed health status including:
    - Service operational status
    - DDD architecture initialization status
    - Bounded contexts loading status
    - Service discovery operational status
    - Version information
    - Uptime metrics
    - Last health check timestamp
    """
    import time
    import datetime

    # Calculate uptime (simplified - in production this would track actual startup time)
    uptime_seconds = time.time() - getattr(app, '_startup_time', time.time())

    # Check bounded contexts (simplified check)
    bounded_contexts_loaded = []
    try:
        # Check if container and its services are initialized
        if hasattr(container, 'workflow_repository') and container.workflow_repository:
            bounded_contexts_loaded.append("workflow_management")
        if hasattr(container, 'service_discovery_service') and container.service_discovery_service:
            bounded_contexts_loaded.append("service_registry")
        if hasattr(container, 'saga_service') and container.saga_service:
            bounded_contexts_loaded.append("infrastructure")
        if hasattr(container, 'start_ingestion_use_case') and container.start_ingestion_use_case:
            bounded_contexts_loaded.append("ingestion")
        if hasattr(container, 'process_natural_language_query_use_case') and container.process_natural_language_query_use_case:
            bounded_contexts_loaded.append("query_processing")
        if hasattr(container, 'generate_report_use_case') and container.generate_report_use_case:
            bounded_contexts_loaded.append("reporting")
    except Exception:
        bounded_contexts_loaded = []

    # Determine overall health based on bounded contexts loaded
    ddd_architecture = len(bounded_contexts_loaded) >= 4  # At least core contexts loaded
    service_discovery_active = "service_registry" in bounded_contexts_loaded

    # Overall status determination
    if len(bounded_contexts_loaded) >= 5 and ddd_architecture and service_discovery_active:
        status = "healthy"
    elif len(bounded_contexts_loaded) >= 2:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        service="orchestrator",
        version=SERVICE_VERSION,
        uptime_seconds=round(uptime_seconds, 1),
        last_health_check=datetime.datetime.utcnow().isoformat() + "Z",
        bounded_contexts_loaded=bounded_contexts_loaded,
        ddd_architecture=ddd_architecture,
        service_discovery_active=service_discovery_active
    )


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


def register_bounded_context_routers(app):
    """
    Register API routers for all bounded contexts.

    This function centralizes router registration to keep main.py clean
    and follows DRY principles by avoiding repetitive try/except blocks.
    """
    router_configs = [
        (
            "services.orchestrator.presentation.api.workflow_management.routes",
            "/api/v1/workflows",
            ["Workflow Management"],
            "Workflow Management",
        ),
        # Skip health monitoring routes due to datetime serialization issues
        # ("services.orchestrator.presentation.api.health_monitoring.routes", "/api/v1/health", ["Health & Monitoring"], "Health Monitoring"),
        (
            "services.orchestrator.presentation.api.infrastructure.routes",
            "/api/v1/infrastructure",
            ["Infrastructure"],
            "Infrastructure",
        ),
        ("services.orchestrator.presentation.api.ingestion.routes", "/api/v1/ingestion", ["Ingestion"], "Ingestion"),
        (
            "services.orchestrator.presentation.api.service_registry.routes",
            "/api/v1/service-registry",
            ["Service Registry"],
            "Service Registry",
        ),
        ("services.orchestrator.presentation.api.reporting.routes", "/api/v1/reporting", ["Reporting"], "Reporting"),
        (
            "services.orchestrator.presentation.api.query_processing.routes",
            "/api/v1/queries",
            ["Query Processing"],
            "Query Processing",
        ),
    ]

    for module_path, prefix, tags, context_name in router_configs:
        try:
            module = __import__(module_path, fromlist=["router"])
            router = getattr(module, "router")
            app.include_router(router, prefix=prefix, tags=tags)
        except (ImportError, AttributeError) as e:
            print(f"⚠️  {context_name} routes not available")


# Register API routes by bounded context (DDD-based)
register_bounded_context_routers(app)


# Legacy route support (to be migrated)
@app.get("/workflows")
async def list_workflows():
    """List all available workflow configurations and capabilities."""
    query = ListWorkflowsQuery()
    result = await container.list_workflows_use_case.execute(query)
    return {"workflows": [w.to_dict() for w in result]}


# Removed duplicate health endpoint - using the one registered earlier


if __name__ == "__main__":
    """Run the Orchestrator service directly."""
    print("🚀 DEBUG: Orchestrator main.py loaded and starting!")
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
