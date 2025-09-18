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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

# Add shared infrastructure to path
sys.path.append(str(Path(__file__).parent.parent / "services" / "shared"))

# Import shared utilities and patterns
from services.shared.core.responses.responses import (
    create_success_response,
    create_error_response,
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
from services.shared.utilities.utilities import (
    setup_common_middleware,
    attach_self_register,
    generate_id,
    clean_string
)
from services.shared.utilities.middleware import ServiceMiddleware
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.logging.correlation_middleware import CorrelationIdMiddleware
from services.shared.utilities.error_handling import register_exception_handlers

# Import local modules
from simulation.infrastructure.di_container import get_simulation_container
from simulation.infrastructure.logging import with_correlation_id, generate_correlation_id
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
    create_hateoas_response,
    create_error_response
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
    name: str
    description: Optional[str] = None
    type: str = "web_application"
    team_size: int = 5
    complexity: str = "medium"
    duration_weeks: int = 8
    team_members: Optional[list] = None
    phases: Optional[list] = None


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

# Apply shared middleware
for middleware_factory in service_middleware.get_middlewares():
    app.middleware("http")(middleware_factory)

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
application_service = container.get_service("simulation_application_service")
simulation_execution_engine = container.get_service("simulation_execution_engine")

# Create health endpoints using shared patterns
health_endpoints = create_simulation_health_endpoints()
register_health_endpoints(app, SERVICE_NAME, SERVICE_VERSION)

# Service discovery instance
service_discovery = get_service_discovery()


@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Starting Project Simulation Service", version=SERVICE_VERSION, environment=config.service.environment)

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


# Simulation endpoints using shared response patterns
@app.post("/api/v1/simulations", response_model=CreateResponse)
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
            # Validate input using shared utilities
            if not request.name or not clean_string(request.name):
                return create_validation_error_response(
                    field_errors={"name": ["Project name cannot be empty"]},
                    message="Invalid project name provided",
                    request_id=correlation_id
                )

            result = await application_service.create_simulation(request.dict())

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

                # Add HATEOAS links
                response_data.resource_url = f"/api/v1/simulations/{simulation_id}"
                response_data.links = links

                return JSONResponse(
                    content=response_data.dict(),
                    status_code=HTTP_STATUS_CODES["created"],
                    headers={"X-Correlation-ID": correlation_id}
                )
            else:
                return create_error_response(
                    message=result.get("message", "Failed to create simulation"),
                    error_code="simulation_creation_failed",
                    details=result,
                    request_id=correlation_id
                )

        except Exception as e:
            logger.error(
                "Failed to create simulation",
                error=str(e),
                correlation_id=correlation_id
            )
            return create_error_response(
                message="Internal server error during simulation creation",
                error_code="internal_server_error",
                details={"error": str(e)},
                request_id=correlation_id
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
                message="Failed to retrieve simulations",
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