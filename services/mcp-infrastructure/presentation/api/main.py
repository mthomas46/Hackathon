"""Main FastAPI Application - MCP Infrastructure Service.

This is the FastAPI application entry point with all routes, middleware,
and configuration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from datetime import datetime

from services.mcp_infrastructure.infrastructure.config.settings import get_settings
from services.mcp_infrastructure.presentation.api.routes import context_router, health_router
from services.mcp_infrastructure.presentation.api.dependencies import (
    init_redis_client,
    close_redis_client,
)
from services.mcp_infrastructure.presentation.api.models.responses import ErrorResponse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown tasks:
    - Initialize Redis client
    - Close Redis client
    """
    # Startup
    logger.info("Starting MCP Infrastructure Service...")
    
    try:
        await init_redis_client()
        logger.info("✓ Redis client initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize Redis: {e}")
        raise
    
    logger.info("✓ MCP Infrastructure Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Infrastructure Service...")
    
    try:
        await close_redis_client()
        logger.info("✓ Redis client closed")
    except Exception as e:
        logger.error(f"✗ Error closing Redis: {e}")
    
    logger.info("✓ MCP Infrastructure Service shutdown complete")


# Load settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="MCP Infrastructure Service",
    description="""
    **MCP Infrastructure Service** - Context and coordination backbone for the MCP ecosystem.
    
    Provides centralized:
    - Context management for MCP instances
    - Training state tracking
    - Knowledge graph metadata
    - Cross-service coordination
    
    ## Features
    
    - **Context Management**: Store, retrieve, and manage MCP operational context
    - **TTL Support**: Automatic expiration of context data
    - **Multi-Index Queries**: Efficient filtering by MCP ID, type, and tags
    - **Health Monitoring**: Health, readiness, and liveness probes
    
    ## Context Types
    
    - `instance`: MCP instance metadata and operational state
    - `training`: Training pipeline progress and statistics
    - `knowledge`: Knowledge graph metadata and schema
    - `performance`: Performance metrics and analytics
    - `coordination`: Cross-service workflow state
    - `query`: Query history and patterns
    - `relationship`: Inter-MCP relationships
    - `error`: Error tracking and incident logs
    
    ## Integration
    
    This service is designed to integrate with:
    - MCP Provisioner (instance lifecycle)
    - MCP Training Coordinator (training state)
    - MCP Gateway (routing decisions)
    - MCP Orchestrator (workflow coordination)
    
    ## API Standards
    
    - **Architecture**: Domain-Driven Design (DDD)
    - **API Style**: RESTful with OpenAPI 3.0
    - **Response Format**: JSON
    - **Error Handling**: Standardized error responses
    """,
    version="1.0.0",
    docs_url=settings.docs_url,
    openapi_url=settings.openapi_url,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with standardized format."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="ValidationError",
            message="Request validation failed",
            detail=str(exc.errors()),
            status_code=status.HTTP_400_BAD_REQUEST,
            timestamp=datetime.utcnow().isoformat() + "Z",
            path=str(request.url.path),
        ).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors with standardized format."""
    logger.error(f"Unexpected error on {request.url.path}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            detail=str(exc),
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            timestamp=datetime.utcnow().isoformat() + "Z",
            path=str(request.url.path),
        ).dict(),
    )


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and their responses."""
    logger.info(f"→ {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    logger.info(f"← {request.method} {request.url.path} - {response.status_code}")
    
    return response


# Include routers
app.include_router(
    health_router,
    prefix=settings.api_prefix,
)

app.include_router(
    context_router,
    prefix=settings.api_prefix,
)


# Root endpoint
@app.get(
    "/",
    tags=["Root"],
    summary="API Root",
    description="Get basic service information and links to documentation",
)
async def root():
    """
    API root endpoint.
    
    Returns basic service information and navigation links.
    """
    return {
        "service": "mcp-infrastructure",
        "version": "1.0.0",
        "description": "Context and coordination backbone for the MCP ecosystem",
        "documentation": settings.docs_url,
        "openapi_spec": settings.openapi_url,
        "health_check": f"{settings.api_prefix}/health",
        "endpoints": {
            "store_context": f"{settings.api_prefix}/context",
            "retrieve_context": f"{settings.api_prefix}/context/{{id}}",
            "list_contexts": f"{settings.api_prefix}/context",
            "delete_context": f"{settings.api_prefix}/context/{{id}}",
            "health": f"{settings.api_prefix}/health",
            "ready": f"{settings.api_prefix}/ready",
            "live": f"{settings.api_prefix}/live",
        },
    }


# Expose app for uvicorn
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "services.mcp_infrastructure.presentation.api.main:app",
        host="0.0.0.0",
        port=settings.service_api_port,
        reload=True,
        log_level=settings.log_level.lower(),
    )

