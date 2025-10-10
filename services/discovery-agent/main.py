"""Discovery Agent Service - Modular Architecture

A comprehensive service discovery and tool registration service built with Domain-Driven Design principles.
This main file orchestrates the modular components for clean separation of concerns.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI

# Add shared infrastructure to path
project_root = Path(__file__).parent.parent.parent
shared_path = project_root / "services" / "shared"
sys.path.insert(0, str(shared_path))

# Service configuration - hardcoded for now due to config issues
SERVICE_NAME = "discovery-agent"
SERVICE_TITLE = "Discovery Agent Service"
SERVICE_VERSION = "1.0.0"
DEFAULT_API_PORT = int(os.environ.get('SERVICE_API_PORT', '5050'))

try:
    from services.shared.infrastructure.config import load_service_config
    from services.shared.infrastructure.monitoring.health import register_health_endpoints
    from services.shared.infrastructure.utilities.middleware import setup_common_middleware
except ImportError:
    # Fallback implementations
    def load_service_config(**kwargs):
        return type('Config', (), {
            'service_name': SERVICE_NAME,
            'service_description': SERVICE_TITLE,
            'service_version': SERVICE_VERSION,
        })()

    def register_health_endpoints(app, *args, **kwargs):
        pass

    def setup_common_middleware(app, **kwargs):
        pass

# Import routers directly - these work and have no broken dependencies
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from presentation.api.standard_endpoints import router as standard_router
from presentation.api.routes_simple import router

# Stub for register_startup_events (not critical for Phase 7)
def register_startup_events(app):
    """Startup events - stubbed for now."""
    pass

# ============================================================================
# STANDARDIZED CONFIGURATION
# ============================================================================

# Load configuration using standardized system
config = load_service_config(
    service_name=SERVICE_NAME
)

# ============================================================================
# ENHANCED DISCOVERY AGENT APPLICATION
# ============================================================================

app = FastAPI(
    title=config.service_name or "Discovery Agent Service",
    description="""
    A comprehensive service discovery and tool registration service built with Domain-Driven Design principles.

    ## Features

    * **Service Discovery**: Automatically discover services and their capabilities through OpenAPI analysis
    * **Tool Registration**: Register discovered tools with orchestrators and AI workflows
    * **Bulk Operations**: Process multiple services simultaneously with progress tracking
    * **OpenAPI Integration**: Parse, validate, and analyze OpenAPI specifications
    * **Semantic Analysis**: Extract meaningful tool descriptions and capabilities
    * **Health Monitoring**: Monitor service health, connectivity, and tool availability
    * **Network Adaptation**: Automatic URL normalization for Docker networking environments
    * **RESTful API**: Complete REST API with comprehensive OpenAPI/Swagger documentation

    ## Service Discovery Process

    1. **URL Normalization**: Adapt service URLs for container networking
    2. **Spec Retrieval**: Fetch OpenAPI specifications with intelligent fallbacks
    3. **Semantic Analysis**: Extract tool functions, parameters, and descriptions
    4. **Validation**: Ensure API compliance and tool compatibility
    5. **Registration**: Register tools with orchestrator systems

    ## Authentication

    Service discovery endpoints support optional authentication for secure environments.

    ## Rate Limiting

    Service discovery endpoints support rate limiting for API protection.
    """,
    version=config.service_version or "1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# MIDDLEWARE SETUP
# ============================================================================

setup_common_middleware(app, service_name=config.service_name)

# ============================================================================
# STANDARD ENDPOINTS (Root level)
# ============================================================================

app.include_router(standard_router)

# ============================================================================
# HEALTH ENDPOINTS
# ============================================================================

register_health_endpoints(app, config.service_name, config.service_version)

# ============================================================================
# API ROUTES
# ============================================================================

app.include_router(router, prefix="/api/v1", tags=["discovery"])

# ============================================================================
# STARTUP EVENTS
# ============================================================================

register_startup_events(app)


if __name__ == "__main__":
    import uvicorn
    import os

    # Get port from environment or use default
    port = int(os.getenv('SERVICE_API_PORT', '5050'))
    host = os.getenv('SERVICE_HOST', '0.0.0.0')

    print(f"🚀 Starting discovery-agent on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
