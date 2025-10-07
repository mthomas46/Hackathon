"""Main application entry point with MCP Logging Integration."""

import logging
import sys
from pathlib import Path
from contextvars import ContextVar
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.logging import MCPLogClient, configure_logging
from shared.middleware import CorrelationMiddleware, get_correlation_id

from infrastructure.config.settings import Settings
from presentation.api import ingestion, health

# Load settings
settings = Settings()

# Configure structured logging
configure_logging(
    service_name="kafka-ingestion",
    log_level="INFO"
)
logger = logging.getLogger(__name__)

# Initialize MCP Log Client
log_client = MCPLogClient(
    service_name="kafka-ingestion",
    mcp_logs_url="http://mcp-logs:8016"
)


# Create FastAPI app
app = FastAPI(
    title="Kafka Ingestion Service",
    description="Event-driven document ingestion service with MCP logging",
    version=settings.service_version
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


@app.on_event("startup")
async def startup():
    """Startup event - initialize logging."""
    await log_client.start()
    
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    await log_client.info(
        "Service starting",
        source="main.startup",
        fields={
            "service": settings.service_name,
            "version": settings.service_version,
            "port": settings.service_port
        },
        tags=["startup", "kafka-ingestion"]
    )


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event - cleanup logging."""
    logger.info("Shutting down service")
    await log_client.info(
        "Service shutting down",
        source="main.shutdown",
        tags=["shutdown", "kafka-ingestion"]
    )
    
    await log_client.stop()


# Include routers
app.include_router(health.router)
app.include_router(ingestion.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "status": "running",
        "logging": "enabled"
    }


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    correlation_id = get_correlation_id()
    
    await log_client.info(
        f"Request received: {request.method} {request.url.path}",
        source="main.log_requests",
        correlation_id=correlation_id,
        fields={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host if request.client else "unknown"
        },
        tags=["http", "request"]
    )
    
    response = await call_next(request)
    
    await log_client.info(
        f"Request completed: {request.method} {request.url.path}",
        source="main.log_requests",
        correlation_id=correlation_id,
        fields={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code
        },
        tags=["http", "response"]
    )
    
    return response


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True
    )
