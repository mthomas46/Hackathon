"""Bedrock Proxy Service - AWS Bedrock Integration Gateway

A FastAPI-based proxy service for AWS Bedrock foundation models with
template-driven response generation and multi-format output support.

Key Features:
- AWS Bedrock model integration (Claude, Titan, etc.)
- Template-driven responses (summary, risks, decisions, PR confidence, lifecycle)
- Multi-format outputs (Markdown, Text, JSON)
- Mock/Production modes for development and testing
- Health monitoring and observability

Endpoints:
- POST /invoke: Process AI requests with template-based responses
- GET /health: Health check endpoint
- GET /about-me: Service descriptor
- GET /endpoints: List all available endpoints
- GET /provider-consumer: Service relationships
- GET /openapi.json: OpenAPI specification

Port: 7090 (internal), 5060 (external)
"""

import os

from fastapi import FastAPI
import uvicorn

# Service configuration
SERVICE_NAME = "bedrock-proxy"
SERVICE_TITLE = "Bedrock Proxy"
SERVICE_VERSION = "1.0.0"
SERVICE_DESCRIPTION = """AWS Bedrock Integration Gateway with template-driven response generation.

Provides seamless access to AWS Bedrock foundation models with intelligent
template processing, multi-format outputs, and comprehensive development capabilities."""

DEFAULT_API_PORT = int(os.environ.get("SERVICE_API_PORT", "7090"))

# Create FastAPI application
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description=SERVICE_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks and monitoring.
    
    Returns:
        Health status with service information
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION
    }


# ============================================================================
# INCLUDE ROUTERS
# ============================================================================

# Include API routes from presentation layer
try:
    from presentation.api.routes import router as api_router
    app.include_router(api_router)
except ImportError as e:
    # Log error but don't fail startup - allows service to run with just health endpoint
    print(f"Warning: Could not load API routes: {e}")


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    """Run the Bedrock Proxy service directly."""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_API_PORT,
        log_level="info"
    )
