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
from .modules.orchestrator_integration import orchestrator_integration
from .modules.ai_tool_selector import ai_tool_selector
from .modules.semantic_analyzer import semantic_tool_analyzer
from .modules.performance_optimizer import performance_optimizer

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


# ============================================================================
# PHASE 3: ORCHESTRATOR INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/orchestrator/register-tools")
async def register_tools_with_orchestrator():
    """PHASE 3: Register discovered tools with orchestrator for workflow use

    Retrieves tools from the registry and registers them with the orchestrator
    to enable dynamic workflow creation and execution.
    """
    try:
        # Get all tools from registry
        all_tools_data = await tool_registry_storage.get_all_tools()
        all_tools = []
        for service_tools in all_tools_data.values():
            all_tools.extend(service_tools)

        if not all_tools:
            return create_success_response(
                message="No tools found in registry to register",
                data={"registered_tools": 0, "message": "Run ecosystem discovery first"}
            )

        # Register tools with orchestrator
        registration_result = await orchestrator_integration.register_discovered_tools(all_tools)

        return create_success_response(
            message=f"Registered {registration_result['registered_tools']} tools with orchestrator",
            data=registration_result
        )

    except Exception as e:
        return handle_discovery_error(
            f"Tool registration failed: {str(e)}",
            {"error_type": "orchestrator_registration_error"}
        )


@app.post("/api/v1/workflows/create-ai")
async def create_ai_workflow(workflow_request: Dict[str, Any]):
    """PHASE 3: Create AI-powered workflow using intelligent tool selection

    Uses AI analysis to understand task requirements and automatically select
    optimal tools, then creates a dynamic workflow in the orchestrator.
    """
    try:
        task_description = workflow_request.get("task_description")
        workflow_name = workflow_request.get("name", f"ai_workflow_{len(str(task_description))}")

        if not task_description:
            return handle_discovery_error(
                "task_description is required",
                {"error_type": "missing_task_description"}
            )

        # Get all available tools from registry
        all_tools_data = await tool_registry_storage.get_all_tools()
        available_tools = []
        for service_tools in all_tools_data.values():
            available_tools.extend(service_tools)

        if not available_tools:
            return handle_discovery_error(
                "No tools available in registry. Run ecosystem discovery first.",
                {"error_type": "no_tools_available"}
            )

        # Use AI to select optimal tools
        tool_selection = await ai_tool_selector.select_tools_for_task(task_description, available_tools)

        if not tool_selection["success"]:
            return handle_discovery_error(
                f"AI tool selection failed: {tool_selection.get('error', 'Unknown error')}",
                {"error_type": "ai_selection_failed", "fallback_tools": tool_selection.get("fallback_tools", [])}
            )

        # Create workflow specification
        workflow_spec = {
            "name": workflow_name,
            "description": f"AI-generated workflow for: {task_description[:50]}...",
            "task_description": task_description,
            "selected_tools": [tool["name"] for tool in tool_selection["selected_tools"]],
            "ai_analysis": tool_selection["task_analysis"],
            "confidence_score": tool_selection["confidence_score"],
            "reasoning": tool_selection["reasoning"]
        }

        # Add workflow steps if AI generated a workflow
        if tool_selection.get("workflow"):
            workflow_spec["steps"] = tool_selection["workflow"]["steps"]
            workflow_spec["required_tools"] = tool_selection["workflow"]["required_tools"]

        # Create workflow in orchestrator
        workflow_result = await orchestrator_integration.create_dynamic_workflow(workflow_spec)

        if workflow_result["success"]:
            return create_success_response(
                message="AI-powered workflow created successfully",
                data={
                    "workflow": workflow_spec,
                    "orchestrator_result": workflow_result,
                    "tool_selection": tool_selection
                }
            )
        else:
            return handle_discovery_error(
                f"Workflow creation failed: {workflow_result.get('error', 'Unknown error')}",
                {"error_type": "workflow_creation_failed", "tool_selection": tool_selection}
            )

    except Exception as e:
        return handle_discovery_error(
            f"AI workflow creation failed: {str(e)}",
            {"error_type": "ai_workflow_error"}
        )


