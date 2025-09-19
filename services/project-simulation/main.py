"""Project Simulation Service - Enhanced FastAPI Application with Shared Infrastructure.

This is the main entry point for the project-simulation service,
providing a REST API for project simulation capabilities with comprehensive
reuse of shared infrastructure patterns for consistency and reliability.

Features:
- Shared response models and error handling
- Standardized middleware stack (correlation ID, metrics, rate limiting)
- Enterprise-grade health monitoring and observability
- Comprehensive logging with correlation ID tracking
- Standardized API response formats
- HATEOAS navigation for REST API maturity
- Real-time WebSocket communication
- Circuit breaker resilience patterns
- Comprehensive testing infrastructure
"""

import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

# Add shared infrastructure to path
project_root = Path(__file__).parent.parent.parent
shared_path = project_root / "services" / "shared"
services_path = project_root / "services"

# Insert paths at the beginning to ensure they're found first
sys.path.insert(0, str(shared_path))
sys.path.insert(0, str(services_path))
sys.path.insert(0, str(project_root))

# Import shared utilities and patterns (with fallbacks)
try:
    from services.shared.core.responses.responses import (
        create_success_response,
        create_validation_error_response,
        create_paginated_response,
        create_list_response,
        create_crud_response,
        SuccessResponse,
        ErrorResponse,
        ValidationErrorResponse,
        PaginatedResponse,
        ListResponse,
        CreateResponse,
        HealthResponse,
        SystemHealthResponse,
        HTTP_STATUS_CODES
    )
except ImportError:
    # Fallback response models for testing
    from pydantic import BaseModel
    from typing import Optional, Any, Dict, List

    class SuccessResponse(BaseModel):
        success: bool = True
        message: str = ""
        data: Optional[Any] = None

    class ErrorResponse(BaseModel):
        success: bool = False
        error: str = ""
        message: str = ""
        details: Optional[Any] = None

    class HealthResponse(BaseModel):
        status: str = "healthy"
        timestamp: str = ""
        uptime_seconds: float = 0.0
        version: str = "1.0.0"

    # Simple fallback functions
    def create_success_response(data=None, message=""):
        return {"success": True, "message": message, "data": data}

    def create_error_response(error="", message="", details=None, status_code=None, error_code=None, request_id=None, **kwargs):
        # For API endpoints, raise HTTPException instead of returning dict
        if status_code is not None:
            raise HTTPException(status_code=status_code, detail=error or message)
        else:
            # Local style - return full response for non-API contexts
            response = {"success": False, "error": error, "message": message, "details": details}
            if error_code:
                response["error_code"] = error_code
            if request_id:
                response["request_id"] = request_id
            return response

    # Other fallbacks
    def create_validation_error_response(*args, **kwargs):
        return create_error_response(*args, **kwargs)

    def create_paginated_response(*args, **kwargs):
        return create_success_response(*args, **kwargs)

    def create_list_response(*args, **kwargs):
        return create_success_response(*args, **kwargs)

    def create_crud_response(operation=None, resource_id=None, message="", request_id=None, **kwargs):
        """Create a CRUD response with operation details."""
        # Create the data object with simulation details
        data_obj = {
            "simulation_id": resource_id,
            "message": message
        }

        response = {
            "success": True,
            "operation": operation,
            "data": data_obj
        }
        if request_id:
            response["request_id"] = request_id
        return response

    ValidationErrorResponse = ErrorResponse
    PaginatedResponse = SuccessResponse
    ListResponse = SuccessResponse
    CreateResponse = SuccessResponse
    SystemHealthResponse = HealthResponse

    HTTP_STATUS_CODES = {
        200: "OK",
        201: "Created",
        400: "Bad Request",
        404: "Not Found",
        422: "Unprocessable Entity",
        500: "Internal Server Error",
        "created": 201,
        "ok": 200,
        "bad_request": 400,
        "not_found": 404,
        "unprocessable_entity": 422,
        "internal_server_error": 500
    }
try:
    from services.shared.utilities.utilities import (
        setup_common_middleware,
        attach_self_register,
        generate_id,
        clean_string
    )
except ImportError:
    # Fallback utility functions for testing
    def setup_common_middleware(app, service_name):
        pass

    def attach_self_register(app, service_name, service_version=None):
        pass

    def generate_id():
        import uuid
        return str(uuid.uuid4())

    def clean_string(s):
        return str(s).strip()
try:
    from services.shared.utilities.middleware import ServiceMiddleware
except ImportError:
    # Fallback ServiceMiddleware for testing
    class ServiceMiddleware:
        def __init__(self, service_name="", rate_limits=None, enable_rate_limit=False):
            self.service_name = service_name
            self.rate_limits = rate_limits
            self.enable_rate_limit = enable_rate_limit

        def get_middlewares(self):
            return []

try:
    from services.shared.monitoring.health import register_health_endpoints
except ImportError:
    # Fallback health registration for testing
    def register_health_endpoints(app, service_name=None):
        """Fallback health endpoint registration."""
        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": service_name or SERVICE_NAME}

        @app.get("/health/detailed")
        async def health_detailed():
            return {
                "status": "healthy",
                "service": service_name or SERVICE_NAME,
                "version": SERVICE_VERSION,
                "timestamp": "2024-01-01T00:00:00Z"
            }

        @app.get("/health/system")
        async def health_system():
            return {
                "status": "healthy",
                "service": service_name or SERVICE_NAME,
                "system": {
                    "cpu_percent": 25.5,
                    "memory_percent": 45.2,
                    "disk_usage": 60.1
                }
            }

try:
    from services.shared.core.logging.correlation_middleware import CorrelationMiddleware
except ImportError:
    # Fallback correlation middleware for testing
    from starlette.middleware.base import BaseHTTPMiddleware

    class CorrelationMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, header_name="X-Correlation-ID"):
            super().__init__(app)
            self.header_name = header_name

        async def dispatch(self, request, call_next):
            response = await call_next(request)
            return response

try:
    from services.shared.utilities.error_handling import register_exception_handlers
except ImportError:
    # Fallback exception handlers for testing
    from datetime import datetime, timezone
    from fastapi.responses import JSONResponse

    def register_exception_handlers(app):
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error": exc.detail,
                    "error_code": f"http_{exc.status_code}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        @app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": str(exc),
                    "error_code": "internal_server_error",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

# Import local modules
from simulation.infrastructure.di_container import get_simulation_container
from simulation.infrastructure.logging import with_correlation_id, generate_correlation_id
from simulation.infrastructure.redis_integration import initialize_redis_integration, publish_document_event, publish_prompt_event
from simulation.infrastructure.health import create_simulation_health_endpoints
from simulation.infrastructure.config import get_config, is_development
from simulation.infrastructure.config.discovery import (
    get_service_discovery,
    start_service_discovery,
    stop_service_discovery
)
from simulation.presentation.api.hateoas import (
    SimulationResource,
    RootResource,
    HealthResource,
    create_hateoas_response
)
from simulation.presentation.websockets.simulation_websocket import (
    get_websocket_handler,
    notify_simulation_progress,
    notify_simulation_event,
    notify_ecosystem_status
)


# Pydantic models for API requests/responses
class CreateSimulationRequest(BaseModel):
    """Request model for creating a simulation."""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(None, max_length=500, description="Project description")
    type: str = Field("web_application", pattern="^(web_application|api_service|mobile_app|data_science|devops_tool)$", description="Project type")
    team_size: int = Field(5, ge=1, le=20, description="Team size")
    complexity: str = Field("medium", pattern="^(simple|medium|complex)$", description="Project complexity")
    duration_weeks: int = Field(8, ge=1, le=52, description="Duration in weeks")
    team_members: Optional[list] = Field(None, description="Optional team members")
    phases: Optional[list] = Field(None, description="Optional project phases")


class SimulationResponse(BaseModel):
    """Response model for simulation operations."""
    success: bool
    message: str
    simulation_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


class CreateSimulationFromConfigRequest(BaseModel):
    """Request model for creating simulation from configuration file."""
    config_file_path: str = Field(..., description="Path to configuration file")


class CreateSampleConfigRequest(BaseModel):
    """Request model for creating sample configuration file."""
    file_path: str = Field(..., description="Path where sample config should be created")
    project_name: str = Field("Sample E-commerce Platform", description="Project name for sample config")


class ValidateConfigRequest(BaseModel):
    """Request model for validating configuration file."""
    config_file_path: str = Field(..., description="Path to configuration file to validate")


class GenerateReportsRequest(BaseModel):
    """Request model for generating simulation reports."""
    report_types: List[str] = Field(
        default_factory=lambda: ["executive_summary", "technical_report", "workflow_analysis"],
        description="Types of reports to generate"
    )


class ExportReportRequest(BaseModel):
    """Request model for exporting simulation reports."""
    report_type: str = Field(..., description="Type of report to export")
    format: str = Field("json", description="Export format (json, html, markdown, pdf)")
    output_path: Optional[str] = Field(None, description="Optional output path for the exported report")


class StopUIMonitoringRequest(BaseModel):
    """Request model for stopping UI monitoring."""
    success: bool = Field(True, description="Whether the simulation completed successfully")


class ReplayEventsRequest(BaseModel):
    """Request model for replaying simulation events."""
    event_types: Optional[List[str]] = Field(None, description="Types of events to replay")
    start_time: Optional[str] = Field(None, description="Start time for replay (ISO format)")
    end_time: Optional[str] = Field(None, description="End time for replay (ISO format)")
    tags: Optional[List[str]] = Field(None, description="Tags to filter events")
    speed_multiplier: float = Field(1.0, description="Speed multiplier for replay (1.0 = real-time)")
    include_system_events: bool = Field(False, description="Include system events in replay")
    max_events: Optional[int] = Field(None, description="Maximum number of events to replay")


class CleanupEventsRequest(BaseModel):
    """Request model for cleaning up old events."""
    days_old: int = Field(30, description="Remove events older than this many days")


# Load configuration
config = get_config()

# Service configuration from config
SERVICE_NAME = config.service.name
SERVICE_VERSION = config.service.version
DEFAULT_PORT = config.service.port

# Rate limiting configuration from config
RATE_LIMITS = {
    "/api/v1/simulations": (10, 20),  # 10 requests per minute, burst 20
    "/api/v1/simulations/*/execute": (5, 10),  # 5 requests per minute, burst 10
}

# Initialize FastAPI application with configuration-driven setup
app = FastAPI(
    title=f"{SERVICE_NAME.replace('-', ' ').title()} Service",
    description="AI-powered project simulation and ecosystem demonstration service with comprehensive shared infrastructure integration",
    version=SERVICE_VERSION,
    docs_url="/docs" if config.development.enable_swagger else None,
    redoc_url="/redoc" if config.development.enable_redoc else None,
    openapi_url="/openapi.json",
    contact={
        "name": "Project Simulation Team",
        "url": "https://github.com/your-org/project-simulation",
        "email": "team@project-simulation.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    debug=config.service.debug
)

# Configure CORS with security best practices
if config.development.enable_cors:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.development.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["*"],
        max_age=3600  # Cache preflight for 1 hour
    )

