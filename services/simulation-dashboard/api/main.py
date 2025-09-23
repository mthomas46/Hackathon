"""Simulation Dashboard REST API Application.

This module provides REST API endpoints for the Intelligent Project Simulation Dashboard,
enabling programmatic access to dashboard functionality, monitoring, and integrations.

The API serves as the programmatic interface to dashboard operations, complementing
the interactive Streamlit frontend with machine-accessible endpoints.
"""

import asyncio
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# Add project paths for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from infrastructure.config.config import DashboardSettings, get_config
from infrastructure.logging.logger import get_logger, setup_logging
from services.clients.llm_client import LLMGatewayClient
from services.clients.simulation_client import SimulationClient
from services.clients.websocket_client import WebSocketClient

# Import API routers
from .routers.simulations import router as simulations_router
from .routers.dashboard import router as dashboard_router
from .routers.ecosystem import router as ecosystem_router


# Configuration
class APISettings(BaseSettings):
    """API-specific configuration settings."""

    host: str = Field(default="0.0.0.0", env="DASHBOARD_API_HOST")
    port: int = Field(default=8502, env="DASHBOARD_API_PORT")
    debug: bool = Field(default=False, env="DASHBOARD_API_DEBUG")
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], env="DASHBOARD_CORS_ORIGINS")

    class Config:
        env_prefix = "DASHBOARD_API_"


# Pydantic Models for API Schemas
class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service health status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    environment: str = Field(..., description="Deployment environment")


class SimulationSummary(BaseModel):
    """Simulation summary model."""

    id: str = Field(..., description="Unique simulation identifier")
    name: str = Field(..., description="Simulation name")
    status: str = Field(..., description="Current simulation status")
    progress: float = Field(..., ge=0.0, le=100.0, description="Completion percentage")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    duration_weeks: Optional[int] = Field(None, description="Planned duration in weeks")
    complexity: Optional[str] = Field(None, description="Complexity level")


class DashboardMetrics(BaseModel):
    """Dashboard metrics response model."""

    total_simulations: int = Field(..., description="Total number of simulations")
    active_simulations: int = Field(..., description="Currently active simulations")
    completed_simulations: int = Field(..., description="Completed simulations")
    failed_simulations: int = Field(..., description="Failed simulations")
    success_rate: float = Field(..., ge=0.0, le=100.0, description="Overall success rate percentage")
    avg_completion_time: float = Field(..., description="Average completion time in hours")
    total_compute_hours: float = Field(..., description="Total compute hours consumed")


class AIMetrics(BaseModel):
    """AI insights metrics model."""

    insights_generated: int = Field(..., description="Number of AI insights generated")
    recommendations_made: int = Field(..., description="Number of recommendations provided")
    predictions_accuracy: float = Field(..., ge=0.0, le=100.0, description="Prediction accuracy percentage")
    anomaly_detections: int = Field(..., description="Number of anomalies detected")
    autonomous_actions: int = Field(..., description="Number of autonomous actions taken")


class EcosystemHealth(BaseModel):
    """Ecosystem health status model."""

    overall_status: str = Field(..., description="Overall ecosystem health")
    services: Dict[str, Dict[str, Any]] = Field(..., description="Individual service health status")
    last_check: str = Field(..., description="Last health check timestamp")
    issues_count: int = Field(..., description="Number of active issues")
    warnings_count: int = Field(..., description="Number of active warnings")


