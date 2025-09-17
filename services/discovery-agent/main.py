"""Service: Discovery Agent

Endpoints:
- POST /discover: Discover and register OpenAPI endpoints from specs or URLs
- GET /health: Service health status with registration capabilities

Responsibilities:
- Parse inline or remote OpenAPI specifications to extract service endpoints
- Register discovered services with the orchestrator's service registry
- Support both inline specs for testing and remote URL fetching for production
- Compute schema hashes for change detection and versioning
- Provide dry-run mode for testing without actual registration

Dependencies: shared middlewares, httpx for HTTP requests, orchestrator service for registration.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.responses.responses import create_success_response
from services.shared.core.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import setup_common_middleware, attach_self_register

# ============================================================================
# LOCAL MODULES - Service-specific functionality
# ============================================================================
from .modules.shared_utils import (
    get_orchestrator_url,
    handle_discovery_error,
    create_discovery_success_response,
    build_discovery_context,
    validate_discovery_request,
    extract_endpoints_from_spec,
    fetch_openapi_spec,
    compute_schema_hash,
    create_discovery_response,
    register_with_orchestrator,
    build_registration_payload
)

# ============================================================================
# HANDLER MODULES - Extracted business logic
# ============================================================================
from .modules.models import DiscoverRequest, ToolDiscoveryRequest
from .modules.discovery_handler import discovery_handler

# Service configuration constants
SERVICE_NAME = "discovery-agent"
SERVICE_TITLE = "Discovery Agent"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5045

# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware and error handlers
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Service discovery agent for OpenAPI endpoint registration and orchestration"
)

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.DISCOVERY_AGENT)

# Auto-register with orchestrator
attach_self_register(app, ServiceNames.DISCOVERY_AGENT)

# Register standardized health endpoints
register_health_endpoints(app, ServiceNames.DISCOVERY_AGENT, SERVICE_VERSION)


@app.post("/discover")
async def discover(req: DiscoverRequest):
    """Discover and register OpenAPI endpoints from specification or URL.

    Parses OpenAPI specifications to extract service endpoints and optionally
    registers them with the orchestrator. Supports both inline specs for testing
    and remote URL fetching for production deployments. Includes dry-run mode
    for testing without actual registration.
    """
    return await discovery_handler.discover_endpoints(req)


@app.post("/discover/tools")
async def discover_tools(req: ToolDiscoveryRequest):
    """Discover and register LangGraph tools from service OpenAPI specifications.

    Automatically analyzes service OpenAPI specs to identify operations that can be
    exposed as LangGraph tools. Categorizes tools by functionality and optionally
    registers them with the orchestrator for use in AI workflows. Supports dry-run
    mode for testing tool discovery without actual registration.

    Tool categories include: create, read, update, delete, analysis, search,
    notification, storage, processing, document, prompt, code, workflow, general.
    """
    return await discovery_handler.discover_tools(req)


if __name__ == "__main__":
    """Run the Discovery Agent service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )

