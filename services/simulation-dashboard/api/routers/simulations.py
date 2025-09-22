"""Simulation Management API Router.

This module provides REST API endpoints for simulation lifecycle management,
including creation, monitoring, status updates, and reporting.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from services.clients.simulation_client import SimulationClient

# Initialize router
router = APIRouter(
    prefix="/simulations",
    tags=["simulations"],
    responses={
        404: {"description": "Simulation not found"},
        500: {"description": "Internal server error"}
    }
)

# Pydantic models for simulation operations
class SimulationCreateRequest(BaseModel):
    """Request model for simulation creation."""

    name: str = Field(..., min_length=1, max_length=200, description="Simulation name")
    type: str = Field(..., description="Simulation type (e.g., software_development, data_pipeline)")
    complexity: str = Field("medium", enum=["low", "medium", "high"], description="Complexity level")
    team_size: int = Field(..., ge=1, le=50, description="Team size")
    duration_weeks: int = Field(..., ge=1, le=52, description="Planned duration in weeks")
    description: Optional[str] = Field(None, max_length=1000, description="Optional description")
    configuration: Optional[dict] = Field(None, description="Additional configuration parameters")


class SimulationUpdateRequest(BaseModel):
    """Request model for simulation updates."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    status: Optional[str] = Field(None, enum=["running", "paused", "cancelled"])
    configuration: Optional[dict] = Field(None)


class SimulationResponse(BaseModel):
    """Response model for simulation operations."""

    id: str = Field(..., description="Unique simulation identifier")
    name: str = Field(..., description="Simulation name")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., ge=0, le=100, description="Completion percentage")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    duration_weeks: Optional[int] = Field(None)
    complexity: Optional[str] = Field(None)
    type: Optional[str] = Field(None)


@router.get("/", response_model=List[SimulationResponse])
async def list_simulations(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    type_filter: Optional[str] = Query(None, alias="type", description="Filter by type"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", enum=["created_at", "updated_at", "name", "progress"]),
    sort_order: str = Query("desc", enum=["asc", "desc"])
):
    """List simulations with advanced filtering and sorting."""
    try:
        # Get simulation client from global state (would be injected in production)
        # For now, return mock data
        mock_simulations = [
            SimulationResponse(
                id=f"sim_{i:03d}",
                name=f"Sample Simulation {i}",
                status="completed" if i % 4 == 0 else "running" if i % 4 == 1 else "pending" if i % 4 == 2 else "failed",
                progress=float((i * 23) % 100),
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z",
                duration_weeks=4 + (i % 12),
                complexity="low" if i % 3 == 0 else "medium" if i % 3 == 1 else "high",
                type="software_development" if i % 2 == 0 else "data_pipeline"
            )
            for i in range(offset, min(offset + limit, 200))  # Mock 200 simulations
        ]

        # Apply filters
        if status_filter:
            mock_simulations = [s for s in mock_simulations if s.status == status_filter]

        if type_filter:
            mock_simulations = [s for s in mock_simulations if s.type == type_filter]

        # Apply sorting
        reverse = sort_order == "desc"
        if sort_by == "name":
            mock_simulations.sort(key=lambda x: x.name, reverse=reverse)
        elif sort_by == "progress":
            mock_simulations.sort(key=lambda x: x.progress, reverse=reverse)
        elif sort_by == "updated_at":
            # Would sort by actual timestamp in production
            pass

        return mock_simulations

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list simulations: {str(e)}"
        )


@router.post("/", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def create_simulation(request: SimulationCreateRequest):
    """Create a new simulation."""
    try:
        # Mock simulation creation
        import uuid
        simulation_id = f"sim_{uuid.uuid4().hex[:6]}"

        response = SimulationResponse(
            id=simulation_id,
            name=request.name,
            status="pending",
            progress=0.0,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            duration_weeks=request.duration_weeks,
            complexity=request.complexity,
            type=request.type
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create simulation: {str(e)}"
        )


@router.get("/{simulation_id}", response_model=SimulationResponse)
async def get_simulation(simulation_id: str):
    """Get detailed information about a specific simulation."""
    try:
        # Validate simulation ID format
        if not simulation_id.startswith("sim_"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid simulation ID format"
            )

        # Mock simulation retrieval
        try:
            sim_num = int(simulation_id.split("_")[1][:3])  # Extract number
        except (IndexError, ValueError):
            sim_num = 1

        return SimulationResponse(
            id=simulation_id,
            name=f"Detailed Simulation {sim_num}",
            status="completed" if sim_num % 3 == 0 else "running",
            progress=float((sim_num * 7) % 100),
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
            duration_weeks=8 + (sim_num % 8),
            complexity="high" if sim_num % 3 == 0 else "medium",
            type="software_development" if sim_num % 2 == 0 else "data_pipeline"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve simulation: {str(e)}"
        )


@router.put("/{simulation_id}", response_model=SimulationResponse)
async def update_simulation(simulation_id: str, request: SimulationUpdateRequest):
    """Update simulation configuration or status."""
    try:
        # First verify simulation exists
        existing = await get_simulation(simulation_id)

        # Apply updates
        updated = existing.copy()
        if request.name:
            updated.name = request.name
        if request.status:
            updated.status = request.status
        if request.configuration:
            # Would apply configuration updates in production
            pass

        updated.updated_at = "2024-01-01T00:00:00Z"  # Current timestamp

        return updated

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update simulation: {str(e)}"
        )