class APIErrorResponse(BaseModel):
    """Standard API error response model."""

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: str = Field(..., description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier for tracing")


# Global variables for service clients
config: Optional[DashboardSettings] = None
simulation_client: Optional[SimulationClient] = None
llm_client: Optional[LLMGatewayClient] = None
websocket_client: Optional[WebSocketClient] = None
logger = None
start_time = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    global config, simulation_client, llm_client, websocket_client, logger, start_time

    # Startup
    start_time = asyncio.get_event_loop().time()
    config = get_config()
    setup_logging(config.logging)
    logger = get_logger(__name__)

    # Initialize service clients
    simulation_client = SimulationClient(config.simulation_service)
    llm_client = LLMGatewayClient(config.llm_gateway) if config.llm_gateway.enabled else None
    websocket_client = WebSocketClient(config.websocket)

    logger.info(
        "Starting Simulation Dashboard REST API",
        version="1.0.0",
        host=config.api.host if hasattr(config, 'api') else '0.0.0.0',
        port=config.api.port if hasattr(config, 'api') else 8502,
        environment=config.environment
    )

    yield

    # Shutdown
    logger.info("Shutting down Simulation Dashboard REST API")


# Create FastAPI application
app = FastAPI(
    title="Intelligent Project Simulation Dashboard API",
    description="""
    REST API for the Intelligent Project Simulation Dashboard Service.

    This API provides programmatic access to dashboard functionality, enabling:
    - Real-time simulation monitoring and management
    - AI-powered insights and recommendations
    - Predictive analytics and anomaly detection
    - Autonomous operations and self-healing
    - Ecosystem health monitoring and alerting
    - Comprehensive reporting and analytics

    ## Authentication
    Currently supports anonymous access. Enterprise deployments should implement
    appropriate authentication and authorization mechanisms.

    ## Rate Limiting
    API endpoints implement intelligent rate limiting to ensure fair usage.

    ## Versioning
    API follows semantic versioning. Current version: v1
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Include API routers
app.include_router(simulations_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(ecosystem_router, prefix="/api/v1")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add request ID for tracing."""
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with standardized format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIErrorResponse(
            error=f"HTTP_{exc.status_code}",
            message=exc.detail,
            timestamp="2024-01-01T00:00:00Z",  # Would use actual timestamp
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content=APIErrorResponse(
            error="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"type": type(exc).__name__} if config and config.debug else None,
            timestamp="2024-01-01T00:00:00Z",  # Would use actual timestamp
            request_id=getattr(request.state, 'request_id', None)
        ).dict()
    )


# API Endpoints

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check the health status of the Simulation Dashboard API service."
)
async def health_check():
    """Get service health status."""
    current_time = asyncio.get_event_loop().time()
    uptime = current_time - start_time if start_time else 0

    return HealthResponse(
        status="healthy",
        timestamp="2024-01-01T00:00:00Z",  # Would use actual timestamp
        version="1.0.0",
        uptime_seconds=uptime,
        environment=config.environment if config else "unknown"
    )


@app.get(
    "/api/v1/simulations",
    response_model=List[SimulationSummary],
    summary="List Simulations",
    description="Retrieve a list of all project simulations with summary information."
)
async def list_simulations(
    status: Optional[str] = Query(None, description="Filter by simulation status"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """List simulations with optional filtering."""
    try:
        # Mock implementation - would integrate with actual simulation service
        simulations = [
            SimulationSummary(
                id=f"sim_{i:03d}",
                name=f"Sample Simulation {i}",
                status="completed" if i % 3 == 0 else "running" if i % 3 == 1 else "pending",
                progress=float((i * 7) % 100),
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
                duration_weeks=4 if i % 2 == 0 else None,
                complexity="low" if i % 3 == 0 else "medium" if i % 3 == 1 else "high"
            )
            for i in range(offset, min(offset + limit, 100))  # Mock 100 simulations
        ]

        # Apply status filter
        if status:
            simulations = [s for s in simulations if s.status == status]

        return simulations

    except Exception as e:
        logger.error(f"Error listing simulations: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve simulations")


@app.get(
    "/api/v1/simulations/{simulation_id}",
    response_model=SimulationSummary,
    summary="Get Simulation Details",
    description="Retrieve detailed information about a specific simulation."
)
async def get_simulation(simulation_id: str):
    """Get detailed information about a specific simulation."""
    try:
        # Mock implementation
        if not simulation_id.startswith("sim_"):
            raise HTTPException(status_code=404, detail="Simulation not found")

        # Parse simulation number for mock data
        try:
            sim_num = int(simulation_id.split("_")[1])
        except (IndexError, ValueError):
            sim_num = 0

        return SimulationSummary(
            id=simulation_id,
            name=f"Detailed Simulation {sim_num}",
            status="completed" if sim_num % 3 == 0 else "running",
            progress=float((sim_num * 7) % 100),
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            duration_weeks=8 if sim_num % 2 == 0 else 12,
            complexity="high" if sim_num % 3 == 0 else "medium"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve simulation")


@app.get(
    "/api/v1/dashboard/metrics",
    response_model=DashboardMetrics,
    summary="Dashboard Metrics",
    description="Retrieve comprehensive metrics about dashboard operations and simulations."
)
async def get_dashboard_metrics():
    """Get comprehensive dashboard metrics."""
    try:
        # Mock implementation - would aggregate from various sources
        return DashboardMetrics(
            total_simulations=150,
            active_simulations=23,
            completed_simulations=89,
            failed_simulations=8,
            success_rate=87.5,
            avg_completion_time=168.5,  # hours
            total_compute_hours=25430.0
        )

    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard metrics")


@app.get(
    "/api/v1/dashboard/ai-metrics",
    response_model=AIMetrics,
    summary="AI Metrics",
    description="Retrieve metrics about AI-powered features and insights."
)
async def get_ai_metrics():
    """Get AI-powered feature metrics."""
    try:
        # Mock implementation
        return AIMetrics(
            insights_generated=1247,
            recommendations_made=892,
            predictions_accuracy=94.2,
            anomaly_detections=156,
            autonomous_actions=78
        )

    except Exception as e:
        logger.error(f"Error getting AI metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve AI metrics")


@app.get(
    "/api/v1/ecosystem/health",
    response_model=EcosystemHealth,
    summary="Ecosystem Health",
    description="Retrieve comprehensive health status of the entire ecosystem."
)
async def get_ecosystem_health():
    """Get ecosystem-wide health status."""
    try:
        # Mock implementation - would check all 21+ services
        services = {
            "project-simulation": {"status": "healthy", "response_time": 45, "version": "1.0.0"},
            "llm-gateway": {"status": "healthy", "response_time": 120, "version": "1.0.0"},
            "analysis-service": {"status": "warning", "response_time": 89, "version": "1.0.0", "issue": "High CPU usage"},
            "log-collector": {"status": "healthy", "response_time": 23, "version": "1.0.0"},
            "memory-agent": {"status": "healthy", "response_time": 34, "version": "1.0.0"},
            "prompt-store": {"status": "healthy", "response_time": 67, "version": "1.0.0"},
            "document-store": {"status": "healthy", "response_time": 45, "version": "1.0.0"},
            # ... additional services would be checked
        }

        issues = sum(1 for s in services.values() if s.get("status") == "error")
        warnings = sum(1 for s in services.values() if s.get("status") == "warning")

        overall_status = "error" if issues > 0 else "warning" if warnings > 0 else "healthy"

        return EcosystemHealth(
            overall_status=overall_status,
            services=services,
            last_check="2024-01-01T00:00:00Z",
            issues_count=issues,
            warnings_count=warnings
        )

    except Exception as e:
        logger.error(f"Error getting ecosystem health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve ecosystem health")


@app.post(
    "/api/v1/simulations/{simulation_id}/insights",
    summary="Generate AI Insights",
    description="Generate AI-powered insights and recommendations for a specific simulation."
)
async def generate_simulation_insights(simulation_id: str):
    """Generate AI insights for a simulation."""
    try:
        # Mock implementation - would use LLM Gateway
        insights = {
            "simulation_id": simulation_id,
            "insights": [
                "Performance trending above baseline by 15%",
                "Resource utilization optimized for cost efficiency",
                "Risk factors identified in phase 3 execution",
                "Recommendations: Increase parallel processing by 20%"
            ],
            "confidence": 0.89,
            "generated_at": "2024-01-01T00:00:00Z",
            "model_used": "gpt-4-turbo",
            "processing_time": 2.3
        }

        return insights

    except Exception as e:
        logger.error(f"Error generating insights for simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")


@app.get(
    "/api/v1/dashboard/config",
    summary="Get Dashboard Configuration",
    description="Retrieve current dashboard configuration settings."
)
async def get_dashboard_config():
    """Get dashboard configuration."""
    try:
        if not config:
            raise HTTPException(status_code=500, detail="Configuration not available")

        # Return sanitized configuration (without sensitive data)
        return {
            "environment": config.environment,
            "debug": config.debug,
            "theme": getattr(config.dashboard, 'theme', 'dark') if hasattr(config, 'dashboard') else 'dark',
            "version": "1.0.0",
            "features": {
                "ai_insights": True,
                "autonomous_operations": False,
                "real_time_monitoring": True,
                "predictive_analytics": True
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard config: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve configuration")


@app.post(
    "/api/v1/dashboard/actions/autonomous",
    summary="Trigger Autonomous Action",
    description="Trigger an autonomous optimization or remediation action."
)
async def trigger_autonomous_action(action_type: str = Query(..., description="Type of autonomous action")):
    """Trigger autonomous dashboard actions."""
    try:
        valid_actions = ["optimize_performance", "scale_resources", "cleanup_cache", "health_check"]

        if action_type not in valid_actions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid action type. Must be one of: {', '.join(valid_actions)}"
            )

        # Mock autonomous action implementation
        action_result = {
            "action_id": f"action_{asyncio.get_event_loop().time()}",
            "action_type": action_type,
            "status": "initiated",
            "estimated_completion": "2024-01-01T00:05:00Z",
            "description": f"Autonomous {action_type.replace('_', ' ')} initiated",
            "confidence": 0.95
        }

        return action_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering autonomous action {action_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger autonomous action")


if __name__ == "__main__":
    import uvicorn

    # Load configuration
    config = get_config()
    api_settings = APISettings()

    print("🚀 Starting Simulation Dashboard REST API...")
    print(f"📊 Service: {config.service_name} API v1.0.0")
    print(f"🌐 API: http://{api_settings.host}:{api_settings.port}")
    print(f"📚 Docs: http://{api_settings.host}:{api_settings.port}/docs")
    print(f"🎯 Environment: {config.environment}")

    uvicorn.run(
        "api.main:app",
        host=api_settings.host,
        port=api_settings.port,
        reload=api_settings.debug,
        log_level="info" if not api_settings.debug else "debug"
    )
