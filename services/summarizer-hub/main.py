"""Summarizer Hub Service - DDD Architecture Main Application.

This is the main FastAPI application for the summarizer-hub service,
implemented using Domain-Driven Design (DDD) principles.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

# Add shared infrastructure to path
project_root = Path(__file__).parent.parent.parent
shared_path = project_root / "services" / "shared"
services_path = project_root / "services"

sys.path.insert(0, str(shared_path))
sys.path.insert(0, str(services_path))
sys.path.insert(0, str(project_root))

# Import shared utilities
try:
    from services.shared.presentation.responses import create_error_response
    from services.shared.infrastructure.config import load_service_config
    from services.shared.infrastructure.utilities.middleware import setup_common_middleware
    from services.shared.monitoring.health import register_health_endpoints
except ImportError:
    def create_error_response(**kwargs):
        return {"error": "Shared utilities not available"}

    def load_service_config(**kwargs):
        return type('Config', (), {
            'service_name': 'summarizer-hub',
            'service_description': 'Summarizer Hub Service',
            'service_version': '1.0.0',
            'server': type('Server', (), {'host': '0.0.0.0', 'port': 5030})(),
        })()

    def setup_common_middleware(app, **kwargs):
        pass

    def register_health_endpoints(app, service_name, **kwargs):
        pass

# Import service modules
from .presentation.routes import document_router, summarization_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config = load_service_config(
    service_type="summarizer-hub",
    config_file="./config.yaml"
)

# Create FastAPI application
app = FastAPI(
    title=config.service_description or "Summarizer Hub API",
    description="""
    AI-Powered Document Summarization and Analysis Service

    This API provides comprehensive document processing capabilities including:
    - Multi-format document summarization
    - Intelligent categorization and tagging
    - Peer review enhancement suggestions
    - Recommendation generation
    - Real-time analysis and insights

    **Key Features:**
    - RESTful API design with comprehensive OpenAPI documentation
    - Multiple AI provider support (OpenAI, Anthropic, etc.)
    - Configurable summarization strategies
    - Quality metrics and validation
    - Enterprise-grade error handling and logging

    **Supported Document Types:**
    - Text documents
    - Code repositories
    - Technical documentation
    - Business reports
    - Research papers
    """,
    version=config.service_version or "1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Setup shared middleware (includes CORS)
setup_common_middleware(app, service_name="summarizer-hub")

# Register health endpoints
register_health_endpoints(app, "summarizer-hub")

# Include API routes
app.include_router(document_router)
app.include_router(summarization_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "summarizer-hub",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Summarizer Hub API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content=create_error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details=str(exc) if os.getenv("DEBUG", "false").lower() == "true" else None
        )
    )


if __name__ == "__main__":
    import uvicorn

    # Environment variable configuration
    host = os.getenv("SUMMARIZER_HUB_HOST", config.server.host)
    port = int(os.getenv("SUMMARIZER_HUB_PORT", config.server.port))

    print(f"🚀 Starting Summarizer Hub Service on {host}:{port}")
    uvicorn.run(
        "main_ddd:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