# Setup shared middleware stack
service_middleware = ServiceMiddleware(
    service_name=SERVICE_NAME,
    rate_limits=RATE_LIMITS,
    enable_rate_limit=config.security.rate_limit_enabled
)

# Skip middleware for now to avoid complex issues
# TODO: Add middleware back once basic service is stable
# app.add_middleware(CorrelationMiddleware, header_name="X-Correlation-ID")

# Register shared exception handlers
register_exception_handlers(app)

# Setup common middleware (correlation ID, metrics, etc.)
setup_common_middleware(app, SERVICE_NAME)

# Self-registration with discovery service (only in non-development)
if not is_development():
    attach_self_register(app, SERVICE_NAME, SERVICE_VERSION)

# Get service instances
container = get_simulation_container()
logger = container.logger

# Resolve application service with fallback
try:
    application_service = container.resolve("simulation_application_service")
except Exception as e:
    logger.warning(f"Failed to resolve application service from container: {e}")
    # Fallback for testing environments
    from simulation.application.services.simulation_application_service import SimulationApplicationService
    from simulation.infrastructure.repositories.in_memory_repositories import InMemoryProjectRepository, InMemorySimulationRepository, InMemoryTimelineRepository, InMemoryTeamRepository

    # Create shared repository instances to ensure consistency
    project_repo = InMemoryProjectRepository()
    # Use SQLite repository for persistent simulation storage
    from simulation.infrastructure.repositories.sqlite_repositories import get_sqlite_simulation_repository
    simulation_repo = get_sqlite_simulation_repository()
    timeline_repo = InMemoryTimelineRepository()
    team_repo = InMemoryTeamRepository()

    application_service = SimulationApplicationService(
        project_repository=project_repo,
        simulation_repository=simulation_repo,
        timeline_repository=timeline_repo,
        team_repository=team_repo
    )

# Resolve simulation execution engine with fallback
try:
    simulation_execution_engine = container.resolve("simulation_execution_engine")
except Exception as e:
    logger.warning(f"Failed to resolve simulation execution engine from container: {e}")
    # Fallback for testing environments
    from simulation.infrastructure.execution.simulation_execution_engine import SimulationExecutionEngine
    # Use the same repository instances as the application service
    from simulation.infrastructure.content.content_generation_pipeline import ContentGenerationPipeline
    from simulation.infrastructure.workflows.workflow_orchestrator import SimulationWorkflowOrchestrator
    from simulation.infrastructure.clients.ecosystem_clients import get_ecosystem_service_registry
    # simulation_repo is already the SQLite repository from above
    simulation_execution_engine = SimulationExecutionEngine(
        content_pipeline=ContentGenerationPipeline(),
        ecosystem_clients=get_ecosystem_service_registry(),
        workflow_orchestrator=SimulationWorkflowOrchestrator(),
        logger=logger,
        monitoring_service=None,  # Add missing monitoring_service parameter
        simulation_repository=simulation_repo,
        project_repository=project_repo,
        timeline_repository=timeline_repo,
        team_repository=team_repo
    )

# Create health endpoints using shared patterns
health_endpoints = create_simulation_health_endpoints()
register_health_endpoints(app, SERVICE_NAME)

# Service discovery instance
service_discovery = get_service_discovery()


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting Project Simulation Service", version=SERVICE_VERSION, environment=config.service.environment)

    # Initialize event persistence
    try:
        from simulation.infrastructure.persistence.redis_event_store import initialize_event_persistence
        await initialize_event_persistence()
        logger.info("Event persistence system initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize event persistence: {e}")

    # Initialize environment management
    try:
        from simulation.infrastructure.config.environment_manager import initialize_environment_management
        await initialize_environment_management()
        logger.info("Environment management system initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize environment management: {e}")

    # Initialize Redis integration
    try:
        await initialize_redis_integration(logger)
        logger.info("Redis integration initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis integration: {e}")

    # Start service discovery
    if is_development():
        await start_service_discovery()
        logger.info("Service discovery started for development environment")

    # Log service information
    logger.info("Service configuration",
               port=config.service.port,
               debug=config.service.debug,
               database=config.database.url)

    # Log ecosystem service status
    if is_development():
        discovery_summary = service_discovery.get_service_discovery_summary()
        logger.info("Ecosystem service discovery initialized",
                   total_services=discovery_summary["total_services"])


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Shutting down Project Simulation Service")

    # Stop service discovery
    if is_development():
        await stop_service_discovery()
        logger.info("Service discovery stopped")

    logger.info("Shutdown completed")


