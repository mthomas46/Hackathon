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
from services.shared.presentation.api.middleware import (
    RequestIdMiddleware,
    MetricsMiddleware,
    RateLimitMiddleware
)

from .presentation.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config = load_service_config()

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
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.get('cors_origins', ['*']),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=config.get('allowed_hosts', ['*'])
)

# Add custom middleware
app.add_middleware(RequestIdMiddleware)
app.add_middleware(MetricsMiddleware)
app.add_middleware(RateLimitMiddleware)

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
            details=str(exc) if config.get('debug', False) else None
        )
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Simulation Dashboard starting up...")

    # Start resource monitoring
    monitor_resources()

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
        host=config.get('host', '0.0.0.0'),
        port=config.get('port', 8000),
        reload=config.get('debug', False),
        log_level=config.get('log_level', 'info')
    )
