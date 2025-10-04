"""
Project Planning Service - Feature Development Roadmap Planning
=================================================================

Central orchestration service for comprehensive feature development planning,
providing AI-powered roadmap creation, team capacity management, and
enterprise tool integration.

Endpoints:
- POST /api/v1/planning/analyze: Analyze feature description with AI
- POST /api/v1/planning/decompose: Decompose feature into tasks
- GET /api/v1/planning/features: List features with filtering
- GET /api/v1/planning/features/{id}: Get feature details
- GET /api/v1/planning/tasks: List tasks with filtering
- GET /health: Service health check

Responsibilities:
- Intelligent feature decomposition and analysis
- Team capacity and skills management
- Timeline estimation and risk assessment
- Enterprise tool integration (Jira, Linear, Asana)
- Real-time roadmap planning and optimization
- Stakeholder communication and reporting

Dependencies: shared infrastructure, LLM Gateway, Source Agent, User Store, Interpreter
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI
from typing import Optional
from contextlib import asynccontextmanager

# Add parent directory to path for proper imports
parent_dir = str(Path(__file__).parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Shared utilities
from services.shared.infrastructure.monitoring.health import register_health_endpoints
from services.shared.infrastructure.utilities.error_handling import register_exception_handlers
from services.shared.core.constants_new import ServiceNames
from services.shared.infrastructure.utilities.utilities import setup_common_middleware
from services.shared.infrastructure.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware

# Import database initialization
from services.project_planning_service.infrastructure.database import init_database

# Import API routes
from services.project_planning_service.presentation.api.routes import planning
from services.project_planning_service.api import roadmap_routes

# Import log client
from services.project_planning_service.infrastructure.integrations.log_collector_client import get_log_client

# Service configuration constants
SERVICE_NAME = "project-planning-service"
SERVICE_VERSION = "1.0.0"
DEFAULT_API_PORT = int(os.environ.get("SERVICE_API_PORT", "5170"))


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    log_client = get_log_client()
    
    try:
        # Initialize database
        init_database()
        print(f"✅ Database initialized successfully")
        
        await log_client.log_info(
            f"{SERVICE_NAME} starting up",
            context={"version": SERVICE_VERSION, "port": DEFAULT_API_PORT}
        )
        
        print(f"✅ {SERVICE_NAME} v{SERVICE_VERSION} started successfully")
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        await log_client.log_error(
            f"Service startup failed: {str(e)}",
            context={"service": SERVICE_NAME, "error": str(e)}
        )
        raise
    
    yield
    
    # Shutdown
    await log_client.log_info(
        f"{SERVICE_NAME} shutting down",
        context={"version": SERVICE_VERSION}
    )
    print(f"✅ {SERVICE_NAME} shutdown complete")


# ============================================================================
# APPLICATION SETUP
# ============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="Project Planning Service",
    version=SERVICE_VERSION,
    description="AI-powered feature development roadmap planning and team orchestration",
    lifespan=lifespan
)

# Setup middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)

# Register health endpoints
register_health_endpoints(app, SERVICE_NAME, SERVICE_VERSION)

# Register exception handlers
register_exception_handlers(app)

# Setup common middleware
setup_common_middleware(app, SERVICE_NAME)

# ============================================================================
# DATASTORE OPERATION LOGGING
# ============================================================================
try:
    from services.shared.infrastructure.logging.datastore_operation_logger import add_datastore_logging
    
    add_datastore_logging(
        app,
        service_name="project-planning-service",
        log_collector_url="http://localhost:8104",
        timeout_seconds=1.0
    )
except ImportError as e:
    logger.warning(f"DataStore operation logging not available: {e}")

# Include API routers
app.include_router(planning.router)
app.include_router(roadmap_routes.router, prefix="/api/v1")


# ============================================================================
# ROOT ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": "operational",
        "description": "AI-powered feature development roadmap planning",
        "documentation": "/docs",
        "health": "/health"
    }


@app.get("/api/v1/info")
async def service_info():
    """Service information endpoint."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "message": "Project Planning Service operational"
    }


if __name__ == "__main__":
    """Run the Project Planning Service directly."""
    import uvicorn
    import atexit

    print(f"Starting {SERVICE_NAME} v{SERVICE_VERSION} on port {DEFAULT_API_PORT}")

    # Register cleanup
    @atexit.register
    def cleanup():
        print(f"Shutting down {SERVICE_NAME}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_API_PORT,
        log_level="info"
    )
