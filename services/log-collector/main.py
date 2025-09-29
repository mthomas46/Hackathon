"""Log Collector Service - DDD + REST Architecture

A comprehensive log collection and analysis service built with Domain-Driven Design
and RESTful API design for reliable log aggregation and monitoring.

Endpoints:
- POST /api/v1/logs: Store log entries
- POST /api/v1/logs/batch: Store multiple log entries
- GET /api/v1/logs: Retrieve logs with filtering
- GET /api/v1/stats: Get aggregated statistics
- GET /api/v1/logs/health: Service health check

Architecture:
- Domain Layer: Log entities, statistics, and log processing services
- Application Layer: Use cases for log operations and analysis
- Infrastructure Layer: Storage, external services, monitoring
- Presentation Layer: REST API with FastAPI

Responsibilities:
- Receive structured log entries from various services
- Maintain bounded in-memory history for recent logs
- Provide basic aggregation and filtering capabilities
- Enable quick diagnostics through statistics endpoint
- Integrated with standardized logging and monitoring system

Dependencies: shared middlewares for request tracking and metrics.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from services.shared.utilities import attach_self_register  # type: ignore
from services.shared.utilities.middleware import setup_common_middleware  # type: ignore

# Import DDD + REST API
from .presentation.api import api_router

# ============================================================================
# SERVICE CONSTANTS
# ============================================================================

SERVICE_NAME = "log-collector"
SERVICE_TITLE = "Log Collector Service"
SERVICE_VERSION = "1.0.0"

# ============================================================================
# DDD + REST APPLICATION SETUP
# ============================================================================

# Lifespan management for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print(f"🚀 Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    yield
    # Shutdown
    print(f"🛑 Shutting down {SERVICE_NAME}")

# Create FastAPI application
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Centralized log collection and analysis service with aggregation and monitoring",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================================================
# MIDDLEWARE & CONFIGURATION
# ============================================================================

# Setup shared middleware (includes CORS)
setup_common_middleware(app, service_name=SERVICE_NAME)

# ============================================================================
# ROUTE REGISTRATION
# ============================================================================

# Include DDD + REST API routes
app.include_router(api_router)

# ============================================================================
# LEGACY COMPATIBILITY (to be removed after migration)
# ============================================================================

# Keep some legacy endpoints for backward compatibility during transition
@app.get("/health")
async def legacy_health_check():
    """Legacy health check endpoint for backward compatibility."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "message": "Use /api/v1/logs/health for new API"
    }


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5012,  # Standard port for log-collector
        reload=True
    )