@router.delete("/{simulation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_simulation(simulation_id: str):
    """Delete a simulation."""
    try:
        # Verify simulation exists
        await get_simulation(simulation_id)

        # Mock deletion - would perform actual deletion in production
        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete simulation: {str(e)}"
        )


@router.post("/{simulation_id}/execute", response_model=dict)
async def execute_simulation(simulation_id: str):
    """Execute/start a simulation."""
    try:
        # Verify simulation exists and is in executable state
        simulation = await get_simulation(simulation_id)

        if simulation.status not in ["pending", "paused"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Simulation is {simulation.status} and cannot be executed"
            )

        # Mock execution start
        execution_response = {
            "simulation_id": simulation_id,
            "execution_id": f"exec_{simulation_id}_{'20240101120000'}",
            "status": "started",
            "started_at": "2024-01-01T12:00:00Z",
            "estimated_completion": "2024-01-01T14:30:00Z"
        }

        return execution_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute simulation: {str(e)}"
        )


@router.get("/{simulation_id}/status", response_model=dict)
async def get_simulation_status(simulation_id: str):
    """Get real-time status of a running simulation."""
    try:
        # Verify simulation exists
        simulation = await get_simulation(simulation_id)

        # Mock real-time status
        status_response = {
            "simulation_id": simulation_id,
            "status": simulation.status,
            "progress": simulation.progress,
            "current_phase": "execution" if simulation.status == "running" else None,
            "phase_progress": 67.5 if simulation.status == "running" else None,
            "estimated_completion": "2024-01-01T13:45:00Z" if simulation.status == "running" else None,
            "last_updated": "2024-01-01T12:30:00Z"
        }

        return status_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get simulation status: {str(e)}"
        )


@router.get("/{simulation_id}/metrics", response_model=dict)
async def get_simulation_metrics(
    simulation_id: str,
    timeframe: str = Query("1h", enum=["1h", "6h", "24h", "7d", "30d"])
):
    """Get performance metrics for a simulation."""
    try:
        # Verify simulation exists
        await get_simulation(simulation_id)

        # Mock metrics based on timeframe
        base_metrics = {
            "cpu_usage_percent": 67.5,
            "memory_usage_mb": 1024,
            "network_io_mbps": 45.2,
            "disk_io_iops": 1250,
            "response_time_ms": 145,
            "error_rate_percent": 0.02
        }

        # Adjust metrics based on timeframe (simulate historical data)
        timeframe_multipliers = {
            "1h": 1.0,
            "6h": 0.9,
            "24h": 0.8,
            "7d": 0.7,
            "30d": 0.6
        }

        multiplier = timeframe_multipliers[timeframe]
        adjusted_metrics = {
            key: round(value * multiplier, 2) if isinstance(value, (int, float)) else value
            for key, value in base_metrics.items()
        }

        metrics_response = {
            "simulation_id": simulation_id,
            "timeframe": timeframe,
            "metrics": adjusted_metrics,
            "collected_at": "2024-01-01T12:00:00Z"
        }

        return metrics_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get simulation metrics: {str(e)}"
        )


@router.get("/{simulation_id}/logs", response_model=dict)
async def get_simulation_logs(
    simulation_id: str,
    level: Optional[str] = Query(None, enum=["DEBUG", "INFO", "WARNING", "ERROR"]),
    limit: int = Query(100, ge=1, le=1000),
    before: Optional[str] = Query(None, description="ISO timestamp to get logs before")
):
    """Get logs for a simulation."""
    try:
        # Verify simulation exists
        await get_simulation(simulation_id)

        # Mock log entries
        log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        mock_logs = []

        for i in range(min(limit, 50)):  # Max 50 mock logs
            log_level = level if level else log_levels[i % len(log_levels)]
            mock_logs.append({
                "timestamp": "2024-01-01T12:00:00Z",
                "level": log_level,
                "message": f"Simulation {simulation_id} log entry {i}",
                "component": "simulation_engine" if i % 2 == 0 else "data_processor",
                "details": {"operation": f"step_{i}", "duration_ms": 45 + i * 2}
            })

        logs_response = {
            "simulation_id": simulation_id,
            "logs": mock_logs,
            "total_count": len(mock_logs),
            "filtered_by_level": level,
            "limit": limit
        }

        return logs_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get simulation logs: {str(e)}"
        )
