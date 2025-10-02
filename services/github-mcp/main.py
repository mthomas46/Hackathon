"""Service: GitHub MCP (Model Context Protocol) local server

Endpoints:
- GET /health: Service health check
- GET /info: Service information and configuration status
- GET /tools: List available GitHub MCP tools with filtering
- POST /tools/{tool}/invoke: Execute a specific GitHub MCP tool

Responsibilities:
- Provide local MCP-like tools to interact with GitHub data (repos, PRs, issues, users, actions)
- Support both mock implementations for testing and real GitHub API calls
- Proxy requests to official GitHub MCP servers when configured
- Gate write operations based on read-only mode settings
- Emit events for downstream service integrations
- Support dynamic toolset filtering for reduced cognitive load

Dependencies: shared middlewares, httpx for HTTP requests, GitHub API credentials.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Set
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Add shared infrastructure to path
project_root = Path(__file__).parent.parent.parent
shared_path = project_root / "services" / "shared"
sys.path.insert(0, str(shared_path))

# Service configuration - hardcoded for now due to config issues
SERVICE_NAME = "github-mcp"
SERVICE_TITLE = "GitHub MCP Service"
SERVICE_VERSION = "1.0.0"
DEFAULT_API_PORT = int(os.environ.get('SERVICE_API_PORT', '5030'))

try:
    from services.shared.infrastructure.config import load_service_config
    from services.shared.utilities.resource_monitor import monitor_resources
    from services.shared.infrastructure.external.clients.clients import ServiceClients
    from services.shared.infrastructure.utilities.utilities import attach_self_register, setup_common_middleware
    from services.shared.infrastructure.utilities.middleware import (
        RequestIdMiddleware,
        RequestMetricsMiddleware,
    )
except ImportError:
    # Fallback implementations
    def load_service_config(service_name=None, **kwargs):
        return type('Config', (), {
            'service_name': SERVICE_NAME,
            'service_description': SERVICE_TITLE,
            'service_version': SERVICE_VERSION,
        })()

    def monitor_resources(**kwargs):
        pass

    class ServiceClients:
        def __init__(self): pass

    def attach_self_register(app=None, service_name=None, **kwargs):
        pass

    def setup_common_middleware(app=None, service_name=None, **kwargs):
        pass

    class RequestIdMiddleware:
        def __init__(self, app): pass
        def __call__(self, scope, receive, send): pass

    class RequestMetricsMiddleware:
        def __init__(self, app): pass
        def __call__(self, scope, receive, send): pass

try:
    from .modules.config import config
    from .modules.event_system import event_system
    from .modules.mock_implementations import mock_implementations
    from .modules.real_implementations import real_implementations
    from .modules.tool_registry import ToolDescription, tool_registry
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.config import config
    from modules.event_system import event_system
    from modules.mock_implementations import mock_implementations
    from modules.real_implementations import real_implementations
    from modules.tool_registry import ToolDescription, tool_registry

# Load standardized configuration
config = load_service_config("github-mcp")

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = "GitHub MCP"
SERVICE_VERSION = config.service_version
DEFAULT_API_PORT = int(os.environ.get("SERVICE_API_PORT", "5030"))

# Timeout and configuration defaults
DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 60
DEFAULT_TOOLSETS_FALLBACK = {"repos"}

app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Local GitHub Model Context Protocol server with mock and real implementations",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=config.service_name)
attach_self_register(app, config.service_name)

# Include DDD API routes
try:
    from .presentation.api import api_router
    app.include_router(api_router)
except ImportError:
    # Fallback if DDD structure not available
    pass


class InvokeRequest(BaseModel):
    """Request model for tool invocation with execution options.

    Allows specification of tool arguments and execution mode controls
    for flexible GitHub MCP tool invocation.
    """

    arguments: Dict[str, Any] = {}
    """Tool-specific arguments as key-value pairs."""

    correlation_id: Optional[str] = None
    """Optional correlation ID for request tracing."""

    mock: Optional[bool] = None
    """Override default mock mode setting (True for mock, False for real API)."""

    write: Optional[bool] = None
    """Indicates if this is a write operation (subject to read-only mode gating)."""


class InvokeResponse(BaseModel):
    """Response model for tool invocation results.

    Contains the execution result and metadata for a tool invocation,
    indicating success or failure with appropriate result data.
    """

    tool: str
    """Name of the tool that was invoked."""

    success: bool
    """Whether the tool invocation was successful."""

    result: Dict[str, Any]
    """Tool execution result data (varies by tool)."""


@app.get("/health")
async def health():
    """Health check endpoint returning service status and basic information."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "description": "GitHub MCP service is operational",
    }