@app.post("/api/v1/workflows/execute-ai")
async def execute_ai_workflow(execution_request: Dict[str, Any]):
    """PHASE 3: Execute AI-generated workflow

    Executes a previously created AI-powered workflow with the provided parameters.
    """
    try:
        workflow_name = execution_request.get("workflow_name")
        parameters = execution_request.get("parameters", {})

        if not workflow_name:
            return handle_discovery_error(
                "workflow_name is required",
                {"error_type": "missing_workflow_name"}
            )

        # Execute workflow
        execution_result = await orchestrator_integration.execute_dynamic_workflow(workflow_name, parameters)

        if execution_result["success"]:
            return create_success_response(
                message=f"Workflow '{workflow_name}' executed successfully",
                data=execution_result
            )
        else:
            return handle_discovery_error(
                f"Workflow execution failed: {execution_result.get('error', 'Unknown error')}",
                {"error_type": "workflow_execution_failed"}
            )

    except Exception as e:
        return handle_discovery_error(
            f"Workflow execution failed: {str(e)}",
            {"error_type": "workflow_execution_error"}
        )


@app.get("/api/v1/orchestrator/status")
async def get_orchestrator_integration_status():
    """PHASE 3: Get orchestrator integration status

    Returns the current status of orchestrator integration, available workflows,
    and registered tools.
    """
    try:
        # Get orchestrator status
        orchestrator_status = await orchestrator_integration.get_orchestrator_status()

        # Get registered workflows
        workflows_result = await orchestrator_integration.list_registered_workflows()

        # Get registry stats
        registry_stats = await tool_registry_storage.get_registry_stats()

        integration_status = {
            "orchestrator": orchestrator_status,
            "workflows": workflows_result.get("workflows", []) if workflows_result.get("success") else [],
            "registry": registry_stats,
            "ai_selector": {
                "status": "available",
                "capabilities": ["task_analysis", "tool_selection", "workflow_generation"]
            }
        }

        return create_success_response(
            message="Orchestrator integration status retrieved",
            data=integration_status
        )

    except Exception as e:
        return handle_discovery_error(
            f"Integration status check failed: {str(e)}",
            {"error_type": "integration_status_error"}
        )


# ============================================================================
# PHASE 4: SEMANTIC ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/api/v1/analysis/semantic")
async def analyze_tools_semantically():
    """PHASE 4: Perform semantic analysis on discovered tools using LLM

    Analyzes tool purposes, categorizes them semantically, and identifies
    relationships between tools for better workflow generation.
    """
    try:
        # Get all tools from registry
        all_tools_data = await tool_registry_storage.get_all_tools()
        all_tools = []
        for service_tools in all_tools_data.values():
            all_tools.extend(service_tools)

        if not all_tools:
            return create_success_response(
                message="No tools found in registry for semantic analysis",
                data={"analyzed_tools": 0, "message": "Run ecosystem discovery first"}
            )

        print(f"🧠 Performing semantic analysis on {len(all_tools)} tools...")

        # Perform semantic analysis
        semantically_enhanced_tools = await semantic_tool_analyzer.enhance_tool_categorization(all_tools)

        # Analyze tool relationships
        relationship_analysis = await semantic_tool_analyzer.analyze_tool_relationships(semantically_enhanced_tools)

        # Store enhanced tools back in registry
        for tool in semantically_enhanced_tools:
            service_name = tool.get("service", "unknown")
            await tool_registry_storage.save_tools(service_name, [tool])

        return create_success_response(
            message=f"Semantic analysis completed for {len(semantically_enhanced_tools)} tools",
            data={
                "analyzed_tools": len(semantically_enhanced_tools),
                "relationship_analysis": relationship_analysis,
                "enhancement_summary": {
                    "tools_with_semantic_analysis": len([t for t in semantically_enhanced_tools if t.get("semantic_analysis")]),
                    "relationships_found": relationship_analysis.get("relationships_found", 0),
                    "workflow_suggestions": len(relationship_analysis.get("workflow_suggestions", []))
                }
            }
        )

    except Exception as e:
        return handle_discovery_error(
            f"Semantic analysis failed: {str(e)}",
            {"error_type": "semantic_analysis_error"}
        )


# ============================================================================
# PHASE 5: PERFORMANCE OPTIMIZATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/optimization/performance")
async def optimize_discovery_performance():
    """PHASE 5: Analyze and optimize discovery performance

    Analyzes discovery performance data and provides optimization recommendations
    for improved efficiency and reduced latency.
    """
    try:
        # Get recent discovery results
        discovery_results = await tool_registry_storage.load_discovery_results()

        if not discovery_results:
            return create_success_response(
                message="No discovery results found for optimization analysis",
                data={"optimizations": [], "message": "Run ecosystem discovery first"}
            )

        # Get the most recent discovery run
        latest_run_key = max(discovery_results.keys()) if discovery_results else None
        if not latest_run_key:
            return handle_discovery_error(
                "No valid discovery results found",
                {"error_type": "no_discovery_data"}
            )

        latest_results = discovery_results[latest_run_key]

        # Perform performance optimization analysis
        optimization_analysis = await performance_optimizer.optimize_discovery_workflow(latest_results)

        return create_success_response(
            message="Performance optimization analysis completed",
            data={
                "analysis": optimization_analysis,
                "discovery_run": latest_run_key,
                "recommendations_count": len(optimization_analysis.get("optimizations", {}).get("parallelization_opportunities", [])) +
                                       len(optimization_analysis.get("optimizations", {}).get("bottleneck_identification", [])) +
                                       len(optimization_analysis.get("optimizations", {}).get("resource_optimization", []))
            }
        )

    except Exception as e:
        return handle_discovery_error(
            f"Performance optimization failed: {str(e)}",
            {"error_type": "performance_optimization_error"}
        )


