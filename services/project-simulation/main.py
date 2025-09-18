"""Project Simulation Service - Main FastAPI Application.

This is the main entry point for the project-simulation service,
providing a REST API for project simulation capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add shared infrastructure to path
sys.path.append(str(Path(__file__).parent.parent / "services" / "shared"))

# Import local modules
from simulation.infrastructure.di_container import get_simulation_container
from simulation.infrastructure.logging import with_correlation_id, generate_correlation_id
from simulation.infrastructure.health import create_simulation_health_endpoints
from simulation.presentation.api.hateoas import (
    SimulationResource,
    RootResource,
    HealthResource,
    create_hateoas_response,
    create_error_response
)


# Pydantic models for API requests/responses
class CreateSimulationRequest(BaseModel):
    """Request model for creating a simulation."""
    name: str
    description: Optional[str] = None
    type: str = "web_application"
    team_size: int = 5
    complexity: str = "medium"
    duration_weeks: int = 8
    team_members: Optional[list] = None
    phases: Optional[list] = None


class SimulationResponse(BaseModel):
    """Response model for simulation operations."""
    success: bool
    message: str
    simulation_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None


# Initialize FastAPI application
app = FastAPI(
    title="Project Simulation Service",
    description="AI-powered project simulation and ecosystem demonstration service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get service instances
container = get_simulation_container()
logger = container.logger
application_service = container.simulation_application_service

# Create health endpoints
health_endpoints = create_simulation_health_endpoints()


# Health endpoints
@app.get("/health")
async def health():
    """Basic health check."""
    return await health_endpoints["health"]()


@app.get("/health/detailed")
async def health_detailed():
    """Detailed health check."""
    return await health_endpoints["health_detailed"]()


@app.get("/health/system")
async def health_system():
    """System-wide health check."""
    return await health_endpoints["health_system"]()


# Simulation endpoints
@app.post("/api/v1/simulations")
async def create_simulation(request: CreateSimulationRequest):
    """Create a new project simulation with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.info(
            "Creating simulation",
            operation="create_simulation",
            project_name=request.name,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.create_simulation(request.dict())

            if result["success"]:
                # Create HATEOAS links for the created simulation
                simulation_id = result.get("simulation_id")
                links = SimulationResource.create_simulation_links(simulation_id)

                return create_hateoas_response(
                    data={
                        "simulation_id": simulation_id,
                        "message": result.get("message", "Simulation created successfully")
                    },
                    links=links,
                    status="created"
                )
            else:
                return create_error_response(
                    error=result.get("message", "Failed to create simulation"),
                    status_code=400
                )

        except Exception as e:
            logger.error(
                "Failed to create simulation",
                error=str(e),
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


@app.post("/api/v1/simulations/{simulation_id}/execute")
async def execute_simulation(simulation_id: str, background_tasks: BackgroundTasks):
    """Execute a simulation with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.info(
            "Executing simulation",
            operation="execute_simulation",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            # Execute simulation in background for long-running operations
            background_tasks.add_task(
                _execute_simulation_background,
                simulation_id,
                correlation_id
            )

            # Create HATEOAS links for the executing simulation
            links = SimulationResource.create_simulation_links(simulation_id)

            return create_hateoas_response(
                data={
                    "simulation_id": simulation_id,
                    "message": "Simulation execution started",
                    "status": "running"
                },
                links=links,
                status="accepted"
            )

        except Exception as e:
            logger.error(
                "Failed to start simulation execution",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


@app.get("/api/v1/simulations/{simulation_id}")
async def get_simulation_status(simulation_id: str):
    """Get simulation status with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.debug(
            "Getting simulation status",
            operation="get_simulation_status",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.get_simulation_status(simulation_id)

            if not result["success"]:
                return create_error_response(
                    error=result["error"],
                    status_code=404
                )

            # Create HATEOAS links for the simulation
            links = SimulationResource.create_simulation_links(simulation_id)

            return create_hateoas_response(
                data=result,
                links=links,
                status="ok"
            )

        except Exception as e:
            logger.error(
                "Failed to get simulation status",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


@app.get("/api/v1/simulations")
async def list_simulations(status: Optional[str] = None, limit: int = 50):
    """List simulations with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.debug(
            "Listing simulations",
            operation="list_simulations",
            status_filter=status,
            limit=limit,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.list_simulations(status, limit)

            # Create HATEOAS links for the collection
            links = SimulationResource.create_simulation_collection_links()

            return create_hateoas_response(
                data=result,
                links=links,
                status="ok"
            )

        except Exception as e:
            logger.error(
                "Failed to list simulations",
                error=str(e),
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


@app.delete("/api/v1/simulations/{simulation_id}")
async def cancel_simulation(simulation_id: str):
    """Cancel a simulation with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.info(
            "Cancelling simulation",
            operation="cancel_simulation",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.cancel_simulation(simulation_id)

            if not result["success"]:
                return create_error_response(
                    error=result["error"],
                    status_code=400
                )

            # Create HATEOAS links for the cancelled simulation
            links = SimulationResource.create_simulation_links(simulation_id)

            return create_hateoas_response(
                data=result,
                links=links,
                status="ok"
            )

        except Exception as e:
            logger.error(
                "Failed to cancel simulation",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


@app.get("/api/v1/simulations/{simulation_id}/results")
async def get_simulation_results(simulation_id: str):
    """Get simulation results with HATEOAS navigation."""
    correlation_id = generate_correlation_id()

    with with_correlation_id(correlation_id):
        logger.debug(
            "Getting simulation results",
            operation="get_simulation_results",
            simulation_id=simulation_id,
            correlation_id=correlation_id
        )

        try:
            result = await application_service.get_simulation_results(simulation_id)

            if not result["success"]:
                return create_error_response(
                    error=result["error"],
                    status_code=404
                )

            # Create HATEOAS links for the simulation
            links = SimulationResource.create_simulation_links(simulation_id)

            return create_hateoas_response(
                data=result,
                links=links,
                status="ok"
            )

        except Exception as e:
            logger.error(
                "Failed to get simulation results",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return create_error_response(
                error=str(e),
                status_code=500
            )


# Background task for simulation execution
async def _execute_simulation_background(simulation_id: str, correlation_id: str):
    """Execute simulation in background."""
    with with_correlation_id(correlation_id):
        try:
            logger.info(
                "Starting background simulation execution",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            result = await application_service.execute_simulation(simulation_id)

            logger.info(
                "Background simulation execution completed",
                simulation_id=simulation_id,
                success=result.get("success", False),
                correlation_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Background simulation execution failed",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )


# WebSocket endpoint for real-time updates (placeholder)
@app.websocket("/ws/simulations/{simulation_id}")
async def simulation_websocket(simulation_id: str):
    """WebSocket endpoint for real-time simulation updates."""
    # Placeholder for WebSocket implementation
    # This would be implemented with proper WebSocket handling
    pass


@app.get("/")
async def root():
    """Root endpoint with service information and HATEOAS navigation."""
    # Create HATEOAS links for API root
    links = RootResource.create_root_links()

    return create_hateoas_response(
        data={
            "service": "project-simulation",
            "version": "1.0.0",
            "description": "AI-powered project simulation and ecosystem demonstration service",
            "features": [
                "HATEOAS navigation",
                "Domain-driven design",
                "Event-driven architecture",
                "Circuit breaker resilience",
                "Comprehensive monitoring",
                "21+ ecosystem service integration"
            ]
        },
        links=links,
        status="ok"
    )


if __name__ == "__main__":
    """Run the Project Simulation Service directly."""
    import uvicorn

    print("🚀 Starting Project Simulation Service...")
    print("📊 Service: project-simulation v1.0.0")
    print("🌐 API Documentation: http://localhost:5075/docs")
    print("💊 Health Check: http://localhost:5075/health")
    print("📋 Root Endpoint: http://localhost:5075/")
    print("\n✨ Features Available:")
    print("  🏗️  Project Simulation Creation")
    print("  🎭 Simulation Execution & Monitoring")
    print("  📊 Real-time Progress Tracking")
    print("  📄 Document Generation Integration")
    print("  🔗 Ecosystem Service Coordination")
    print("  📈 Performance Analytics")
    print("  🏥 Health Monitoring")
    print("  📝 Structured Logging with Correlation IDs")
    print("\n🔧 Built with:")
    print("  🏛️  Domain Driven Design (DDD)")
    print("  🧹 Clean Architecture")
    print("  🔄 Dependency Injection")
    print("  📡 REST API with HATEOAS")
    print("  🧪 Comprehensive Testing Infrastructure")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5075,
        reload=True,
        log_level="info"
    )