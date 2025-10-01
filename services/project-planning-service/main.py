"""
Project Planning Service - Feature Development Roadmap Planning
=================================================================

Central orchestration service for comprehensive feature development planning,
providing AI-powered roadmap creation, team capacity management, and
enterprise tool integration.

Endpoints:
- POST /api/v1/features/plan: Create comprehensive feature development plan
- GET /api/v1/features/{id}: Retrieve feature planning details
- POST /api/v1/roadmaps/create: Generate development roadmap
- GET /api/v1/teams/capacity: Get team capacity and availability
- POST /api/v1/integrations/sync: Sync with external PM tools
- GET /health: Service health check

Responsibilities:
- Intelligent feature decomposition and analysis
- Team capacity and skills management
- Timeline estimation and risk assessment
- Enterprise tool integration (Jira, Linear, Asana)
- Real-time roadmap planning and optimization
- Stakeholder communication and reporting

Dependencies: shared infrastructure, LLM Gateway, Source Agent, User Store
"""

from services.shared.infrastructure.config import load_service_config

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
from services.shared.infrastructure.monitoring.health import register_health_endpoints
from services.shared.infrastructure.utilities.error_handling import register_exception_handlers
from services.shared.core.constants_new import ServiceNames
from services.shared.infrastructure.utilities.utilities import setup_common_middleware, attach_self_register
from services.shared.infrastructure.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware

# Service configuration constants
# Load service configuration
config = load_service_config("project-planning-service")

# Extract commonly used configuration values
SERVICE_NAME = config.service_name
SERVICE_VERSION = config.service_version
DEFAULT_API_PORT = config.server.port
SERVICE_VERSION = "1.0.0"
DEFAULT_API_PORT = 5170

# Initialize FastAPI app
app = FastAPI(
    title="Project Planning Service",
    version=SERVICE_VERSION,
    description="AI-powered feature development roadmap planning and team orchestration"
)

# Setup middleware
app.add_middleware(RequestIdMiddleware, service_name=SERVICE_NAME)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)

# Register health endpoints
register_health_endpoints(app, SERVICE_NAME, SERVICE_VERSION)

# Register exception handlers
register_exception_handlers(app)

# Setup common middleware
setup_common_middleware(app, SERVICE_NAME)

# Attach service registration
attach_self_register(app, SERVICE_NAME, DEFAULT_API_PORT)


@app.get("/api/v1/features/plan")
async def plan_feature():
    """Placeholder for feature planning endpoint."""
    return {
        "status": "development",
        "message": "Project Planning Service is under development",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
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
