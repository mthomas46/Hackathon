"""MCP Provisioner Service - Main Application.

FastAPI application for managing MCP instance lifecycle.
"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from services.mcp_provisioner.infrastructure.config.settings import get_settings
from services.mcp_provisioner.presentation.api.routes import mcp_router, health_router
from services.mcp_provisioner.presentation.api.dependencies import close_dependencies


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting MCP Provisioner service...")
    settings = get_settings()
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API Port: {settings.service_api_port}")
    logger.info(f"Redis: {settings.redis_host}:{settings.redis_port}")
    logger.info(f"Docker Network: {settings.docker_network}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Provisioner service...")
    await close_dependencies()
    logger.info("Shutdown complete")


# Create FastAPI app
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title="MCP Provisioner Service",
        description="""
        ## Model Context Protocol (MCP) Provisioner Service
        
        Manages the lifecycle of MCP instances in the ecosystem.
        
        ### Features
        - **Provision** new MCP instances
        - **Start/Stop** MCP containers
        - **Monitor** MCP status and health
        - **Manage** MCP lifecycle states
        
        ### Architecture
        - **Domain-Driven Design (DDD)** with clean architecture
        - **Docker SDK** for container management
        - **Redis** for state persistence
        - **REST API** with OpenAPI documentation
        
        ### MCP States
        - `COLD`: Provisioned but not running
        - `WARMING`: Starting up
        - `HOT`: Running and ready
        - `COOLING`: Shutting down
        - `ERROR`: Error state
        """,
        version="1.0.0",
        docs_url=settings.docs_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )
    
    # Include routers
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(mcp_router, prefix=settings.api_prefix)
    
    # Exception handlers
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "detail": str(exc) if settings.environment == "development" else None
            }
        )
    
    logger.info("FastAPI app created")
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_api_port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )

