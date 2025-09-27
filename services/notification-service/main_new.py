"""Notification Service - DDD + REST Architecture

A comprehensive notification service built with Domain-Driven Design principles
and RESTful API design for reliable, scalable notification delivery.

Endpoints:
- POST /api/v1/notifications/send: Send notifications to owners
- POST /api/v1/notifications/test: Test notification configuration
- GET /api/v1/notifications/health: Service health check

Architecture:
- Domain Layer: Entities, value objects, and domain services
- Application Layer: Use cases orchestrating business operations
- Infrastructure Layer: External services, repositories, messaging
- Presentation Layer: REST API with FastAPI

Responsibilities:
- Resolve owner names to notification targets (email, Slack, webhooks, SMS)
- Send notifications with automatic deduplication to prevent spam
- Maintain a dead-letter queue for failed notification delivery
- Cache owner resolutions with configurable TTL for performance
- Support multiple notification channels and priorities

Dependencies: shared middlewares for request tracking; httpx for webhook delivery.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.shared.utilities import attach_self_register  # type: ignore
from services.shared.utilities.middleware import setup_common_middleware  # type: ignore

# Import DDD + REST API
from .presentation.api import api_router

# ============================================================================
# SERVICE CONSTANTS
# ============================================================================

SERVICE_NAME = "notification-service"
SERVICE_TITLE = "Notification Service"
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
    description="Centralized notification service with owner resolution, deduplication, and dead letter queue",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# ============================================================================
# MIDDLEWARE & CONFIGURATION
# ============================================================================

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup shared middleware
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
        "message": "Use /api/v1/notifications/health for new API"
    }


# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5011,  # Standard port for notification-service
        reload=True
    )