@app.post("/api/v1/optimization/dependencies")
async def analyze_tool_dependencies():
    """PHASE 5: Analyze tool dependencies and relationships

    Performs dependency analysis on discovered tools to identify optimization
    opportunities and workflow improvement suggestions.
    """
    try:
        # Get all tools from registry
        all_tools_data = await tool_registry_storage.get_all_tools()
        all_tools = []
        for service_tools in all_tools_data.values():
            all_tools.extend(service_tools)

        if not all_tools:
            return create_success_response(
                message="No tools found in registry for dependency analysis",
                data={"dependencies": [], "message": "Run ecosystem discovery first"}
            )

        # Analyze tool dependencies
        dependency_analysis = await performance_optimizer.analyze_tool_dependencies(all_tools)

        return create_success_response(
            message=f"Dependency analysis completed for {len(all_tools)} tools",
            data={
                "dependency_analysis": dependency_analysis,
                "optimization_opportunities": len(dependency_analysis.get("optimization_opportunities", [])),
                "independent_tools": len(dependency_analysis.get("independent_tools", []))
            }
        )

    except Exception as e:
        return handle_discovery_error(
            f"Dependency analysis failed: {str(e)}",
            {"error_type": "dependency_analysis_error"}
        )


@app.post("/api/v1/optimization/baseline")
async def create_performance_baseline():
    """PHASE 5: Create performance baseline for monitoring trends

    Establishes a performance baseline using recent discovery results
    for future trend analysis and optimization tracking.
    """
    try:
        # Get recent discovery results
        discovery_results = await tool_registry_storage.load_discovery_results()

        if not discovery_results:
            return handle_discovery_error(
                "No discovery results available for baseline creation",
                {"error_type": "no_baseline_data"}
            )

        # Use the most recent discovery run
        latest_run_key = max(discovery_results.keys())
        latest_results = discovery_results[latest_run_key]

        # Create performance baseline
        baseline = await performance_optimizer.create_performance_baseline(latest_results)

        return create_success_response(
            message="Performance baseline established successfully",
            data={
                "baseline": baseline,
                "based_on_discovery_run": latest_run_key,
                "metrics_tracked": list(baseline.keys())
            }
        )

    except Exception as e:
        return handle_discovery_error(
            f"Baseline creation failed: {str(e)}",
            {"error_type": "baseline_creation_error"}
        )


@app.get("/api/v1/optimization/status")
async def get_optimization_status():
    """PHASE 5: Get comprehensive optimization status

    Returns current optimization status including performance metrics,
    dependency analysis, and baseline comparisons.
    """
    try:
        # Get registry stats
        registry_stats = await tool_registry_storage.get_registry_stats()

        # Get recent discovery results for performance analysis
        discovery_results = await tool_registry_storage.load_discovery_results()
        latest_run = None
        if discovery_results:
            latest_run_key = max(discovery_results.keys())
            latest_run = discovery_results[latest_run_key]

        optimization_status = {
            "registry_health": registry_stats,
            "latest_discovery_run": latest_run_key if latest_run else None,
            "performance_summary": {},
            "optimization_readiness": {
                "has_discovery_data": bool(latest_run),
                "has_tools": registry_stats.get("total_tools", 0) > 0,
                "can_optimize_performance": bool(latest_run and latest_run.get("performance_metrics")),
                "can_analyze_dependencies": registry_stats.get("total_tools", 0) > 1
            }
        }

        # Add performance summary if available
        if latest_run:
            summary = latest_run.get("summary", {})
            optimization_status["performance_summary"] = {
                "services_tested": summary.get("services_healthy", 0),
                "tools_discovered": summary.get("tools_discovered", 0),
                "avg_tools_per_service": summary.get("avg_tools_per_service", 0)
            }

        return create_success_response(
            message="Optimization status retrieved successfully",
            data=optimization_status
        )

    except Exception as e:
        return handle_discovery_error(
            f"Optimization status retrieval failed: {str(e)}",
            {"error_type": "optimization_status_error"}
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

