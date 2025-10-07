"""Main application entry point for llm-tagging-pipeline with MCP Logging."""

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

# Configure structured logging
configure_logging(
    service_name="llm-tagging-pipeline",
    log_level="INFO"
)
logger = logging.getLogger(__name__)

# Initialize MCP Log Client
log_client = MCPLogClient(
    service_name="llm-tagging-pipeline",
    mcp_logs_url="http://mcp-logs:8016"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Start log client
    await log_client.start()
    
    logger.info("Starting llm-tagging-pipeline service")
    await log_client.info(
        "Service starting",
        source="main.lifespan",
        fields={
            "service": "llm-tagging-pipeline",
            "version": "1.0.0"
        },
        tags=["startup", "llm-tagging"]
    )
    
    yield
    
    logger.info("Shutting down service")
    await log_client.info(
        "Service shutting down",
        source="main.lifespan",
        tags=["shutdown", "llm-tagging"]
    )
    
    # Stop log client
    await log_client.stop()


# Create FastAPI app
app = FastAPI(
    title="LLM Tagging Pipeline",
    description="Automated LLM metadata tagging service with observability",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Correlation middleware for request tracking
app.add_middleware(CorrelationMiddleware)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with tagging context."""
    correlation_id = get_correlation_id()
    
    await log_client.info(
        f"Tagging request: {request.method} {request.url.path}",
        source="main.log_requests",
        correlation_id=correlation_id,
        fields={
            "method": request.method,
            "path": request.url.path
        },
        tags=["http", "tagging", "request"]
    )
    
    response = await call_next(request)
    
    await log_client.info(
        f"Tagging response: {request.method} {request.url.path}",
        source="main.log_requests",
        correlation_id=correlation_id,
        fields={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code
        },
        tags=["http", "tagging", "response"]
    )
    
    return response


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "llm-tagging-pipeline",
        "version": "1.0.0",
        "status": "running",
        "logging": "enabled"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "llm-tagging-pipeline"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8021,
        reload=True
    )
