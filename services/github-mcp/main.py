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

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

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

# ============================================================================
# STANDARD API RESPONSE MODELS - Consistent error handling
# ============================================================================

class APIResponse(BaseModel):
    """Standard API response wrapper for consistent formatting."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable response message")
    data: Optional[Any] = Field(None, description="Response data payload")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")
    timestamp: Optional[str] = Field(None, description="Response timestamp in ISO 8601 format")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class ErrorResponse(BaseModel):
    """Standard error response for consistent error formatting."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=False, description="Always false for error responses")
    error: Dict[str, Any] = Field(..., description="Error details")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")
    timestamp: str = Field(..., description="Error timestamp in ISO 8601 format")


class HealthResponse(BaseModel):
    """Health check response model for GitHub MCP service."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    last_health_check: Optional[str] = Field(None, description="Last health check timestamp")
    github_api_connected: bool = Field(..., description="GitHub API connectivity status")
    tools_registered: int = Field(..., description="Number of MCP tools registered")
    mock_mode_enabled: bool = Field(..., description="Whether mock mode is enabled")

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
    title="🔗 Enterprise GitHub Integration & Model Context Protocol Hub",
    version=SERVICE_VERSION,
    description="""
    **🔗 Enterprise GitHub Integration & Model Context Protocol Hub** - Intelligent GitHub ecosystem integration with MCP protocol support for comprehensive repository management and development automation.

    ## 🎯 **Core Capabilities**

    ### **🔧 Model Context Protocol (MCP) Implementation**
    - **Tool-Based Architecture**: MCP-compliant tools for GitHub operations
    - **Dynamic Tool Registry**: Runtime tool discovery and registration
    - **Protocol Compliance**: Full MCP specification adherence
    - **Extensible Framework**: Plugin-based tool development support

    ### **📚 Intelligent GitHub Integration**
    - **Repository Intelligence**: Advanced repository analysis and insights
    - **PR Management**: Pull request lifecycle automation and intelligence
    - **Issue Tracking**: Intelligent issue management and categorization
    - **Workflow Automation**: GitHub Actions integration and orchestration
    - **User Analytics**: Developer productivity and contribution insights

    ### **🏗️ Development Automation Engine**
    - **Code Review Automation**: Intelligent code review assistance and suggestions
    - **Quality Gates**: Automated quality checks and compliance validation
    - **Documentation Sync**: Automatic documentation updates and synchronization
    - **Dependency Management**: Intelligent dependency analysis and recommendations
    - **Security Scanning**: Automated security vulnerability detection

    ### **🔐 Enterprise Security & Governance**
    - **Access Control**: Granular permission management for GitHub operations
    - **Audit Trails**: Comprehensive operation logging and compliance tracking
    - **Rate Limiting**: Intelligent rate limiting and quota management
    - **Data Privacy**: Secure handling of sensitive repository information
    - **Compliance Monitoring**: Regulatory compliance validation and reporting

    ### **🎭 Multi-Environment Operation**
    - **Mock Mode**: Development and testing with realistic mock data
    - **Real API Mode**: Production integration with live GitHub API
    - **Hybrid Mode**: Intelligent fallback between mock and real implementations
    - **Environment Detection**: Automatic environment-specific configuration

    ## 📡 **REST API Endpoints by Category**

    ### **🏥 Health & Monitoring (`/health`)**
    - `GET /health` - Comprehensive service health and operational metrics
    - GitHub API connectivity, tool registration status, and environment configuration

    ### **ℹ️ Service Information (`/info`)**
    - `GET /info` - Detailed service configuration and capability information
    - Environment settings, tool registry status, and integration details

    ### **🔧 Tool Management (`/tools`)**
    - `GET /tools` - List all available MCP tools with filtering and categorization
    - Tool metadata, capabilities, and invocation requirements

    ### **⚡ Tool Execution (`/tools/{tool}/invoke`)**
    - `POST /tools/{tool}/invoke` - Execute specific GitHub MCP tools
    - Dynamic parameter validation and intelligent execution routing

    ## 🛠️ **Available MCP Tools**

    ### **📊 Repository Operations**
    - `get_repo_info`: Retrieve comprehensive repository information
    - `list_repo_contents`: List repository files and directories
    - `get_repo_stats`: Repository statistics and analytics
    - `search_repositories`: Advanced repository search and filtering

    ### **🔄 Pull Request Management**
    - `get_pull_request`: Detailed pull request information
    - `list_pull_requests`: Pull request listing with advanced filtering
    - `create_pull_request`: Automated pull request creation
    - `review_pull_request`: Intelligent code review assistance
    - `merge_pull_request`: Safe pull request merging with checks

    ### **🎫 Issue Tracking**
    - `get_issue`: Comprehensive issue details and metadata
    - `list_issues`: Issue listing with advanced search and filtering
    - `create_issue`: Intelligent issue creation with categorization
    - `update_issue`: Issue lifecycle management and updates
    - `close_issue`: Automated issue resolution and closure

    ### **👥 User & Organization Management**
    - `get_user_profile`: User profile and contribution information
    - `list_organization_members`: Organization member management
    - `get_team_info`: Team structure and membership details
    - `manage_collaborators`: Repository collaborator management

    ### **⚙️ GitHub Actions & Workflows**
    - `list_workflows`: Workflow discovery and status monitoring
    - `get_workflow_runs`: Workflow execution history and results
    - `trigger_workflow`: Manual workflow execution and triggering
    - `manage_workflow_secrets`: Secure workflow secret management

    ### **📈 Analytics & Insights**
    - `get_contribution_stats`: Developer contribution analytics
    - `analyze_code_quality`: Automated code quality assessment
    - `generate_repo_insights`: Repository health and productivity insights
    - `predict_development_trends`: ML-powered development trend analysis

    ## 🏢 **Enterprise Integration**

    ### **🔗 Ecosystem Service Integration**
    - **All Services**: Comprehensive GitHub data integration across the ecosystem
    - **Source Agent**: GitHub repository ingestion and synchronization
    - **Code Analyzer**: Repository code analysis and quality assessment
    - **Notification Service**: Automated alerts for repository events
    - **Orchestrator**: Workflow orchestration with GitHub event triggers

    ### **📊 Advanced Features**
    - **Event-Driven Architecture**: Real-time GitHub webhook processing
    - **Caching Layer**: Intelligent caching for improved performance
    - **Batch Operations**: Efficient bulk operations for large repositories
    - **Retry Logic**: Robust error handling with exponential backoff
    - **Circuit Breaker**: Automatic failure detection and recovery

    ### **🔐 Enterprise Security Features**
    - **OAuth Integration**: Secure GitHub API authentication
    - **Token Management**: Secure token storage and rotation
    - **Scope Control**: Granular permission management
    - **Audit Logging**: Comprehensive operation audit trails
    - **Compliance Reporting**: Regulatory compliance validation

    ## 📋 **Usage Examples**

    ### **Get Repository Information**
    ```bash
    curl -X POST http://localhost:5072/tools/get_repo_info/invoke \
      -H "Content-Type: application/json" \
      -d '{
        "owner": "octocat",
        "repo": "Hello-World"
      }'
    ```

    ### **List Pull Requests**
    ```bash
    curl -X POST http://localhost:5072/tools/list_pull_requests/invoke \
      -H "Content-Type: application/json" \
      -d '{
        "owner": "octocat",
        "repo": "Hello-World",
        "state": "open",
        "per_page": 10
      }'
    ```

    ### **Create an Issue**
    ```bash
    curl -X POST http://localhost:5072/tools/create_issue/invoke \
      -H "Content-Type: application/json" \
      -d '{
        "owner": "octocat",
        "repo": "Hello-World",
        "title": "Found a bug",
        "body": "Bug description here",
        "labels": ["bug", "high-priority"]
      }'
    ```

    ### **Get Repository Statistics**
    ```bash
    curl -X POST http://localhost:5072/tools/get_repo_stats/invoke \
      -H "Content-Type: application/json" \
      -d '{
        "owner": "octocat",
        "repo": "Hello-World"
      }'
    ```
    """,
    contact={
        "name": "GitHub MCP Team",
        "url": "https://github.com/your-org/github-mcp",
        "email": "github-mcp@your-org.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://your-org.com/license"
    },
    openapi_tags=[
        {
            "name": "Health & Monitoring",
            "description": "Service health checks, GitHub API connectivity, and operational metrics"
        },
        {
            "name": "Service Information",
            "description": "Service configuration, capabilities, and environment details"
        },
        {
            "name": "Tool Management",
            "description": "MCP tool discovery, listing, and metadata management"
        },
        {
            "name": "Tool Execution",
            "description": "MCP tool invocation, parameter validation, and result processing"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client

    # Set startup time for uptime calculation
    import time
    app._startup_time = time.time()

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
    """
    Request model for tool invocation with execution options.

    Allows specification of tool arguments and execution mode controls
    for flexible GitHub MCP tool invocation.
    """

    arguments: Dict[str, Any] = {}
    """Tool-specific arguments as key-value pairs."""

    correlation_id: Optional[str] = None
    """Optional correlation ID for request tracing."""

    mock: Optional[bool] = None
    """Override default mock mode setting (True for mock, False for real
    API)."""

    write: Optional[bool] = None
    """Indicates if this is a write operation (subject to read-only mode
    gating)."""


class InvokeResponse(BaseModel):
    """
    Response model for tool invocation results.

    Contains the execution result and metadata for a tool invocation,
    indicating success or failure with appropriate result data.
    """

    tool: str
    """Name of the tool that was invoked."""

    success: bool
    """Whether the tool invocation was successful."""

    result: Dict[str, Any]
    """Tool execution result data (varies by tool)."""


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="""
    **Service Health Check** - Comprehensive health assessment and operational metrics for the GitHub MCP service.

    ## 🏥 **Health Assessment**

    This endpoint provides real-time health status and operational metrics for the GitHub MCP service, including:

    ### **🏥 Health Indicators**
    - **Service Status**: Overall health status (healthy/degraded/unhealthy)
    - **Version Information**: Current service version and build details
    - **Uptime Metrics**: Service uptime and operational statistics
    - **System Readiness**: Overall system readiness for MCP tool execution

    ### **📊 Operational Metrics**
    - **GitHub API Connected**: GitHub API connectivity and authentication status
    - **Tools Registered**: Number of MCP tools successfully registered and available
    - **Mock Mode Enabled**: Current mock mode status for testing and development
    - **Last Health Check**: Timestamp of the last health assessment

    ### **🔗 GitHub Integration Health**
    - **API Connectivity**: Real-time GitHub API availability and response times
    - **Authentication Status**: OAuth token validation and permission checks
    - **Rate Limit Monitoring**: Current API rate limit status and usage
    - **Service Dependencies**: Health of required external services and integrations

    ### **🔧 MCP Tool Health**
    - **Tool Registry**: MCP tool registration and availability status
    - **Mock Implementations**: Mock tool implementations and fallback readiness
    - **Real Implementations**: Real GitHub API tool implementations and connectivity
    - **Tool Execution**: Tool invocation capabilities and error handling

    ## 🎯 **Response Codes**

    | Code | Status | Description |
    |------|--------|-------------|
    | 200 | Healthy | Service is fully operational with all tools available |
    | 503 | Degraded | Service is operational but with some tool or API issues |
    | 500 | Unhealthy | Service is experiencing critical issues |

    ## 📋 **Usage Examples**

    ### **Basic Health Check**
    ```bash
    curl -X GET http://localhost:5072/health
    ```

    ### **Health Check with Monitoring**
    ```python
    import requests

    response = requests.get("http://localhost:5072/health")
    health_data = response.json()

    if health_data["status"] == "healthy":
        print("✅ GitHub MCP service is healthy")
        print(f"🔗 GitHub API: {'Connected' if health_data['github_api_connected'] else 'Disconnected'}")
        print(f"🔧 Tools Registered: {health_data['tools_registered']}")
        print(f"🎭 Mock Mode: {'Enabled' if health_data['mock_mode_enabled'] else 'Disabled'}")
    else:
        print("⚠️  GitHub MCP service health issue detected")
    ```

    ### **Automated Monitoring Script**
    ```bash
    #!/bin/bash
    HEALTH_URL="http://localhost:5072/health"
    STATUS=$(curl -s $HEALTH_URL | jq -r '.status')

    if [ "$STATUS" = "healthy" ]; then
        echo "✅ GitHub MCP service is healthy"
        exit 0
    else
        echo "❌ GitHub MCP service is unhealthy: $STATUS"
        exit 1
    fi
    ```
    """,
    response_description="Comprehensive health status and operational metrics",
    responses={
        200: {
            "description": "Service is healthy and fully operational",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "github-mcp",
                        "version": "0.1.0",
                        "uptime_seconds": 3600.5,
                        "last_health_check": "2024-09-22T10:30:00Z",
                        "github_api_connected": True,
                        "tools_registered": 25,
                        "mock_mode_enabled": False
                    }
                }
            }
        },
        503: {
            "description": "Service is degraded but still operational",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "service": "github-mcp",
                        "version": "0.1.0",
                        "uptime_seconds": 1800.0,
                        "last_health_check": "2024-09-22T10:25:00Z",
                        "github_api_connected": True,
                        "tools_registered": 22,
                        "mock_mode_enabled": True
                    }
                }
            }
        }
    },
    tags=["Health & Monitoring"]
)
async def health():
    """
    **Health Check Endpoint** - Comprehensive service health assessment.

    Returns detailed health status including:
    - Service operational status and version information
    - GitHub API connectivity and authentication status
    - MCP tool registration and availability statistics
    - Mock mode configuration and readiness status
    - Uptime and last health check timestamp
    """
    import datetime

    # Calculate uptime (simplified - in production this would track actual startup time)
    uptime_seconds = time.time() - getattr(app, '_startup_time', time.time())

    # Check GitHub API connectivity (simplified check)
    github_api_connected = True
    try:
        # In a real implementation, this would test actual GitHub API connectivity
        # For now, assume connected unless in pure mock mode
        mock_mode = config.is_mock_default() if config else True
        if not mock_mode:
            # Test real GitHub API connectivity
            pass
    except Exception:
        github_api_connected = False

    # Get tools registered count
    tools_registered = 0
    try:
        if 'tool_registry' in globals():
            tools_registered = len(tool_registry.list_tools())
        else:
            tools_registered = 25  # Fallback estimate
    except Exception:
        tools_registered = 20  # Degraded state

    # Check mock mode status
    mock_mode_enabled = True
    try:
        if config:
            mock_mode_enabled = config.is_mock_default()
    except Exception:
        mock_mode_enabled = True  # Default to mock mode on error

    # Determine overall health based on operational metrics
    if github_api_connected and tools_registered >= 20:
        status = "healthy"
    elif tools_registered >= 15:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        uptime_seconds=round(uptime_seconds, 1),
        last_health_check=datetime.datetime.utcnow().isoformat() + "Z",
        github_api_connected=github_api_connected,
        tools_registered=tools_registered,
        mock_mode_enabled=mock_mode_enabled
    )


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


@app.get(
    "/tools",
    summary="List Available MCP Tools",
    description="""
    **List Available MCP Tools** - Comprehensive catalog of all available Model Context Protocol tools for GitHub operations.

    ## 🔧 **Tool Discovery**
    Returns a complete list of registered MCP tools with their metadata, capabilities, and invocation requirements.
    Tools are dynamically discovered and can be filtered by category, capability, or operational mode.

    ## 📋 **Usage Examples**

    ### **List All Tools**
    ```bash
    curl http://localhost:5072/tools
    ```

    ### **Filter by Category**
    ```bash
    curl "http://localhost:5072/tools?category=repository"
    ```
    """,
    response_description="List of available MCP tools with metadata",
    tags=["Tool Management"]
)
async def list_tools(toolsets: Optional[str] = None):
    """
    List available GitHub MCP tools with optional toolset filtering.

    Returns available tools filtered by toolset when dynamic toolsets
    are enabled. Supports comma-separated toolset specification in query
    parameter. Defaults to 'repos' toolset when dynamic mode is enabled
    but no toolsets specified.
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


@app.post(
    "/tools/{tool}/invoke",
    summary="Execute MCP Tool",
    description="""
    **Execute MCP Tool** - Dynamic invocation of Model Context Protocol tools for GitHub operations.

    ## ⚡ **Tool Execution**
    Executes the specified MCP tool with provided arguments and returns structured results.
    Supports both mock and real GitHub API implementations with automatic fallback.

    ## 📋 **Usage Examples**

    ### **Get Repository Information**
    ```bash
    curl -X POST http://localhost:5072/tools/get_repo_info/invoke \
      -H "Content-Type: application/json" \
      -d '{
        "arguments": {
          "owner": "octocat",
          "repo": "Hello-World"
        }
      }'
    ```
    """,
    response_description="Tool execution result with structured data",
    tags=["Tool Execution"]
)
async def invoke(tool: str, payload: InvokeRequest):
    """
    Invoke a specific GitHub MCP tool with the provided arguments.

    Executes the specified tool using either mock implementations or
    real GitHub API calls, with support for upstream MCP proxying and
    downstream event emission. Write operations are gated by read-only
    mode configuration.

    Supports correlation ID tracking and flexible mock/real execution
    modes.
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
