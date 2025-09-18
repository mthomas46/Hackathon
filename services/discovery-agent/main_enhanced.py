"""Enhanced Discovery Agent Service with All Phase Features

This enhanced version includes all implemented phases:
- Phase 1: CLI Integration (existing)
- Phase 2: Comprehensive Ecosystem Discovery 
- Phase 3: Orchestrator Integration
- Phase 4: Security Scanning
- Phase 5: Monitoring and Observability
- Additional: Semantic Analysis, Performance Optimization, AI Tool Selection

New endpoints:
- POST /discover-ecosystem: Bulk discovery for entire ecosystem
- GET /registry/tools: Query discovered tools registry
- GET /registry/stats: Registry statistics
- POST /security/scan-tools: Security scan discovered tools
- GET /monitoring/dashboard: Monitoring dashboard
- POST /ai/select-tools: AI-powered tool selection
- POST /semantic/analyze-tools: Semantic analysis of tools
- GET /performance/optimize: Performance optimization analysis
- POST /orchestrator/register-tools: Register tools with orchestrator
- POST /orchestrator/create-workflow: Create AI workflows
"""

import os
import re
import httpx
import asyncio
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.responses.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import setup_common_middleware, attach_self_register

# ============================================================================
# LOCAL MODULES - Enhanced feature modules
# ============================================================================
from .modules.tool_discovery import ToolDiscoveryService
from .modules.tool_registry import ToolRegistryStorage
from .modules.monitoring_service import DiscoveryAgentMonitoring
from .modules.security_scanner import ToolSecurityScanner
from .modules.ai_tool_selector import AIToolSelector
from .modules.semantic_analyzer import SemanticToolAnalyzer
from .modules.performance_optimizer import PerformanceOptimizer
from .modules.orchestrator_integration import OrchestratorIntegration

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class DiscoverRequest(BaseModel):
    """Request model for single service discovery"""
    name: str = Field(..., description="Service name")
    base_url: str = Field(..., description="Base URL of the service") 
    openapi_url: Optional[str] = Field(None, description="OpenAPI spec URL")
    spec: Optional[Dict[str, Any]] = Field(None, description="Inline OpenAPI spec")
    dry_run: bool = Field(False, description="Dry run mode for testing")

class BulkDiscoverRequest(BaseModel):
    """Request model for bulk service discovery"""
    services: List[Dict[str, str]] = Field(..., description="List of services to discover")
    auto_detect: bool = Field(False, description="Auto-detect services in Docker network")
    include_health_check: bool = Field(True, description="Check service health before discovery")
    dry_run: bool = Field(False, description="Dry run mode for testing")

class SecurityScanRequest(BaseModel):
    """Request model for security scanning"""
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Specific tools to scan")
    scan_all_discovered: bool = Field(True, description="Scan all discovered tools")
    include_recommendations: bool = Field(True, description="Include security recommendations")

class AIToolSelectionRequest(BaseModel):
    """Request model for AI tool selection"""
    task_description: str = Field(..., description="Description of the task")
    available_tools: Optional[List[Dict[str, Any]]] = Field(None, description="Available tools")
    use_discovered_tools: bool = Field(True, description="Use tools from registry")
    max_tools: int = Field(5, description="Maximum number of tools to select")

class SemanticAnalysisRequest(BaseModel):
    """Request model for semantic analysis"""
    tools: Optional[List[Dict[str, Any]]] = Field(None, description="Tools to analyze")
    analyze_all_discovered: bool = Field(True, description="Analyze all discovered tools")
    include_relationships: bool = Field(True, description="Include tool relationships")

class WorkflowCreationRequest(BaseModel):
    """Request model for AI workflow creation"""
    workflow_description: str = Field(..., description="Description of desired workflow")
    available_tools: Optional[List[Dict[str, Any]]] = Field(None, description="Available tools")
    workflow_type: str = Field("general", description="Type of workflow")

# ============================================================================
# ENHANCED DISCOVERY AGENT APPLICATION
# ============================================================================

app = FastAPI(
    title="Enhanced Discovery Agent",
    description="Advanced service discovery with ecosystem integration, security scanning, and AI-powered features",
    version="2.0.0"
)