@app.get("/info")
async def info():
    """Information endpoint returning service configuration and status."""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "mock_mode_default": config.is_mock_default(),
        "toolsets": list(config.parse_toolsets_from_env() or []),
        "dynamic_toolsets": config.is_dynamic_enabled(),
        "read_only": config.is_read_only(),
        "github_host": config.get_github_host(),
        "token_present": config.has_github_token(),
    }


@app.get("/tools", response_model=List[ToolDescription])
async def list_tools(toolsets: Optional[str] = None):
    """List available GitHub MCP tools with optional toolset filtering.

    Returns available tools filtered by toolset when dynamic toolsets are enabled.
    Supports comma-separated toolset specification in query parameter.
    Defaults to 'repos' toolset when dynamic mode is enabled but no toolsets specified.
    """
    # Determine effective toolsets from query (if dynamic) or environment
    effective_toolsets: Optional[Set[str]] = None
    if toolsets and config.is_dynamic_enabled():
        # Parse comma-separated toolsets from query parameter
        effective_toolsets = set([p.strip() for p in toolsets.split(",") if p.strip()])
    else:
        # Use toolsets from environment configuration
        effective_toolsets = config.parse_toolsets_from_env()

    # Default to repos toolset when dynamic enabled and nothing specified (reduces cognitive load)
    if config.is_dynamic_enabled() and not effective_toolsets:
        effective_toolsets = DEFAULT_TOOLSETS_FALLBACK

    return tool_registry.filter_tools_by_toolsets(effective_toolsets)


@app.post("/tools/{tool}/invoke", response_model=InvokeResponse)
async def invoke(tool: str, payload: InvokeRequest):
    """Invoke a specific GitHub MCP tool with the provided arguments.

    Executes the specified tool using either mock implementations or real GitHub API calls,
    with support for upstream MCP proxying and downstream event emission.
    Write operations are gated by read-only mode configuration.

    Supports correlation ID tracking and flexible mock/real execution modes.
    """
    # Determine execution mode (mock vs real)
    use_mock_mode = (
        payload.mock if payload.mock is not None else config.is_mock_default()
    )

    # Gate write operations when in read-only mode
    if config.is_read_only() and payload.write:
        raise HTTPException(
            status_code=403,
            detail="Read-only mode enabled - write operations not allowed",
        )

    # Optional proxy to official GitHub MCP server
    if config.should_use_official_mcp():
        upstream_base_url = config.get_official_mcp_base_url()
        try:
            service_clients = ServiceClients(timeout=DEFAULT_UPSTREAM_TIMEOUT_SECONDS)
            upstream_response = await service_clients.post_json(
                f"{upstream_base_url}/tools/{tool}/invoke", payload.model_dump()
            )
            return InvokeResponse(tool=tool, success=True, result=upstream_response)
        except Exception as upstream_error:
            raise HTTPException(
                status_code=502,
                detail=f"Upstream GitHub MCP server error: {upstream_error}",
            )

    # Execute tool using local implementations
    try:
        if use_mock_mode:
            tool_result = await mock_implementations.invoke_tool(
                tool, payload.arguments
            )
        else:
            tool_result = await real_implementations.invoke_tool(
                tool, payload.arguments
            )

        # Optional downstream event emission for integrations
        await event_system.maybe_emit_events(tool, tool_result)

        return InvokeResponse(tool=tool, success=True, result=tool_result)

    except HTTPException:
        # Re-raise HTTP exceptions as-is (they contain proper status codes)
        raise
    except Exception as execution_error:
        # Wrap other exceptions in 500 error
        raise HTTPException(
            status_code=500, detail=f"Tool execution failed: {execution_error}"
        )


if __name__ == "__main__":
    """Run the GitHub MCP service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_API_PORT, log_level="info")
