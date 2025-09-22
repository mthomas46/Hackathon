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

import time
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from services.shared.core.constants_new import ServiceNames  # type: ignore
from services.shared.integrations.clients.clients import ServiceClients  # type: ignore
from services.shared.utilities import attach_self_register, setup_common_middleware  # type: ignore
from services.shared.utilities.logging_client import get_log_collector_client
from services.shared.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

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

# Service configuration constants
SERVICE_NAME = "github-mcp"
SERVICE_TITLE = "GitHub MCP"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5072

# Timeout and configuration defaults
DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 60
DEFAULT_TOOLSETS_FALLBACK = {"repos"}

# Initialize log collector client
logger_client = None

app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Local GitHub Model Context Protocol server with mock and real implementations",
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client
    try:
        # Use a fallback service name if GITHUB doesn't exist in ServiceNames
        service_name = getattr(ServiceNames, "GITHUB", SERVICE_NAME)
        logger_client = await get_log_collector_client(service_name)
        if logger_client:
            await logger_client.log_business_event(
                "github_mcp_startup",
                {
                    "version": SERVICE_VERSION,
                    "capabilities": [
                        "github_api_integration",
                        "mcp_tool_execution",
                        "mock_implementations",
                        "read_write_gating",
                        "event_system",
                    ],
                    "integrations": ["github_api", "log_collector", "event_system"],
                    "tool_categories": ["repositories", "pull_requests", "issues", "users", "actions", "organizations"],
                    "features": ["mock_mode", "read_only_mode", "tool_filtering", "event_emission"],
                },
            )
            await logger_client.log_info(
                "GitHub MCP service started",
                {
                    "mock_mode_enabled": True,
                    "real_api_enabled": False,  # Default to mock mode
                    "tool_count": len(tool_registry.list_tools()),
                    "supported_categories": ["repos", "prs", "issues", "users", "actions"],
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("GitHub MCP service shutting down")
        except Exception:
            pass


setup_common_middleware(app, ServiceNames.GITHUB if hasattr(ServiceNames, "GITHUB") else SERVICE_NAME)
attach_self_register(app, ServiceNames.GITHUB if hasattr(ServiceNames, "GITHUB") else SERVICE_NAME)


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
    start_time = time.time()
    request_id = f"github_mcp_invoke_{int(time.time() * 1000)}"

    try:
        # Determine execution mode (mock vs real)
        use_mock_mode = payload.mock if payload.mock is not None else config.is_mock_default()

        # Log tool invocation start
        if logger_client:
            await logger_client.log_business_event(
                "github_mcp_tool_invocation_started",
                {
                    "request_id": request_id,
                    "tool": tool,
                    "execution_mode": "mock" if use_mock_mode else "real_api",
                    "is_write_operation": bool(payload.write),
                    "correlation_id": payload.correlation_id,
                    "argument_count": len(payload.arguments) if payload.arguments else 0,
                    "upstream_proxy": config.should_use_official_mcp(),
                },
            )

            await logger_client.log_info(
                "Invoking GitHub MCP tool",
                {
                    "request_id": request_id,
                    "tool": tool,
                    "execution_mode": "mock" if use_mock_mode else "real_api",
                    "read_only_mode": config.is_read_only(),
                    "upstream_proxy_enabled": config.should_use_official_mcp(),
                },
            )

        # Gate write operations when in read-only mode
        if config.is_read_only() and payload.write:
            error_time = time.time() - start_time

            # Log read-only mode violation
            if logger_client:
                await logger_client.log_error(
                    f"GitHub MCP tool invocation blocked: Read-only mode violation for tool {tool}",
                    {
                        "request_id": request_id,
                        "tool": tool,
                        "error_type": "read_only_violation",
                        "processing_time_seconds": error_time,
                    },
                    error=Exception("Read-only mode enabled - write operations not allowed"),
                )

                await logger_client.log_business_event(
                    "github_mcp_tool_invocation_blocked",
                    {
                        "request_id": request_id,
                        "tool": tool,
                        "block_reason": "read_only_mode",
                        "processing_time_seconds": error_time,
                    },
                )

            raise HTTPException(status_code=403, detail="Read-only mode enabled - write operations not allowed")

        # Optional proxy to official GitHub MCP server
        if config.should_use_official_mcp():
            upstream_base_url = config.get_official_mcp_base_url()
            try:
                service_clients = ServiceClients(timeout=DEFAULT_UPSTREAM_TIMEOUT_SECONDS)
                upstream_response = await service_clients.post_json(
                    f"{upstream_base_url}/tools/{tool}/invoke", payload.model_dump()
                )

                processing_time = time.time() - start_time

                # Log successful upstream proxy invocation
                if logger_client:
                    await logger_client.log_business_event(
                        "github_mcp_tool_invocation_completed",
                        {
                            "request_id": request_id,
                            "tool": tool,
                            "execution_mode": "upstream_proxy",
                            "upstream_url": upstream_base_url,
                            "processing_time_seconds": processing_time,
                            "success": True,
                        },
                    )

                    await logger_client.log_performance_metric(
                        "github_mcp_tool_invocation",
                        processing_time,
                        {
                            "request_id": request_id,
                            "tool": tool,
                            "execution_mode": "upstream_proxy",
                            "invocation_success": True,
                        },
                    )

                return InvokeResponse(tool=tool, success=True, result=upstream_response)

            except Exception as upstream_error:
                error_time = time.time() - start_time

                # Log upstream proxy failure
                if logger_client:
                    await logger_client.log_error(
                        f"GitHub MCP upstream proxy failed: {str(upstream_error)}",
                        {
                            "request_id": request_id,
                            "tool": tool,
                            "upstream_url": upstream_base_url,
                            "error_type": type(upstream_error).__name__,
                            "processing_time_seconds": error_time,
                        },
                        error=upstream_error,
                    )

                    await logger_client.log_business_event(
                        "github_mcp_tool_invocation_failed",
                        {
                            "request_id": request_id,
                            "tool": tool,
                            "execution_mode": "upstream_proxy",
                            "upstream_url": upstream_base_url,
                            "error_type": type(upstream_error).__name__,
                            "error_message": str(upstream_error),
                            "processing_time_seconds": error_time,
                        },
                    )

                raise HTTPException(status_code=502, detail=f"Upstream GitHub MCP server error: {upstream_error}")

        # Execute tool using local implementations
        try:
            if use_mock_mode:
                tool_result = await mock_implementations.invoke_tool(tool, payload.arguments)
            else:
                tool_result = await real_implementations.invoke_tool(tool, payload.arguments)

            processing_time = time.time() - start_time

            # Calculate result metrics
            result_size = len(str(tool_result)) if tool_result else 0
            has_data = bool(tool_result)

            # Optional downstream event emission for integrations
            await event_system.maybe_emit_events(tool, tool_result)

            # Log successful local tool invocation
            if logger_client:
                await logger_client.log_business_event(
                    "github_mcp_tool_invocation_completed",
                    {
                        "request_id": request_id,
                        "tool": tool,
                        "execution_mode": "mock" if use_mock_mode else "real_api",
                        "result_size_bytes": result_size,
                        "has_data": has_data,
                        "processing_time_seconds": processing_time,
                        "events_emitted": True,  # Assuming event emission was attempted
                        "success": True,
                    },
                )

                await logger_client.log_performance_metric(
                    "github_mcp_tool_invocation",
                    processing_time,
                    {
                        "request_id": request_id,
                        "tool": tool,
                        "execution_mode": "mock" if use_mock_mode else "real_api",
                        "invocation_success": True,
                        "result_has_data": has_data,
                    },
                )

            return InvokeResponse(tool=tool, success=True, result=tool_result)

        except HTTPException:
            # Re-raise HTTP exceptions as-is (they contain proper status codes)
            raise
        except Exception as execution_error:
            error_time = time.time() - start_time

            # Log local tool execution failure
            if logger_client:
                await logger_client.log_error(
                    f"GitHub MCP tool execution failed: {str(execution_error)}",
                    {
                        "request_id": request_id,
                        "tool": tool,
                        "execution_mode": "mock" if use_mock_mode else "real_api",
                        "error_type": type(execution_error).__name__,
                        "processing_time_seconds": error_time,
                    },
                    error=execution_error,
                )

                await logger_client.log_business_event(
                    "github_mcp_tool_invocation_failed",
                    {
                        "request_id": request_id,
                        "tool": tool,
                        "execution_mode": "mock" if use_mock_mode else "real_api",
                        "error_type": type(execution_error).__name__,
                        "error_message": str(execution_error),
                        "processing_time_seconds": error_time,
                    },
                )

            # Wrap other exceptions in 500 error
            raise HTTPException(status_code=500, detail=f"Tool execution failed: {execution_error}")

    except HTTPException:
        # Re-raise HTTP exceptions as-is (already logged above)
        raise
    except Exception as unexpected_error:
        error_time = time.time() - start_time

        # Log unexpected error
        if logger_client:
            await logger_client.log_error(
                f"GitHub MCP tool invocation failed unexpectedly: {str(unexpected_error)}",
                {
                    "request_id": request_id,
                    "tool": tool if "tool" in locals() else None,
                    "error_type": "unexpected_error",
                    "processing_time_seconds": error_time,
                },
                error=unexpected_error,
            )

        raise HTTPException(status_code=500, detail=f"Unexpected error: {unexpected_error}")


if __name__ == "__main__":
    """Run the GitHub MCP service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
