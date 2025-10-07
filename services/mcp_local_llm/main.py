"""MCP Local LLM - Main Application with MCP Logging."""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logging import MCPLogClient, configure_logging
from shared.middleware import CorrelationMiddleware, get_correlation_id

from infrastructure.config.settings import Settings
from presentation.api import (
    model_router,
    inference_router,
    context_router,
)

# Settings
settings = Settings()

# Configure structured logging
configure_logging(
    service_name="mcp-local-llm",
    log_level="INFO"
)
logger = logging.getLogger(__name__)

# Initialize MCP Log Client
log_client = MCPLogClient(
    service_name="mcp-local-llm",
    mcp_logs_url="http://mcp-logs:8016"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Start log client
    await log_client.start()
    
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    await log_client.info(
        "Service starting",
        source="main.lifespan",
        fields={
            "service": settings.service_name,
            "version": settings.service_version,
            "ollama": f"{settings.ollama_host}:{settings.ollama_port}",
            "model": settings.default_model
        },
        tags=["startup", "local-llm"]
    )
    
    yield
    
    logger.info("Shutting down")
    await log_client.info(
        "Service shutting down",
        source="main.lifespan",
        tags=["shutdown", "local-llm"]
    )
    
    # Stop log client
    await log_client.stop()


# Create FastAPI app
app = FastAPI(
    title="MCP Local LLM",
    description="Local Language Model Inference Platform",
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

# Include routers
app.include_router(model_router)
app.include_router(inference_router)
app.include_router(context_router)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with LLM context."""
    correlation_id = get_correlation_id()
    
    await log_client.info(
        f"LLM request: {request.method} {request.url.path}",
        source="main.log_requests",
        correlation_id=correlation_id,
        fields={
            "method": request.method,
            "path": request.url.path
        },
        tags=["http", "local-llm"]
    )
    
    response = await call_next(request)
    
    await log_client.info(
        f"LLM response: {request.method} {request.url.path}",
        source="main.log_requests",
        correlation_id=correlation_id,
        fields={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code
        },
        tags=["http", "local-llm"]
    )
    
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "description": "Local LLM Inference",
        "status": "operational",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ollama": f"{settings.ollama_host}:{settings.ollama_port}",
        "default_model": settings.default_model,
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