# Initialize enhanced modules
tool_discovery = ToolDiscoveryService()
registry_storage = ToolRegistryStorage()
monitoring = DiscoveryAgentMonitoring()
security_scanner = ToolSecurityScanner()
ai_selector = AIToolSelector()
semantic_analyzer = SemanticToolAnalyzer()
performance_optimizer = PerformanceOptimizer()
orchestrator_integration = OrchestratorIntegration()

# Setup middleware and health endpoints
setup_common_middleware(app)
register_health_endpoints(app, ServiceNames.DISCOVERY_AGENT)

# ============================================================================
# ENHANCED DISCOVERY ENDPOINTS
# ============================================================================

def normalize_service_url(url: str, service_name: str = None) -> str:
    """Normalize service URL to use Docker internal networking when appropriate"""
    if not url:
        return url
        
    # If it's a localhost URL and we have a service name, try Docker internal URL
    if "localhost" in url or "127.0.0.1" in url:
        if service_name:
            # Extract port from URL
            port_match = re.search(r':(\d+)', url)
            if port_match:
                port = port_match.group(1)
                return f"http://{service_name}:{port}"
    
    return url

@app.post("/discover")
async def discover_service(request: DiscoverRequest):
    """Enhanced single service discovery with network URL normalization"""
    try:
        # Normalize URLs for Docker networking
        normalized_base_url = normalize_service_url(request.base_url, request.name)
        normalized_openapi_url = normalize_service_url(request.openapi_url, request.name) if request.openapi_url else None
        
        # Log the discovery attempt
        monitoring.log_discovery_event("service_discovery_started", {
            "service_name": request.name,
            "original_url": request.base_url,
            "normalized_url": normalized_base_url,
            "dry_run": request.dry_run
        })
        
        # Perform discovery using normalized URLs
        discovery_request = DiscoverRequest(
            name=request.name,
            base_url=normalized_base_url,
            openapi_url=normalized_openapi_url,
            spec=request.spec,
            dry_run=request.dry_run
        )
        
        # Use existing discovery logic with enhanced error handling
        if not discovery_request.openapi_url and not discovery_request.spec:
            # Try common OpenAPI endpoints
            common_paths = ["/openapi.json", "/docs/openapi.json", "/api/openapi.json"]
            for path in common_paths:
                test_url = f"{normalized_base_url}{path}"
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(test_url)
                        if response.status_code == 200:
                            discovery_request.openapi_url = test_url
                            break
                except:
                    continue
        
        if not discovery_request.openapi_url and not discovery_request.spec:
            raise HTTPException(
                status_code=400,
                detail="Either openapi_url or spec must be provided, and auto-detection failed"
            )
        
        # Fetch and parse OpenAPI spec
        if discovery_request.openapi_url:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(discovery_request.openapi_url)
                response.raise_for_status()
                spec = response.json()
        else:
            spec = discovery_request.spec
        
        # Extract endpoints and tools
        endpoints = extract_endpoints_from_spec(spec)
        tools = tool_discovery.generate_langraph_tools(endpoints, discovery_request.name)
        
        # Store in registry if not dry run
        if not discovery_request.dry_run:
            discovery_result = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "service_name": discovery_request.name,
                "base_url": normalized_base_url,
                "openapi_url": discovery_request.openapi_url,
                "endpoints_discovered": len(endpoints),
                "tools_generated": len(tools),
                "endpoints": endpoints,
                "tools": tools
            }
            registry_storage.save_discovery_results({
                "timestamp": discovery_result["timestamp"],
                "services_tested": 1,
                "total_tools_discovered": len(tools),
                "services": {
                    discovery_request.name: {
                        "base_url": normalized_base_url,
                        "endpoints_discovered": len(endpoints),
                        "tools": tools
                    }
                }
            })
        
        # Log success
        monitoring.log_discovery_event("service_discovery_completed", {
            "service_name": discovery_request.name,
            "endpoints_found": len(endpoints),
            "tools_generated": len(tools),
            "success": True
        })
        
        return create_success_response({
            "service_name": discovery_request.name,
            "base_url": normalized_base_url,
            "endpoints_discovered": len(endpoints),
            "tools_generated": len(tools),
            "endpoints": endpoints,
            "tools": tools,
            "registry_updated": not discovery_request.dry_run
        })
        
    except httpx.HTTPError as e:
        error_msg = f"Failed to fetch OpenAPI spec from {discovery_request.openapi_url if hasattr(discovery_request, 'openapi_url') else 'unknown URL'}"
        monitoring.log_discovery_event("service_discovery_failed", {
            "service_name": request.name,
            "error": str(e),
            "error_type": "http_error"
        })
        return create_error_response(
            message="Failed to discover endpoints",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={
                "error": error_msg,
                "service": ServiceNames.DISCOVERY_AGENT,
                "service_name": request.name
            }
        )
    except Exception as e:
        monitoring.log_discovery_event("service_discovery_failed", {
            "service_name": request.name,
            "error": str(e),
            "error_type": "general_error"
        })
        return create_error_response(
            message="Discovery failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={
                "error": str(e),
                "service": ServiceNames.DISCOVERY_AGENT,
                "service_name": request.name
            }
        )

@app.post("/discover-ecosystem")
async def discover_ecosystem(request: BulkDiscoverRequest):
    """Comprehensive ecosystem discovery for multiple services"""
    try:
        monitoring.log_discovery_event("ecosystem_discovery_started", {
            "auto_detect": request.auto_detect,
            "services_count": len(request.services),
            "dry_run": request.dry_run
        })
        
        services_to_discover = []
        
        # Auto-detect services if requested
        if request.auto_detect:
            # Known services in Docker network
            known_services = [
                {"name": "orchestrator", "port": "5099"},
                {"name": "doc_store", "port": "5050"},
                {"name": "prompt_store", "port": "5051"},
                {"name": "analysis_service", "port": "5052"},
                {"name": "source_agent", "port": "5053"},
                {"name": "github_mcp", "port": "5054"},
                {"name": "bedrock_proxy", "port": "5055"},
                {"name": "interpreter", "port": "5056"},
                {"name": "cli", "port": "5057"},
                {"name": "memory_agent", "port": "5058"},
                {"name": "notification_service", "port": "5059"},
                {"name": "code_analyzer", "port": "5060"},
                {"name": "secure_analyzer", "port": "5061"},
                {"name": "log_collector", "port": "5062"},
                {"name": "frontend", "port": "5063"},
                {"name": "summarizer_hub", "port": "5064"},
                {"name": "architecture_digitizer", "port": "5065"}
            ]
            
            for service in known_services:
                if request.include_health_check:
                    # Check if service is healthy before adding
                    try:
                        health_url = f"http://{service['name']}:{service['port']}/health"
                        async with httpx.AsyncClient(timeout=5.0) as client:
                            response = await client.get(health_url)
                            if response.status_code == 200:
                                services_to_discover.append({
                                    "name": service["name"],
                                    "base_url": f"http://{service['name']}:{service['port']}",
                                    "openapi_url": f"http://{service['name']}:{service['port']}/openapi.json"
                                })
                    except:
                        continue
                else:
                    services_to_discover.append({
                        "name": service["name"],
                        "base_url": f"http://{service['name']}:{service['port']}",
                        "openapi_url": f"http://{service['name']}:{service['port']}/openapi.json"
                    })
        
        # Add explicitly requested services
        for service in request.services:
            service_data = {
                "name": service.get("name"),
                "base_url": normalize_service_url(service.get("base_url"), service.get("name")),
            }
            if "openapi_url" in service:
                service_data["openapi_url"] = normalize_service_url(service["openapi_url"], service.get("name"))
            services_to_discover.append(service_data)
        
        # Discover all services
        discovery_results = {}
        total_endpoints = 0
        total_tools = 0
        successful_discoveries = 0
        failed_discoveries = []
        
        for service_data in services_to_discover:
            try:
                discover_request = DiscoverRequest(
                    name=service_data["name"],
                    base_url=service_data["base_url"],
                    openapi_url=service_data.get("openapi_url"),
                    dry_run=request.dry_run
                )
                
                # Call individual discovery endpoint
                result = await discover_service(discover_request)
                
                if result.get("success", False):
                    service_result = result["data"]
                    discovery_results[service_data["name"]] = service_result
                    total_endpoints += service_result.get("endpoints_discovered", 0)
                    total_tools += service_result.get("tools_generated", 0)
                    successful_discoveries += 1
                else:
                    failed_discoveries.append({
                        "service": service_data["name"],
                        "error": result.get("message", "Unknown error")
                    })
                    
            except Exception as e:
                failed_discoveries.append({
                    "service": service_data["name"],
                    "error": str(e)
                })
        
        # Save ecosystem discovery results
        if not request.dry_run and successful_discoveries > 0:
            ecosystem_result = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "services_tested": len(services_to_discover),
                "successful_discoveries": successful_discoveries,
                "failed_discoveries": len(failed_discoveries),
                "total_tools_discovered": total_tools,
                "services": {name: {"tools": result.get("tools", [])} for name, result in discovery_results.items()}
            }
            registry_storage.save_discovery_results(ecosystem_result)
        
        monitoring.log_discovery_event("ecosystem_discovery_completed", {
            "total_services": len(services_to_discover),
            "successful": successful_discoveries,
            "failed": len(failed_discoveries),
            "total_tools": total_tools
        })
        
        return create_success_response({
            "ecosystem_discovery": {
                "services_discovered": successful_discoveries,
                "total_services_attempted": len(services_to_discover),
                "total_endpoints_discovered": total_endpoints,
                "total_tools_generated": total_tools,
                "failed_discoveries": failed_discoveries,
                "discovery_results": discovery_results,
                "registry_updated": not request.dry_run
            }
        })
        
    except Exception as e:
        monitoring.log_discovery_event("ecosystem_discovery_failed", {
            "error": str(e),
            "error_type": "general_error"
        })
        return create_error_response(
            message="Ecosystem discovery failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e), "service": ServiceNames.DISCOVERY_AGENT}
        )

# ============================================================================
# REGISTRY MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/registry/tools")
async def get_registry_tools(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    category: Optional[str] = Query(None, description="Filter by tool category"),
    limit: int = Query(100, description="Maximum number of tools to return")
):
    """Query discovered tools from registry"""
    try:
        tools = registry_storage.query_tools(
            service_name=service_name,
            category=category,
            limit=limit
        )
        
        return create_success_response({
            "tools": tools,
            "total_found": len(tools),
            "filters_applied": {
                "service_name": service_name,
                "category": category,
                "limit": limit
            }
        })
        
    except Exception as e:
        return create_error_response(
            message="Failed to query registry tools",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

@app.get("/registry/stats")
async def get_registry_stats():
    """Get registry statistics and summary"""
    try:
        stats = registry_storage.get_registry_stats()
        return create_success_response(stats)
        
    except Exception as e:
        return create_error_response(
            message="Failed to get registry stats",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

# ============================================================================
# SECURITY SCANNING ENDPOINTS
# ============================================================================

@app.post("/security/scan-tools")
async def scan_tools_security(request: SecurityScanRequest):
    """Security scan discovered tools using secure-analyzer"""
    try:
        tools_to_scan = []
        
        if request.scan_all_discovered:
            # Get all tools from registry
            tools_to_scan = registry_storage.query_tools()
        elif request.tools:
            tools_to_scan = request.tools
        
        if not tools_to_scan:
            return create_error_response(
                message="No tools found to scan",
                error_code=ErrorCodes.VALIDATION_ERROR,
                details={"message": "Specify tools or enable scan_all_discovered"}
            )
        
        # Perform security scanning
        scan_results = await security_scanner.scan_discovered_tools(
            tools_to_scan,
            include_recommendations=request.include_recommendations
        )
        
        monitoring.log_discovery_event("security_scan_completed", {
            "tools_scanned": len(tools_to_scan),
            "high_risk_tools": len([r for r in scan_results if r.get("overall_risk") == "HIGH"]),
            "scan_timestamp": datetime.utcnow().isoformat()
        })
        
        return create_success_response({
            "security_scan": {
                "tools_scanned": len(tools_to_scan),
                "scan_results": scan_results,
                "summary": {
                    "high_risk": len([r for r in scan_results if r.get("overall_risk") == "HIGH"]),
                    "medium_risk": len([r for r in scan_results if r.get("overall_risk") == "MEDIUM"]),
                    "low_risk": len([r for r in scan_results if r.get("overall_risk") == "LOW"])
                }
            }
        })
        
    except Exception as e:
        return create_error_response(
            message="Security scanning failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

# ============================================================================
# MONITORING AND OBSERVABILITY ENDPOINTS
# ============================================================================

@app.get("/monitoring/dashboard")
async def get_monitoring_dashboard():
    """Get monitoring dashboard for discovery operations"""
    try:
        dashboard = monitoring.create_monitoring_dashboard()
        return create_success_response(dashboard)
        
    except Exception as e:
        return create_error_response(
            message="Failed to create monitoring dashboard",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

@app.get("/monitoring/events")
async def get_monitoring_events(
    limit: int = Query(50, description="Number of events to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type")
):
    """Get discovery events from monitoring"""
    try:
        events = monitoring.get_recent_events(limit=limit, event_type=event_type)
        return create_success_response({
            "events": events,
            "total_returned": len(events),
            "filters": {"limit": limit, "event_type": event_type}
        })
        
    except Exception as e:
        return create_error_response(
            message="Failed to get monitoring events",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

# ============================================================================
# AI-POWERED TOOL SELECTION ENDPOINTS
# ============================================================================

@app.post("/ai/select-tools")
async def ai_select_tools(request: AIToolSelectionRequest):
    """AI-powered tool selection for tasks"""
    try:
        available_tools = []
        
        if request.use_discovered_tools:
            available_tools = registry_storage.query_tools()
        
        if request.available_tools:
            available_tools.extend(request.available_tools)
        
        if not available_tools:
            return create_error_response(
                message="No tools available for selection",
                error_code=ErrorCodes.VALIDATION_ERROR,
                details={"message": "Enable use_discovered_tools or provide available_tools"}
            )
        
        # AI tool selection
        selection_result = await ai_selector.select_tools_for_task(
            task_description=request.task_description,
            available_tools=available_tools,
            max_tools=request.max_tools
        )
        
        monitoring.log_discovery_event("ai_tool_selection", {
            "task_description": request.task_description,
            "tools_available": len(available_tools),
            "tools_selected": len(selection_result.get("selected_tools", []))
        })
        
        return create_success_response(selection_result)
        
    except Exception as e:
        return create_error_response(
            message="AI tool selection failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

@app.post("/ai/create-workflow")
async def ai_create_workflow(request: WorkflowCreationRequest):
    """Create AI-powered workflow from description"""
    try:
        available_tools = []
        
        if request.available_tools:
            available_tools = request.available_tools
        else:
            available_tools = registry_storage.query_tools()
        
        # Create workflow
        workflow_result = await ai_selector.create_multi_service_workflow(
            description=request.workflow_description,
            available_tools=available_tools,
            workflow_type=request.workflow_type
        )
        
        monitoring.log_discovery_event("ai_workflow_creation", {
            "workflow_description": request.workflow_description,
            "workflow_type": request.workflow_type,
            "tools_used": len(workflow_result.get("selected_tools", []))
        })
        
        return create_success_response(workflow_result)
        
    except Exception as e:
        return create_error_response(
            message="AI workflow creation failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

# ============================================================================
# SEMANTIC ANALYSIS ENDPOINTS
# ============================================================================

@app.post("/semantic/analyze-tools")
async def semantic_analyze_tools(request: SemanticAnalysisRequest):
    """Semantic analysis of discovered tools"""
    try:
        tools_to_analyze = []
        
        if request.analyze_all_discovered:
            tools_to_analyze = registry_storage.query_tools()
        elif request.tools:
            tools_to_analyze = request.tools
        
        if not tools_to_analyze:
            return create_error_response(
                message="No tools found to analyze",
                error_code=ErrorCodes.VALIDATION_ERROR,
                details={"message": "Specify tools or enable analyze_all_discovered"}
            )
        
        # Semantic analysis
        analysis_result = await semantic_analyzer.analyze_tool_ecosystem(
            tools=tools_to_analyze,
            include_relationships=request.include_relationships
        )
        
        monitoring.log_discovery_event("semantic_analysis", {
            "tools_analyzed": len(tools_to_analyze),
            "categories_found": len(analysis_result.get("categories", {})),
            "relationships_found": len(analysis_result.get("relationships", []))
        })
        
        return create_success_response(analysis_result)
        
    except Exception as e:
        return create_error_response(
            message="Semantic analysis failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

# ============================================================================
# PERFORMANCE OPTIMIZATION ENDPOINTS
# ============================================================================

@app.get("/performance/optimize")
async def optimize_performance():
    """Get performance optimization recommendations"""
    try:
        # Get current discovery data for analysis
        registry_stats = registry_storage.get_registry_stats()
        
        optimization_result = await performance_optimizer.optimize_discovery_workflow({
            "services_tested": registry_stats.get("total_services", 0),
            "total_tools_discovered": registry_stats.get("total_tools", 0),
            "performance_metrics": []  # Would be populated from real metrics
        })
        
        return create_success_response(optimization_result)
        
    except Exception as e:
        return create_error_response(
            message="Performance optimization failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

@app.get("/performance/dependencies")
async def analyze_tool_dependencies():
    """Analyze dependencies between discovered tools"""
    try:
        tools = registry_storage.query_tools()
        dependency_analysis = await performance_optimizer.analyze_tool_dependencies(tools)
        
        return create_success_response(dependency_analysis)
        
    except Exception as e:
        return create_error_response(
            message="Dependency analysis failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

# ============================================================================
# ORCHESTRATOR INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/orchestrator/register-tools")
async def register_tools_with_orchestrator(
    service_names: Optional[List[str]] = Body(None, description="Specific services to register"),
    register_all: bool = Body(True, description="Register all discovered tools")
):
    """Register discovered tools with orchestrator"""
    try:
        tools_to_register = []
        
        if register_all:
            tools_to_register = registry_storage.query_tools()
        elif service_names:
            for service_name in service_names:
                tools_to_register.extend(registry_storage.query_tools(service_name=service_name))
        
        if not tools_to_register:
            return create_error_response(
                message="No tools found to register",
                error_code=ErrorCodes.VALIDATION_ERROR,
                details={"message": "Specify service_names or enable register_all"}
            )
        
        # Register with orchestrator
        registration_result = await orchestrator_integration.register_discovered_tools(tools_to_register)
        
        monitoring.log_discovery_event("orchestrator_registration", {
            "tools_registered": len(tools_to_register),
            "registration_successful": registration_result.get("success", False)
        })
        
        return create_success_response(registration_result)
        
    except Exception as e:
        return create_error_response(
            message="Orchestrator registration failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

@app.post("/orchestrator/create-workflow") 
async def create_orchestrator_workflow(request: WorkflowCreationRequest):
    """Create workflow in orchestrator using discovered tools"""
    try:
        available_tools = registry_storage.query_tools()
        
        workflow_result = await orchestrator_integration.create_ai_workflow(
            description=request.workflow_description,
            available_tools=available_tools,
            workflow_type=request.workflow_type
        )
        
        monitoring.log_discovery_event("orchestrator_workflow_creation", {
            "workflow_description": request.workflow_description,
            "tools_available": len(available_tools),
            "workflow_created": workflow_result.get("success", False)
        })
        
        return create_success_response(workflow_result)
        
    except Exception as e:
        return create_error_response(
            message="Orchestrator workflow creation failed",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )

# ============================================================================
# UTILITY FUNCTIONS (from original shared_utils)
# ============================================================================

def extract_endpoints_from_spec(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract endpoints from OpenAPI specification"""
    endpoints = []
    paths = spec.get("paths", {})
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": details.get("operationId"),
                    "summary": details.get("summary"),
                    "description": details.get("description"),
                    "tags": details.get("tags", []),
                    "parameters": details.get("parameters", []),
                    "request_body": details.get("requestBody"),
                    "responses": details.get("responses", {})
                }
                endpoints.append(endpoint)
    
    return endpoints

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize enhanced discovery agent"""
    monitoring.log_discovery_event("service_startup", {
        "version": "2.0.0",
        "features": [
            "bulk_discovery",
            "security_scanning", 
            "ai_tool_selection",
            "semantic_analysis",
            "performance_optimization",
            "orchestrator_integration",
            "persistent_registry",
            "monitoring_dashboard"
        ]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5045)
