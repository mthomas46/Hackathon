"""Discovery Agent Service

Parses inline or remote OpenAPI specs, extracts endpoints, and optionally
registers the service with the orchestrator's registry. Supports in-process
ASGI transport for tests using `http://testserver`.

Endpoints:
- POST /discover - Discover and register OpenAPI endpoints
- GET /health - Service health status

Dependencies: shared middlewares, httpx for HTTP requests, optional in-process ASGI transport.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response
from services.shared.constants_new import ServiceNames, ErrorCodes
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
from .modules.models import DiscoverRequest
from .modules.discovery_handler import discovery_handler

# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware and error handlers
app = FastAPI(title="Discovery Agent", version="1.0.0")

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.DISCOVERY_AGENT)

# Auto-register with orchestrator
attach_self_register(app, ServiceNames.DISCOVERY_AGENT)

# Register standardized health endpoints
register_health_endpoints(app, ServiceNames.DISCOVERY_AGENT, "1.0.0")


@app.post("/discover")
async def discover(req: DiscoverRequest):
    """Discover and register OpenAPI endpoints using handler module."""
    return await discovery_handler.discover_endpoints(req)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5045)

