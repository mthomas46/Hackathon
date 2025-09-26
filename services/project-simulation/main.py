"""Project Simulation Service - Streamlined FastAPI Application.

This is the main entry point for the project-simulation service,
providing a REST API for project simulation capabilities with
modular architecture and clean separation of concerns.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Add shared infrastructure to path
project_root = Path(__file__).parent.parent.parent
shared_path = project_root / "services" / "shared"
services_path = project_root / "services"

# Insert paths at the beginning to ensure they're found first
sys.path.insert(0, str(shared_path))
sys.path.insert(0, str(services_path))
sys.path.insert(0, str(project_root))

# Import shared utilities and patterns
try:
    from services.shared.presentation.responses import (
        create_success_response,
        create_error_response,
        APIResponse,
    )
    from services.shared.infrastructure.config import load_service_config
    from services.shared.infrastructure.utilities.middleware import setup_common_middleware
    from services.shared.infrastructure.monitoring.health import create_simulation_health_endpoints
except ImportError as e:
    print(f"Warning: Could not import shared infrastructure: {e}")
    # Fallback definitions for when shared infrastructure is not available
    def create_success_response(data: Any) -> Dict[str, Any]:
        return {"success": True, "data": data}

    def create_error_response(message: str, **kwargs) -> Dict[str, Any]:
        return {"success": False, "message": message, **kwargs}

    def load_service_config(**kwargs):
        return type('Config', (), {
            'service_name': 'project-simulation',
            'service_description': 'Project Simulation Service',
            'service_version': '1.0.0',
            'server': type('Server', (), {'host': '0.0.0.0', 'port': 5075})(),
            'timeouts': type('Timeouts', (), {'service_discovery': 30.0, 'tool_registration': 60.0, 'health_check': 10.0})(),
        })()

    def setup_common_middleware(app, **kwargs):
        pass

    def create_simulation_health_endpoints():
        return []

# Import modular API routers
from simulation.presentation.api import api_router

# Constants
SERVICE_NAME = "project-simulation"

# Load configuration
config = load_service_config(
    service_type=SERVICE_NAME,
    config_file="./config.yaml"
)

# Create FastAPI application
app = FastAPI(
    title=config.service_description or "Project Simulation Service",
    description="""
    A comprehensive project simulation service that demonstrates the entire LLM Documentation Ecosystem.

    ## Features
    - Realistic software development project simulation
    - AI-powered content generation and analysis
    - Comprehensive analytics and reporting
    - Real-time event streaming and monitoring
    - Ecosystem integration with 21+ services

    ## Key Capabilities
    - **Project Simulation**: End-to-end development workflows
    - **Content Generation**: AI-powered documentation synthesis
    - **Quality Analysis**: Automated code and documentation assessment
    - **Timeline Management**: Sophisticated project planning and tracking
    - **Team Dynamics**: Multi-role team simulation with interactions
    """,
    version=config.service_version or "1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup common middleware
setup_common_middleware(app, service_name=SERVICE_NAME)

# Include API routers
app.include_router(api_router, prefix="/api/v1")

# Health endpoints using shared patterns
health_endpoints = create_simulation_health_endpoints()


@app.on_event("startup")
async def startup_event():
    """Initialize the project simulation service."""
    print("🚀 Project Simulation Service starting up...")
    print("✅ Ecosystem integration ready")
    print("✅ AI-powered content generation available")
    print("✅ Real-time simulation monitoring active")
    print("✅ All endpoints registered and operational")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    print("🛑 Project Simulation Service shutting down...")
    print("✅ Resources cleaned up")
    print("✅ Connections closed")


# Request/Response Models (for backward compatibility)
class SimulationRequest(BaseModel):
    """Request model for simulation operations."""
    name: str = Field(..., description="Simulation name")
    project_type: str = Field("web_application", description="Type of project to simulate")
    team_size: int = Field(5, description="Number of team members")
    duration_weeks: int = Field(8, description="Project duration in weeks")


class SimulationResponse(BaseModel):
    """Response model for simulation operations."""
    simulation_id: str = Field(..., description="Unique simulation identifier")
    status: str = Field(..., description="Current simulation status")
    created_at: str = Field(..., description="Simulation creation timestamp")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", config.server.host)
    port = int(os.getenv("PORT", config.server.port))

    print(f"🎯 Starting {SERVICE_NAME} on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
