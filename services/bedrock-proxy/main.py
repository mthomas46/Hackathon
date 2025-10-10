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
# INCLUDE ROUTERS
# ============================================================================

# Import routers with proper error handling
import sys
import os

# Add current directory to path if not already there
if os.path.dirname(__file__) not in sys.path:
    sys.path.insert(0, os.path.dirname(__file__))

# Include standard endpoints (health, about-me, endpoints, provider-consumer)
try:
    import presentation.api.standard_endpoints as standard_endpoints_module
    app.include_router(standard_endpoints_module.router)
except (ImportError, AttributeError) as e:
    print(f"Warning: Could not load standard endpoints: {e}")
    # Add a fallback health endpoint
    @app.get("/health")
    async def fallback_health():
        return {"service": "bedrock-proxy", "version": "1.0.0", "status": "healthy"}

# Include API routes from presentation layer (core business logic)
try:
    import presentation.api.routes as routes_module
    app.include_router(routes_module.router)
except (ImportError, AttributeError) as e:
    # Log error but don't fail startup
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
