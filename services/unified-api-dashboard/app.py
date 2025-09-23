"""
Unified API Dashboard - Enterprise API Management Platform

FastAPI application providing comprehensive API discovery, testing, monitoring,
analytics, and management capabilities for enterprise API ecosystems.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import stub classes from modules
from modules.discovery import DiscoveryClient
from modules.catalog import APICatalogManager
from modules.health import HealthMonitor
from modules.testing import APITester
from modules.analytics import UsageAnalytics, PerformanceInsights, ErrorTracking, UsagePatterns
from modules.developer_tools import ClientCodeGenerator, APIValidator, IntegrationTester
from modules.topology import TopologyAnalyzer, TopologyVisualizer, DependencyGraphBuilder, TopologyMetrics
from modules.security import AuthenticationManager, AuthorizationManager
from modules.performance import CacheManager, PerformanceMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(level)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global service instances
service_instances: Dict[str, Any] = {}

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""

    logger.info("🚀 Starting Unified API Dashboard...")

    try:
        # Initialize core services
        logger.info("📦 Initializing core services...")

        # Cache system - stub implementation for now
        # memory_cache = MemoryCache(max_size=1000, compression_threshold=1024)
        # cache_manager = CacheManager(cache=TieredCache(
        #     l1_cache=memory_cache,
        #     l2_cache=None  # Redis cache would be initialized here if available
        # ))
        cache_manager = CacheManager()

        # Core discovery and catalog
        discovery_client = DiscoveryClient(
            base_url=os.getenv("DISCOVERY_AGENT_URL", "http://localhost:5045")
        )
        catalog_manager = APICatalogManager(
            discovery_client=discovery_client,
            cache_manager=cache_manager
        )
        health_monitor = HealthMonitor(discovery_client=discovery_client)
        api_tester = APITester()

        # Analytics modules
        usage_analytics = UsageAnalytics(
            discovery_client=discovery_client,
            health_monitor=health_monitor
        )
        performance_insights = PerformanceInsights(
            discovery_client=discovery_client,
            health_monitor=health_monitor
        )
        error_tracking = ErrorTracking(
            discovery_client=discovery_client,
            health_monitor=health_monitor
        )
        usage_patterns = UsagePatterns(
            discovery_client=discovery_client,
            health_monitor=health_monitor
        )

        # Developer tools
        client_generator = ClientCodeGenerator()
        api_validator = APIValidator()
        integration_tester = IntegrationTester()

        # Service topology
        topology_analyzer = TopologyAnalyzer(
            discovery_client=discovery_client,
            catalog_manager=catalog_manager,
            health_monitor=health_monitor
        )
        topology_visualizer = TopologyVisualizer()
        graph_builder = DependencyGraphBuilder()
        topology_metrics = TopologyMetrics()

        # Security modules
        auth_manager = AuthenticationManager()
        authorization_manager = AuthorizationManager()
        access_control = AccessControlManager()
        audit_logger = AuditLogger()
        security_monitor = SecurityMonitor()

        # Performance monitoring
        performance_monitor = PerformanceMonitor()
        bottleneck_detector = BottleneckDetector(performance_monitor)

        # Store service instances
        service_instances.update({
            "cache_manager": cache_manager,
            "discovery_client": discovery_client,
            "catalog_manager": catalog_manager,
            "health_monitor": health_monitor,
            "api_tester": api_tester,
            "usage_analytics": usage_analytics,
            "performance_insights": performance_insights,
            "error_tracking": error_tracking,
            "usage_patterns": usage_patterns,
            "client_generator": client_generator,
            "api_validator": api_validator,
            "integration_tester": integration_tester,
            "topology_analyzer": topology_analyzer,
            "topology_visualizer": topology_visualizer,
            "graph_builder": graph_builder,
            "topology_metrics": topology_metrics,
            "auth_manager": auth_manager,
            "authorization_manager": authorization_manager,
            "access_control": access_control,
            "audit_logger": audit_logger,
            "security_monitor": security_monitor,
            "performance_monitor": performance_monitor,
            "bottleneck_detector": bottleneck_detector
        })

        # Start background services
        logger.info("🔄 Starting background services...")
        # await performance_monitor.start_monitoring()  # Commented out for stub implementation

        logger.info("✅ All services initialized successfully")

    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down services...")

    try:
        # await performance_monitor.stop_monitoring()  # Commented out for stub implementation
        logger.info("✅ Services shut down gracefully")
    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")

# Create FastAPI application
app = FastAPI(
    title="Unified API Dashboard",
    description="Enterprise API Management Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Security
security = HTTPBearer(auto_error=False)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8501").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(TrustedHostMiddleware,
        allowed_hosts=os.getenv("ALLOWED_HOSTS", "").split(",") if os.getenv("ALLOWED_HOSTS") else None
    )

# Dependency injection
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current authenticated user."""
    if not credentials:
        return None

    try:
        # In a real implementation, this would validate the JWT token
        # For now, return a mock user
        return {"user_id": "demo-user", "username": "demo", "role": "developer"}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": list(service_instances.keys())
    }