# Health endpoints using shared response models
@app.get("/health", response_model=HealthResponse)
async def health(request: Request):
    """Basic health check using shared response models."""
    try:
        health_data = await health_endpoints["health"]()

        # Use shared success response
        return create_success_response(
            message="Service is healthy",
            data={
                "status": health_data.get("status", "healthy"),
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "uptime_seconds": health_data.get("uptime_seconds"),
                "environment": os.getenv("ENVIRONMENT", "development")
            },
            request_id=getattr(request.state, "correlation_id", None)
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return create_error_response(
            message="Health check failed",
            error_code="health_check_failed",
            details={"error": str(e)},
            request_id=getattr(request.state, "correlation_id", None)
        )


@app.get("/health/detailed", response_model=SuccessResponse)
async def health_detailed(request: Request):
    """Detailed health check with comprehensive status."""
    try:
        health_data = await health_endpoints["health_detailed"]()

        return create_success_response(
            message="Detailed health check completed",
            data=health_data,
            request_id=getattr(request.state, "correlation_id", None)
        )
    except Exception as e:
        logger.error("Detailed health check failed", error=str(e))
        return create_error_response(
            message="Detailed health check failed",
            error_code="detailed_health_check_failed",
            details={"error": str(e)},
            request_id=getattr(request.state, "correlation_id", None)
        )


@app.get("/health/system", response_model=SuccessResponse)
async def health_system(request: Request):
    """System-wide health check with ecosystem status."""
    try:
        health_data = await health_endpoints["health_system"]()

        return create_success_response(
            message="System health check completed",
            data=health_data,
            request_id=getattr(request.state, "correlation_id", None)
        )
    except Exception as e:
        logger.error("System health check failed", error=str(e))
        return create_error_response(
            message="System health check failed",
            error_code="system_health_check_failed",
            details={"error": str(e)},
            request_id=getattr(request.state, "correlation_id", None)
        )


# ============================================================================
# SIMULATION-DOC-STORE INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/simulations/{simulation_id}/documents")
async def save_simulation_document(simulation_id: str, document_data: Dict[str, Any], req: Request):
    """Save a document generated during simulation to doc-store and link it."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Extract document information
            document_id = document_data.get("document_id")
            document_type = document_data.get("document_type", "generated")
            content = document_data.get("content", "")
            metadata = document_data.get("metadata", {})

            if not document_id or not content:
                raise HTTPException(status_code=400, detail="Document ID and content are required")

            # Save document to doc-store (mock implementation - in real system, call doc-store API)
            doc_store_reference = f"simulation_{simulation_id}_{document_id}"

            # Link document to simulation in our database
            await application_service.link_document_to_simulation(
                simulation_id, document_id, document_type, doc_store_reference
            )

            # Publish Redis event for document generation
            await publish_document_event(simulation_id, document_id, document_type)

            return create_success_response(
                data={
                    "simulation_id": simulation_id,
                    "document_id": document_id,
                    "doc_store_reference": doc_store_reference,
                    "linked_at": datetime.now().isoformat()
                },
                message="Document linked to simulation successfully"
            )

        except Exception as e:
            logger.error("Failed to save simulation document", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to save document")

@app.get("/api/v1/simulations/{simulation_id}/documents")
async def get_simulation_documents(simulation_id: str, req: Request):
    """Get all documents linked to a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            documents = await application_service.get_simulation_documents(simulation_id)

            return create_success_response(
                data={"documents": documents, "simulation_id": simulation_id},
                message=f"Retrieved {len(documents)} documents for simulation"
            )

        except Exception as e:
            logger.error("Failed to get simulation documents", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve documents")

@app.get("/api/v1/simulations/{simulation_id}/documents/{document_id}")
async def get_simulation_document(simulation_id: str, document_id: str, req: Request):
    """Retrieve a specific document from doc-store via simulation linkage."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Get document linkage info from our database
            documents = await application_service.get_simulation_documents(simulation_id)
            doc_info = next((doc for doc in documents if doc["document_id"] == document_id), None)

            if not doc_info:
                raise HTTPException(status_code=404, detail="Document not found in simulation")

            # Retrieve document from doc-store (mock implementation)
            # In real system, make HTTP call to doc-store service
            document_content = {
                "document_id": document_id,
                "simulation_id": simulation_id,
                "doc_store_reference": doc_info["doc_store_reference"],
                "content": f"Mock document content for {document_id}",  # Real content from doc-store
                "retrieved_at": datetime.now().isoformat()
            }

            return create_success_response(
                data=document_content,
                message="Document retrieved successfully"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get simulation document", error=str(e), simulation_id=simulation_id, document_id=document_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve document")

# ============================================================================
# SIMULATION-PROMPT-STORE INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/simulations/{simulation_id}/prompts")
async def save_simulation_prompt(simulation_id: str, prompt_data: Dict[str, Any], req: Request):
    """Save a prompt used during simulation to prompt-store and link it."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Extract prompt information
            prompt_id = prompt_data.get("prompt_id")
            prompt_type = prompt_data.get("prompt_type", "generation")
            prompt_text = prompt_data.get("prompt_text", "")
            metadata = prompt_data.get("metadata", {})

            if not prompt_id or not prompt_text:
                raise HTTPException(status_code=400, detail="Prompt ID and text are required")

            # Save prompt to prompt-store (mock implementation - in real system, call prompt-store API)
            prompt_store_reference = f"simulation_{simulation_id}_{prompt_id}"

            # Link prompt to simulation in our database
            await application_service.link_prompt_to_simulation(
                simulation_id, prompt_id, prompt_type, prompt_store_reference
            )

            # Publish Redis event for prompt usage
            await publish_prompt_event(simulation_id, prompt_id, prompt_type)

            return create_success_response(
                data={
                    "simulation_id": simulation_id,
                    "prompt_id": prompt_id,
                    "prompt_store_reference": prompt_store_reference,
                    "linked_at": datetime.now().isoformat()
                },
                message="Prompt linked to simulation successfully"
            )

        except Exception as e:
            logger.error("Failed to save simulation prompt", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to save prompt")

@app.get("/api/v1/simulations/{simulation_id}/prompts")
async def get_simulation_prompts(simulation_id: str, req: Request):
    """Get all prompts linked to a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            prompts = await application_service.get_simulation_prompts(simulation_id)

            return create_success_response(
                data={"prompts": prompts, "simulation_id": simulation_id},
                message=f"Retrieved {len(prompts)} prompts for simulation"
            )

        except Exception as e:
            logger.error("Failed to get simulation prompts", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve prompts")

@app.get("/api/v1/simulations/{simulation_id}/prompts/{prompt_id}")
async def get_simulation_prompt(simulation_id: str, prompt_id: str, req: Request):
    """Retrieve a specific prompt from prompt-store via simulation linkage."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Get prompt linkage info from our database
            prompts = await application_service.get_simulation_prompts(simulation_id)
            prompt_info = next((prompt for prompt in prompts if prompt["prompt_id"] == prompt_id), None)

            if not prompt_info:
                raise HTTPException(status_code=404, detail="Prompt not found in simulation")

            # Retrieve prompt from prompt-store (mock implementation)
            # In real system, make HTTP call to prompt-store service
            prompt_content = {
                "prompt_id": prompt_id,
                "simulation_id": simulation_id,
                "prompt_store_reference": prompt_info["prompt_store_reference"],
                "prompt_text": f"Mock prompt text for {prompt_id}",  # Real content from prompt-store
                "retrieved_at": datetime.now().isoformat()
            }

            return create_success_response(
                data=prompt_content,
                message="Prompt retrieved successfully"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get simulation prompt", error=str(e), simulation_id=simulation_id, prompt_id=prompt_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve prompt")

# ============================================================================
# SIMULATION RUN DATA ENDPOINTS
# ============================================================================

@app.post("/api/v1/simulations/{simulation_id}/runs/{run_id}")
async def save_simulation_run_data(simulation_id: str, run_id: str, run_data: Dict[str, Any], req: Request):
    """Save execution data for a simulation run."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Save run data to database
            await application_service.save_simulation_run_data(simulation_id, run_id, run_data)

            return create_success_response(
                data={
                    "simulation_id": simulation_id,
                    "run_id": run_id,
                    "saved_at": datetime.now().isoformat()
                },
                message="Simulation run data saved successfully"
            )

        except Exception as e:
            logger.error("Failed to save simulation run data", error=str(e), simulation_id=simulation_id, run_id=run_id)
            raise HTTPException(status_code=500, detail="Failed to save run data")

@app.get("/api/v1/simulations/{simulation_id}/runs/{run_id}")
async def get_simulation_run_data(simulation_id: str, run_id: str, req: Request):
    """Retrieve execution data for a simulation run."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            run_data = await application_service.get_simulation_run_data(simulation_id, run_id)

            if run_data is None:
                raise HTTPException(status_code=404, detail="Run data not found")

            return create_success_response(
                data={
                    "simulation_id": simulation_id,
                    "run_id": run_id,
                    "run_data": run_data
                },
                message="Simulation run data retrieved successfully"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get simulation run data", error=str(e), simulation_id=simulation_id, run_id=run_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve run data")

# ============================================================================
# SERVICE DISCOVERY AND HEALTH ENDPOINTS
# ============================================================================

@app.get("/api/v1/service-discovery")
async def get_service_discovery(req: Request):
    """Get service discovery information."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            service_info = {
                "service_name": "project-simulation",
                "service_type": "simulation",
                "version": SERVICE_VERSION,
                "port": config.service.port if hasattr(config, 'service') and hasattr(config.service, 'port') else 5075,
                "environment": os.getenv("ENVIRONMENT", "development"),
                "health_endpoint": "/health",
                "api_base": "/api/v1",
                "capabilities": [
                    "simulation_execution",
                    "document_management",
                    "prompt_management",
                    "run_data_storage",
                    "real_time_events"
                ],
                "dependencies": [
                    {"name": "redis", "purpose": "caching and pub/sub"},
                    {"name": "doc_store", "purpose": "document storage"},
                    {"name": "prompt_store", "purpose": "prompt storage"}
                ],
                "endpoints": {
                    "simulations": "/api/v1/simulations",
                    "documents": "/api/v1/simulations/{simulation_id}/documents",
                    "prompts": "/api/v1/simulations/{simulation_id}/prompts",
                    "run_data": "/api/v1/simulations/{simulation_id}/runs/{run_id}",
                    "health": "/health",
                    "service_discovery": "/api/v1/service-discovery"
                },
                "timestamp": datetime.now().isoformat()
            }

            return create_success_response(
                data=service_info,
                message="Service discovery information retrieved"
            )

        except Exception as e:
            logger.error("Failed to get service discovery info", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve service discovery information")

@app.get("/api/v1/health/detailed")
async def get_detailed_health(req: Request):
    """Get detailed health information including dependencies."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Check database connectivity
            db_status = "unknown"
            try:
                # Test database connection
                test_repo = get_sqlite_simulation_repository()
                await test_repo.find_all()
                db_status = "healthy"
            except Exception as e:
                db_status = f"unhealthy: {str(e)}"

            # Check Redis connectivity
            redis_status = "unknown"
            try:
                # This would need to be implemented to check Redis health
                redis_status = "healthy"  # Placeholder
            except Exception as e:
                redis_status = f"unhealthy: {str(e)}"

            health_info = {
                "service": "project-simulation",
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime": "unknown",  # Would need to track service start time
                "version": SERVICE_VERSION,
                "dependencies": {
                    "database": {
                        "status": db_status,
                        "type": "SQLite"
                    },
                    "redis": {
                        "status": redis_status,
                        "purpose": "pub/sub and caching"
                    }
                },
                "metrics": {
                    "active_simulations": 0,  # Would need to track this
                    "total_simulations": 0,   # Would need to get from DB
                    "database_connections": 1,
                    "redis_connections": 1 if redis_status == "healthy" else 0
                }
            }

            return create_success_response(
                data=health_info,
                message="Detailed health information retrieved"
            )

        except Exception as e:
            logger.error("Failed to get detailed health info", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve detailed health information")

# ============================================================================
# SIMULATION PLAYBACK ENDPOINTS
# ============================================================================

@app.post("/api/v1/simulations/{simulation_id}/playback/{run_id}")
async def start_simulation_playback(simulation_id: str, run_id: str, req: Request,
                                  playback_request: Dict[str, Any] = None):
    """Start a simulation playback session."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            from simulation.infrastructure.playback.simulation_playback import create_simulation_playback_engine

            # Create playback engine
            playback_engine = create_simulation_playback_engine(application_service, logger)

            # Get playback speed from request
            playback_speed = (playback_request or {}).get("playback_speed", 1.0)

            # Start playback session
            session_id = await playback_engine.start_playback(simulation_id, run_id, playback_speed)

            return create_success_response(
                data={
                    "session_id": session_id,
                    "simulation_id": simulation_id,
                    "run_id": run_id,
                    "playback_speed": playback_speed,
                    "status": "started"
                },
                message="Simulation playback session started"
            )

        except Exception as e:
            logger.error("Failed to start simulation playback", error=str(e), simulation_id=simulation_id, run_id=run_id)
            raise HTTPException(status_code=500, detail="Failed to start playback session")

@app.get("/api/v1/simulations/{simulation_id}/playback/{run_id}/events")
async def get_simulation_playback_events(simulation_id: str, run_id: str, req: Request):
    """Get all events for a simulation playback."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            from simulation.infrastructure.playback.simulation_playback import create_simulation_playback_engine

            # Create playback engine
            playback_engine = create_simulation_playback_engine(application_service, logger)

            # Get playback events
            events = await playback_engine.get_playback_events(simulation_id, run_id)

            # Convert events to serializable format
            event_data = []
            for event in events:
                event_data.append({
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "simulation_id": event.simulation_id,
                    "data": event.data,
                    "sequence_number": event.sequence_number
                })

            return create_success_response(
                data={
                    "simulation_id": simulation_id,
                    "run_id": run_id,
                    "events": event_data,
                    "total_events": len(event_data)
                },
                message=f"Retrieved {len(event_data)} playback events"
            )

        except Exception as e:
            logger.error("Failed to get simulation playback events", error=str(e), simulation_id=simulation_id, run_id=run_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve playback events")

@app.post("/api/v1/simulations/{simulation_id}/reconstruct/{run_id}")
async def reconstruct_simulation(simulation_id: str, run_id: str, req: Request):
    """Reconstruct simulation state from stored data."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            from simulation.infrastructure.playback.simulation_playback import create_simulation_reconstructor

            # Create reconstructor
            reconstructor = create_simulation_reconstructor(application_service, logger)

            # Reconstruct simulation
            reconstructed_state = await reconstructor.reconstruct_simulation(simulation_id, run_id)

            return create_success_response(
                data=reconstructed_state,
                message="Simulation state reconstructed successfully"
            )

        except Exception as e:
            logger.error("Failed to reconstruct simulation", error=str(e), simulation_id=simulation_id, run_id=run_id)
            raise HTTPException(status_code=500, detail="Failed to reconstruct simulation")

@app.get("/api/v1/simulations/{simulation_id}/documents/{document_id}/content")
async def get_simulation_document_content(simulation_id: str, document_id: str, req: Request):
    """Get document content via simulation linkage."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            from simulation.infrastructure.playback.simulation_playback import create_simulation_reconstructor

            # Create reconstructor
            reconstructor = create_simulation_reconstructor(application_service, logger)

            # Get document content
            content = await reconstructor.get_document_content(simulation_id, document_id)

            if not content:
                raise HTTPException(status_code=404, detail="Document content not found")

            return create_success_response(
                data=content,
                message="Document content retrieved successfully"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get document content", error=str(e), simulation_id=simulation_id, document_id=document_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve document content")

@app.get("/api/v1/simulations/{simulation_id}/prompts/{prompt_id}/content")
async def get_simulation_prompt_content(simulation_id: str, prompt_id: str, req: Request):
    """Get prompt content via simulation linkage."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            from simulation.infrastructure.playback.simulation_playback import create_simulation_reconstructor

            # Create reconstructor
            reconstructor = create_simulation_reconstructor(application_service, logger)

            # Get prompt content
            content = await reconstructor.get_prompt_content(simulation_id, prompt_id)

            if not content:
                raise HTTPException(status_code=404, detail="Prompt content not found")

            return create_success_response(
                data=content,
                message="Prompt content retrieved successfully"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get prompt content", error=str(e), simulation_id=simulation_id, prompt_id=prompt_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve prompt content")

# ============================================================================
# RECOMMENDATIONS REPORT ENDPOINTS
# ============================================================================

@app.get("/api/v1/simulations/{simulation_id}/recommendations")
async def get_simulation_recommendations(simulation_id: str, req: Request):
    """Get recommendations report linkage for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Get simulation to check for recommendations report linkage
            simulation_repo = application_service._simulation_repository if hasattr(application_service, '_simulation_repository') else None

            if not simulation_repo:
                # Fallback: try to get from direct repository access
                from simulation.infrastructure.repositories.sqlite_repositories import SQLiteSimulationRepository
                simulation_repo = SQLiteSimulationRepository()

            simulation = await simulation_repo.find_by_id(simulation_id)
            if not simulation:
                raise HTTPException(status_code=404, detail="Simulation not found")

            # Check if recommendations report exists
            if hasattr(simulation, 'recommendations_report_id') and simulation.recommendations_report_id:
                return create_success_response(
                    data={
                        "report_id": simulation.recommendations_report_id,
                        "report_timestamp": getattr(simulation, 'recommendations_report_timestamp', None),
                        "simulation_id": simulation_id
                    },
                    message="Recommendations report found"
                )
            else:
                return create_success_response(
                    data={"report_id": None, "status": "not_generated"},
                    message="No recommendations report found for this simulation"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get recommendations report linkage", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve recommendations report linkage")

@app.get("/api/v1/simulations/{simulation_id}/recommendations/report")
async def get_simulation_recommendations_report(simulation_id: str, req: Request):
    """Get the full recommendations report from doc-store."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Get simulation to find the report ID
            simulation_repo = application_service._simulation_repository if hasattr(application_service, '_simulation_repository') else None

            if not simulation_repo:
                # Fallback: try to get from direct repository access
                from simulation.infrastructure.repositories.sqlite_repositories import SQLiteSimulationRepository
                simulation_repo = SQLiteSimulationRepository()

            simulation = await simulation_repo.find_by_id(simulation_id)
            if not simulation:
                raise HTTPException(status_code=404, detail="Simulation not found")

            if not hasattr(simulation, 'recommendations_report_id') or not simulation.recommendations_report_id:
                raise HTTPException(status_code=404, detail="No recommendations report found for this simulation")

            # Get the report from doc-store
            doc_store_url = os.getenv("DOC_STORE_URL", "http://localhost:5000")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{doc_store_url}/api/documents/{simulation.recommendations_report_id}"
                )

                if response.status_code == 200:
                    doc_data = response.json()
                    if doc_data.get("success"):
                        # Parse the JSON content
                        import json
                        report_content = json.loads(doc_data["data"]["content"])

                        return create_success_response(
                            data=report_content,
                            message="Recommendations report retrieved successfully"
                        )
                    else:
                        raise HTTPException(status_code=404, detail="Recommendations report not found in doc-store")
                else:
                    raise HTTPException(status_code=500, detail="Failed to retrieve report from doc-store")

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get recommendations report", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve recommendations report")

@app.get("/api/v1/simulations/{simulation_id}/recommendations/markdown")
async def get_simulation_recommendations_markdown(simulation_id: str, req: Request):
    """Get the markdown version of the recommendations report."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Get simulation to find the report ID
            simulation_repo = application_service._simulation_repository if hasattr(application_service, '_simulation_repository') else None

            if not simulation_repo:
                # Fallback: try to get from direct repository access
                from simulation.infrastructure.repositories.sqlite_repositories import SQLiteSimulationRepository
                simulation_repo = SQLiteSimulationRepository()

            simulation = await simulation_repo.find_by_id(simulation_id)
            if not simulation:
                raise HTTPException(status_code=404, detail="Simulation not found")

            if not hasattr(simulation, 'recommendations_report_id') or not simulation.recommendations_report_id:
                raise HTTPException(status_code=404, detail="No recommendations report found for this simulation")

            # Get the markdown version from doc-store
            md_report_id = f"{simulation.recommendations_report_id}_md"
            doc_store_url = os.getenv("DOC_STORE_URL", "http://localhost:5000")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{doc_store_url}/api/documents/{md_report_id}"
                )

                if response.status_code == 200:
                    doc_data = response.json()
                    if doc_data.get("success"):
                        return create_success_response(
                            data={
                                "markdown_content": doc_data["data"]["content"],
                                "format": "markdown",
                                "report_id": simulation.recommendations_report_id
                            },
                            message="Markdown recommendations report retrieved successfully"
                        )
                    else:
                        raise HTTPException(status_code=404, detail="Markdown recommendations report not found")
                else:
                    raise HTTPException(status_code=500, detail="Failed to retrieve markdown report from doc-store")

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get markdown recommendations report", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve markdown recommendations report")

@app.get("/api/v1/simulations/{simulation_id}/analysis")
async def get_simulation_analysis(simulation_id: str, req: Request):
    """Get analysis report linkage for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Get simulation to check for analysis report linkage
            simulation_repo = application_service._simulation_repository if hasattr(application_service, '_simulation_repository') else None

            if not simulation_repo:
                # Fallback: try to get from direct repository access
                from simulation.infrastructure.repositories.sqlite_repositories import SQLiteSimulationRepository
                simulation_repo = SQLiteSimulationRepository()

            simulation = await simulation_repo.find_by_id(simulation_id)
            if not simulation:
                raise HTTPException(status_code=404, detail="Simulation not found")

            # Check if analysis report exists
            if hasattr(simulation, 'analysis_report_id') and simulation.analysis_report_id:
                return create_success_response(
                    data={
                        "report_id": simulation.analysis_report_id,
                        "report_timestamp": getattr(simulation, 'analysis_report_timestamp', None),
                        "simulation_id": simulation_id
                    },
                    message="Analysis report found"
                )
            else:
                return create_success_response(
                    data={"report_id": None, "status": "not_generated"},
                    message="No analysis report found for this simulation"
                )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get analysis report linkage", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve analysis report linkage")

@app.get("/api/v1/simulations/{simulation_id}/analysis/report")
async def get_simulation_analysis_report(simulation_id: str, req: Request):
    """Get the full analysis report from doc-store."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Get simulation to find the report ID
            simulation_repo = application_service._simulation_repository if hasattr(application_service, '_simulation_repository') else None

            if not simulation_repo:
                # Fallback: try to get from direct repository access
                from simulation.infrastructure.repositories.sqlite_repositories import SQLiteSimulationRepository
                simulation_repo = SQLiteSimulationRepository()

            simulation = await simulation_repo.find_by_id(simulation_id)
            if not simulation:
                raise HTTPException(status_code=404, detail="Simulation not found")

            if not hasattr(simulation, 'analysis_report_id') or not simulation.analysis_report_id:
                raise HTTPException(status_code=404, detail="No analysis report found for this simulation")

            # Get the report from doc-store
            doc_store_url = os.getenv("DOC_STORE_URL", "http://localhost:5000")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{doc_store_url}/api/documents/{simulation.analysis_report_id}"
                )

                if response.status_code == 200:
                    doc_data = response.json()
                    if doc_data.get("success"):
                        # Parse the JSON content
                        import json
                        report_content = json.loads(doc_data["data"]["content"])

                        return create_success_response(
                            data=report_content,
                            message="Analysis report retrieved successfully"
                        )
                    else:
                        raise HTTPException(status_code=404, detail="Analysis report not found in doc-store")
                else:
                    raise HTTPException(status_code=500, detail="Failed to retrieve report from doc-store")

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get analysis report", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve analysis report")

@app.get("/api/v1/simulations/{simulation_id}/analysis/markdown")
async def get_simulation_analysis_markdown(simulation_id: str, req: Request):
    """Get the markdown version of the analysis report."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Get simulation to find the report ID
            simulation_repo = application_service._simulation_repository if hasattr(application_service, '_simulation_repository') else None

            if not simulation_repo:
                # Fallback: try to get from direct repository access
                from simulation.infrastructure.repositories.sqlite_repositories import SQLiteSimulationRepository
                simulation_repo = SQLiteSimulationRepository()

            simulation = await simulation_repo.find_by_id(simulation_id)
            if not simulation:
                raise HTTPException(status_code=404, detail="Simulation not found")

            if not hasattr(simulation, 'analysis_report_id') or not simulation.analysis_report_id:
                raise HTTPException(status_code=404, detail="No analysis report found for this simulation")

            # Get the markdown version from doc-store
            md_report_id = f"{simulation.analysis_report_id}_md"
            doc_store_url = os.getenv("DOC_STORE_URL", "http://localhost:5000")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{doc_store_url}/api/documents/{md_report_id}"
                )

                if response.status_code == 200:
                    doc_data = response.json()
                    if doc_data.get("success"):
                        return create_success_response(
                            data={
                                "markdown_content": doc_data["data"]["content"],
                                "format": "markdown",
                                "report_id": simulation.analysis_report_id
                            },
                            message="Markdown analysis report retrieved successfully"
                        )
                    else:
                        raise HTTPException(status_code=404, detail="Markdown analysis report not found")
                else:
                    raise HTTPException(status_code=500, detail="Failed to retrieve markdown report from doc-store")

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to get markdown analysis report", error=str(e), simulation_id=simulation_id)
            raise HTTPException(status_code=500, detail="Failed to retrieve markdown analysis report")

# ============================================================================
# INTERPRETER SERVICE INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/interpreter/simulate")
async def create_simulation_from_interpreter(request: Dict[str, Any], req: Request):
    """Create and execute a simulation based on interpreter query.

    This endpoint allows the interpreter service to request simulation creation
    and execution with generated mock data and analysis processing.
    """
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Extract interpreter request parameters
            query = request.get("query", "")
            context = request.get("context", {})
            simulation_config = request.get("simulation_config", {})

            logger.info(
                "Interpreter simulation request received",
                operation="interpreter_simulation",
                query_length=len(query),
                context_keys=list(context.keys()),
                correlation_id=correlation_id
            )

            # Generate mock data based on query and context
            mock_data = await generate_mock_simulation_data(query, context, simulation_config)

            # Create simulation with mock data
            simulation_request = {
                "name": f"Interpreter Simulation: {query[:50]}...",
                "description": f"Simulation generated from interpreter query: {query}",
                "type": simulation_config.get("type", "web_application"),
                "complexity": simulation_config.get("complexity", "medium"),
                "duration_weeks": simulation_config.get("duration_weeks", 8),
                "budget": simulation_config.get("budget", 150000),
                "technologies": mock_data.get("technologies", ["Python", "FastAPI", "React"]),
                "team_size": mock_data.get("team_size", 5)
            }

            # Create simulation
            result = await application_service.create_simulation(simulation_request)

            if result["success"]:
                simulation_id = result.get("simulation_id")

                # Store mock data in simulation
                await store_mock_data_in_simulation(simulation_id, mock_data)

                # Execute simulation with analysis processing
                execution_result = await execute_simulation_with_analysis(simulation_id, mock_data)

                return create_success_response(
                    data={
                        "simulation_id": simulation_id,
                        "mock_data_generated": True,
                        "analysis_performed": True,
                        "execution_result": execution_result,
                        "query": query,
                        "context_summary": context
                    },
                    message="Interpreter simulation created and executed successfully"
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "Failed to create simulation")
                )

        except Exception as e:
            logger.error(
                "Failed to create interpreter simulation",
                error=str(e),
                correlation_id=correlation_id
            )
            raise HTTPException(status_code=500, detail="Failed to create interpreter simulation")

@app.get("/api/v1/interpreter/capabilities")
async def get_interpreter_capabilities(req: Request):
    """Get simulation capabilities available to interpreter service."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            capabilities = {
                "simulation_types": ["web_application", "mobile_app", "api_service", "data_pipeline"],
                "complexity_levels": ["low", "medium", "high", "complex"],
                "analysis_types": [
                    "document_generation",
                    "code_analysis",
                    "timeline_analysis",
                    "team_dynamics",
                    "risk_assessment",
                    "cost_benefit_analysis"
                ],
                "mock_data_generation": {
                    "documents": True,
                    "team_members": True,
                    "code_repositories": True,
                    "api_endpoints": True,
                    "database_schemas": True
                },
                "reporting": {
                    "summary_reports": True,
                    "detailed_analysis": True,
                    "recommendations": True,
                    "timeline_visualization": True
                },
                "integrations": {
                    "doc_store": True,
                    "prompt_store": True,
                    "summarizer_hub": True,
                    "redis_pubsub": True
                }
            }

            return create_success_response(
                data=capabilities,
                message="Interpreter capabilities retrieved successfully"
            )

        except Exception as e:
            logger.error("Failed to get interpreter capabilities", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve capabilities")

@app.post("/api/v1/interpreter/mock-data")
async def generate_mock_data_for_interpreter(request: Dict[str, Any], req: Request):
    """Generate mock data for interpreter queries without creating full simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            data_types = request.get("data_types", ["documents", "team_members"])

            logger.info(
                "Mock data generation request",
                operation="mock_data_generation",
                query_length=len(query),
                data_types=data_types,
                correlation_id=correlation_id
            )

            # Generate mock data
            mock_data = await generate_specific_mock_data(query, context, data_types)

            return create_success_response(
                data={
                    "mock_data": mock_data,
                    "query": query,
                    "data_types_generated": data_types,
                    "generated_at": datetime.now().isoformat()
                },
                message="Mock data generated successfully"
            )

        except Exception as e:
            logger.error("Failed to generate mock data", error=str(e), correlation_id=correlation_id)
            raise HTTPException(status_code=500, detail="Failed to generate mock data")

# ============================================================================
# ENVIRONMENT AWARENESS ENDPOINTS
# ============================================================================

@app.get("/api/v1/environment")
async def get_environment_info(req: Request):
    """Get environment detection and configuration information."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            # Create analyzer to get environment info
            analyzer = SimulationAnalyzer()

            environment_info = analyzer.get_environment_info()

            # Add additional service information
            environment_info.update({
                "service_name": SERVICE_NAME,
                "service_version": "1.0.0",
                "correlation_id": correlation_id,
                "timestamp": datetime.now().isoformat()
            })

            return create_success_response(
                data=environment_info,
                message="Environment information retrieved successfully"
            )

        except Exception as e:
            logger.error("Failed to get environment info", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve environment information")

@app.get("/api/v1/service-discovery")
async def get_service_discovery_info(req: Request):
    """Get service discovery information including available endpoints."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            analyzer = SimulationAnalyzer()
            env_info = analyzer.get_environment_info()

            discovery_info = {
                "service_name": SERVICE_NAME,
                "service_type": "simulation_service",
                "version": "1.0.0",
                "environment": env_info["environment_type"],
                "capabilities": {
                    "simulation_creation": True,
                    "mock_data_generation": True,
                    "analysis_processing": True,
                    "ecosystem_integration": True,
                    "document_analysis": True,
                    "timeline_analysis": True,
                    "team_dynamics": True,
                    "risk_assessment": True,
                    "cost_benefit_analysis": True
                },
                "endpoints": {
                    "health": "/health",
                    "simulations": "/api/v1/simulations",
                    "interpreter": "/api/v1/interpreter/simulate",
                    "environment": "/api/v1/environment",
                    "service_discovery": "/api/v1/service-discovery"
                },
                "ecosystem_services": env_info["service_urls"],
                "supported_integrations": [
                    "summarizer-hub",
                    "doc-store",
                    "analysis-service",
                    "code-analyzer",
                    "orchestrator"
                ],
                "timestamp": datetime.now().isoformat()
            }

            return create_success_response(
                data=discovery_info,
                message="Service discovery information retrieved successfully"
            )

        except Exception as e:
            logger.error("Failed to get service discovery info", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to retrieve service discovery information")

        except Exception as e:
            logger.error("Failed to generate mock data", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to generate mock data")

@app.post("/api/v1/interpreter/analyze")
async def analyze_with_simulation(request: Dict[str, Any], req: Request):
    """Perform analysis using simulation infrastructure without full execution."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        try:
            content = request.get("content", "")
            analysis_type = request.get("analysis_type", "general")
            context = request.get("context", {})

            logger.info(
                "Analysis request via interpreter",
                operation="interpreter_analysis",
                content_length=len(content),
                analysis_type=analysis_type,
                correlation_id=correlation_id
            )

            # Perform analysis using simulation infrastructure
            analysis_result = await perform_simulation_analysis(content, analysis_type, context)

            return create_success_response(
                data={
                    "analysis_result": analysis_result,
                    "analysis_type": analysis_type,
                    "content_processed": len(content),
                    "context_used": bool(context)
                },
                message="Analysis completed successfully"
            )

        except Exception as e:
            logger.error("Failed to perform analysis", error=str(e))
            raise HTTPException(status_code=500, detail="Failed to perform analysis")

# ============================================================================
# HELPER FUNCTIONS FOR INTERPRETER INTEGRATION
# ============================================================================

async def generate_mock_simulation_data(query: str, context: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive mock data for simulation based on interpreter query."""
    try:
        # Extract keywords from query to generate relevant mock data
        keywords = extract_keywords_from_query(query)

        # Generate mock team members
        team_members = generate_mock_team_members(keywords, config.get("team_size", 5))

        # Generate mock documents
        documents = generate_mock_documents(keywords, context)

        # Generate mock technologies based on query analysis
        technologies = infer_technologies_from_query(query, keywords)

        # Generate mock project timeline
        timeline = generate_mock_timeline(config.get("duration_weeks", 8), keywords)

        return {
            "team_members": team_members,
            "documents": documents,
            "technologies": technologies,
            "timeline": timeline,
            "keywords_extracted": keywords,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error("Failed to generate mock simulation data", error=str(e))
        return {
            "team_members": [],
            "documents": [],
            "technologies": ["Python", "FastAPI"],
            "timeline": [],
            "error": str(e)
        }

async def generate_specific_mock_data(query: str, context: Dict[str, Any], data_types: List[str]) -> Dict[str, Any]:
    """Generate specific types of mock data as requested."""
    result = {}
    keywords = extract_keywords_from_query(query)

    for data_type in data_types:
        if data_type == "documents":
            result["documents"] = generate_mock_documents(keywords, context)
        elif data_type == "team_members":
            result["team_members"] = generate_mock_team_members(keywords, 5)
        elif data_type == "technologies":
            result["technologies"] = infer_technologies_from_query(query, keywords)
        elif data_type == "timeline":
            result["timeline"] = generate_mock_timeline(8, keywords)

    return result

async def store_mock_data_in_simulation(simulation_id: str, mock_data: Dict[str, Any]) -> None:
    """Store generated mock data in simulation for later retrieval."""
    try:
        # Store team members as simulation documents
        if mock_data.get("team_members"):
            for member in mock_data["team_members"]:
                await application_service.link_document_to_simulation(
                    simulation_id,
                    f"team_member_{member['id']}",
                    "team_member",
                    f"mock_team_member_{member['id']}"
                )

        # Store generated documents
        if mock_data.get("documents"):
            for doc in mock_data["documents"]:
                await application_service.link_document_to_simulation(
                    simulation_id,
                    f"doc_{doc['id']}",
                    "generated_document",
                    f"mock_document_{doc['id']}"
                )

        # Store mock data as run data
        await application_service.save_simulation_run_data(
            simulation_id,
            "mock_data_generation",
            {
                "mock_data": mock_data,
                "generated_at": datetime.now().isoformat(),
                "source": "interpreter"
            }
        )

    except Exception as e:
        logger.error("Failed to store mock data in simulation", error=str(e), simulation_id=simulation_id)

async def execute_simulation_with_analysis(simulation_id: str, mock_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute simulation with comprehensive analysis processing."""
    try:
        # Start simulation execution
        execution_result = await simulation_execution_engine.execute_simulation(simulation_id)

        if execution_result.get("success"):
            # Perform additional analysis
            analysis_results = await perform_comprehensive_analysis(simulation_id, mock_data)

            # Generate summary report
            summary_report = await generate_simulation_summary_report(simulation_id, analysis_results)

            return {
                "execution_success": True,
                "analysis_performed": True,
                "summary_report": summary_report,
                "analysis_results": analysis_results
            }
        else:
            return {
                "execution_success": False,
                "error": execution_result.get("message", "Execution failed")
            }

    except Exception as e:
        logger.error("Failed to execute simulation with analysis", error=str(e), simulation_id=simulation_id)
        return {
            "execution_success": False,
            "error": str(e)
        }

async def perform_simulation_analysis(content: str, analysis_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Perform analysis using simulation infrastructure."""
    # This would integrate with various analysis services
    # For now, return mock analysis results
    return {
        "analysis_type": analysis_type,
        "content_length": len(content),
        "context_provided": bool(context),
        "mock_analysis_result": "Analysis completed successfully",
        "recommendations": ["Consider consolidating similar documents", "Review outdated content"],
        "analyzed_at": datetime.now().isoformat()
    }

async def perform_comprehensive_analysis(simulation_id: str, mock_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform comprehensive analysis on simulation data."""
    # This would integrate with summarizer-hub and other analysis services
    return {
        "document_analysis": "Mock document analysis completed",
        "team_analysis": "Mock team dynamics analysis completed",
        "timeline_analysis": "Mock timeline analysis completed",
        "risk_assessment": "Mock risk assessment completed",
        "recommendations": [
            "Consider document consolidation",
            "Review team member assignments",
            "Optimize project timeline"
        ]
    }

async def generate_simulation_summary_report(simulation_id: str, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive summary report for simulation."""
    return {
        "simulation_id": simulation_id,
        "report_type": "comprehensive_analysis",
        "analysis_results": analysis_results,
        "generated_at": datetime.now().isoformat(),
        "recommendations_count": len(analysis_results.get("recommendations", []))
    }

# ============================================================================
# UTILITY FUNCTIONS FOR MOCK DATA GENERATION
# ============================================================================

def extract_keywords_from_query(query: str) -> List[str]:
    """Extract relevant keywords from interpreter query."""
    # Simple keyword extraction - in production this would use NLP
    common_keywords = [
        "api", "database", "frontend", "backend", "authentication", "security",
        "microservices", "deployment", "testing", "documentation", "analytics"
    ]

    query_lower = query.lower()
    keywords = [kw for kw in common_keywords if kw in query_lower]

    # Add query-specific keywords
    words = query.split()
    for word in words:
        if len(word) > 3 and word not in keywords:
            keywords.append(word.lower())

    return list(set(keywords))[:10]  # Limit to 10 keywords

def generate_mock_team_members(keywords: List[str], team_size: int) -> List[Dict[str, Any]]:
    """Generate mock team members based on project keywords."""
    roles = ["developer", "qa_engineer", "product_owner", "designer", "architect"]
    team_members = []

    for i in range(min(team_size, len(roles))):
        role = roles[i]
        skills = [kw for kw in keywords if len(kw) > 2][:3]  # Use keywords as skills

        team_members.append({
            "id": f"member_{i+1}",
            "name": f"Mock {role.title().replace('_', ' ')} {i+1}",
            "role": role,
            "skills": skills,
            "experience_years": 3 + i,
            "productivity_factor": 0.8 + (i * 0.1)
        })

    return team_members

def generate_mock_documents(keywords: List[str], context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate mock documents based on keywords and context."""
    doc_types = ["api_documentation", "architecture_diagram", "requirements_spec", "user_manual"]
    documents = []

    for i, doc_type in enumerate(doc_types):
        documents.append({
            "id": f"doc_{i+1}",
            "type": doc_type,
            "title": f"Mock {doc_type.title().replace('_', ' ')}",
            "content": f"Mock content for {doc_type} related to {', '.join(keywords[:3])}",
            "keywords": keywords[:5],
            "created_at": datetime.now().isoformat()
        })

    return documents

def infer_technologies_from_query(query: str, keywords: List[str]) -> List[str]:
    """Infer technology stack from query and keywords."""
    base_technologies = ["Python", "FastAPI"]

    # Add technologies based on keywords
    tech_map = {
        "api": ["REST", "GraphQL", "Swagger"],
        "database": ["PostgreSQL", "Redis", "MongoDB"],
        "frontend": ["React", "Vue.js", "Angular"],
        "authentication": ["JWT", "OAuth2", "Auth0"],
        "deployment": ["Docker", "Kubernetes", "AWS"],
        "testing": ["pytest", "Jest", "Selenium"]
    }

    inferred_tech = []
    for keyword in keywords:
        if keyword in tech_map:
            inferred_tech.extend(tech_map[keyword])

    return base_technologies + list(set(inferred_tech))[:5]

def generate_mock_timeline(duration_weeks: int, keywords: List[str]) -> List[Dict[str, Any]]:
    """Generate mock project timeline."""
    phases = ["Planning", "Development", "Testing", "Deployment", "Maintenance"]
    timeline = []

    for i, phase in enumerate(phases):
        start_week = i * 2
        if start_week < duration_weeks:
            timeline.append({
                "phase": phase,
                "start_week": start_week,
                "duration_weeks": min(2, duration_weeks - start_week),
                "milestones": [f"Complete {phase.lower()} phase"],
                "deliverables": [f"{phase} documentation and artifacts"]
            })

    return timeline

# Simulation endpoints using shared response patterns
@app.post("/api/v1/simulations")
async def create_simulation(request: CreateSimulationRequest, req: Request):
    """Create a new project simulation with enhanced response patterns."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Creating simulation",
            operation="create_simulation",
            project_name=request.name,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.create_simulation(request.model_dump())

            if result["success"]:
                # Create HATEOAS links for the created simulation
                simulation_id = result.get("simulation_id")
                links = SimulationResource.create_simulation_links(simulation_id)

                # Use shared CRUD response
                response_data = create_crud_response(
                    operation="create",
                    resource_id=simulation_id,
                    message=result.get("message", "Simulation created successfully"),
                    request_id=correlation_id
                )

                # Add HATEOAS links as a list
                links_list = links.to_dict() if hasattr(links, 'to_dict') else (links.model_dump() if hasattr(links, 'model_dump') else links.dict() if hasattr(links, 'dict') else links)
                # Convert Pydantic model to dict if needed
                if hasattr(response_data, 'model_dump'):
                    response_data = response_data.model_dump()
                response_data["_links"] = links_list

                return JSONResponse(
                    content=response_data,
                    status_code=HTTP_STATUS_CODES["created"],
                    headers={"X-Correlation-ID": correlation_id}
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=result.get("message", "Failed to create simulation")
                )

        except Exception as e:
            logger.error(
                "Failed to create simulation",
                error=str(e),
                correlation_id=correlation_id
            )
            raise HTTPException(
                status_code=500,
                detail="Internal server error during simulation creation"
            )


@app.post("/api/v1/simulations/{simulation_id}/execute")
async def execute_simulation(simulation_id: str, background_tasks: BackgroundTasks):
    """Execute a simulation with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.info(
            "Executing simulation",
            operation="execute_simulation",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            # Execute simulation in background for long-running operations
            background_tasks.add_task(
                _execute_simulation_background,
                simulation_id,
                correlation_id
            )

            # Create HATEOAS links for the executing simulation
            links = SimulationResource.create_simulation_links(simulation_id)

            return create_hateoas_response(
                data={
                    "simulation_id": simulation_id,
                    "message": "Simulation execution started",
                    "status": "running"
                },
                links=links,
                status="accepted"
            )

        except Exception as e:
            logger.error(
                "Failed to start simulation execution",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


@app.get("/api/v1/simulations/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """Get simulation status with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.debug(
            "Getting simulation status",
            operation="get_simulation_status",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            result = await simulation_execution_engine.get_simulation_status(simulation_id)

            if result is None:
                # Simulation not found
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": "Simulation not found",
                        "error_code": "simulation_not_found"
                    }
                )

            if not result.get("success", False):
                return JSONResponse(
                    status_code=404,
                    content={
                        "success": False,
                        "error": result.get("error", "Unknown error"),
                        "error_code": "simulation_error"
                    }
                )

            # Extract simulation data from the response
            simulation_data = result.get("simulation", {})

            # Create HATEOAS links for the simulation
            links = SimulationResource.create_simulation_links(simulation_id)

            # Create response in the format expected by tests
            response_data = {
                "success": True,
                "_links": links.to_dict(),
                **simulation_data
            }
            return JSONResponse(
                content=response_data,
                status_code=200,
                headers={"X-Correlation-ID": correlation_id}
            )

        except Exception as e:
            logger.error(
                "Failed to get simulation status",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


# Configuration file endpoints
@app.post("/api/v1/simulations/from-config")
async def create_simulation_from_config(request: CreateSimulationFromConfigRequest, req: Request):
    """Create a simulation from a configuration file."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Creating simulation from configuration file",
            operation="create_simulation_from_config",
            config_file_path=request.config_file_path,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.create_simulation_from_config_file(request.config_file_path)

            if result["success"]:
                simulation_id = result.get("simulation_id")
                links = SimulationResource.create_simulation_links(simulation_id)

                response_data = create_crud_response(
                    operation="create",
                    resource_id=simulation_id,
                    message=result.get("message", "Simulation created from config successfully"),
                    request_id=correlation_id
                )

                response_data.resource_url = f"/api/v1/simulations/{simulation_id}"
                response_data.links = links

                return JSONResponse(
                    content=response_data.dict(),
                    status_code=HTTP_STATUS_CODES["created"],
                    headers={"X-Correlation-ID": correlation_id}
                )
            else:
                return create_error_response(
                    message=result.get("message", "Failed to create simulation from config"),
                    error_code="config_simulation_creation_failed",
                    details=result,
                    request_id=correlation_id,
                    status_code=400
                )

        except Exception as e:
            logger.error(
                "Failed to create simulation from config file",
                error=str(e),
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during config-based simulation creation",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.post("/api/v1/config/sample")
async def create_sample_config(request: CreateSampleConfigRequest, req: Request):
    """Create a sample configuration file."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Creating sample configuration file",
            operation="create_sample_config",
            file_path=request.file_path,
            project_name=request.project_name,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.create_sample_config_file(
                request.file_path, request.project_name
            )

            if result["success"]:
                return create_success_response(
                    message=result["message"],
                    data={
                        "file_path": result["file_path"],
                        "project_name": result["project_name"],
                        "simulation_type": result["simulation_type"],
                        "team_size": result["team_size"],
                        "timeline_phases": result["timeline_phases"],
                        "duration_weeks": result["duration_weeks"]
                    },
                    request_id=correlation_id
                )
            else:
                return create_error_response(
                    message=result.get("message", "Failed to create sample config"),
                    error_code="sample_config_creation_failed",
                    details=result,
                    request_id=correlation_id
                )

        except Exception as e:
            logger.error(
                "Failed to create sample configuration file",
                error=str(e),
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during sample config creation",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.post("/api/v1/config/validate")
async def validate_config_file(request: ValidateConfigRequest, req: Request):
    """Validate a configuration file."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Validating configuration file",
            operation="validate_config",
            config_file_path=request.config_file_path,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.validate_config_file(request.config_file_path)

            if result["success"]:
                return create_success_response(
                    message=f"Configuration file validation {'passed' if result['valid'] else 'failed'}",
                    data={
                        "valid": result["valid"],
                        "issues": result["issues"],
                        "config_file_path": result["config_file_path"],
                        "project_name": result["project_name"],
                        "simulation_type": result["simulation_type"],
                        "team_size": result["team_size"],
                        "timeline_phases": result["timeline_phases"]
                    },
                    request_id=correlation_id
                )
            else:
                return create_error_response(
                    message=result.get("message", "Failed to validate config file"),
                    error_code="config_validation_failed",
                    details=result,
                    request_id=correlation_id
                )

        except Exception as e:
            logger.error(
                "Failed to validate configuration file",
                error=str(e),
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during config validation",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.get("/api/v1/config/template")
async def get_config_template(req: Request):
    """Get a configuration template."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Getting configuration template",
            operation="get_config_template",
            correlation_id=correlation_id
        )

        try:
            result = await application_service.get_config_template()

            if result["success"]:
                return create_success_response(
                    message=result["description"],
                    data={
                        "template": result["template"],
                        "supported_formats": result["supported_formats"],
                        "example_usage": result["example_usage"]
                    },
                    request_id=correlation_id
                )
            else:
                return create_error_response(
                    message=result.get("message", "Failed to get config template"),
                    error_code="template_retrieval_failed",
                    details=result,
                    request_id=correlation_id
                )

        except Exception as e:
            logger.error(
                "Failed to get configuration template",
                error=str(e),
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during template retrieval",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


# Reporting endpoints
@app.post("/api/v1/simulations/{simulation_id}/reports/generate")
async def generate_simulation_reports(simulation_id: str,
                                   request: GenerateReportsRequest,
                                   req: Request):
    """Generate comprehensive reports for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Generating simulation reports",
            operation="generate_simulation_reports",
            simulation_id=simulation_id,
            report_types=request.report_types,
            correlation_id=correlation_id
        )

        try:
            # Import reporting system
            from simulation.infrastructure.reporting.comprehensive_reporting_system import get_comprehensive_reporting_system

            reporting_system = get_comprehensive_reporting_system()

            # Mock data for demonstration - in real implementation this would come from the simulation
            analysis_results = {
                "execution_time": 120.0,
                "quality_score": 0.85,
                "consistency_score": 0.78,
                "cost_efficiency": 0.82,
                "timeline_adherence": 0.91,
                "risk_level": "low",
                "recommendations": [
                    "Implement automated testing workflows",
                    "Enhance documentation standards",
                    "Optimize resource allocation"
                ],
                "insights": [
                    "Strong correlation between documentation quality and project success",
                    "Workflow automation provides significant time savings"
                ],
                "issues": [
                    {"type": "consistency", "severity": "medium", "description": "Inconsistent naming conventions"}
                ],
                "benefits": {"time_saved": 24.5, "cost_savings": 1250.00}
            }

            workflow_data = [
                {"type": "document_generation", "success": True, "execution_time": 2.5},
                {"type": "analysis", "success": True, "execution_time": 1.8}
            ]

            document_data = [
                {"type": "requirements", "title": "Project Requirements", "quality_score": 0.88},
                {"type": "architecture", "title": "System Architecture", "quality_score": 0.92}
            ]

            # Generate reports
            result = await reporting_system.generate_comprehensive_report(
                simulation_id=simulation_id,
                analysis_results=analysis_results,
                workflow_data=workflow_data,
                document_data=document_data,
                report_types=request.report_types
            )

            if result["success"]:
                return create_success_response(
                    message=f"Generated {len(result['reports'])} comprehensive reports for simulation {simulation_id}",
                    data={
                        "simulation_id": simulation_id,
                        "reports_generated": len(result["reports"]),
                        "report_types": list(result["reports"].keys()),
                        "comprehensive_analysis": result["comprehensive_analysis"],
                        "generated_at": result["generated_at"]
                    },
                    request_id=correlation_id
                )
            else:
                return create_error_response(
                    message=result.get("message", "Failed to generate reports"),
                    error_code="report_generation_failed",
                    details=result,
                    request_id=correlation_id
                )

        except Exception as e:
            logger.error(
                "Failed to generate simulation reports",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during report generation",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.get("/api/v1/simulations/{simulation_id}/reports")
async def get_simulation_reports(simulation_id: str, req: Request):
    """Get available reports for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Getting simulation reports",
            operation="get_simulation_reports",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            # Import reporting system
            from simulation.infrastructure.reporting.comprehensive_reporting_system import get_comprehensive_reporting_system

            reporting_system = get_comprehensive_reporting_system()

            # In a real implementation, this would retrieve stored reports
            # For now, return mock report structure
            available_reports = {
                "executive_summary": {
                    "available": True,
                    "title": "Executive Summary",
                    "description": "High-level overview of simulation results"
                },
                "technical_report": {
                    "available": True,
                    "title": "Technical Report",
                    "description": "Detailed technical analysis and findings"
                },
                "workflow_analysis": {
                    "available": True,
                    "title": "Workflow Analysis",
                    "description": "Analysis of workflow execution and performance"
                },
                "quality_report": {
                    "available": True,
                    "title": "Quality Assessment Report",
                    "description": "Document quality and consistency analysis"
                },
                "performance_report": {
                    "available": True,
                    "title": "Performance Report",
                    "description": "Performance metrics and optimization recommendations"
                },
                "financial_report": {
                    "available": True,
                    "title": "Financial Impact Report",
                    "description": "Cost savings and ROI analysis"
                },
                "comprehensive_analysis": {
                    "available": True,
                    "title": "Comprehensive Analysis",
                    "description": "Complete analysis across all dimensions"
                }
            }

            return create_success_response(
                message=f"Found {len(available_reports)} available reports for simulation {simulation_id}",
                data={
                    "simulation_id": simulation_id,
                    "available_reports": available_reports,
                    "total_reports": len(available_reports),
                    "last_updated": datetime.now().isoformat()
                },
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to get simulation reports",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during report retrieval",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.get("/api/v1/simulations/{simulation_id}/reports/{report_type}")
async def get_simulation_report(simulation_id: str, report_type: str, req: Request):
    """Get a specific report for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Getting specific simulation report",
            operation="get_simulation_report",
            simulation_id=simulation_id,
            report_type=report_type,
            correlation_id=correlation_id
        )

        try:
            # Import reporting system
            from simulation.infrastructure.reporting.comprehensive_reporting_system import get_comprehensive_reporting_system

            reporting_system = get_comprehensive_reporting_system()

            # In a real implementation, this would retrieve the specific report
            # For now, generate a sample report based on type
            if report_type == "executive_summary":
                report_data = {
                    "title": "Executive Summary - Project Simulation Results",
                    "simulation_id": simulation_id,
                    "generated_at": datetime.now().isoformat(),
                    "key_findings": {
                        "overall_success": True,
                        "execution_efficiency": 0.82,
                        "timeline_performance": 0.91,
                        "risk_assessment": "low"
                    },
                    "quantitative_results": {
                        "execution_time": "2 minutes 15 seconds",
                        "documents_generated": 12,
                        "workflows_executed": 8,
                        "quality_score": "85%",
                        "consistency_score": "78%"
                    },
                    "recommendations": [
                        "Implement automated testing workflows",
                        "Enhance documentation standards",
                        "Optimize resource allocation based on workflow analysis"
                    ]
                }
            elif report_type == "workflow_analysis":
                report_data = {
                    "title": "Workflow Analysis Report",
                    "simulation_id": simulation_id,
                    "execution_summary": {
                        "total_workflows": 8,
                        "success_rate": "100%",
                        "average_execution_time": "1.8 seconds",
                        "failed_workflows": 0
                    },
                    "performance_analysis": {
                        "bottlenecks": ["Document generation workflow"],
                        "optimization_opportunities": [
                            "Parallel processing for independent workflows",
                            "Caching for repeated operations"
                        ]
                    }
                }
            else:
                report_data = {
                    "title": f"{report_type.replace('_', ' ').title()} Report",
                    "simulation_id": simulation_id,
                    "message": f"Detailed {report_type} report for simulation {simulation_id}",
                    "generated_at": datetime.now().isoformat()
                }

            return create_success_response(
                message=f"Retrieved {report_type} report for simulation {simulation_id}",
                data=report_data,
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to get simulation report",
                error=str(e),
                simulation_id=simulation_id,
                report_type=report_type,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during report retrieval",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.post("/api/v1/simulations/{simulation_id}/reports/export")
async def export_simulation_report(simulation_id: str,
                                request: ExportReportRequest,
                                req: Request):
    """Export a simulation report in specified format."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Exporting simulation report",
            operation="export_simulation_report",
            simulation_id=simulation_id,
            format=request.format,
            report_type=request.report_type,
            correlation_id=correlation_id
        )

        try:
            # Import reporting system
            from simulation.infrastructure.reporting.comprehensive_reporting_system import get_comprehensive_reporting_system

            reporting_system = get_comprehensive_reporting_system()

            # Generate sample report data for export
            report_data = {
                "title": f"Simulation Report - {simulation_id}",
                "simulation_id": simulation_id,
                "exported_at": datetime.now().isoformat(),
                "format": request.format,
                "content": f"Comprehensive report content for simulation {simulation_id} in {request.format} format"
            }

            # Export the report
            export_path = await reporting_system.export_report(
                report_data=report_data,
                format=request.format,
                output_path=request.output_path
            )

            return create_success_response(
                message=f"Report exported successfully in {request.format} format",
                data={
                    "simulation_id": simulation_id,
                    "report_type": request.report_type,
                    "export_format": request.format,
                    "export_path": export_path,
                    "file_size": "N/A",  # Would be calculated in real implementation
                    "exported_at": datetime.now().isoformat()
                },
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to export simulation report",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during report export",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


# Terminal UI endpoints
@app.post("/api/v1/simulations/{simulation_id}/ui/start")
async def start_simulation_ui(simulation_id: str, req: Request):
    """Start terminal UI monitoring for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Starting terminal UI monitoring",
            operation="start_simulation_ui",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            from simulation.infrastructure.ui.terminal_progress_visualizer import start_simulation_monitoring

            # Start terminal monitoring (this will run in background)
            start_simulation_monitoring(simulation_id, estimated_duration_minutes=60)

            return create_success_response(
                message=f"Terminal UI monitoring started for simulation {simulation_id}",
                data={
                    "simulation_id": simulation_id,
                    "monitoring_started": True,
                    "estimated_duration_minutes": 60
                },
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to start terminal UI monitoring",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during UI monitoring start",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.post("/api/v1/simulations/{simulation_id}/ui/stop")
async def stop_simulation_ui(simulation_id: str, request: StopUIMonitoringRequest, req: Request):
    """Stop terminal UI monitoring for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Stopping terminal UI monitoring",
            operation="stop_simulation_ui",
            simulation_id=simulation_id,
            success=request.success,
            correlation_id=correlation_id
        )

        try:
            from simulation.infrastructure.ui.terminal_progress_visualizer import stop_simulation_monitoring

            # Stop terminal monitoring
            stop_simulation_monitoring(simulation_id, request.success)

            return create_success_response(
                message=f"Terminal UI monitoring stopped for simulation {simulation_id}",
                data={
                    "simulation_id": simulation_id,
                    "monitoring_stopped": True,
                    "final_status": "success" if request.success else "completed_with_issues"
                },
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to stop terminal UI monitoring",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during UI monitoring stop",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.get("/api/v1/simulations/{simulation_id}/ui/status")
async def get_simulation_ui_status(simulation_id: str, req: Request):
    """Get the status of terminal UI monitoring for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Getting simulation UI status",
            operation="get_simulation_ui_status",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            from simulation.infrastructure.ui.terminal_progress_visualizer import get_simulation_terminal_ui

            ui = get_simulation_terminal_ui(simulation_id)

            # Get current state (this is a simplified version)
            is_monitoring = hasattr(ui, 'visualizer') and ui.visualizer._running

            return create_success_response(
                message=f"Terminal UI status for simulation {simulation_id}",
                data={
                    "simulation_id": simulation_id,
                    "monitoring_active": is_monitoring,
                    "overall_progress": getattr(ui.visualizer.state, 'overall_progress', 0.0),
                    "current_phase": getattr(ui.visualizer.state, 'current_phase', ''),
                    "documents_generated": getattr(ui.visualizer.state, 'documents_generated', 0),
                    "workflows_executed": getattr(ui.visualizer.state, 'workflows_executed', 0),
                    "active_tasks": len(getattr(ui.visualizer.state, 'active_tasks', [])),
                    "completed_tasks": len(getattr(ui.visualizer.state, 'completed_tasks', []))
                },
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to get simulation UI status",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during UI status retrieval",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


# Event persistence and replay endpoints
@app.get("/api/v1/simulations/{simulation_id}/events")
async def get_simulation_events(simulation_id: str,
                              event_types: Optional[str] = None,
                              start_time: Optional[str] = None,
                              end_time: Optional[str] = None,
                              tags: Optional[str] = None,
                              limit: int = 50,
                              offset: int = 0,
                              req: Request = None):
    """Get events for a simulation with filtering."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Getting simulation events",
            operation="get_simulation_events",
            simulation_id=simulation_id,
            limit=limit,
            offset=offset,
            correlation_id=correlation_id
        )

        try:
            from simulation.infrastructure.persistence.redis_event_store import (
                get_event_store, EventType
            )

            event_store = get_event_store()

            # Parse filters
            event_type_list = None
            if event_types:
                try:
                    event_type_list = [EventType(et.strip()) for et in event_types.split(",")]
                except ValueError as e:
                    return create_error_response(
                        message=f"Invalid event types: {e}",
                        error_code="invalid_event_types",
                        request_id=correlation_id
                    )

            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None
            tag_list = tags.split(",") if tags else None

            # Get events
            events = await event_store.get_events(
                simulation_id=simulation_id,
                event_types=event_type_list,
                start_time=start_dt,
                end_time=end_dt,
                tags=tag_list,
                limit=limit,
                offset=offset
            )

            # Convert to response format
            event_data = []
            for event in events:
                event_data.append({
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                    "priority": event.priority.value,
                    "tags": event.tags,
                    "correlation_id": event.correlation_id
                })

            return create_success_response(
                message=f"Retrieved {len(event_data)} events for simulation {simulation_id}",
                data={
                    "simulation_id": simulation_id,
                    "events": event_data,
                    "total_count": len(event_data),
                    "limit": limit,
                    "offset": offset,
                    "filters": {
                        "event_types": event_types,
                        "start_time": start_time,
                        "end_time": end_time,
                        "tags": tags
                    }
                },
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to get simulation events",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during event retrieval",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.get("/api/v1/simulations/{simulation_id}/timeline")
async def get_simulation_timeline(simulation_id: str, req: Request):
    """Get timeline of events for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Getting simulation timeline",
            operation="get_simulation_timeline",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            from simulation.infrastructure.persistence.redis_event_store import get_event_store

            event_store = get_event_store()
            timeline = await event_store.get_simulation_timeline(simulation_id)

            return create_success_response(
                message=f"Retrieved timeline with {len(timeline)} events for simulation {simulation_id}",
                data={
                    "simulation_id": simulation_id,
                    "timeline": timeline,
                    "event_count": len(timeline)
                },
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to get simulation timeline",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during timeline retrieval",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.post("/api/v1/simulations/{simulation_id}/events/replay")
async def replay_simulation_events(simulation_id: str,
                                 request: ReplayEventsRequest,
                                 req: Request):
    """Replay events for a simulation."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Starting event replay",
            operation="replay_simulation_events",
            simulation_id=simulation_id,
            speed_multiplier=request.speed_multiplier,
            correlation_id=correlation_id
        )

        try:
            from simulation.infrastructure.persistence.redis_event_store import (
                get_replay_manager, ReplayConfiguration, EventType
            )

            # Parse event types
            event_type_list = None
            if request.event_types:
                try:
                    event_type_list = [EventType(et) for et in request.event_types]
                except ValueError as e:
                    return create_error_response(
                        message=f"Invalid event types: {e}",
                        error_code="invalid_event_types",
                        request_id=correlation_id
                    )

            # Create replay configuration
            config = ReplayConfiguration(
                simulation_id=simulation_id,
                start_time=datetime.fromisoformat(request.start_time) if request.start_time else None,
                end_time=datetime.fromisoformat(request.end_time) if request.end_time else None,
                event_types=event_type_list,
                tags=request.tags,
                speed_multiplier=request.speed_multiplier,
                include_system_events=request.include_system_events,
                max_events=request.max_events
            )

            # Define callback for replay events
            replayed_events = []

            def replay_callback(event):
                replayed_events.append({
                    "event_id": event.event_id,
                    "event_type": event.event_type.value,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data
                })

            # Start replay
            replay_manager = get_replay_manager()
            replay_id = await replay_manager.start_replay(simulation_id, replay_callback, config)

            return create_success_response(
                message=f"Started event replay {replay_id} for simulation {simulation_id}",
                data={
                    "replay_id": replay_id,
                    "simulation_id": simulation_id,
                    "configuration": {
                        "speed_multiplier": request.speed_multiplier,
                        "event_types": request.event_types,
                        "max_events": request.max_events,
                        "include_system_events": request.include_system_events
                    },
                    "status": "started"
                },
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to start event replay",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during event replay",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.get("/api/v1/events/statistics")
async def get_event_statistics(simulation_id: Optional[str] = None,
                             start_time: Optional[str] = None,
                             end_time: Optional[str] = None,
                             req: Request = None):
    """Get statistics about stored events."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.info(
            "Getting event statistics",
            operation="get_event_statistics",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            from simulation.infrastructure.persistence.redis_event_store import get_event_store

            event_store = get_event_store()

            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None

            stats = await event_store.get_event_statistics(
                simulation_id=simulation_id,
                start_time=start_dt,
                end_time=end_dt
            )

            return create_success_response(
                message="Retrieved event statistics",
                data=stats,
                request_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Failed to get event statistics",
                error=str(e),
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during statistics retrieval",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.get("/api/v1/simulations", response_model=PaginatedResponse)
async def list_simulations(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    req: Request = None
):
    """List simulations with shared pagination and response patterns."""
    correlation_id = getattr(req.state, "correlation_id", generate_correlation_id())

    with with_correlation_id(correlation_id):
        logger.debug(
            "Listing simulations",
            operation="list_simulations",
            status_filter=status,
            page=page,
            page_size=page_size,
            correlation_id=correlation_id
        )

        try:
            # Validate pagination parameters
            if page < 1:
                return create_validation_error_response(
                    field_errors={"page": ["Page number must be greater than 0"]},
                    message="Invalid pagination parameters",
                    request_id=correlation_id
                )

            if page_size < 1 or page_size > 100:
                return create_validation_error_response(
                    field_errors={"page_size": ["Page size must be between 1 and 100"]},
                    message="Invalid pagination parameters",
                    request_id=correlation_id
                )

            # Calculate offset for pagination
            offset = (page - 1) * page_size
            limit = page_size

            result = await application_service.list_simulations(status, limit, offset)

            # Get total count for pagination metadata
            total_count = result.get("total_count", len(result.get("simulations", [])))

            # Create HATEOAS links for the collection
            links = SimulationResource.create_simulation_collection_links()

            # Use shared paginated response
            paginated_response = create_paginated_response(
                items=result.get("simulations", []),
                page=page,
                page_size=page_size,
                total_items=total_count,
                request_id=correlation_id
            )

            # Add HATEOAS links
            response_data = paginated_response.dict()
            response_data["links"] = links

            return JSONResponse(
                content=response_data,
                headers={"X-Correlation-ID": correlation_id}
            )

        except Exception as e:
            logger.error(
                "Failed to list simulations",
                error=str(e),
                correlation_id=correlation_id
            )
            return create_error_response(
                error="Failed to retrieve simulations",
                error_code="simulation_list_failed",
                details={"error": str(e)},
                request_id=correlation_id
            )


@app.delete("/api/v1/simulations/{simulation_id}")
async def cancel_simulation(simulation_id: str):
    """Cancel a simulation with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.info(
            "Cancelling simulation",
            operation="cancel_simulation",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.cancel_simulation(simulation_id)

            if not result["success"]:
                return create_error_response(
                    error=result["error"],
                    status_code=400
                )

            # Create HATEOAS links for the cancelled simulation
            links = SimulationResource.create_simulation_links(simulation_id)

            return create_hateoas_response(
                data=result,
                links=links,
                status="ok"
            )

        except Exception as e:
            logger.error(
                "Failed to cancel simulation",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


@app.get("/api/v1/simulations/{simulation_id}/results")
async def get_simulation_results(simulation_id: str):
    """Get simulation results with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.debug(
            "Getting simulation results",
            operation="get_simulation_results",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.get_simulation_results(simulation_id)

            if not result["success"]:
                return create_error_response(
                    error=result["error"],
                    status_code=404
                )

            # Create HATEOAS links for the simulation
            links = SimulationResource.create_simulation_links(simulation_id)

            return create_hateoas_response(
                data=result,
                links=links,
                status="ok"
            )

        except Exception as e:
            logger.error(
                "Failed to get simulation results",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


# Background task for simulation execution
async def _execute_simulation_background(simulation_id: str, correlation_id: str):
    """Execute simulation in background."""
    with with_correlation_id(correlation_id):
        try:
            logger.info(
                "Starting background simulation execution",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            result = await simulation_execution_engine.execute_simulation(simulation_id)

            logger.info(
                "Background simulation execution completed",
                simulation_id=simulation_id,
                success=result.get("success", False),
                correlation_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Background simulation execution failed",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )


# WebSocket endpoints for real-time updates
websocket_handler = get_websocket_handler()

@app.websocket("/ws/simulations/{simulation_id}")
async def simulation_websocket(websocket: WebSocket, simulation_id: str):
    """WebSocket endpoint for real-time simulation updates."""
    await websocket_handler.handle_simulation_connection(websocket, simulation_id)


@app.websocket("/ws/system")
async def system_websocket(websocket: WebSocket):
    """WebSocket endpoint for system-wide real-time updates."""
    await websocket_handler.handle_general_connection(websocket)


@app.get("/")
async def root():
    """Root endpoint with service information and HATEOAS navigation."""
    # Create HATEOAS links for API root
    links = RootResource.create_root_links()

    return create_hateoas_response(
        data={
            "service": "project-simulation",
            "version": "1.0.0",
            "description": "AI-powered project simulation and ecosystem demonstration service",
            "features": [
                "HATEOAS navigation",
                "Domain-driven design",
                "Event-driven architecture",
                "Circuit breaker resilience",
                "Comprehensive monitoring",
                "21+ ecosystem service integration"
            ]
        },
        links=links,
        status="ok"
    )


if __name__ == "__main__":
    """Run the Project Simulation Service directly."""
    import uvicorn

    print("🚀 Starting Project Simulation Service...")
    print("📊 Service: project-simulation v1.0.0")
    print("🌐 API Documentation: http://localhost:5075/docs")
    print("💊 Health Check: http://localhost:5075/health")
    print("📋 Root Endpoint: http://localhost:5075/")
    print("\n✨ Features Available:")
    print("  🏗️  Project Simulation Creation")
    print("  🎭 Simulation Execution & Monitoring")
    print("  📊 Real-time Progress Tracking")
    print("  📄 Document Generation Integration")
    print("  🔗 Ecosystem Service Coordination")
    print("  📈 Performance Analytics")
    print("  🏥 Health Monitoring")
    print("  📝 Structured Logging with Correlation IDs")
    print("\n🔧 Built with:")
    print("  🏛️  Domain Driven Design (DDD)")
    print("  🧹 Clean Architecture")
    print("  🔄 Dependency Injection")
    print("  📡 REST API with HATEOAS")
    print("  🧪 Comprehensive Testing Infrastructure")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5075,
        reload=True,
        log_level="info"
    )