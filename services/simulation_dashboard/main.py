"""Simulation Dashboard - Main FastAPI Application."""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

from services.shared.infrastructure.config import load_service_config
from services.shared.utilities.resource_monitor import monitor_resources
from services.shared.presentation.api.responses import create_error_response
from services.shared.infrastructure.utilities.middleware import (
    RequestIdMiddleware,
    RequestMetricsMiddleware,
    RateLimitMiddleware
)

from services.simulation_dashboard.presentation.api import api_router

# Import DDD application layer
from services.simulation_dashboard.application import (
    CreateSimulationHandler,
    UpdateSimulationHandler,
    DeleteSimulationHandler,
    StartSimulationHandler,
    StopSimulationHandler,
)
from services.simulation_dashboard.application.simulation_queries import (
    ListSimulationsQueryHandler,
    GetSimulationQueryHandler,
    GetSimulationProgressQueryHandler,
)

# Import domain and infrastructure
from services.simulation_dashboard.domain.services.simulation_service import SimulationService
from services.simulation_dashboard.infrastructure.repositories.simulation_repository import SimulationRepository

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
try:
    config = load_service_config(service_name="simulation-dashboard")
    print("DEBUG: Config loaded successfully")
except Exception as e:
    print(f"DEBUG: Config loading failed: {e}")
    import sys
    sys.exit(1)

# Override config with environment variables if they exist
import os
if os.getenv('SERVER__PORT'):
    config.server.port = int(os.getenv('SERVER__PORT'))
if os.getenv('SERVER__HOST'):
    config.server.host = os.getenv('SERVER__HOST')

print(f"DEBUG: Final config server.port = {config.server.port}")
print(f"DEBUG: Final config server.host = {config.server.host}")

# Initialize dependencies (DDD pattern)
simulation_repository = SimulationRepository()
simulation_service = SimulationService(simulation_repository)

# Initialize application layer handlers
create_simulation_handler = CreateSimulationHandler(simulation_service, simulation_repository)
update_simulation_handler = UpdateSimulationHandler(simulation_service, simulation_repository)
delete_simulation_handler = DeleteSimulationHandler(simulation_repository)
start_simulation_handler = StartSimulationHandler(simulation_service, simulation_repository)
stop_simulation_handler = StopSimulationHandler(simulation_service, simulation_repository)

# Initialize query handlers
list_simulations_query = ListSimulationsQueryHandler(simulation_repository)
get_simulation_query = GetSimulationQueryHandler(simulation_repository)
get_simulation_progress_query = GetSimulationProgressQueryHandler(simulation_service, simulation_repository)

# Create FastAPI application
app = FastAPI(
    title="Simulation Dashboard API",
    description="""
    Enterprise Simulation Dashboard - AI-Powered Analytics Platform

    This API provides comprehensive simulation capabilities including:
    - Multi-scenario project simulations
    - Risk analysis and assessment
    - Resource optimization modeling
    - Budget planning and forecasting
    - Team performance optimization
    - Real-time AI insights and recommendations
    - Advanced analytics and reporting

    **Key Features:**
    - RESTful API design with comprehensive OpenAPI documentation
    - Real-time progress tracking and status updates
    - AI-powered insights and recommendations
    - Comprehensive audit logging and compliance
    - Scalable architecture with DDD patterns
    - Enterprise-grade security and monitoring

    **Architecture:**
    - Domain-Driven Design (DDD) with clear layer separation
    - CQRS pattern for optimal read/write operations
    - Dependency injection for testability and maintainability
    - Application layer orchestrates domain services
    - Clean separation between infrastructure and domain logic
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.security.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware (development - allow all hosts)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=['*']
)

# Add custom middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware)
app.add_middleware(RateLimitMiddleware)

# Make handlers available to routes via app state (DDD pattern)
app.state.create_simulation_handler = create_simulation_handler
app.state.update_simulation_handler = update_simulation_handler
app.state.delete_simulation_handler = delete_simulation_handler
app.state.start_simulation_handler = start_simulation_handler
app.state.stop_simulation_handler = stop_simulation_handler
app.state.list_simulations_query = list_simulations_query
app.state.get_simulation_query = get_simulation_query
app.state.get_simulation_progress_query = get_simulation_progress_query

# Include API routes
app.include_router(api_router)

# Health check endpoint
@app.get(
    "/health",
    summary="Health check endpoint",
    description="Returns the health status of the simulation dashboard service"
)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "simulation-dashboard",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# Readiness check endpoint
@app.get(
    "/ready",
    summary="Readiness check endpoint",
    description="Returns whether the service is ready to handle requests"
)
async def readiness_check():
    """Readiness check endpoint."""
    return {
        "status": "ready",
        "service": "simulation-dashboard",
        "timestamp": datetime.utcnow().isoformat()
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details=str(exc) if config.server.debug else None
        )
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Simulation Dashboard starting up...")

    # Start resource monitoring
    monitor_resources(config.service_name)

    logger.info("Simulation Dashboard startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Simulation Dashboard shutting down...")

    # Cleanup resources
    logger.info("Simulation Dashboard shutdown complete")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        reload=config.server.debug,
        log_level=config.logging.level.lower()
    )