# API Discovery endpoints
@app.get("/api/discovery/services")
async def get_discovered_services(user: Dict = Depends(get_current_user)):
    """Get all discovered services."""
    try:
        discovery_client = service_instances["discovery_client"]
        services = await discovery_client.discover_services()
        return {"success": True, "data": services}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

@app.post("/api/discovery/scan")
async def trigger_discovery_scan(user: Dict = Depends(get_current_user)):
    """Trigger a new discovery scan."""
    try:
        discovery_client = service_instances["discovery_client"]
        result = await discovery_client.scan_network()
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")

# API Catalog endpoints
@app.get("/api/catalog/endpoints")
async def get_api_catalog(service: Optional[str] = None, search: Optional[str] = None,
                         limit: int = 50, offset: int = 0, user: Dict = Depends(get_current_user)):
    """Get API catalog with filtering and pagination."""
    try:
        catalog_manager = service_instances["catalog_manager"]
        result = await catalog_manager.get_catalog(
            service_filter=service,
            search_term=search,
            limit=limit,
            offset=offset
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Catalog query failed: {str(e)}")

# Health monitoring endpoints
@app.get("/api/health/services")
async def get_service_health(user: Dict = Depends(get_current_user)):
    """Get health status of all services."""
    try:
        health_monitor = service_instances["health_monitor"]
        health_status = await health_monitor.get_health_overview()
        return {"success": True, "data": health_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Analytics endpoints
@app.get("/api/analytics/usage/overview")
async def get_usage_overview(user: Dict = Depends(get_current_user)):
    """Get API usage overview."""
    try:
        usage_analytics = service_instances["usage_analytics"]
        overview = await usage_analytics.get_usage_overview()
        return {"success": True, "data": overview}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics query failed: {str(e)}")

@app.get("/api/analytics/performance/insights")
async def get_performance_insights(user: Dict = Depends(get_current_user)):
    """Get performance insights."""
    try:
        performance_insights = service_instances["performance_insights"]
        insights = await performance_insights.analyze_response_times()
        return {"success": True, "data": insights}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Performance analysis failed: {str(e)}")

# Developer tools endpoints
@app.post("/api/tools/generate-client")
async def generate_client_code(request: Dict[str, Any], user: Dict = Depends(get_current_user)):
    """Generate client SDK code."""
    try:
        client_generator = service_instances["client_generator"]
        service_name = request.get("service_name")
        language = request.get("language", "python")

        code = await client_generator.generate_client(service_name, language)
        return {"success": True, "data": {"language": language, "client_code": code}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")

@app.post("/api/tools/validate-spec")
async def validate_api_spec(request: Dict[str, Any], user: Dict = Depends(get_current_user)):
    """Validate OpenAPI specification."""
    try:
        api_validator = service_instances["api_validator"]
        service_name = request.get("service_name")
        openapi_spec = request.get("openapi_spec")

        validation_result = await api_validator.validate_openapi_spec(service_name, openapi_spec)
        return {"success": True, "data": validation_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

# Service topology endpoints
@app.get("/api/topology/analysis")
async def get_topology_analysis(user: Dict = Depends(get_current_user)):
    """Get service topology analysis."""
    try:
        topology_analyzer = service_instances["topology_analyzer"]
        analysis = await topology_analyzer.analyze_topology()
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Topology analysis failed: {str(e)}")

@app.get("/api/topology/visualization")
async def get_topology_visualization(format: str = "cytoscape", user: Dict = Depends(get_current_user)):
    """Get topology visualization data."""
    try:
        topology_visualizer = service_instances["topology_visualizer"]
        visualization = await topology_visualizer.generate_visualization(format=format)
        return {"success": True, "data": visualization}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Visualization failed: {str(e)}")

# Security endpoints
@app.post("/api/auth/login")
async def login(request: Dict[str, str]):
    """User authentication."""
    try:
        auth_manager = service_instances["auth_manager"]
        username = request.get("username")
        password = request.get("password")

        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")

        token = await auth_manager.authenticate_user(username, password)
        return {"success": True, "data": {"token": token}}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@app.get("/api/security/threats")
async def get_security_threats(limit: int = 100, user: Dict = Depends(get_current_user)):
    """Get security threats and alerts."""
    try:
        security_monitor = service_instances["security_monitor"]
        threats = await security_monitor.get_recent_threats(limit=limit)
        return {"success": True, "data": threats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Security query failed: {str(e)}")

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )

# Startup message
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("🌐 Unified API Dashboard started successfully")
    logger.info(f"📊 Available services: {len(service_instances)}")
    logger.info("🔗 API Documentation: http://localhost:8000/docs")

if __name__ == "__main__":
    port = int(os.getenv("SERVICE_PORT", "8000"))
    host = os.getenv("SERVICE_HOST", "127.0.0.1")

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
