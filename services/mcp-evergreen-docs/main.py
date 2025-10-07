"""MCP Evergreen Docs - Main Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from infrastructure.config.settings import Settings
from presentation.api import (
    documentation_router,
    sync_router,
    validation_router,
)

# Settings
settings = Settings()

# Configure structured logging
configure_logging(
    service_name="mcp-evergreen-docs",
    log_level="INFO"
)
logger = logging.getLogger(__name__)

# Initialize MCP Log Client
log_client = MCPLogClient(
    service_name="mcp-evergreen-docs",
    mcp_logs_url="http://mcp-logs:8016"
)

# Global state
redis_client: redis.Redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global redis_client
    
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    # Initialize Redis
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password if settings.redis_password else None,
        decode_responses=True,
    )
    
    try:
        await redis_client.ping()
        logger.info("✅ Redis connection established")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
    
    yield
    
    # Cleanup
    if redis_client:
        await redis_client.close()
        logger.info("Redis connection closed")


# Create FastAPI app
app = FastAPI(
    title="MCP Evergreen Docs",
    description="Self-healing documentation service with multi-source synchronization",
    version=settings.service_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Correlation middleware for request tracking
app.add_middleware(CorrelationMiddleware)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests for documentation operations."""
    correlation_id = get_correlation_id()
    
    await log_client.info(
        f"Docs request: {request.method} {request.url.path}",
        source="main.log_requests",
        correlation_id=correlation_id,
        fields={
            "method": request.method,
            "path": request.url.path
        },
        tags=["http", "docs"]
    )
    
    response = await call_next(request)
    
    await log_client.info(
        f"Docs response: {request.method} {request.url.path}",
        source="main.log_requests",
        correlation_id=correlation_id,
        fields={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code
        },
        tags=["http", "docs"]
    )
    
    return response


# Include routers
app.include_router(documentation_router)
app.include_router(sync_router)
app.include_router(validation_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "operational",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    redis_status = "healthy"
    
    try:
        if redis_client:
            await redis_client.ping()
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if redis_status == "healthy" else "degraded",
        "redis": redis_status,
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )

