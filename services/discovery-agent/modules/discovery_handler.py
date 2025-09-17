"""Discovery handler for Discovery Agent service.

Handles the complex logic for discovering and registering OpenAPI endpoints.
"""
from typing import Dict, Any, List
import httpx

from .shared_utils import (
    validate_discovery_request,
    extract_endpoints_from_spec,
    fetch_openapi_spec,
    compute_schema_hash,
    create_discovery_response,
    build_registration_payload,
    register_with_orchestrator,
    get_orchestrator_url,
    create_discovery_success_response,
    build_discovery_context,
    handle_discovery_error
)


class DiscoveryHandler:
    """Handles discovery and registration operations."""

    @staticmethod
    async def discover_endpoints(req) -> Dict[str, Any]:
        """Discover and register OpenAPI endpoints."""
        try:
            # Validate discovery request
            validate_discovery_request(req)

            # Extract endpoints from spec
            endpoints: List[Dict[str, Any]] = []
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

        except httpx.HTTPStatusError as e:
            # Handle HTTP errors specifically
            context = build_discovery_context("discover", service_name=getattr(req, 'name', None))
            context = {k: v for k, v in context.items() if k != "operation"}
            return handle_discovery_error("discover endpoints", e, status_code=e.response.status_code, **context)

        except Exception as e:
            from services.shared.utilities.error_handling import ValidationException
            from fastapi import HTTPException

            # Handle validation errors with proper HTTP status codes
            if isinstance(e, ValidationException):
                raise HTTPException(status_code=400, detail=str(e))

            context = build_discovery_context("discover", service_name=getattr(req, 'name', None))
            context = {k: v for k, v in context.items() if k != "operation"}
            return handle_discovery_error("discover endpoints", e, **context)


# Create singleton instance
discovery_handler = DiscoveryHandler()
