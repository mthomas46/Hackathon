"""MCP Package Manager - Main Application with MCP Logging."""

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

# Settings
settings = Settings()

# Configure structured logging
configure_logging(
    service_name="mcp-package-manager",
    log_level="INFO"
)
logger = logging.getLogger(__name__)

# Initialize MCP Log Client
log_client = MCPLogClient(
    service_name="mcp-package-manager",
    mcp_logs_url="http://mcp-logs:8016"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    logger.info(f"Storage directory: {settings.storage_dir}")
    
    yield
    
    logger.info("Shutting down")


# Create FastAPI app
app = FastAPI(
    title="MCP Package Manager",
    description="Docker for Knowledge Graphs - Package, version, and deploy MCP knowledge",
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


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "description": "Docker for Knowledge Graphs",
        "status": "operational",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "storage_dir": settings.storage_dir,
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

