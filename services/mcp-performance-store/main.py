"""
MCP Orchestration Performance Store Service.

Main FastAPI application for tracking orchestration performance metrics.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.mcp_performance_store.infrastructure.config import Settings
from services.mcp_performance_store.presentation.routes import router
from services.mcp_performance_store.presentation.analytics_routes import router as analytics_router
from services.mcp_performance_store.presentation.dependencies import get_repository


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Load settings
settings = Settings()


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    # Startup
    logger.info("Starting MCP Performance Store Service...")
    try:
        repository = await get_repository()
        logger.info("Repository initialized")
    except Exception as e:
        logger.error(f"Failed to initialize repository: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down MCP Performance Store Service...")
    try:
        repository = await get_repository()
        await repository.disconnect()
        logger.info("Repository disconnected")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="MCP Orchestration Performance Store",
    description=(
        "Service for tracking performance metrics, pattern scores, and prompts "
        "from all MCP orchestration operations across the ecosystem."
    ),
    version="1.0.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Include routes
app.include_router(router)
app.include_router(analytics_router)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mcp-performance-store",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "service": "MCP Orchestration Performance Store",
        "version": "1.0.0",
        "docs": "/api/v1/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower()
    )
