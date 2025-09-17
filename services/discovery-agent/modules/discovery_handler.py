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
from .tool_discovery import tool_discovery_service


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
            from services.shared.error_handling import ValidationException
            from fastapi import HTTPException

            # Handle validation errors with proper HTTP status codes
            if isinstance(e, ValidationException):
                raise HTTPException(status_code=400, detail=str(e))

            context = build_discovery_context("discover", service_name=getattr(req, 'name', None))
            context = {k: v for k, v in context.items() if k != "operation"}
            return handle_discovery_error("discover endpoints", e, **context)

    @staticmethod
    async def discover_tools(req) -> Dict[str, Any]:
        """Discover LangGraph tools for a service."""
        try:
            # Discover tools using the tool discovery service
            discovery_result = await tool_discovery_service.discover_tools(
                service_name=req.service_name,
                service_url=req.service_url,
                openapi_url=req.openapi_url,
                tool_categories=req.tool_categories
            )

            # Handle dry run mode
            if req.dry_run:
                return create_discovery_success_response(
                    "tool discovery completed (dry run)",
                    discovery_result,
                    **build_discovery_context("discover_tools", service_name=req.service_name, dry_run=True)
                )

            # Register tools with orchestrator if available
            orchestrator_url = req.orchestrator_url or get_orchestrator_url()
            try:
                await DiscoveryHandler._register_tools_with_orchestrator(
                    discovery_result, orchestrator_url
                )
                discovery_result["registration_status"] = "completed"
            except Exception as reg_error:
                discovery_result["registration_status"] = "failed"
                discovery_result["registration_error"] = str(reg_error)

            return create_discovery_success_response(
                "tool discovery and registration completed",
                discovery_result,
                **build_discovery_context("discover_tools", service_name=req.service_name,
                                        tool_count=discovery_result.get("tools_discovered", 0))
            )

        except httpx.HTTPStatusError as e:
            context = build_discovery_context("discover_tools", service_name=getattr(req, 'service_name', None))
            context = {k: v for k, v in context.items() if k != "operation"}
            return handle_discovery_error("discover tools", e, status_code=e.response.status_code, **context)

        except Exception as e:
            context = build_discovery_context("discover_tools", service_name=getattr(req, 'service_name', None))
            context = {k: v for k, v in context.items() if k != "operation"}
            return handle_discovery_error("discover tools", e, **context)

    @staticmethod
    async def _register_tools_with_orchestrator(discovery_result: Dict[str, Any], orchestrator_url: str):
        """Register discovered tools with the orchestrator."""
        try:
            # Prepare tool registration payload
            payload = {
                "service_name": discovery_result["service_name"],
                "service_url": discovery_result["service_url"],
                "tools": discovery_result["tools"],
                "metadata": {
                    "discovered_at": discovery_result.get("timestamp"),
                    "tool_count": discovery_result["tools_discovered"],
                    "spec_url": discovery_result["spec_url"]
                }
            }

            # Register with orchestrator (assuming tools endpoint exists)
            # For now, we'll use the existing registration endpoint
            registration_payload = {
                "name": f"{discovery_result['service_name']}_tools",
                "base_url": discovery_result["service_url"],
                "endpoints": [],  # Tools don't map directly to endpoints
                "metadata": payload["metadata"]
            }

            await register_with_orchestrator(registration_payload, orchestrator_url)

        except Exception as e:
            raise Exception(f"Failed to register tools with orchestrator: {str(e)}")


# Create singleton instance
discovery_handler = DiscoveryHandler()
