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


class DiscoverRequest(BaseModel):
    """Input for discovery.

    - `spec`: Optional inline OpenAPI for offline/testing flows
    - `openapi_url`: Fetch spec from URL when provided
    - `orchestrator_url`: Override orchestrator base for tests
    """
    name: str
    base_url: str
    openapi_url: Optional[str] = None  # e.g., http://service:port/openapi.json
    spec: Optional[dict] = None  # inline OpenAPI for testing/offline
    dry_run: bool = False
    orchestrator_url: Optional[str] = None


@app.post("/discover")
async def discover(req: DiscoverRequest):
    """Discover and register OpenAPI endpoints with validation and error handling."""
    try:
        # Validate discovery request
        validate_discovery_request(req)

        # Extract endpoints from spec
        endpoints = []
        schema_hash = None
        spec = None

        if req.spec is not None:
            spec = req.spec
            endpoints = extract_endpoints_from_spec(spec)
        elif req.openapi_url:
            spec = await fetch_openapi_spec(req.openapi_url)
            endpoints = extract_endpoints_from_spec(spec)

        # Compute schema hash for change detection
        schema_hash = compute_schema_hash(spec)

        # Build registration payload
        payload = build_registration_payload(
            name=req.name,
            base_url=req.base_url,
            openapi_url=req.openapi_url,
            endpoints=endpoints,
            schema_hash=schema_hash
        )

        # Handle dry run mode
        if req.dry_run:
            response_data = create_discovery_response(endpoints, {"dry_run": True})
            return create_discovery_success_response(
                "completed (dry run)",
                response_data,
                **build_discovery_context("discover", service_name=req.name, dry_run=True)
            )

        # Register with orchestrator
        orchestrator_url = req.orchestrator_url or get_orchestrator_url()
        reg_resp = await register_with_orchestrator(payload, orchestrator_url)

        # Return success response
        response_data = create_discovery_response(endpoints, {"registered": reg_resp})
        return create_discovery_success_response(
            "and registration completed",
            response_data,
            **build_discovery_context("discover", service_name=req.name, endpoint_count=len(endpoints))
        )

    except Exception as e:
        from services.shared.error_handling import ValidationException
        from fastapi import HTTPException

        # Handle validation errors with proper HTTP status codes
        if isinstance(e, ValidationException):
            raise HTTPException(status_code=400, detail=str(e))

        context = build_discovery_context("discover", service_name=getattr(req, 'name', None))
        return handle_discovery_error("discover endpoints", e, **context)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5045)

