"""Shared utilities for Discovery Agent service modules.

This module contains common utilities used across all discovery-agent modules
to eliminate code duplication and ensure consistency.
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional, List
import httpx

# Import shared utilities
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames, ErrorCodes, EnvVars
from services.shared.error_handling import ServiceException, ValidationException
from services.shared.responses import create_success_response, create_error_response
from services.shared.logging import fire_and_forget
from services.shared.utilities import utc_now

# Global configuration for discovery agent
_DEFAULT_TIMEOUT = 30
_ORCHESTRATOR_URL_ENV = EnvVars.ORCHESTRATOR_URL_ENV
_DEFAULT_ORCHESTRATOR_URL = "http://orchestrator:5099"

def get_default_timeout() -> int:
    """Get default service client timeout."""
    return _DEFAULT_TIMEOUT

def get_orchestrator_url() -> str:
    """Get orchestrator service URL from environment."""
    return os.environ.get(_ORCHESTRATOR_URL_ENV, _DEFAULT_ORCHESTRATOR_URL)

def get_discovery_clients(timeout: int = _DEFAULT_TIMEOUT) -> ServiceClients:
    """Create and return a ServiceClients instance with proper timeout."""
    return ServiceClients(timeout=timeout)

def handle_discovery_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for discovery operations.

    Logs the error and returns a standardized error response.
    """
    from services.shared.error_handling import ValidationException

    # Remove 'operation' from context to avoid conflict
    safe_context = {k: v for k, v in context.items() if k != 'operation'}
    fire_and_forget("error", f"Discovery-agent {operation} error: {error}", ServiceNames.DISCOVERY_AGENT, safe_context)

    # Return appropriate error code based on exception type
    if isinstance(error, ValidationException):
        error_code = ErrorCodes.VALIDATION_ERROR
    else:
        error_code = ErrorCodes.INTERNAL_ERROR

    return create_error_response(
        f"Failed to {operation}",
        error_code=error_code,
        details={"error": str(error), **safe_context}
    )

def create_discovery_success_response(operation: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response for discovery operations.

    Returns a consistent success response format.
    """
    # Extract only the parameters that create_success_response accepts
    accepted_params = {}
    if 'request_id' in context:
        accepted_params['request_id'] = context['request_id']

    return create_success_response(f"Discovery {operation} successful", data, **accepted_params)

def build_discovery_context(operation: str, **additional) -> Dict[str, Any]:
    """Build context dictionary for discovery operations.

    Provides consistent context for logging and responses.
    """
    context = {
        "service": ServiceNames.DISCOVERY_AGENT
    }
    context.update(additional)
    return context

def validate_discovery_request(req) -> None:
    """Validate discovery request parameters."""
    if not req.openapi_url and not req.spec:
        raise ValidationException(
            "Either openapi_url or spec must be provided",
            {
                "openapi_url": ["Required if spec is not provided"],
                "spec": ["Required if openapi_url is not provided"]
            }
        )

    if not req.name:
        raise ValidationException(
            "Service name is required",
            {"name": ["Required field"]}
        )

    if not req.base_url:
        raise ValidationException(
            "Base URL is required",
            {"base_url": ["Required field"]}
        )

def extract_endpoints_from_spec(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract endpoints from OpenAPI specification."""
    endpoints = []

    if not isinstance(spec, dict) or "paths" not in spec:
        return endpoints

    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return endpoints

    for path, methods in paths.items():
        if not isinstance(methods, dict):
            continue

        for method, details in methods.items():
            if not isinstance(details, dict):
                continue

            endpoint = {
                "path": path,
                "method": method.upper(),
                "summary": details.get("summary", ""),
                "description": details.get("description", ""),
                "operation_id": details.get("operationId", ""),
                "tags": details.get("tags", []),
                "parameters": details.get("parameters", [])
            }
            endpoints.append(endpoint)

    return endpoints

def fetch_openapi_spec(openapi_url: str, timeout: int = _DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Fetch OpenAPI specification from URL."""
    if not openapi_url:
        raise ServiceException(
            "OpenAPI URL is required",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={"openapi_url": "Cannot be empty"}
        )

    try:
        import asyncio
        # Create event loop if not exists (for synchronous calls)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async fetch in sync context
        return loop.run_until_complete(_async_fetch_openapi_spec(openapi_url, timeout))

    except Exception as e:
        raise ServiceException(
            f"Failed to fetch OpenAPI spec from {openapi_url}",
            error_code=ErrorCodes.SERVICE_UNAVAILABLE,
            details={
                "openapi_url": openapi_url,
                "error": str(e)
            }
        )

async def _async_fetch_openapi_spec(openapi_url: str, timeout: int = _DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Async version of fetch_openapi_spec."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(openapi_url)
        response.raise_for_status()
        return response.json()

def compute_schema_hash(spec: Dict[str, Any]) -> Optional[str]:
    """Compute SHA256 hash of OpenAPI specification for change detection."""
    if not spec:
        return None

    try:
        # Sort keys for consistent hashing
        spec_str = json.dumps(spec, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(spec_str.encode('utf-8')).hexdigest()
    except Exception:
        return None

def create_discovery_response(endpoints: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create standardized discovery response."""
    response = {
        "endpoints": endpoints,
        "count": len(endpoints),
        "timestamp": utc_now().isoformat(),
    }

    if metadata:
        response["metadata"] = metadata

    return response

def register_with_orchestrator(payload: Dict[str, Any], orchestrator_url: Optional[str] = None, timeout: int = _DEFAULT_TIMEOUT):
    """Register service with orchestrator."""
    if not orchestrator_url:
        orchestrator_url = get_orchestrator_url()

    try:
        import asyncio
        # Create event loop if not exists
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async registration in sync context
        return loop.run_until_complete(_async_register_with_orchestrator(payload, orchestrator_url, timeout))

    except Exception as e:
        raise ServiceException(
            f"Failed to register with orchestrator at {orchestrator_url}",
            error_code=ErrorCodes.SERVICE_UNAVAILABLE,
            details={
                "orchestrator_url": orchestrator_url,
                "error": str(e),
                "payload_keys": list(payload.keys()) if payload else []
            }
        )

async def _async_register_with_orchestrator(payload: Dict[str, Any], orchestrator_url: str, timeout: int = _DEFAULT_TIMEOUT):
    """Async version of register_with_orchestrator."""
    # Support in-process orchestrator when testing with http://testserver
    if orchestrator_url.startswith("http://testserver"):
        from services.orchestrator.main import app as orchestrator_app
        transport = httpx.ASGITransport(app=orchestrator_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=timeout) as client:
            response = await client.post("/registry/register", json=payload)
            response.raise_for_status()
            return response.json()
    else:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(f"{orchestrator_url}/registry/register", json=payload)
            response.raise_for_status()
            return response.json()

def build_registration_payload(name: str, base_url: str, openapi_url: Optional[str], endpoints: List[Dict[str, Any]], schema_hash: Optional[str] = None) -> Dict[str, Any]:
    """Build standardized registration payload for orchestrator."""
    payload = {
        "name": name,
        "base_url": base_url,
        "openapi_url": openapi_url,
        "endpoints": endpoints,
    }

    if schema_hash:
        payload["metadata"] = {"openapi_hash": schema_hash}

    return payload
