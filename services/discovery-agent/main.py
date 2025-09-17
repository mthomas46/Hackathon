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

# ============================================================================
# PHASE IMPLEMENTATION MODULES - Enhanced capabilities
# ============================================================================
from .modules.tool_discovery import tool_discovery_service
from .modules.security_scanner import tool_security_scanner
from .modules.monitoring_service import discovery_monitoring_service
from .modules.tool_registry import tool_registry_storage
from .modules.discovery_handler import handle_tool_discovery_request

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

# ============================================================================
# PHASE SERVICE INITIALIZATION - Initialize enhanced phase services
# ============================================================================

def initialize_phase_services():
    """Initialize all phase services with proper integration"""
    # Configure tool discovery service with dependencies
    tool_discovery_service.set_security_scanner(tool_security_scanner)
    tool_discovery_service.set_monitoring_service(discovery_monitoring_service)
    tool_discovery_service.set_registry_storage(tool_registry_storage)

    print("✅ Phase services initialized:")
    print("  🔍 Tool Discovery Service: Configured")
    print("  🔒 Security Scanner: Configured")
    print("  📊 Monitoring Service: Configured")
    print("  💾 Registry Storage: Configured")

# Initialize services on startup
initialize_phase_services()


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
    return await handle_tool_discovery_request(req)


# ============================================================================
# PHASE 2: COMPREHENSIVE ECOSYSTEM DISCOVERY ENDPOINTS
# ============================================================================

@app.post("/api/v1/discovery/ecosystem")
async def discover_ecosystem_tools():
    """PHASE 2: Run comprehensive tool discovery across entire ecosystem

    Discovers LangGraph tools from all available services in the ecosystem.
    Performs health checks, OpenAPI analysis, tool extraction, security scanning,
    and monitoring for all services automatically.

    Returns comprehensive discovery results with tools, metrics, and validation.
    """
    try:
        # Define all available services in the ecosystem
        service_configs = {
            "analysis-service": {
                "url": "http://localhost:5020",
                "openapi_path": "/openapi.json",
                "category": "analysis",
                "priority": 1
            },
            "source-agent": {
                "url": "http://localhost:5000",
                "openapi_path": "/openapi.json",
                "category": "integration",
                "priority": 1
            },
            "memory-agent": {
                "url": "http://localhost:5040",
                "openapi_path": "/openapi.json",
                "category": "storage",
                "priority": 1
            },
            "prompt_store": {
                "url": "http://localhost:5110",
                "openapi_path": "/openapi.json",
                "category": "ai",
                "priority": 1
            },
            "github-mcp": {
                "url": "http://localhost:5072",
                "openapi_path": "/openapi.json",
                "category": "integration",
                "priority": 2
            },
            "interpreter": {
                "url": "http://localhost:5120",
                "openapi_path": "/openapi.json",
                "category": "execution",
                "priority": 2
            },
            "secure-analyzer": {
                "url": "http://localhost:5070",
                "openapi_path": "/openapi.json",
                "category": "security",
                "priority": 1
            },
            "summarizer-hub": {
                "url": "http://localhost:5160",
                "openapi_path": "/openapi.json",
                "category": "ai",
                "priority": 2
            },
            "doc_store": {
                "url": "http://localhost:5087",
                "openapi_path": "/openapi.json",
                "category": "storage",
                "priority": 1
            },
            "orchestrator": {
                "url": "http://localhost:5099",
                "openapi_path": "/openapi.json",
                "category": "orchestration",
                "priority": 1
            },
            "architecture-digitizer": {
                "url": "http://localhost:5105",
                "openapi_path": "/openapi.json",
                "category": "analysis",
                "priority": 3
            },
            "log-collector": {
                "url": "http://localhost:5080",
                "openapi_path": "/openapi.json",
                "category": "monitoring",
                "priority": 2
            },
            "notification-service": {
                "url": "http://localhost:5095",
                "openapi_path": "/openapi.json",
                "category": "communication",
                "priority": 3
            },
            "code-analyzer": {
                "url": "http://localhost:5065",
                "openapi_path": "/openapi.json",
                "category": "analysis",
                "priority": 3
            }
        }

        # Run comprehensive discovery
        results = await tool_discovery_service.discover_ecosystem_tools(service_configs)

        # Monitor discovery performance
        await tool_discovery_service.monitor_discovery_performance(results)

        return create_success_response(
            message="Ecosystem discovery completed successfully",
            data=results
        )

    except Exception as e:
        return handle_discovery_error(
            f"Ecosystem discovery failed: {str(e)}",
            {"error_type": "ecosystem_discovery_error"}
        )


# ============================================================================
# PHASE 5: REGISTRY AND MONITORING ENDPOINTS
# ============================================================================

@app.get("/api/v1/registry/tools")
async def get_registry_tools(service: Optional[str] = None, category: Optional[str] = None):
    """PHASE 5: Retrieve tools from persistent registry

    Query the persistent tool registry with optional filtering by service or category.
    Returns all discovered tools that have been stored in the registry.
    """
    try:
        if service:
            # Get tools for specific service
            tools = await tool_registry_storage.get_tools_for_service(service)
        else:
            # Get all tools
            all_tools = await tool_registry_storage.get_all_tools()
            tools = []
            for service_tools in all_tools.values():
                tools.extend(service_tools)

        # Apply category filter if specified
        if category:
            tools = [t for t in tools if t.get("category") == category]

        return create_success_response(
            message=f"Retrieved {len(tools)} tools from registry",
            data={
                "tools": tools,
                "count": len(tools),
                "filters": {
                    "service": service,
                    "category": category
                }
            }
        )

    except Exception as e:
        return handle_discovery_error(
            f"Registry query failed: {str(e)}",
            {"error_type": "registry_query_error"}
        )


@app.get("/api/v1/monitoring/dashboard")
async def get_monitoring_dashboard():
    """PHASE 5: Get comprehensive monitoring dashboard

    Returns real-time monitoring data including discovery performance,
    security scan results, system health, and recommendations.
    """
    try:
        dashboard = await discovery_monitoring_service.create_monitoring_dashboard()

        return create_success_response(
            message="Monitoring dashboard generated successfully",
            data=dashboard
        )

    except Exception as e:
        return handle_discovery_error(
            f"Dashboard generation failed: {str(e)}",
            {"error_type": "dashboard_error"}
        )


@app.get("/api/v1/registry/stats")
async def get_registry_stats():
    """PHASE 5: Get comprehensive registry statistics

    Returns detailed statistics about the tool registry including
    service breakdown, tool categories, and performance metrics.
    """
    try:
        stats = await tool_registry_storage.get_registry_stats()

        return create_success_response(
            message="Registry statistics retrieved successfully",
            data=stats
        )

    except Exception as e:
        return handle_discovery_error(
            f"Registry stats failed: {str(e)}",
            {"error_type": "stats_error"}
        )


if __name__ == "__main__":
    """Run the Discovery Agent service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )

