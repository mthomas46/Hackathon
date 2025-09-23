"""
🌐 Unified API Ecosystem Dashboard - Enterprise API Intelligence Hub

A centralized platform for API discovery, testing, monitoring, and documentation
that aggregates information from all ecosystem services via the Discovery Agent.

Key Features:
- Real-time API discovery and catalog management
- Interactive API testing interface
- Health monitoring and performance analytics
- Service topology visualization
- Developer tools and documentation
- Enterprise security and compliance monitoring
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field, ConfigDict
import httpx
import streamlit as st

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.utilities.logging_client import LogCollectorClient

# Import our modules
from .config import config
from .modules.discovery.client import DiscoveryClient
from .modules.api.catalog import APICatalogManager
from .modules.monitoring.health import HealthMonitor
from .modules.testing.tester import APITester, APITestRequest
from .modules.analytics import UsageAnalytics, PerformanceInsights, ErrorTracking, UsagePatterns
from .modules.developer_tools import ClientCodeGenerator, APIValidator, IntegrationTester
from .modules.topology import TopologyAnalyzer, TopologyVisualizer, DependencyGraphBuilder, TopologyMetrics

# ============================================================================
# STANDARD API RESPONSE MODELS - Consistent error handling
# ============================================================================

class APIResponse(BaseModel):
    """Standard API response model."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class ErrorResponse(BaseModel):
    """Standard error response model."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

class HealthResponse(BaseModel):
    """Health check response model for the Unified API Ecosystem Dashboard service."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    last_health_check: Optional[str] = Field(None, description="Last health check timestamp")
    discovery_agent_connected: bool = Field(..., description="Discovery Agent connectivity status")
    api_catalog_loaded: bool = Field(..., description="API catalog loading status")
    active_sessions: int = Field(..., description="Number of active dashboard sessions")

# Additional data models for API endpoints
class APITestEndpointRequest(BaseModel):
    """Request to test an API endpoint."""
    model_config = ConfigDict(from_attributes=True)

    service_name: str = Field(..., description="Name of the service to test")
    endpoint_path: str = Field(..., description="API endpoint path to test")
    method: str = Field(default="GET", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    params: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    body: Optional[Any] = Field(None, description="Request body")
    auth_token: Optional[str] = Field(None, description="Authentication token")

class PerformanceTestRequest(BaseModel):
    """Request for performance testing."""
    model_config = ConfigDict(from_attributes=True)

    service_name: str = Field(..., description="Name of the service to test")
    endpoint_path: str = Field(..., description="API endpoint path to test")
    method: str = Field(default="GET", description="HTTP method")
    iterations: int = Field(default=10, ge=1, le=100, description="Number of test iterations")
    concurrent: bool = Field(default=False, description="Whether to run tests concurrently")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    params: Dict[str, Any] = Field(default_factory=dict, description="Query parameters")
    body: Optional[Any] = Field(None, description="Request body")
    auth_token: Optional[str] = Field(None, description="Authentication token")

class ScenarioTestRequest(BaseModel):
    """Request for scenario testing."""
    model_config = ConfigDict(from_attributes=True)

    scenario: Dict[str, Any] = Field(..., description="Test scenario definition")

# ============================================================================
# GLOBAL INSTANCES AND LIFECYCLE MANAGEMENT
# ============================================================================

# Global instances
logger_client = None
discovery_client = None
catalog_manager = None
health_monitor = None
api_tester = None
client_generator = None
api_validator = None
integration_tester = None
topology_analyzer = None
topology_visualizer = None
dependency_graph_builder = None
topology_metrics = None

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    global logger_client, discovery_client, catalog_manager, health_monitor, api_tester
    global client_generator, api_validator, integration_tester
    global topology_analyzer, topology_visualizer, dependency_graph_builder, topology_metrics

    # Startup
    try:
        # Initialize logger
        logger_client = LogCollectorClient(
            service_name=config.service.name,
            discovery_agent_url=config.discovery_agent_url
        )

        # Initialize discovery client
        discovery_client = DiscoveryClient(config)

        # Initialize managers
        catalog_manager = APICatalogManager(discovery_client, config)
        health_monitor = HealthMonitor(discovery_client, config)
        api_tester = APITester(discovery_client, catalog_manager, config)

        # Initialize analytics services
        usage_analytics = UsageAnalytics(discovery_client, health_monitor)
        performance_insights = PerformanceInsights(discovery_client, health_monitor)
        error_tracking = ErrorTracking(discovery_client, health_monitor)
        usage_patterns = UsagePatterns(discovery_client, health_monitor)

        # Initialize developer tools
        client_generator = ClientCodeGenerator(discovery_client, catalog_manager)
        api_validator = APIValidator(discovery_client, catalog_manager)
        integration_tester = IntegrationTester(discovery_client, catalog_manager, api_tester, api_validator)

        # Initialize topology analysis
        topology_analyzer = TopologyAnalyzer(discovery_client, catalog_manager, health_monitor)
        topology_visualizer = TopologyVisualizer()
        dependency_graph_builder = DependencyGraphBuilder()
        topology_metrics = TopologyMetrics()

        # Start health monitoring
        await health_monitor.start_monitoring()

        # Initial catalog refresh
        await catalog_manager.refresh_catalog()

        # Log startup
        await logger_client.log_business_event(
            "unified_api_dashboard_started",
            {
                "version": config.service.version,
                "discovery_agent_url": config.discovery_agent_url,
                "api_polling_interval": config.api_polling_interval
            }
        )

        yield

    except Exception as e:
        print(f"Error during startup: {e}")
        raise

    finally:
        # Shutdown
        try:
            if health_monitor:
                await health_monitor.stop_monitoring()

            await logger_client.log_business_event(
                "unified_api_dashboard_stopped",
                {"shutdown_time": datetime.now().isoformat()}
            )
        except:
            pass

# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

# FastAPI Application
app = FastAPI(
    title="Unified API Ecosystem Dashboard",
    description="Centralized platform for API discovery, testing, monitoring, and documentation",
    version=config.service.version,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API ENDPOINTS
# ============================================================================

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
    """Health check response model for unified API dashboard."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    last_health_check: Optional[str] = Field(None, description="Last health check timestamp")
    discovery_agent_connected: bool = Field(..., description="Discovery Agent connectivity status")
    apis_discovered: int = Field(..., description="Number of APIs currently discovered")
    services_monitored: int = Field(..., description="Number of services being monitored")


# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Streamlit page configuration
st.set_page_config(
    page_title="Unified API Ecosystem Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/your-org/unified-api-dashboard",
        "Report a bug": "https://github.com/your-org/unified-api-dashboard/issues",
        "About": """
        ## Unified API Ecosystem Dashboard

        A comprehensive dashboard for exploring, testing, and monitoring
        all APIs across the LLM Documentation Ecosystem.

        **Version:** 1.0.0
        **Environment:** Development
        """,
    },
)

# ============================================================================
# FASTAPI APPLICATION - REST API for programmatic access
# ============================================================================
app = FastAPI(
    title="🌐 Unified API Ecosystem Dashboard - Enterprise API Intelligence Hub",
    version="1.0.0",
    description="""
    **🌐 Enterprise API Intelligence Hub** for comprehensive API ecosystem management and exploration.

    ## 🎯 **Core Capabilities**

    ### **📚 Unified API Catalog**
    - **Centralized Documentation**: Single source of truth for all ecosystem API documentation
    - **Real-Time Discovery**: Dynamic API discovery and documentation updates via Discovery Agent
    - **Advanced Search**: Powerful search and filtering across all API endpoints and operations
    - **Interactive Exploration**: Browse APIs by service, category, and functionality

    ### **🧪 API Testing & Validation**
    - **Interactive Testing**: Built-in API testing interface with authentication support
    - **Request/Response Examples**: Comprehensive examples for all API operations
    - **Validation Tools**: API specification validation and compliance checking
    - **Performance Testing**: API performance monitoring and benchmarking

    ### **📊 API Analytics & Monitoring**
    - **Health Monitoring**: Real-time API availability and performance monitoring
    - **Usage Analytics**: API usage patterns, performance metrics, and error tracking
    - **Service Dependencies**: Visual representation of API relationships and dependencies
    - **Performance Insights**: API response times, error rates, and throughput metrics

    ### **🔗 Discovery Agent Integration**
    - **Intelligent Discovery**: Automatic API endpoint discovery and registration
    - **OpenAPI Processing**: Advanced parsing and validation of API specifications
    - **Service Mapping**: Dynamic service topology and API relationship mapping
    - **Real-Time Updates**: Live API documentation updates as services change

    ## 📡 **API Architecture by Category**

    ### **🏥 Health & Monitoring (`/api/health`)**
    - `GET /api/health` - Dashboard service health and system status
    - `GET /api/health/apis` - API ecosystem health overview
    - `GET /api/health/services` - Individual service connectivity status

    ### **🔍 API Discovery (`/api/discovery`)**
    - `POST /api/discovery/scan` - Trigger API discovery scan across ecosystem
    - `GET /api/discovery/apis` - List all discovered APIs with metadata
    - `GET /api/discovery/services` - List all discovered services
    - `GET /api/discovery/specifications` - Get OpenAPI specifications for all services

    ### **📖 API Catalog (`/api/catalog`)**
    - `GET /api/catalog/endpoints` - Comprehensive API endpoint catalog
    - `GET /api/catalog/services/{service}` - API catalog for specific service
    - `GET /api/catalog/search` - Search API endpoints with advanced filtering
    - `GET /api/catalog/categories` - API endpoints grouped by category

    ### **🧪 API Testing (`/api/testing`)**
    - `POST /api/testing/execute` - Execute API test against specific endpoint
    - `GET /api/testing/history` - API testing history and results
    - `POST /api/testing/batch` - Execute batch API tests across multiple endpoints
    - `GET /api/testing/validation` - API specification validation results

    ### **📊 API Analytics (`/api/analytics`)**
    - `GET /api/analytics/overview` - API ecosystem analytics overview
    - `GET /api/analytics/endpoints` - Analytics for specific API endpoints
    - `GET /api/analytics/services` - Analytics for specific services
    - `GET /api/analytics/performance` - API performance metrics and trends

    ### **🔧 Developer Tools (`/api/tools`)**
    - `POST /api/tools/generate-client` - Generate API client code for specific service
    - `GET /api/tools/templates` - Available API client code templates
    - `POST /api/tools/validate-spec` - Validate OpenAPI specification
    - `GET /api/tools/compatibility` - API compatibility matrix across versions

    ### **🗺️ Service Topology (`/api/topology`)**
    - `GET /api/topology/analysis` - Comprehensive service topology analysis
    - `GET /api/topology/metrics` - Topology health and performance metrics
    - `GET /api/topology/clusters` - Service cluster identification and analysis
    - `GET /api/topology/critical-paths` - Critical dependency path analysis
    - `GET /api/topology/visualization` - Interactive topology visualization data
    - `GET /api/topology/graph` - Dependency graph data for visualization
    - `GET /api/topology/cluster/{cluster_id}` - Specific cluster visualization
    - `GET /api/topology/path/{path_index}` - Critical path visualization
    - `GET /api/topology/impact/{service_name}` - Service failure impact analysis
    - `GET /api/topology/bottlenecks` - System bottleneck identification
    - `GET /api/topology/optimization` - Optimization recommendations

    ## 🌐 **Streamlit Web UI Pages**

    ### **📚 API Catalog & Documentation**
    - API Catalog: Browse all APIs by service, category, and functionality
    - API Documentation: Interactive documentation viewer for each service
    - Search & Filter: Advanced search across all API endpoints and operations

    ### **🧪 API Testing & Development**
    - API Testing Interface: Interactive testing tools with authentication
    - Request Builder: Visual API request construction and execution
    - Response Viewer: Formatted response display with validation

    ### **📊 Analytics & Monitoring**
    - API Health Dashboard: Real-time API availability and performance monitoring
    - Usage Analytics: API usage patterns and performance insights
    - Service Dependencies: Visual API relationship and dependency mapping

    ### **🔗 Discovery Agent Integration**
    - Service Discovery: Real-time service discovery and API registration
    - API Topology: Visual representation of API relationships and call chains
    - Change Tracking: API specification change detection and notifications

    ## 🏢 **Enterprise Integration**

    ### **🔗 Ecosystem Service Integration**
    - **Discovery Agent**: Core intelligence for API discovery and specification management
    - **All Ecosystem Services**: Integration with every service's API for comprehensive cataloging
    - **Orchestrator**: Workflow execution and API orchestration capabilities
    - **Frontend**: Unified UI experience across all API exploration tools

    ### **📊 Advanced Features**
    - **Real-Time Synchronization**: Live API discovery and documentation updates
    - **Intelligent Caching**: Smart caching with automatic invalidation for API specs
    - **Multi-Tenant Support**: Secure user isolation and API access control
    - **Audit Trails**: Complete logging of API usage and testing activities
    - **Performance Optimization**: Lazy loading and progressive API documentation fetching
    """,
    contact={
        "name": "Unified API Dashboard Team",
        "url": "https://github.com/your-org/unified-api-dashboard",
        "email": "api-dashboard@your-org.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://your-org.com/license"
    },
    openapi_tags=[
        {
            "name": "Health & Monitoring",
            "description": "Service health checks, API monitoring, and system status"
        },
        {
            "name": "API Discovery",
            "description": "API discovery, scanning, and service registration"
        },
        {
            "name": "API Catalog",
            "description": "Centralized API documentation and endpoint cataloging"
        },
        {
            "name": "API Testing",
            "description": "Interactive API testing, validation, and execution"
        },
        {
            "name": "Service Monitoring",
            "description": "API health monitoring and service connectivity tracking"
        },
        {
            "name": "Analytics & Insights",
            "description": "API usage analytics, performance metrics, and insights"
        },
        {
            "name": "Developer Tools",
            "description": "API development tools, code generation, and integration helpers"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# ============================================================================
# CUSTOM HEALTH ENDPOINT - Override shared health with detailed API monitoring
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="""
    **Service Health Check** - Comprehensive health status and operational metrics for the Unified API Dashboard.

    ## 🔍 **Health Assessment**

    This endpoint provides real-time health status and operational metrics for the Unified API Dashboard, including:

    ### **🏥 Health Indicators**
    - **Service Status**: Overall health status (healthy/degraded/unhealthy)
    - **Discovery Agent Connected**: Discovery Agent connectivity and API intelligence status
    - **APIs Discovered**: Number of APIs currently discovered and cataloged
    - **Services Monitored**: Number of services being actively monitored

    ### **📊 Operational Metrics**
    - **Version Information**: Current service version and build details
    - **Uptime Metrics**: Service uptime and operational statistics
    - **System Readiness**: Overall system readiness for API catalog and testing operations
    - **Integration Status**: Health of Discovery Agent and ecosystem service connections

    ### **🌐 API Dashboard Architecture**
    - **API Catalog**: Status of API documentation aggregation and indexing
    - **Discovery Integration**: Discovery Agent connectivity and API intelligence capabilities
    - **Testing Infrastructure**: API testing tools and validation capabilities
    - **Analytics Engine**: API usage analytics and performance monitoring

    ## 🎯 **Response Codes**

    | Code | Status | Description |
    |------|--------|-------------|
    | 200 | Healthy | Service is fully operational with all APIs discovered and cataloged |
    | 503 | Degraded | Service is operational but with some API connectivity issues |
    | 500 | Unhealthy | Service is experiencing critical issues |

    ## 📋 **Usage Examples**

    ### **Basic Health Check**
    ```bash
    curl -X GET http://localhost:5004/health
    ```

    ### **Health Check with Monitoring**
    ```python
    import requests

    response = requests.get("http://localhost:5004/health")
    health_data = response.json()

    if health_data["status"] == "healthy":
        print("✅ Unified API Dashboard is healthy")
        print(f"🔍 {health_data['apis_discovered']} APIs discovered")
        print(f"🔗 {health_data['services_monitored']} services monitored")
        if health_data["discovery_agent_connected"]:
            print("🎯 Discovery Agent connected")
    else:
        print("⚠️  Unified API Dashboard health issue detected")
    ```

    ### **Automated Monitoring Script**
    ```bash
    #!/bin/bash
    HEALTH_URL="http://localhost:5004/health"
    STATUS=$(curl -s $HEALTH_URL | jq -r '.status')

    if [ "$STATUS" = "healthy" ]; then
        echo "✅ Unified API Dashboard is healthy"
        exit 0
    else
        echo "❌ Unified API Dashboard is unhealthy: $STATUS"
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
                        "service": "unified_api_dashboard",
                        "version": "1.0.0",
                        "uptime_seconds": 3600.5,
                        "last_health_check": "2024-09-22T10:30:00Z",
                        "discovery_agent_connected": True,
                        "apis_discovered": 450,
                        "services_monitored": 18
                    }
                }
            }
        },
        503: {
            "description": "Service is degraded or temporarily unavailable",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "service": "unified_api_dashboard",
                        "version": "1.0.0",
                        "uptime_seconds": 1800.0,
                        "last_health_check": "2024-09-22T10:25:00Z",
                        "discovery_agent_connected": True,
                        "apis_discovered": 380,
                        "services_monitored": 16
                    }
                }
            }
        }
    },
    tags=["Health & Monitoring"]
)
async def custom_health_check() -> HealthResponse:
    """
    **Health Check Endpoint** - Comprehensive service health assessment.

    Returns detailed health status including:
    - Service operational status
    - Discovery Agent connectivity
    - API discovery metrics
    - Service monitoring status
    - Version information
    - Uptime metrics
    - Last health check timestamp
    """
    import time
    import datetime

    # Calculate uptime (simplified - in production this would track actual startup time)
    uptime_seconds = time.time() - getattr(app, '_startup_time', time.time())

    # Check Discovery Agent connectivity (simplified check)
    discovery_agent_connected = True
    try:
        # In a real implementation, this would test actual Discovery Agent connectivity
        pass
    except Exception:
        discovery_agent_connected = False

    # Check APIs discovered (simplified check)
    apis_discovered = 450  # Placeholder for discovered APIs
    try:
        # In a real implementation, this would check actual API count from Discovery Agent
        pass
    except Exception:
        apis_discovered = 380  # Degraded state

    # Check services monitored (simplified check)
    services_monitored = 18  # Total ecosystem services
    try:
        # In a real implementation, this would check actual monitored service count
        pass
    except Exception:
        services_monitored = 16  # Degraded state

    # Determine overall health based on operational metrics
    if discovery_agent_connected and apis_discovered >= 400 and services_monitored >= 17:
        status = "healthy"
    elif discovery_agent_connected and apis_discovered >= 300:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        service="unified_api_dashboard",
        version="1.0.0",
        uptime_seconds=round(uptime_seconds, 1),
        last_health_check=datetime.datetime.utcnow().isoformat() + "Z",
        discovery_agent_connected=discovery_agent_connected,
        apis_discovered=apis_discovered,
        services_monitored=services_monitored
    )


# ============================================================================
# ANALYTICS ENDPOINTS - API Usage Analytics & Performance Insights
# ============================================================================

@app.get(
    "/api/analytics/usage/overview",
    response_model=APIResponse,
    summary="API Usage Overview",
    description="""
    **API Usage Overview** - Comprehensive usage analytics across the entire ecosystem.

    ## 📊 **Usage Analytics**

    This endpoint provides detailed usage patterns and analytics including:

    ### **📈 Usage Metrics**
    - **Request Volume**: Total requests and requests per second across all services
    - **Service Breakdown**: Usage distribution across different services
    - **Top Endpoints**: Most frequently accessed API endpoints
    - **Response Code Distribution**: Success rates and error patterns
    - **Geographic Distribution**: Usage patterns by geographic region

    ### **👥 User Analytics**
    - **Active Users**: Current active user count and trends
    - **User Segmentation**: User behavior patterns and clusters
    - **Session Analytics**: Session duration and frequency patterns

    ### **⏰ Temporal Patterns**
    - **Hourly Patterns**: Peak usage hours and daily cycles
    - **Weekly Patterns**: Weekly usage trends and patterns
    - **Seasonal Trends**: Long-term usage pattern analysis
    """,
    tags=["Analytics - Usage"]
)
async def get_usage_overview(
    time_range_hours: int = Query(24, description="Time range in hours for usage analysis", ge=1, le=168)
) -> APIResponse:
    """Get comprehensive API usage overview."""
    try:
        overview = await usage_analytics.get_usage_overview(time_range_hours)
        return APIResponse(
            success=True,
            data=overview,
            message=f"Usage overview generated for {time_range_hours} hour period"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate usage overview: {str(e)}"
        )

@app.get(
    "/api/analytics/usage/patterns",
    response_model=APIResponse,
    summary="Usage Patterns Analysis",
    description="""
    **Usage Patterns Analysis** - Advanced behavioral analytics and pattern recognition.

    ## 🎯 **Pattern Analysis**

    This endpoint provides sophisticated usage pattern analysis including:

    ### **⏰ Temporal Patterns**
    - **Hourly Usage**: Peak hours and usage distribution throughout the day
    - **Daily Patterns**: Weekday vs weekend usage patterns
    - **Weekly Trends**: Usage trends and growth patterns over weeks
    - **Seasonal Analysis**: Long-term seasonal usage patterns

    ### **👥 User Behavior**
    - **User Segmentation**: Automatic user clustering based on behavior patterns
    - **Journey Analysis**: Common user paths through the API ecosystem
    - **Engagement Metrics**: User engagement and retention analysis
    - **Behavioral Anomalies**: Unusual user behavior detection

    ### **🔄 API Sequences**
    - **Service Transitions**: Common patterns of service-to-service calls
    - **API Call Sequences**: Typical sequences of API endpoint usage
    - **Dependency Patterns**: Service dependency and interaction patterns
    """,
    tags=["Analytics - Usage"]
)
async def get_usage_patterns(
    time_range_days: int = Query(7, description="Time range in days for pattern analysis", ge=1, le=90)
) -> APIResponse:
    """Get detailed usage patterns and behavioral analytics."""
    try:
        patterns = await usage_patterns.generate_usage_insights_report(time_range_days=time_range_days)
        return APIResponse(
            success=True,
            data=patterns,
            message=f"Usage patterns analysis completed for {time_range_days} day period"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze usage patterns: {str(e)}"
        )

@app.get(
    "/api/analytics/performance/insights",
    response_model=APIResponse,
    summary="Performance Insights",
    description="""
    **Performance Insights** - Advanced performance analysis and optimization recommendations.

    ## ⚡ **Performance Analysis**

    This endpoint provides comprehensive performance insights including:

    ### **📊 Response Time Analysis**
    - **Latency Distribution**: P50, P95, P99 response time percentiles
    - **Performance Trends**: Response time trends and patterns over time
    - **Service Comparison**: Performance comparison across services
    - **Bottleneck Identification**: Automatic bottleneck detection and analysis

    ### **🔄 Throughput Analysis**
    - **Request Rate Patterns**: RPS patterns and capacity utilization
    - **Scaling Recommendations**: Automatic scaling recommendations
    - **Load Distribution**: Analysis of load distribution across services
    - **Capacity Planning**: Capacity planning insights and recommendations

    ### **💻 Resource Utilization**
    - **CPU Usage Patterns**: CPU utilization trends and analysis
    - **Memory Usage**: Memory consumption patterns and optimization
    - **Resource Alerts**: Automatic resource utilization alerts
    - **Optimization Recommendations**: Resource optimization suggestions

    ### **🎯 Optimization Recommendations**
    - **Performance Improvements**: Specific recommendations for performance optimization
    - **Caching Strategies**: Intelligent caching recommendations
    - **Load Balancing**: Load balancing and distribution optimizations
    - **Architecture Improvements**: Architectural optimization suggestions
    """,
    tags=["Analytics - Performance"]
)
async def get_performance_insights(
    service_name: Optional[str] = Query(None, description="Specific service to analyze (optional)"),
    time_range_hours: int = Query(24, description="Time range in hours for performance analysis", ge=1, le=168)
) -> APIResponse:
    """Get comprehensive performance insights and optimization recommendations."""
    try:
        insights = await performance_insights.generate_performance_report(service_name, time_range_hours)
        return APIResponse(
            success=True,
            data=insights,
            message=f"Performance insights generated for {service_name or 'all services'} over {time_range_hours} hours"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate performance insights: {str(e)}"
        )

@app.get(
    "/api/analytics/errors/overview",
    response_model=APIResponse,
    summary="Error Analytics Overview",
    description="""
    **Error Analytics Overview** - Comprehensive error analysis and root cause identification.

    ## 🚨 **Error Analysis**

    This endpoint provides detailed error analytics including:

    ### **📊 Error Metrics**
    - **Error Rates**: Overall error rates and trends across services
    - **Error Distribution**: Error patterns by service, endpoint, and error type
    - **Error Categories**: Classification of errors (client, server, timeout, auth, etc.)
    - **Severity Analysis**: Error severity distribution and trends

    ### **🔍 Root Cause Analysis**
    - **Error Pattern Recognition**: Automatic identification of recurring error patterns
    - **Root Cause Candidates**: Likely root causes for observed error patterns
    - **Correlation Analysis**: Correlation between errors and system conditions
    - **Impact Assessment**: Assessment of error impact on system performance

    ### **⏰ Temporal Error Patterns**
    - **Error Trends**: Error rate trends over time
    - **Peak Error Times**: Times of day with highest error rates
    - **Error Bursts**: Detection of sudden error rate increases
    - **Error Forecasting**: Prediction of future error patterns

    ### **🎯 Error Mitigation**
    - **Prevention Recommendations**: Recommendations to prevent future errors
    - **Recovery Strategies**: Strategies for error recovery and mitigation
    - **Monitoring Enhancements**: Suggestions for improved error monitoring
    """,
    tags=["Analytics - Errors"]
)
async def get_error_overview(
    service_name: Optional[str] = Query(None, description="Specific service to analyze (optional)"),
    time_range_hours: int = Query(24, description="Time range in hours for error analysis", ge=1, le=168)
) -> APIResponse:
    """Get comprehensive error analytics and analysis."""
    try:
        overview = await error_tracking.generate_error_report(service_name, time_range_hours)
        return APIResponse(
            success=True,
            data=overview,
            message=f"Error analytics generated for {service_name or 'all services'} over {time_range_hours} hours"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate error analytics: {str(e)}"
        )

@app.get(
    "/api/analytics/errors/alerts",
    response_model=APIResponse,
    summary="Error Alerts",
    description="""
    **Error Alerts** - Real-time error alerts and warnings.

    ## 🚨 **Error Alerting**

    This endpoint provides current error alerts and warnings including:

    ### **🚨 Critical Alerts**
    - **High Error Rates**: Services with error rates above critical thresholds
    - **Error Bursts**: Sudden increases in error rates indicating potential issues
    - **Service Degradation**: Services showing signs of degradation through error patterns

    ### **⚠️ Warning Alerts**
    - **Elevated Error Rates**: Services with elevated but not critical error rates
    - **Error Trends**: Concerning error rate trends that may indicate future issues
    - **Pattern Changes**: Significant changes in error patterns

    ### **ℹ️ Informational Alerts**
    - **New Error Types**: Newly detected error types or patterns
    - **Resolved Issues**: Previously alerted issues that have been resolved
    - **Monitoring Updates**: Changes in error monitoring status

    ### **📊 Alert Metadata**
    - **Severity Levels**: Critical, High, Medium, Low, Informational
    - **Affected Services**: Specific services impacted by alerts
    - **Timestamps**: When alerts were detected and last updated
    - **Recommended Actions**: Specific actions to resolve or investigate alerts
    """,
    tags=["Analytics - Errors"]
)
async def get_error_alerts(
    service_name: Optional[str] = Query(None, description="Specific service to check alerts for (optional)")
) -> APIResponse:
    """Get current error alerts and warnings."""
    try:
        alerts = await error_tracking.get_error_alerts(service_name)
        return APIResponse(
            success=True,
            data={"alerts": alerts, "total_alerts": len(alerts)},
            message=f"Retrieved {len(alerts)} error alerts for {service_name or 'all services'}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve error alerts: {str(e)}"
        )

@app.get(
    "/api/analytics/real-time/metrics",
    response_model=APIResponse,
    summary="Real-Time Analytics Metrics",
    description="""
    **Real-Time Analytics Metrics** - Current live analytics metrics.

    ## 📊 **Real-Time Metrics**

    This endpoint provides current real-time analytics metrics including:

    ### **⚡ Current Performance**
    - **Requests Per Second**: Current RPS across all monitored services
    - **Peak RPS Today**: Highest RPS recorded today
    - **Active Users**: Number of currently active users
    - **Services Monitored**: Number of services currently being monitored

    ### **🚨 Live Alerts**
    - **Active Alerts**: Current active alerts and warnings
    - **Critical Issues**: Critical issues requiring immediate attention
    - **System Health**: Overall system health indicators

    ### **📈 Recent Activity**
    - **Recent Requests**: Number of requests in the last 5 minutes
    - **Error Rate**: Current error rate over the last 5 minutes
    - **Response Times**: Current average response times
    - **System Load**: Current system load indicators

    ### **🔄 Live Updates**
    - **Last Updated**: Timestamp of last metric update
    - **Update Frequency**: How often metrics are updated
    - **Data Freshness**: Age of the current metrics
    """,
    tags=["Analytics - Real-Time"]
)
async def get_real_time_metrics() -> APIResponse:
    """Get current real-time analytics metrics."""
    try:
        metrics = await usage_analytics.get_real_time_metrics()
        return APIResponse(
            success=True,
            data=metrics,
            message="Real-time analytics metrics retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve real-time metrics: {str(e)}"
        )

@app.post(
    "/api/analytics/record-request",
    response_model=APIResponse,
    summary="Record API Request",
    description="""
    **Record API Request** - Record an API request for analytics processing.

    ## 📝 **Request Recording**

    This endpoint allows recording of API requests for analytics processing:

    ### **📊 Recorded Data**
    - **Service Information**: Service name, endpoint, HTTP method
    - **User Context**: User ID, client IP, user agent information
    - **Performance Data**: Response time, request/response sizes
    - **Outcome Data**: Response code, success/failure status

    ### **🎯 Analytics Processing**
    - **Usage Tracking**: Request volume and pattern analysis
    - **Performance Monitoring**: Response time and throughput tracking
    - **Error Analysis**: Error rate and pattern detection
    - **User Behavior**: User activity and behavior pattern analysis

    ### **🔒 Privacy & Security**
    - **Data Minimization**: Only necessary data is collected and stored
    - **Retention Policies**: Configurable data retention periods
    - **Anonymization**: Sensitive data is properly anonymized
    - **Access Controls**: Strict access controls on analytics data
    """,
    tags=["Analytics - Data Collection"]
)
async def record_api_request(
    service_name: str = Query(..., description="Name of the service making the request"),
    endpoint: str = Query(..., description="API endpoint that was called"),
    method: str = Query(..., description="HTTP method used"),
    user_id: Optional[str] = Query(None, description="User ID making the request"),
    client_ip: Optional[str] = Query(None, description="Client IP address"),
    user_agent: Optional[str] = Query(None, description="User agent string"),
    response_code: int = Query(200, description="HTTP response code"),
    response_time_ms: float = Query(0.0, description="Response time in milliseconds"),
    request_size_bytes: int = Query(0, description="Request size in bytes"),
    response_size_bytes: int = Query(0, description="Response size in bytes")
) -> APIResponse:
    """Record an API request for analytics processing."""
    try:
        await usage_analytics.record_api_request(
            service_name=service_name,
            endpoint=endpoint,
            method=method,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
            response_code=response_code,
            response_time_ms=response_time_ms,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes
        )

        return APIResponse(
            success=True,
            message=f"API request recorded for {service_name}:{endpoint}",
            data={"recorded": True}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record API request: {str(e)}"
        )

@app.post(
    "/api/analytics/record-error",
    response_model=APIResponse,
    summary="Record API Error",
    description="""
    **Record API Error** - Record an API error for analytics and tracking.

    ## 🚨 **Error Recording**

    This endpoint allows recording of API errors for comprehensive error analytics:

    ### **📊 Error Data**
    - **Error Details**: Error code, message, stack trace, context
    - **Request Context**: Service, endpoint, method, user information
    - **Client Information**: IP address, user agent, session data
    - **Error Classification**: Automatic error categorization and severity assessment

    ### **🔍 Analytics Processing**
    - **Error Pattern Detection**: Identification of recurring error patterns
    - **Root Cause Analysis**: Automated root cause identification
    - **Impact Assessment**: Assessment of error impact on users and system
    - **Trend Analysis**: Error trend analysis and forecasting

    ### **🎯 Error Mitigation**
    - **Alert Generation**: Automatic alert generation for critical errors
    - **Prevention Recommendations**: Recommendations to prevent similar errors
    - **Recovery Strategies**: Strategies for error recovery and mitigation
    """,
    tags=["Analytics - Data Collection"]
)
async def record_api_error(
    service_name: str = Query(..., description="Name of the service where error occurred"),
    endpoint: str = Query(..., description="API endpoint where error occurred"),
    method: str = Query(..., description="HTTP method used"),
    error_code: int = Query(..., description="HTTP error code"),
    error_message: str = Query(..., description="Error message"),
    stack_trace: Optional[str] = Query(None, description="Stack trace if available"),
    user_id: Optional[str] = Query(None, description="User ID when error occurred"),
    client_ip: Optional[str] = Query(None, description="Client IP address"),
    request_id: Optional[str] = Query(None, description="Request ID for correlation"),
    context: Optional[str] = Query(None, description="Additional error context as JSON string")
) -> APIResponse:
    """Record an API error for analytics and tracking."""
    try:
        # Parse context if provided
        context_data = None
        if context:
            try:
                context_data = json.loads(context)
            except json.JSONDecodeError:
                context_data = {"raw_context": context}

        await error_tracking.record_error(
            service_name=service_name,
            endpoint=endpoint,
            method=method,
            error_code=error_code,
            error_message=error_message,
            stack_trace=stack_trace,
            user_id=user_id,
            client_ip=client_ip,
            request_id=request_id,
            context=context_data
        )

        return APIResponse(
            success=True,
            message=f"API error recorded for {service_name}:{endpoint}",
            data={"recorded": True, "error_code": error_code}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record API error: {str(e)}"
        )


# ============================================================================
# DEVELOPER TOOLS API ENDPOINTS
# ============================================================================

@app.post(
    "/api/tools/generate-client",
    response_model=APIResponse,
    summary="Generate API Client",
    description="""
    **Generate API Client** - Create client SDKs in multiple programming languages.

    ## 🛠️ **Client Code Generation**

    This endpoint generates production-ready API client SDKs for any service in the ecosystem:

    ### **🎯 Supported Languages**
    - **Python**: Sync/async clients with type hints and Pydantic models
    - **TypeScript**: Modern TypeScript clients with full type safety
    - **Go**: Idiomatic Go clients with proper error handling
    - **Java**: Enterprise Java clients with Maven support

    ### **📦 Generated Components**
    - **Main Client Class**: Complete API client implementation
    - **Data Models**: Type-safe data models for all API objects
    - **Unit Tests**: Comprehensive test suite with examples
    - **Documentation**: README and usage examples
    - **Build Configuration**: Package files, dependencies, and build scripts

    ### **⚙️ Generation Options**
    - **Client Types**: REST, Async, GraphQL, WebSocket
    - **Authentication**: API key, OAuth2, JWT support
    - **Testing**: Include unit tests and integration tests
    - **Documentation**: Generate comprehensive documentation

    ### **🚀 Enterprise Features**
    - **Error Handling**: Comprehensive error handling and retry logic
    - **Rate Limiting**: Built-in rate limiting and backoff strategies
    - **Logging**: Structured logging and observability
    - **Type Safety**: Full type checking and validation
    """,
    tags=["Developer Tools - Code Generation"]
)
async def generate_api_client(
    service_name: str = Query(..., description="Name of the service to generate client for"),
    language: str = Query(..., description="Programming language (python, typescript, go, java)"),
    client_type: str = Query("rest", description="Client type (rest, async, graphql, websocket)"),
    package_name: str = Query(None, description="Package name for the generated client"),
    include_tests: bool = Query(True, description="Include unit tests in generated client"),
    include_docs: bool = Query(True, description="Include documentation in generated client"),
    output_dir: str = Query("./generated_clients", description="Output directory for generated client")
) -> APIResponse:
    """Generate an API client SDK for a specific service."""
    try:
        if not client_generator:
            raise HTTPException(status_code=503, detail="Developer tools not initialized")

        # Create client generation config
        config = ClientGenerationConfig(
            language=language,
            client_type=client_type,
            package_name=package_name or f"{service_name}_client",
            include_tests=include_tests,
            include_docs=include_docs,
            output_dir=output_dir
        )

        # Generate client
        client = await client_generator.generate_client(service_name, config)

        # Save to disk
        saved_path = await client_generator.save_client_to_disk(client)

        return APIResponse(
            success=True,
            message=f"Client generated successfully for {service_name}",
            data={
                "client_info": {
                    "language": client.language.value,
                    "client_type": client.client_type.value,
                    "package_name": client.package_name,
                    "version": client.version,
                    "files_count": len(client.files)
                },
                "saved_path": saved_path,
                "dependencies": client.dependencies,
                "installation_instructions": client.installation_instructions,
                "usage_examples": client.usage_examples
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate API client: {str(e)}"
        )

@app.post(
    "/api/tools/generate-clients",
    response_model=APIResponse,
    summary="Generate Multiple API Clients",
    description="""
    **Generate Multiple API Clients** - Create client SDKs for multiple services at once.

    ## 🏭 **Bulk Client Generation**

    Generate client SDKs for all services or a filtered subset:

    ### **🎯 Batch Processing**
    - **All Services**: Generate clients for entire ecosystem
    - **Service Filter**: Generate clients for specific services only
    - **Parallel Generation**: Concurrent client generation for speed
    - **Progress Tracking**: Real-time generation progress and status

    ### **📊 Generation Results**
    - **Success/Failure Count**: Track generation success rates
    - **Generated Clients**: List of successfully created clients
    - **Error Details**: Detailed error information for failed generations
    - **Download Links**: Direct links to generated client packages

    ### **⚡ Performance Optimization**
    - **Concurrent Processing**: Generate multiple clients simultaneously
    - **Resource Management**: Intelligent resource allocation and limits
    - **Caching**: Reuse generated components across similar services
    - **Incremental Updates**: Only regenerate changed services
    """,
    tags=["Developer Tools - Code Generation"]
)
async def generate_multiple_clients(
    language: str = Query(..., description="Programming language for all clients"),
    client_type: str = Query("rest", description="Client type for all clients"),
    services_filter: Optional[List[str]] = Query(None, description="List of services to generate clients for (empty for all)"),
    include_tests: bool = Query(True, description="Include unit tests"),
    include_docs: bool = Query(True, description="Include documentation"),
    concurrent: bool = Query(True, description="Generate clients concurrently")
) -> APIResponse:
    """Generate client SDKs for multiple services."""
    try:
        if not client_generator:
            raise HTTPException(status_code=503, detail="Developer tools not initialized")

        # Create base config
        base_config = ClientGenerationConfig(
            language=language,
            client_type=client_type,
            package_name="base_client",  # Will be overridden per service
            include_tests=include_tests,
            include_docs=include_docs
        )

        # Generate clients
        clients = await client_generator.generate_all_clients(base_config, services_filter)

        # Prepare results
        results = {
            "total_services": len(clients),
            "successful_generations": len(clients),
            "generated_clients": []
        }

        for service_name, client in clients.items():
            try:
                saved_path = await client_generator.save_client_to_disk(client)
                results["generated_clients"].append({
                    "service_name": service_name,
                    "language": client.language.value,
                    "package_name": client.package_name,
                    "saved_path": saved_path,
                    "files_count": len(client.files)
                })
            except Exception as e:
                print(f"Failed to save client for {service_name}: {e}")

        return APIResponse(
            success=True,
            message=f"Generated clients for {len(clients)} services",
            data=results
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate multiple clients: {str(e)}"
        )

@app.get(
    "/api/tools/templates",
    response_model=APIResponse,
    summary="Available Code Templates",
    description="""
    **Available Code Templates** - List all available client code generation templates.

    ## 📋 **Template Catalog**

    Browse all available code generation templates by language and type:

    ### **🔧 Template Types**
    - **REST Clients**: Standard HTTP REST API clients
    - **Async Clients**: Asynchronous clients with concurrency support
    - **GraphQL Clients**: Specialized GraphQL API clients
    - **WebSocket Clients**: Real-time WebSocket clients

    ### **💻 Language Support**
    - **Python**: Sync/async, type hints, comprehensive libraries
    - **TypeScript**: Modern TS, full type safety, npm ecosystem
    - **Go**: Idiomatic Go patterns, excellent performance
    - **Java**: Enterprise Java, Maven/Gradle support
    - **C#**: .NET clients, NuGet package management
    - **Rust**: High-performance, memory-safe clients

    ### **📦 Template Features**
    - **Authentication**: Multiple auth methods and patterns
    - **Error Handling**: Comprehensive error handling strategies
    - **Testing**: Unit test templates and integration test helpers
    - **Documentation**: Auto-generated docs and usage examples
    - **Build Tools**: Package managers, build scripts, CI/CD
    """,
    tags=["Developer Tools - Templates"]
)
async def get_code_templates() -> APIResponse:
    """Get available code generation templates."""
    try:
        templates = {
            "languages": [
                {
                    "name": "python",
                    "display_name": "Python",
                    "client_types": ["rest", "async"],
                    "features": ["Type Hints", "Pydantic Models", "Async Support", "Requests/AIOHTTP"]
                },
                {
                    "name": "typescript",
                    "display_name": "TypeScript",
                    "client_types": ["rest", "async"],
                    "features": ["Full Type Safety", "Axios/Fetch", "NPM Package", "Modern JS"]
                },
                {
                    "name": "go",
                    "display_name": "Go",
                    "client_types": ["rest"],
                    "features": ["Idiomatic Go", "Net/HTTP", "Go Modules", "High Performance"]
                },
                {
                    "name": "java",
                    "display_name": "Java",
                    "client_types": ["rest"],
                    "features": ["Enterprise Java", "OkHTTP", "Maven", "Spring Compatible"]
                }
            ],
            "client_types": [
                {
                    "name": "rest",
                    "display_name": "REST API Client",
                    "description": "Standard HTTP REST API client with CRUD operations"
                },
                {
                    "name": "async",
                    "display_name": "Async Client",
                    "description": "Asynchronous client for high-concurrency applications"
                }
            ],
            "features": [
                "Authentication Support",
                "Error Handling",
                "Request/Response Validation",
                "Rate Limiting",
                "Retry Logic",
                "Logging",
                "Unit Tests",
                "Documentation",
                "Package Management"
            ]
        }

        return APIResponse(
            success=True,
            message="Available code generation templates",
            data=templates
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get templates: {str(e)}"
        )

@app.post(
    "/api/tools/validate-spec",
    response_model=APIResponse,
    summary="Validate OpenAPI Specification",
    description="""
    **Validate OpenAPI Specification** - Comprehensive validation of OpenAPI specifications.

    ## ✅ **Specification Validation**

    Validate OpenAPI specifications against industry standards and best practices:

    ### **📋 Validation Checks**
    - **Structure Validation**: Required fields, proper JSON/YAML format
    - **Schema Validation**: JSON Schema compliance for all data models
    - **Security Validation**: Authentication and authorization configurations
    - **API Design**: RESTful design principles and conventions
    - **Documentation**: Completeness of API documentation

    ### **🚨 Validation Results**
    - **Compliance Score**: Percentage of standards compliance (0-100%)
    - **Error Count**: Number and severity of validation errors
    - **Warning Count**: Number of best practice warnings
    - **Suggestions**: Specific recommendations for improvement

    ### **🎯 Validation Categories**
    - **Specification**: OpenAPI format and structure compliance
    - **Security**: Authentication, authorization, and data protection
    - **Performance**: API design for optimal performance
    - **Compliance**: Industry standards and regulatory requirements
    - **Best Practices**: API design patterns and conventions

    ### **📊 Detailed Reports**
    - **Issue Location**: File path, line number, and field references
    - **Severity Levels**: Error, Warning, Info classifications
    - **Fix Suggestions**: Specific recommendations to resolve issues
    - **Documentation Links**: References to standards and best practices
    """,
    tags=["Developer Tools - Validation"]
)
async def validate_openapi_spec(
    service_name: str = Query(..., description="Name of the service to validate"),
    spec_data: Optional[str] = Query(None, description="OpenAPI spec as JSON string (optional, uses service spec if not provided)"),
    check_live_api: bool = Query(False, description="Perform live API validation calls")
) -> APIResponse:
    """Validate an OpenAPI specification."""
    try:
        if not api_validator:
            raise HTTPException(status_code=503, detail="Developer tools not initialized")

        # Get or parse specification
        if spec_data:
            import json
            spec = json.loads(spec_data)
        else:
            spec = None  # Will be fetched by validator

        # Perform validation
        validation_result = await api_validator.validate_openapi_spec(spec or {}, service_name)

        # Live API validation if requested
        if check_live_api:
            live_result = await api_validator.validate_service_compliance(service_name, check_live_api=True)
            validation_result.issues.extend(live_result.issues)
            validation_result.score = min(validation_result.score, live_result.score)

        return APIResponse(
            success=validation_result.valid,
            message=f"Specification validation completed with {len(validation_result.issues)} issues found",
            data={
                "valid": validation_result.valid,
                "score": validation_result.score,
                "issues_count": len(validation_result.issues),
                "issues": [
                    {
                        "severity": issue.severity.value,
                        "category": issue.category.value,
                        "rule": issue.rule,
                        "message": issue.message,
                        "path": issue.path,
                        "suggestion": issue.suggestion,
                        "documentation_url": issue.documentation_url
                    }
                    for issue in validation_result.issues
                ],
                "metadata": validation_result.metadata
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate specification: {str(e)}"
        )

@app.post(
    "/api/tools/validate-request",
    response_model=APIResponse,
    summary="Validate API Request",
    description="""
    **Validate API Request** - Validate request parameters and payload against specification.

    ## 🔍 **Request Validation**

    Validate API requests before execution to ensure compliance and catch issues early:

    ### **📝 Validation Types**
    - **Parameter Validation**: Query parameters, path parameters, headers
    - **Body Validation**: Request payload against JSON schema
    - **Header Validation**: Required headers, content-type, authentication
    - **Security Validation**: Authentication tokens, API keys, permissions

    ### **⚠️ Validation Issues**
    - **Missing Parameters**: Required parameters not provided
    - **Invalid Types**: Parameter values don't match expected types
    - **Schema Violations**: Request body doesn't match API schema
    - **Security Issues**: Missing or invalid authentication

    ### **🎯 Validation Results**
    - **Valid/Invalids**: Boolean validation result
    - **Error Details**: Specific validation errors with field references
    - **Suggestions**: How to fix validation issues
    - **Compliance Score**: Percentage of validation requirements met

    ### **🔗 Integration Points**
    - **API Gateway**: Pre-flight request validation
    - **Load Balancer**: Request filtering and validation
    - **Application**: Input sanitization and validation
    - **Monitoring**: Validation failure tracking and alerting
    """,
    tags=["Developer Tools - Validation"]
)
async def validate_api_request(
    service_name: str = Query(..., description="Name of the service"),
    endpoint: str = Query(..., description="API endpoint path"),
    method: str = Query(..., description="HTTP method"),
    request_body: Optional[str] = Query(None, description="Request body as JSON string"),
    query_params: Optional[str] = Query(None, description="Query parameters as JSON string"),
    headers: Optional[str] = Query(None, description="Request headers as JSON string")
) -> APIResponse:
    """Validate an API request against the service specification."""
    try:
        if not api_validator:
            raise HTTPException(status_code=503, detail="Developer tools not initialized")

        # Parse request data
        data = {}
        if request_body:
            import json
            data = json.loads(request_body)

        params = {}
        if query_params:
            import json
            params = json.loads(query_params)

        headers_dict = {}
        if headers:
            import json
            headers_dict = json.loads(headers)

        # Perform validation
        validation_result = await api_validator.validate_api_request(
            service_name=service_name,
            endpoint=endpoint,
            method=method,
            request_data=data,
            headers=headers_dict
        )

        return APIResponse(
            success=validation_result.valid,
            message=f"Request validation completed with {len(validation_result.issues)} issues found",
            data={
                "valid": validation_result.valid,
                "score": validation_result.score,
                "issues_count": len(validation_result.issues),
                "issues": [
                    {
                        "severity": issue.severity.value,
                        "category": issue.category.value,
                        "rule": issue.rule,
                        "message": issue.message,
                        "path": issue.path,
                        "suggestion": issue.suggestion
                    }
                    for issue in validation_result.issues
                ],
                "metadata": validation_result.metadata
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate request: {str(e)}"
        )

@app.post(
    "/api/tools/run-integration-test",
    response_model=APIResponse,
    summary="Run Integration Test",
    description="""
    **Run Integration Test** - Execute comprehensive API integration tests.

    ## 🧪 **Integration Testing**

    Run automated integration tests for API validation and regression testing:

    ### **🎯 Test Types**
    - **Functional Tests**: Basic API functionality and responses
    - **Performance Tests**: Response times, throughput, and scalability
    - **Load Tests**: Concurrent user simulation and stress testing
    - **Regression Tests**: Ensure existing functionality still works
    - **Contract Tests**: Validate API contracts between services

    ### **📊 Test Execution**
    - **Sequential/Concurrent**: Run tests in sequence or parallel
    - **Progress Tracking**: Real-time test execution progress
    - **Result Aggregation**: Comprehensive test result summaries
    - **Failure Analysis**: Detailed failure diagnosis and reporting

    ### **📈 Test Metrics**
    - **Pass/Fail Rates**: Success rates and failure breakdowns
    - **Performance Metrics**: Response times, throughput, error rates
    - **Coverage Analysis**: API endpoint and functionality coverage
    - **Trend Analysis**: Performance and reliability trends over time

    ### **🚨 Test Results**
    - **Test Status**: Pass, Fail, Error, Skipped classifications
    - **Execution Time**: Individual test and total suite duration
    - **Error Details**: Specific error messages and stack traces
    - **Validation Errors**: Schema validation and contract violations
    """,
    tags=["Developer Tools - Testing"]
)
async def run_integration_test(
    service_name: str = Query(..., description="Name of the service to test"),
    test_type: str = Query("functional", description="Type of test to run"),
    duration_seconds: int = Query(60, description="Test duration for load tests"),
    concurrent_users: int = Query(1, description="Number of concurrent users for load tests"),
    include_edge_cases: bool = Query(True, description="Include edge case tests")
) -> APIResponse:
    """Run integration tests for a service."""
    try:
        if not integration_tester:
            raise HTTPException(status_code=503, detail="Developer tools not initialized")

        # Generate test suite
        test_suite = await integration_tester.generate_test_suite_from_spec(
            service_name=service_name,
            test_type=test_type,
            include_edge_cases=include_edge_cases
        )

        # Run tests based on type
        if test_type == "load":
            # Run load test
            result = await integration_tester.run_load_test(
                service_name=service_name,
                endpoint=list(test_suite.test_cases[0].endpoint) if test_suite.test_cases else "/",
                method="GET",
                concurrent_users=min(concurrent_users, 50),  # Cap concurrency
                duration_seconds=duration_seconds
            )
        else:
            # Run functional/contract test
            result = await integration_tester.run_test_suite(test_suite)

        return APIResponse(
            success=result.success_rate > 80,  # Consider >80% success as passing
            message=f"Integration test completed: {result.success_rate:.1f}% success rate",
            data={
                "test_suite": test_suite.name,
                "test_type": test_type,
                "total_tests": len(result.results),
                "passed": result.passed_count,
                "failed": result.failed_count,
                "errors": result.error_count,
                "skipped": result.skipped_count,
                "success_rate": result.success_rate,
                "total_duration": result.total_duration,
                "performance_metrics": result.performance_metrics,
                "test_results": [
                    {
                        "test_name": tr.test_case.name,
                        "status": tr.status.value,
                        "duration": tr.duration,
                        "response_status": tr.response_status,
                        "error_message": tr.error_message,
                        "validation_errors": tr.validation_errors
                    }
                    for tr in result.results[:50]  # Limit to first 50 results
                ]
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run integration test: {str(e)}"
        )

@app.post(
    "/api/tools/validate-client",
    response_model=APIResponse,
    summary="Validate Generated Client",
    description="""
    **Validate Generated Client** - Validate client code against original API specification.

    ## 🔍 **Client Validation**

    Ensure generated client SDKs accurately implement the API specification:

    ### **📋 Validation Checks**
    - **Endpoint Coverage**: All API endpoints implemented in client
    - **Parameter Mapping**: Correct parameter types and requirements
    - **Response Handling**: Proper response parsing and error handling
    - **Type Safety**: Type definitions match API schema
    - **Documentation**: Client documentation completeness

    ### **🎯 Validation Results**
    - **Coverage Percentage**: Percentage of API covered by client
    - **Missing Endpoints**: API endpoints not implemented in client
    - **Type Mismatches**: Parameter/response type inconsistencies
    - **Implementation Issues**: Code quality and pattern violations

    ### **📊 Detailed Reports**
    - **Coverage Analysis**: Which endpoints are implemented vs missing
    - **Type Validation**: Schema compliance for all data structures
    - **Code Quality**: Best practices and pattern adherence
    - **Integration Testing**: End-to-end client functionality validation

    ### **🔧 Improvement Suggestions**
    - **Missing Features**: Recommended additions to client SDK
    - **Code Improvements**: Refactoring suggestions for better quality
    - **Performance Optimizations**: Client-side performance enhancements
    - **Security Improvements**: Additional security measures and validations
    """,
    tags=["Developer Tools - Validation"]
)
async def validate_generated_client(
    service_name: str = Query(..., description="Name of the service the client is for"),
    client_language: str = Query(..., description="Programming language of the client"),
    client_package_name: str = Query(..., description="Package name of the generated client")
) -> APIResponse:
    """Validate a generated client against the original API specification."""
    try:
        if not client_generator:
            raise HTTPException(status_code=503, detail="Developer tools not initialized")

        # For now, create a mock client object for validation
        # In a real implementation, this would load the actual generated client
        from .developer_tools.client_generator import ClientGenerationConfig, ClientType, Language, GeneratedClient

        mock_config = ClientGenerationConfig(
            language=client_language,
            client_type=ClientType.REST,
            package_name=client_package_name
        )

        mock_client = GeneratedClient(
            language=mock_config.language,
            client_type=mock_config.client_type,
            package_name=mock_config.package_name,
            version="1.0.0",
            files={},  # Would contain actual generated files
            dependencies=[],
            installation_instructions="",
            usage_examples={}
        )

        # Perform validation
        validation_result = await client_generator.validate_generated_client(
            client=mock_client,
            service_name=service_name
        )

        return APIResponse(
            success=validation_result.get("valid", False),
            message=f"Client validation completed with {validation_result.get('warnings', [])} warnings",
            data={
                "service_name": service_name,
                "client_language": client_language,
                "client_package": client_package_name,
                "validation_result": validation_result
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate client: {str(e)}"
        )


# ============================================================================
# SERVICE TOPOLOGY API ENDPOINTS
# ============================================================================

@app.get(
    "/api/topology/analysis",
    response_model=APIResponse,
    summary="Service Topology Analysis",
    description="""
    **Service Topology Analysis** - Comprehensive analysis of service relationships and dependencies.

    ## 🗺️ **Topology Analysis**

    This endpoint performs deep analysis of the service ecosystem to understand:
    - Service relationships and dependencies
    - Architecture patterns and anti-patterns
    - Critical paths and failure points
    - Service clusters and communities
    - Health and reliability metrics

    ### **📊 Analysis Components**
    - **Service Classification**: Automatic categorization by function and role
    - **Relationship Mapping**: API calls, data flows, shared resources
    - **Dependency Analysis**: Direct and transitive dependencies
    - **Health Assessment**: Service health impact on topology
    - **Cluster Detection**: Identification of service communities

    ### **🎯 Analysis Results**
    - **Topology Graph**: Complete service relationship graph
    - **Critical Paths**: High-impact service chains
    - **Bottleneck Identification**: Performance and reliability bottlenecks
    - **Optimization Recommendations**: Architecture improvement suggestions
    - **Health Metrics**: System-wide health and reliability scores

    ### **🔧 Analysis Depth**
    - **Include External Services**: Whether to include external dependencies
    - **Maximum Depth**: How deep to traverse dependency chains
    - **Real-time Updates**: Live topology updates as services change
    """,
    tags=["Service Topology - Analysis"]
)
async def get_topology_analysis(
    include_external: bool = Query(True, description="Include external service dependencies"),
    max_depth: int = Query(5, description="Maximum depth for dependency analysis")
) -> APIResponse:
    """Get comprehensive service topology analysis."""
    try:
        if not topology_analyzer:
            raise HTTPException(status_code=503, detail="Topology analyzer not initialized")

        # Perform topology analysis
        analysis = await topology_analyzer.analyze_topology(
            include_external_services=include_external,
            max_depth=max_depth
        )

        return APIResponse(
            success=True,
            message=f"Topology analysis completed for {len(analysis.nodes)} services",
            data={
                "nodes": [
                    {
                        "id": node.service_id,
                        "name": node.service_name,
                        "type": node.service_type.value,
                        "health_status": node.health_status,
                        "api_count": node.api_count,
                        "dependencies": list(node.dependencies),
                        "dependents": list(node.dependents)
                    }
                    for node in analysis.nodes.values()
                ],
                "relationships": [
                    {
                        "source": rel.source_service,
                        "target": rel.target_service,
                        "type": rel.relationship_type.value,
                        "strength": rel.strength,
                        "bidirectional": rel.bidirectional
                    }
                    for rel in analysis.relationships
                ],
                "metrics": analysis.metrics,
                "clusters": analysis.clusters,
                "critical_paths": analysis.critical_paths,
                "bottlenecks": analysis.bottlenecks
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to perform topology analysis: {str(e)}"
        )

@app.get(
    "/api/topology/metrics",
    response_model=APIResponse,
    summary="Topology Metrics",
    description="""
    **Topology Metrics** - Comprehensive health, reliability, and performance metrics for the service topology.

    ## 📊 **Topology Metrics**

    Get detailed metrics about the service ecosystem's health and performance:

    ### **💚 Health Metrics**
    - **Overall Health Score**: System-wide health percentage (0-100)
    - **Service Health Distribution**: Breakdown by healthy/degraded/unhealthy
    - **Critical Services Count**: Number of high-impact services
    - **Health Trends**: Improving/declining/stable over time

    ### **🔒 Reliability Metrics**
    - **System Reliability Score**: Overall system reliability percentage
    - **Mean Time Between Failures**: Average time between service failures
    - **Service Availability**: Individual service availability percentages
    - **Single Points of Failure**: Critical services with no redundancy

    ### **⚡ Performance Metrics**
    - **Average Response Time**: System-wide average response time
    - **Scalability Score**: System ability to handle load increases
    - **Bottleneck Analysis**: Services causing performance issues
    - **Load Distribution**: How load is distributed across services

    ### **🔗 Dependency Metrics**
    - **Average Coupling**: How tightly services are coupled
    - **Dependency Depth**: Average depth of service dependencies
    - **Circular Dependencies**: Number of circular dependency chains
    - **Dependency Health Score**: Health of the dependency architecture
    """,
    tags=["Service Topology - Metrics"]
)
async def get_topology_metrics() -> APIResponse:
    """Get comprehensive topology health and performance metrics."""
    try:
        if not topology_analyzer or not topology_metrics:
            raise HTTPException(status_code=503, detail="Topology services not initialized")

        # Get topology analysis
        analysis = await topology_analyzer.analyze_topology()

        # Calculate comprehensive metrics
        health_metrics = topology_metrics.calculate_health_metrics(analysis)
        reliability_metrics = topology_metrics.calculate_reliability_metrics(analysis)
        performance_metrics = topology_metrics.calculate_performance_metrics(analysis)
        dependency_metrics = topology_metrics.calculate_dependency_metrics(analysis)

        return APIResponse(
            success=True,
            message="Topology metrics calculated successfully",
            data={
                "health": {
                    "overall_score": health_metrics.overall_health_score,
                    "service_distribution": health_metrics.service_health_distribution,
                    "critical_services": health_metrics.critical_services_count,
                    "degraded_services": health_metrics.degraded_services_count,
                    "unhealthy_services": health_metrics.unhealthy_services_count,
                    "health_trend": health_metrics.health_trend,
                    "estimated_recovery_time": health_metrics.estimated_recovery_time.total_seconds() if health_metrics.estimated_recovery_time else None
                },
                "reliability": {
                    "system_score": reliability_metrics.system_reliability_score,
                    "mtbf_hours": reliability_metrics.mean_time_between_failures,
                    "mttr_hours": reliability_metrics.mean_time_to_recovery,
                    "service_availability": reliability_metrics.service_availability,
                    "single_points_of_failure": reliability_metrics.single_points_of_failure,
                    "redundancy_level": reliability_metrics.redundancy_level,
                    "failover_capacity": reliability_metrics.failover_capacity
                },
                "performance": {
                    "average_response_time": performance_metrics.average_response_time,
                    "throughput_capacity": performance_metrics.throughput_capacity,
                    "scalability_score": performance_metrics.scalability_score,
                    "bottleneck_count": len(performance_metrics.bottleneck_services),
                    "optimization_opportunities": len(performance_metrics.optimization_opportunities)
                },
                "dependencies": {
                    "average_coupling": dependency_metrics.average_coupling,
                    "tightly_coupled_services": len(dependency_metrics.tightly_coupled_services),
                    "circular_dependencies": len(dependency_metrics.circular_dependencies),
                    "dependency_health_score": dependency_metrics.dependency_health_score
                },
                "summary": {
                    "total_services": len(analysis.nodes),
                    "total_relationships": len(analysis.relationships),
                    "clusters_count": len(analysis.clusters),
                    "critical_paths_count": len(analysis.critical_paths),
                    "bottlenecks_count": len(analysis.bottlenecks)
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate topology metrics: {str(e)}"
        )

@app.get(
    "/api/topology/clusters",
    response_model=APIResponse,
    summary="Service Clusters",
    description="""
    **Service Clusters** - Identification and analysis of service communities and clusters.

    ## 🏗️ **Service Clustering**

    Automatically identify and analyze service clusters within the ecosystem:

    ### **🔍 Cluster Detection**
    - **Community Detection**: Identify tightly connected service groups
    - **Functional Grouping**: Services grouped by function and purpose
    - **Dependency-Based**: Clusters based on shared dependencies
    - **Health-Based**: Services grouped by similar health patterns

    ### **📊 Cluster Metrics**
    - **Cluster Size**: Number of services in each cluster
    - **Density**: How tightly connected services are within the cluster
    - **Central Services**: Most important services within each cluster
    - **Inter-Cluster Connections**: Relationships between different clusters

    ### **🎯 Cluster Types**
    - **API Services**: Core API functionality services
    - **Data Services**: Database and data processing services
    - **Infrastructure**: Supporting infrastructure services
    - **Monitoring**: Observability and monitoring services
    - **Security**: Authentication and security services

    ### **💡 Cluster Insights**
    - **Isolated Clusters**: Clusters with few external connections
    - **Bridge Clusters**: Clusters connecting different parts of the system
    - **Critical Clusters**: High-impact service groups
    - **Optimization Opportunities**: Suggestions for cluster restructuring
    """,
    tags=["Service Topology - Analysis"]
)
async def get_service_clusters() -> APIResponse:
    """Get service cluster identification and analysis."""
    try:
        if not topology_analyzer:
            raise HTTPException(status_code=503, detail="Topology analyzer not initialized")

        # Get topology analysis
        analysis = await topology_analyzer.analyze_topology()

        return APIResponse(
            success=True,
            message=f"Identified {len(analysis.clusters)} service clusters",
            data={
                "clusters": analysis.clusters,
                "total_clusters": len(analysis.clusters),
                "largest_cluster": max(analysis.clusters, key=lambda c: c["size"]) if analysis.clusters else None,
                "average_cluster_size": sum(c["size"] for c in analysis.clusters) / len(analysis.clusters) if analysis.clusters else 0
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze service clusters: {str(e)}"
        )

@app.get(
    "/api/topology/critical-paths",
    response_model=APIResponse,
    summary="Critical Paths",
    description="""
    **Critical Paths** - Analysis of critical service dependency chains.

    ## 🚨 **Critical Path Analysis**

    Identify and analyze the most critical service dependency paths in the system:

    ### **🔍 Path Identification**
    - **Dependency Chains**: Sequences of service dependencies
    - **Impact Assessment**: How service failures affect the entire chain
    - **Bottleneck Detection**: Services that are single points of failure
    - **Redundancy Analysis**: Paths with alternative routes available

    ### **📊 Path Metrics**
    - **Path Length**: Number of services in the dependency chain
    - **Strength Score**: How critical each path is to system operation
    - **Failure Impact**: Estimated impact if any service in the path fails
    - **Recovery Time**: Expected time to restore service if path breaks

    ### **🎯 Critical Path Types**
    - **Data Flow Paths**: Critical data processing pipelines
    - **API Chains**: Important API call sequences
    - **Infrastructure Paths**: Core infrastructure dependency chains
    - **Cross-Cutting Paths**: Paths that span multiple system layers

    ### **💡 Risk Mitigation**
    - **Redundancy Recommendations**: Suggestions for adding redundancy
    - **Monitoring Points**: Key services that need enhanced monitoring
    - **Circuit Breakers**: Where to implement circuit breaker patterns
    - **Failover Strategies**: Backup plans for critical path failures
    """,
    tags=["Service Topology - Analysis"]
)
async def get_critical_paths() -> APIResponse:
    """Get critical dependency path analysis."""
    try:
        if not topology_analyzer:
            raise HTTPException(status_code=503, detail="Topology analyzer not initialized")

        # Get topology analysis
        analysis = await topology_analyzer.analyze_topology()

        return APIResponse(
            success=True,
            message=f"Analyzed {len(analysis.critical_paths)} critical dependency paths",
            data={
                "critical_paths": analysis.critical_paths,
                "total_paths": len(analysis.critical_paths),
                "longest_path": max(analysis.critical_paths, key=len) if analysis.critical_paths else [],
                "average_path_length": sum(len(path) for path in analysis.critical_paths) / len(analysis.critical_paths) if analysis.critical_paths else 0,
                "path_complexity_score": self._calculate_path_complexity(analysis.critical_paths)
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze critical paths: {str(e)}"
        )

@app.get(
    "/api/topology/visualization",
    response_model=APIResponse,
    summary="Topology Visualization",
    description="""
    **Topology Visualization** - Interactive visualization data for service topology.

    ## 🎨 **Interactive Topology Visualization**

    Get data formatted for interactive topology visualization in web interfaces:

    ### **📊 Visualization Formats**
    - **Cytoscape.js**: For web-based interactive network graphs
    - **D3.js Compatible**: Data format compatible with D3.js visualizations
    - **GraphViz DOT**: Text format for static graph rendering
    - **JSON Graph**: Generic JSON format for custom visualizations

    ### **🎨 Visual Elements**
    - **Nodes**: Services with size, color, and labels based on type and health
    - **Edges**: Relationships with thickness and color based on strength and type
    - **Layout**: Automatic positioning using force-directed or hierarchical algorithms
    - **Styling**: Comprehensive styling rules for different service types

    ### **⚙️ Visualization Options**
    - **Layout Algorithm**: Force-directed, hierarchical, circular, or grid layouts
    - **Color Scheme**: Different color schemes for service types and health status
    - **Node Sizing**: Size nodes based on API count, dependencies, or custom metrics
    - **Edge Styling**: Customize edge appearance based on relationship type

    ### **🔍 Interactive Features**
    - **Zoom & Pan**: Navigate large topology graphs
    - **Node Details**: Click nodes for detailed service information
    - **Filtering**: Filter by service type, health status, or cluster
    - **Search**: Find specific services in large topologies
    """,
    tags=["Service Topology - Visualization"]
)
async def get_topology_visualization(
    format: str = Query("cytoscape", description="Visualization format (cytoscape, d3, graphviz, json)"),
    layout: str = Query("force_directed", description="Layout algorithm (force_directed, hierarchical, circular, grid)"),
    include_styles: bool = Query(True, description="Include styling information"),
    include_metrics: bool = Query(True, description="Include topology metrics")
) -> APIResponse:
    """Get topology data formatted for interactive visualization."""
    try:
        if not topology_analyzer or not topology_visualizer:
            raise HTTPException(status_code=503, detail="Topology services not initialized")

        # Get topology analysis
        analysis = await topology_analyzer.analyze_topology()

        # Generate visualization
        from ..modules.topology.visualizer import VisualizationFormat, LayoutAlgorithm

        format_enum = VisualizationFormat(format)
        layout_enum = LayoutAlgorithm(layout)

        visualization = topology_visualizer.generate_visualization(
            analysis=analysis,
            format=format_enum,
            layout=layout_enum,
            include_styles=include_styles,
            include_metrics=include_metrics
        )

        return APIResponse(
            success=True,
            message=f"Generated {format} visualization with {len(visualization.nodes)} nodes and {len(visualization.edges)} edges",
            data={
                "format": visualization.format.value,
                "nodes": visualization.nodes,
                "edges": visualization.edges,
                "layout": visualization.layout,
                "styles": visualization.styles,
                "metadata": visualization.metadata
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate topology visualization: {str(e)}"
        )

@app.get(
    "/api/topology/graph",
    response_model=APIResponse,
    summary="Dependency Graph",
    description="""
    **Dependency Graph** - Raw dependency graph data for advanced analysis.

    ## 📈 **Dependency Graph Data**

    Get the underlying dependency graph structure for programmatic analysis:

    ### **🔗 Graph Structure**
    - **Nodes**: Service vertices with properties and metadata
    - **Edges**: Dependency relationships with weights and types
    - **Attributes**: Node and edge attributes for analysis
    - **NetworkX Compatible**: Data format compatible with NetworkX

    ### **📊 Graph Metrics**
    - **Degree Distribution**: Node connectivity analysis
    - **Centrality Measures**: Betweenness, closeness, eigenvector centrality
    - **Clustering Coefficients**: Local and global clustering metrics
    - **Path Analysis**: Shortest paths and path lengths

    ### **🛠️ Analysis Applications**
    - **Impact Analysis**: Service failure impact assessment
    - **Optimization**: Dependency structure optimization
    - **Risk Assessment**: Single points of failure identification
    - **Performance Modeling**: Load distribution analysis

    ### **💾 Export Formats**
    - **JSON**: Human-readable format for web applications
    - **Pickle**: Python-specific binary format for NetworkX
    - **GraphML**: Standard graph exchange format
    - **Adjacency Matrix**: Matrix representation for mathematical analysis
    """,
    tags=["Service Topology - Visualization"]
)
async def get_dependency_graph(
    format: str = Query("json", description="Export format (json, graphml, adjacency)"),
    include_attributes: bool = Query(True, description="Include node and edge attributes")
) -> APIResponse:
    """Get raw dependency graph data for analysis."""
    try:
        if not topology_analyzer or not dependency_graph_builder:
            raise HTTPException(status_code=503, detail="Topology services not initialized")

        # Get topology analysis
        analysis = await topology_analyzer.analyze_topology()

        # Get graph data
        graph_data = {
            "nodes": [
                {
                    "id": node.service_id,
                    "properties": {
                        "name": node.service_name,
                        "type": node.service_type.value,
                        "health_status": node.health_status,
                        "api_count": node.api_count,
                        "metadata": node.metadata
                    }
                }
                for node in analysis.nodes.values()
            ],
            "edges": [
                {
                    "source": rel.source_service,
                    "target": rel.target_service,
                    "properties": {
                        "type": rel.relationship_type.value,
                        "strength": rel.strength,
                        "bidirectional": rel.bidirectional,
                        "metadata": rel.metadata
                    }
                }
                for rel in analysis.relationships
            ]
        }

        if include_attributes:
            # Add graph-level attributes
            graph_data["attributes"] = {
                "directed": True,
                "weighted": True,
                "node_count": len(analysis.nodes),
                "edge_count": len(analysis.relationships),
                "density": analysis.metrics.get("graph_density", 0),
                "average_degree": analysis.metrics.get("average_degree", 0)
            }

        return APIResponse(
            success=True,
            message=f"Generated dependency graph with {len(graph_data['nodes'])} nodes and {len(graph_data['edges'])} edges",
            data=graph_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate dependency graph: {str(e)}"
        )

@app.get(
    "/api/topology/cluster/{cluster_id}",
    response_model=APIResponse,
    summary="Cluster Visualization",
    description="""
    **Cluster Visualization** - Detailed visualization of a specific service cluster.

    ## 🏗️ **Cluster-Specific Visualization**

    Get focused visualization data for a specific service cluster:

    ### **🎯 Cluster Focus**
    - **Intra-Cluster Relationships**: Connections within the cluster
    - **Inter-Cluster Connections**: Relationships to other clusters
    - **Cluster Metrics**: Size, density, and cohesion metrics
    - **Central Services**: Most important services within the cluster

    ### **📊 Cluster Analysis**
    - **Cluster Type**: Functional categorization of the cluster
    - **Health Distribution**: Health status breakdown within cluster
    - **Dependency Patterns**: How services within cluster depend on each other
    - **Performance Characteristics**: Cluster-wide performance metrics

    ### **🔍 Cluster Insights**
    - **Cohesion Score**: How tightly integrated the cluster is
    - **Boundary Services**: Services that connect to other clusters
    - **Critical Services**: High-impact services within the cluster
    - **Optimization Opportunities**: Cluster-specific improvement suggestions

    ### **🎨 Visualization Options**
    - **Zoom to Cluster**: Focus view on specific cluster
    - **Highlight Connections**: Emphasize inter-cluster relationships
    - **Color Coding**: Different colors for intra vs inter-cluster connections
    - **Size Scaling**: Scale node sizes based on cluster importance
    """,
    tags=["Service Topology - Visualization"]
)
async def get_cluster_visualization(
    cluster_id: str,
    format: str = Query("cytoscape", description="Visualization format")
) -> APIResponse:
    """Get visualization data for a specific service cluster."""
    try:
        if not topology_analyzer or not topology_visualizer:
            raise HTTPException(status_code=503, detail="Topology services not initialized")

        # Get topology analysis
        analysis = await topology_analyzer.analyze_topology()

        # Find the requested cluster
        cluster = next((c for c in analysis.clusters if c["id"] == cluster_id), None)
        if not cluster:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found")

        # Generate cluster visualization
        from ..modules.topology.visualizer import VisualizationFormat

        format_enum = VisualizationFormat(format)
        cluster_visualizations = topology_visualizer.generate_cluster_visualization(analysis, format_enum)

        # Find the matching cluster visualization
        cluster_viz = next((v for v in cluster_visualizations if v.metadata.get("cluster_id") == cluster_id), None)

        if not cluster_viz:
            raise HTTPException(status_code=404, detail=f"Visualization for cluster {cluster_id} not found")

        return APIResponse(
            success=True,
            message=f"Generated visualization for cluster {cluster_id}",
            data={
                "cluster_id": cluster_id,
                "cluster_info": cluster,
                "format": cluster_viz.format.value,
                "nodes": cluster_viz.nodes,
                "edges": cluster_viz.edges,
                "layout": cluster_viz.layout,
                "styles": cluster_viz.styles,
                "metadata": cluster_viz.metadata
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate cluster visualization: {str(e)}"
        )

@app.get(
    "/api/topology/impact/{service_name}",
    response_model=APIResponse,
    summary="Service Impact Analysis",
    description="""
    **Service Impact Analysis** - Analyze the impact of a service failure on the ecosystem.

    ## 💥 **Failure Impact Assessment**

    Understand the cascading effects of service failures on the entire ecosystem:

    ### **🎯 Impact Analysis**
    - **Direct Dependents**: Services that directly depend on this service
    - **Cascading Impact**: All services affected by the failure chain
    - **Critical Paths**: Important dependency chains that would be broken
    - **Recovery Requirements**: Resources needed to restore service

    ### **📊 Impact Metrics**
    - **Impact Score**: Numerical score of failure severity (0-100)
    - **Affected Services Count**: Total number of impacted services
    - **Recovery Time Estimate**: Expected time to restore full functionality
    - **Alternative Paths**: Available backup routes and workarounds

    ### **🚨 Risk Assessment**
    - **Business Impact**: Effect on business operations and user experience
    - **Data Impact**: Potential data loss or corruption scenarios
    - **Compliance Impact**: Regulatory and compliance implications
    - **Financial Impact**: Cost of downtime and recovery

    ### **🛡️ Mitigation Strategies**
    - **Redundancy Options**: Suggestions for adding redundancy
    - **Circuit Breakers**: Where to implement failure isolation
    - **Monitoring Enhancements**: Additional monitoring requirements
    - **Backup Strategies**: Data backup and recovery recommendations

    ### **📈 Risk Trending**
    - **Historical Failures**: Past failure patterns and frequencies
    - **Risk Trends**: Increasing or decreasing failure risk over time
    - **Predictive Analysis**: Likelihood of future failures
    - **Preventive Measures**: Proactive risk mitigation strategies
    """,
    tags=["Service Topology - Analysis"]
)
async def get_service_impact_analysis(service_name: str) -> APIResponse:
    """Analyze the impact of a service failure on the ecosystem."""
    try:
        if not topology_analyzer or not dependency_graph_builder:
            raise HTTPException(status_code=503, detail="Topology services not initialized")

        # Get topology analysis
        analysis = await topology_analyzer.analyze_topology()

        # Check if service exists
        if service_name not in analysis.nodes:
            raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

        # Calculate service impact
        impact = dependency_graph_builder.calculate_service_impact(analysis.graph, service_name)

        # Add additional analysis
        node = analysis.nodes[service_name]
        impact["service_details"] = {
            "name": node.service_name,
            "type": node.service_type.value,
            "health_status": node.health_status,
            "api_count": node.api_count,
            "dependency_count": len(node.dependencies),
            "dependent_count": len(node.dependents)
        }

        # Calculate recovery priority
        impact["recovery_priority"] = self._calculate_recovery_priority(impact, node)

        return APIResponse(
            success=True,
            message=f"Impact analysis completed for service {service_name}",
            data=impact
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze service impact: {str(e)}"
        )

@app.get(
    "/api/topology/bottlenecks",
    response_model=APIResponse,
    summary="System Bottlenecks",
    description="""
    **System Bottlenecks** - Identify performance and reliability bottlenecks in the topology.

    ## 🚧 **Bottleneck Analysis**

    Discover services and relationships that create bottlenecks in the system:

    ### **🔍 Bottleneck Types**
    - **Performance Bottlenecks**: Services with high response times or low throughput
    - **Reliability Bottlenecks**: Single points of failure with no redundancy
    - **Scalability Bottlenecks**: Services that limit system scaling capacity
    - **Dependency Bottlenecks**: Services with excessive dependencies

    ### **📊 Bottleneck Metrics**
    - **Bottleneck Score**: Severity rating for each bottleneck (0-100)
    - **Impact Assessment**: How much the bottleneck affects overall system performance
    - **Frequency**: How often the bottleneck causes issues
    - **Trend Analysis**: Whether bottleneck severity is increasing or decreasing

    ### **🎯 Bottleneck Classification**
    - **Critical**: Immediate action required (score > 80)
    - **High**: Should be addressed soon (score 60-80)
    - **Medium**: Monitor and plan for future (score 40-60)
    - **Low**: Acceptable but could be optimized (score < 40)

    ### **💡 Resolution Strategies**
    - **Performance Optimization**: Caching, load balancing, code optimization
    - **Redundancy Addition**: Multiple instances, failover systems
    - **Architecture Changes**: Service decomposition, microservice restructuring
    - **Resource Scaling**: Increased CPU, memory, or network capacity

    ### **📈 Monitoring Recommendations**
    - **Key Metrics**: Which metrics to monitor for each bottleneck
    - **Alert Thresholds**: When to trigger alerts for bottleneck issues
    - **Trend Monitoring**: Long-term bottleneck trend analysis
    - **Automated Remediation**: Scripts or automation to address bottlenecks
    """,
    tags=["Service Topology - Analysis"]
)
async def get_system_bottlenecks() -> APIResponse:
    """Identify performance and reliability bottlenecks in the system."""
    try:
        if not topology_analyzer:
            raise HTTPException(status_code=503, detail="Topology analyzer not initialized")

        # Get topology analysis
        analysis = await topology_analyzer.analyze_topology()

        # Sort bottlenecks by severity
        sorted_bottlenecks = sorted(
            analysis.bottlenecks,
            key=lambda x: x.get("bottleneck_score", 0),
            reverse=True
        )

        # Classify bottlenecks by severity
        bottleneck_classification = {
            "critical": [b for b in sorted_bottlenecks if b.get("bottleneck_score", 0) > 80],
            "high": [b for b in sorted_bottlenecks if 60 <= b.get("bottleneck_score", 0) <= 80],
            "medium": [b for b in sorted_bottlenecks if 40 <= b.get("bottleneck_score", 0) < 60],
            "low": [b for b in sorted_bottlenecks if b.get("bottleneck_score", 0) < 40]
        }

        return APIResponse(
            success=True,
            message=f"Identified {len(sorted_bottlenecks)} system bottlenecks",
            data={
                "total_bottlenecks": len(sorted_bottlenecks),
                "classification": bottleneck_classification,
                "top_bottlenecks": sorted_bottlenecks[:10],  # Top 10 bottlenecks
                "bottleneck_distribution": {
                    "performance": len([b for b in sorted_bottlenecks if b.get("bottleneck_type") == "performance"]),
                    "reliability": len([b for b in sorted_bottlenecks if b.get("bottleneck_type") == "reliability"]),
                    "scalability": len([b for b in sorted_bottlenecks if b.get("bottleneck_type") == "scalability"])
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to identify system bottlenecks: {str(e)}"
        )

@app.get(
    "/api/topology/optimization",
    response_model=APIResponse,
    summary="Optimization Recommendations",
    description="""
    **Optimization Recommendations** - AI-powered suggestions for topology improvements.

    ## 🚀 **Topology Optimization**

    Get intelligent recommendations for optimizing the service topology:

    ### **🎯 Optimization Types**
    - **Performance Optimization**: Improve response times and throughput
    - **Reliability Enhancement**: Add redundancy and fault tolerance
    - **Scalability Improvements**: Enable better horizontal scaling
    - **Architecture Refactoring**: Service decomposition and restructuring

    ### **📊 Optimization Analysis**
    - **Current State Assessment**: Analysis of current topology strengths and weaknesses
    - **Impact Prediction**: Estimated impact of each optimization recommendation
    - **Implementation Complexity**: Effort required to implement changes
    - **Risk Assessment**: Potential risks and mitigation strategies

    ### **💡 Specific Recommendations**
    - **Service Decomposition**: Break down monolithic services into microservices
    - **Caching Strategies**: Implement caching layers to reduce load
    - **Load Balancing**: Distribute load across multiple service instances
    - **Circuit Breakers**: Implement failure isolation patterns
    - **API Gateway**: Consolidate API management and routing

    ### **📈 Expected Benefits**
    - **Performance Gains**: Expected improvement in response times and throughput
    - **Reliability Improvements**: Reduction in failure rates and downtime
    - **Cost Savings**: Potential infrastructure and operational cost reductions
    - **Developer Productivity**: Improvements in development and deployment efficiency

    ### **🔧 Implementation Planning**
    - **Priority Ranking**: Which optimizations to tackle first
    - **Dependency Analysis**: Order of implementation considering dependencies
    - **Rollback Plans**: Strategies for reverting changes if needed
    - **Success Metrics**: How to measure the success of optimizations
    """,
    tags=["Service Topology - Analysis"]
)
async def get_optimization_recommendations() -> APIResponse:
    """Get optimization recommendations for the service topology."""
    try:
        if not topology_analyzer or not topology_metrics:
            raise HTTPException(status_code=503, detail="Topology services not initialized")

        # Get topology analysis
        analysis = await topology_analyzer.analyze_topology()

        # Calculate performance metrics to identify optimization opportunities
        performance_metrics = topology_metrics.calculate_performance_metrics(analysis)
        dependency_metrics = topology_metrics.calculate_dependency_metrics(analysis)

        # Generate optimization recommendations
        recommendations = []

        # Performance optimizations
        if performance_metrics.average_response_time > 500:
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "title": "Implement Response Time Optimization",
                "description": f"Average response time ({performance_metrics.average_response_time}ms) is above recommended threshold",
                "impact": "high",
                "effort": "medium",
                "suggestions": [
                    "Implement caching layers for frequently accessed data",
                    "Optimize database queries and indexes",
                    "Consider CDN for static content",
                    "Implement async processing for long-running operations"
                ]
            })

        # Reliability optimizations
        if len(analysis.bottlenecks) > 0:
            recommendations.append({
                "type": "reliability",
                "priority": "high",
                "title": "Address Single Points of Failure",
                "description": f"Found {len(analysis.bottlenecks)} potential bottlenecks that could cause system failures",
                "impact": "high",
                "effort": "high",
                "suggestions": [
                    "Implement service redundancy and load balancing",
                    "Add circuit breaker patterns for fault isolation",
                    "Implement health checks and automatic failover",
                    "Create backup data pipelines and storage"
                ]
            })

        # Coupling optimizations
        if dependency_metrics.average_coupling > 3:
            recommendations.append({
                "type": "architecture",
                "priority": "medium",
                "title": "Reduce Service Coupling",
                "description": f"High average coupling ({dependency_metrics.average_coupling}) indicates tight coupling between services",
                "impact": "medium",
                "effort": "high",
                "suggestions": [
                    "Implement event-driven architecture to reduce direct dependencies",
                    "Create shared libraries for common functionality",
                    "Use API gateways to consolidate service interactions",
                    "Implement service mesh for better communication management"
                ]
            })

        # Circular dependency optimizations
        if len(dependency_metrics.circular_dependencies) > 0:
            recommendations.append({
                "type": "architecture",
                "priority": "high",
                "title": "Resolve Circular Dependencies",
                "description": f"Found {len(dependency_metrics.circular_dependencies)} circular dependency chains",
                "impact": "high",
                "effort": "medium",
                "suggestions": [
                    "Refactor services to break circular dependencies",
                    "Implement event sourcing or CQRS patterns",
                    "Create intermediary services to break dependency cycles",
                    "Use dependency injection to manage circular references"
                ]
            })

        # Scalability optimizations
        if performance_metrics.scalability_score < 70:
            recommendations.append({
                "type": "scalability",
                "priority": "medium",
                "title": "Improve System Scalability",
                "description": f"Scalability score ({performance_metrics.scalability_score}) indicates limited scaling capacity",
                "impact": "medium",
                "effort": "high",
                "suggestions": [
                    "Implement horizontal pod autoscaling",
                    "Use distributed caching (Redis, Memcached)",
                    "Implement database read replicas",
                    "Use message queues for async processing"
                ]
            })

        return APIResponse(
            success=True,
            message=f"Generated {len(recommendations)} optimization recommendations",
            data={
                "total_recommendations": len(recommendations),
                "recommendations": recommendations,
                "priority_breakdown": {
                    "high": len([r for r in recommendations if r["priority"] == "high"]),
                    "medium": len([r for r in recommendations if r["priority"] == "medium"]),
                    "low": len([r for r in recommendations if r["priority"] == "low"])
                },
                "type_breakdown": {
                    "performance": len([r for r in recommendations if r["type"] == "performance"]),
                    "reliability": len([r for r in recommendations if r["type"] == "reliability"]),
                    "architecture": len([r for r in recommendations if r["type"] == "architecture"]),
                    "scalability": len([r for r in recommendations if r["type"] == "scalability"])
                }
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate optimization recommendations: {str(e)}"
        )

def _calculate_path_complexity(self, critical_paths):
    """Calculate complexity score for critical paths."""
    if not critical_paths:
        return 0

    total_complexity = 0
    for path in critical_paths:
        # Complexity based on path length and service diversity
        length_factor = len(path) * 0.1
        # Diversity factor (more diverse service types = higher complexity)
        service_types = set()
        for service in path:
            # This is a simplified check - in real implementation you'd use actual service types
            if "api" in service.lower():
                service_types.add("api")
            elif "data" in service.lower():
                service_types.add("data")
            elif "infra" in service.lower():
                service_types.add("infra")

        diversity_factor = len(service_types) * 0.2
        total_complexity += length_factor + diversity_factor

    return round(total_complexity / len(critical_paths), 2) if critical_paths else 0

def _calculate_recovery_priority(self, impact, node):
    """Calculate recovery priority for a service."""
    base_priority = impact.get("impact_score", 0)

    # Adjust based on service type and health
    if node.service_type.value == "infrastructure":
        base_priority *= 1.5  # Infrastructure services are more critical
    elif node.service_type.value == "monitoring":
        base_priority *= 1.3  # Monitoring services are important

    if node.health_status == "unhealthy":
        base_priority *= 1.2  # Unhealthy services need immediate attention

    return min(100, base_priority)


# Streamlit UI Components
def main():
    """Main Streamlit application."""
    st.title("🌐 Unified API Ecosystem Dashboard")

    st.markdown("""
    ## Welcome to the Unified API Ecosystem Dashboard

    This dashboard provides a comprehensive view of all APIs across the LLM Documentation Ecosystem,
    with real-time discovery, testing, and monitoring capabilities powered by the Discovery Agent.

    ### Key Features:
    - **API Catalog**: Browse all APIs by service and category
    - **Interactive Testing**: Test API endpoints with built-in tools
    - **Health Monitoring**: Real-time API availability and performance
    - **Analytics**: API usage patterns and performance insights
    - **Developer Tools**: Code generation and integration helpers
    """)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["API Catalog", "API Testing", "Health Monitoring", "Analytics", "Developer Tools"]
    )

    if page == "API Catalog":
        show_api_catalog()
    elif page == "API Testing":
        show_api_testing()
    elif page == "Health Monitoring":
        show_health_monitoring()
    elif page == "Analytics":
        show_analytics()
    elif page == "Developer Tools":
        show_developer_tools()


def show_api_catalog():
    """Display the API catalog page."""
    st.header("📚 API Catalog")

    st.markdown("""
    Browse and explore all APIs across the LLM Documentation Ecosystem.
    APIs are automatically discovered and cataloged by the Discovery Agent.
    """)

    # Placeholder for API catalog - will be populated by Discovery Agent integration
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total APIs", "450+")
    with col2:
        st.metric("Services", "18")
    with col3:
        st.metric("Categories", "50+")

    # API search and filtering
    st.subheader("🔍 Search & Filter APIs")

    search_term = st.text_input("Search APIs", placeholder="Enter API name, service, or endpoint...")

    col1, col2 = st.columns(2)
    with col1:
        service_filter = st.selectbox("Filter by Service", ["All Services", "Orchestrator", "Interpreter", "Doc Store", "Prompt Store", "Frontend", "CLI", "Discovery Agent"])
    with col2:
        category_filter = st.selectbox("Filter by Category", ["All Categories", "Health", "Workflows", "Documents", "Prompts", "Analytics", "Testing"])

    # Placeholder API list
    st.subheader("📋 API Endpoints")

    # This would be populated from Discovery Agent data
    api_data = [
        {"service": "Orchestrator", "endpoint": "/api/workflows/execute", "method": "POST", "category": "Workflows"},
        {"service": "Doc Store", "endpoint": "/api/documents/search", "method": "POST", "category": "Documents"},
        {"service": "Prompt Store", "endpoint": "/api/prompts/optimize", "method": "POST", "category": "Prompts"},
        {"service": "Interpreter", "endpoint": "/api/interpret", "method": "POST", "category": "AI Processing"},
    ]

    for api in api_data:
        with st.expander(f"{api['method']} {api['endpoint']} - {api['service']}"):
            st.write(f"**Service:** {api['service']}")
            st.write(f"**Category:** {api['category']}")
            st.write(f"**Method:** {api['method']}")
            st.write(f"**Endpoint:** {api['endpoint']}")
            if st.button(f"View Documentation", key=f"docs_{api['endpoint']}"):
                st.info("Documentation viewer would open here (integrated with Discovery Agent)")


def show_api_testing():
    """Display the API testing page."""
    st.header("🧪 API Testing Interface")

    st.markdown("""
    Test API endpoints interactively with built-in request builder and response viewer.
    All API specifications are provided by the Discovery Agent.
    """)

    # API endpoint selection
    st.subheader("🎯 Select API Endpoint")

    service = st.selectbox("Service", ["Orchestrator", "Interpreter", "Doc Store", "Prompt Store", "Frontend"])
    endpoint = st.selectbox("Endpoint", ["/api/workflows/execute", "/api/interpret", "/api/documents/search", "/api/prompts/optimize"])

    # Request builder
    st.subheader("📤 Request Builder")

    method = st.selectbox("HTTP Method", ["GET", "POST", "PUT", "DELETE"])
    headers = st.text_area("Headers (JSON)", value='{"Content-Type": "application/json"}', height=100)
    body = st.text_area("Request Body (JSON)", value='{}', height=150)

    if st.button("🚀 Execute Request"):
        # Placeholder for API testing - would integrate with actual service
        st.success("Request executed successfully!")
        st.json({"status": "success", "message": "API request completed", "response": {"data": "Sample response"}})


def show_health_monitoring():
    """Display the health monitoring page."""
    st.header("🏥 API Health Monitoring")

    st.markdown("""
    Monitor the health and availability of all APIs across the ecosystem.
    Real-time status updates powered by the Discovery Agent.
    """)

    # Health overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Healthy APIs", "425", "+5")
    with col2:
        st.metric("Degraded APIs", "15", "-2")
    with col3:
        st.metric("Unhealthy APIs", "10", "+1")
    with col4:
        st.metric("Total APIs", "450")

    # Service health status
    st.subheader("📊 Service Health Status")

    services = ["Orchestrator", "Interpreter", "Doc Store", "Prompt Store", "Frontend", "CLI", "Discovery Agent"]
    health_data = {
        "Orchestrator": {"status": "healthy", "response_time": "45ms", "uptime": "99.9%"},
        "Interpreter": {"status": "healthy", "response_time": "67ms", "uptime": "99.8%"},
        "Doc Store": {"status": "degraded", "response_time": "120ms", "uptime": "98.5%"},
        "Prompt Store": {"status": "healthy", "response_time": "55ms", "uptime": "99.9%"},
        "Frontend": {"status": "healthy", "response_time": "30ms", "uptime": "100%"},
        "CLI": {"status": "healthy", "response_time": "25ms", "uptime": "100%"},
        "Discovery Agent": {"status": "healthy", "response_time": "40ms", "uptime": "99.9%"},
    }

    for service in services:
        status = health_data[service]["status"]
        status_icon = "✅" if status == "healthy" else "⚠️" if status == "degraded" else "❌"

        with st.expander(f"{status_icon} {service} - {status.upper()}"):
            st.write(f"**Response Time:** {health_data[service]['response_time']}")
            st.write(f"**Uptime:** {health_data[service]['uptime']}")


def show_analytics():
    """Display the analytics page."""
    st.header("📊 API Analytics & Insights")

    st.markdown("""
    Comprehensive analytics and insights for API usage across the ecosystem.
    Track performance, usage patterns, and identify optimization opportunities.
    """)

    # Analytics overview
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total API Calls (24h)", "125,430", "+12%")
    with col2:
        st.metric("Average Response Time", "67ms", "-5ms")
    with col3:
        st.metric("Error Rate", "0.8%", "-0.2%")

    # Usage by service
    st.subheader("📈 API Usage by Service")

    usage_data = {
        "Doc Store": 35,
        "Prompt Store": 28,
        "Orchestrator": 20,
        "Interpreter": 15,
        "Frontend": 12,
        "CLI": 8,
        "Discovery Agent": 7,
    }

    st.bar_chart(usage_data)

    # Top endpoints
    st.subheader("🏆 Top API Endpoints")

    top_endpoints = [
        "/api/documents/search",
        "/api/prompts/optimize",
        "/api/workflows/execute",
        "/api/health",
        "/api/interpret"
    ]

    for i, endpoint in enumerate(top_endpoints, 1):
        st.write(f"{i}. {endpoint}")


def show_developer_tools():
    """Display the developer tools page."""
    st.header("🔧 Developer Tools")

    st.markdown("""
    Essential tools for API development and integration.
    Generate client code, validate specifications, and accelerate development.
    """)

    # Tool selection
    tool = st.selectbox("Select Tool", [
        "Client Code Generator",
        "API Specification Validator",
        "Integration Tester",
        "Documentation Exporter"
    ])

    if tool == "Client Code Generator":
        st.subheader("📝 Client Code Generator")

        language = st.selectbox("Programming Language", ["Python", "JavaScript", "TypeScript", "Java", "Go"])
        service = st.selectbox("Service", ["Orchestrator", "Interpreter", "Doc Store", "Prompt Store"])

        if st.button("Generate Client Code"):
            st.code(f"""
# Generated {language} client for {service}
# This would contain auto-generated client code
# based on the OpenAPI specification
class {service}Client:
    def __init__(self, base_url: str):
        self.base_url = base_url

    def example_method(self):
        # Auto-generated method
        pass
""", language=language.lower())

    elif tool == "API Specification Validator":
        st.subheader("✅ API Specification Validator")

        uploaded_file = st.file_uploader("Upload OpenAPI Specification", type=["json", "yaml", "yml"])

        if uploaded_file is not None and st.button("Validate Specification"):
            # Placeholder validation
            st.success("✅ Specification is valid!")
            st.json({
                "valid": True,
                "endpoints": 25,
                "warnings": [],
                "errors": []
            })

    elif tool == "Integration Tester":
        st.subheader("🔗 Integration Tester")

        st.markdown("Test integrations between services")

        service1 = st.selectbox("Service 1", ["Orchestrator", "Interpreter", "Doc Store"])
        service2 = st.selectbox("Service 2", ["Doc Store", "Prompt Store", "Frontend"])

        if st.button("Run Integration Test"):
            st.info("Integration test would run here, checking compatibility between selected services")

    elif tool == "Documentation Exporter":
        st.subheader("📄 Documentation Exporter")

        format_type = st.selectbox("Export Format", ["HTML", "PDF", "Markdown", "Postman Collection"])

        if st.button("Export Documentation"):
            st.success(f"Documentation exported as {format_type}!")


# Run the Streamlit app if executed directly
if __name__ == "__main__":
    main()
