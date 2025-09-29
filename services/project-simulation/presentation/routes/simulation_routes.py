"""Simulation API routes for project-simulation service.

This module contains all API endpoints related to simulation management,
including creation, execution, monitoring, and reporting.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, Query

from presentation.models import (
    CreateSimulationRequest,
    SimulationResponse,
    CreateSimulationFromConfigRequest,
    GenerateReportsRequest,
    ExportReportRequest,
)
from application.handlers import SimulationHandler

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/simulations", tags=["simulations"])
handler = SimulationHandler()


@router.post("", response_model=SimulationResponse)
async def create_simulation(request: CreateSimulationRequest) -> SimulationResponse:
    """Create a new simulation.

    Args:
        request: Simulation creation parameters

    Returns:
        Simulation creation response
    """
    try:
        result = await handler.create_simulation(
            name=request.name,
            description=request.description,
            project_type=request.type,
            team_size=request.team_size,
            complexity=request.complexity,
            duration_weeks=request.duration_weeks,
            team_members=request.team_members,
            phases=request.phases,
        )

        return SimulationResponse(
            success=True,
            message="Simulation created successfully",
            simulation_id=result.get("simulation_id"),
            data=result,
            created_at=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Failed to create simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{simulation_id}/execute")
async def execute_simulation(
    simulation_id: str = Path(..., description="Simulation ID"),
    background_tasks: BackgroundTasks = None,
) -> Dict[str, Any]:
    """Execute a simulation.

    Args:
        simulation_id: ID of the simulation to execute
        background_tasks: FastAPI background tasks

    Returns:
        Execution status
    """
    try:
        # Add background task for simulation execution
        if background_tasks:
            background_tasks.add_task(handler.execute_simulation, simulation_id)

        return {
            "success": True,
            "message": f"Simulation {simulation_id} execution started",
            "simulation_id": simulation_id,
            "status": "running",
        }
    except Exception as e:
        logger.error(f"Failed to execute simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}")
async def get_simulation_status(
    simulation_id: str = Path(..., description="Simulation ID"),
) -> Dict[str, Any]:
    """Get simulation status and details.

    Args:
        simulation_id: ID of the simulation

    Returns:
        Simulation status and details
    """
    try:
        result = await handler.get_simulation_status(simulation_id)
        return result
    except Exception as e:
        logger.error(f"Failed to get simulation status for {simulation_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} not found")


@router.get("")
async def list_simulations(
    limit: int = Query(50, description="Maximum number of simulations to return"),
    offset: int = Query(0, description="Number of simulations to skip"),
    status: Optional[str] = Query(None, description="Filter by simulation status"),
) -> Dict[str, Any]:
    """List simulations with optional filtering.

    Args:
        limit: Maximum number of simulations to return
        offset: Number of simulations to skip
        status: Filter by simulation status

    Returns:
        List of simulations
    """
    try:
        result = await handler.list_simulations(
            limit=limit, offset=offset, status_filter=status
        )
        return result
    except Exception as e:
        logger.error(f"Failed to list simulations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{simulation_id}")
async def cancel_simulation(
    simulation_id: str = Path(..., description="Simulation ID"),
) -> Dict[str, Any]:
    """Cancel/stop a simulation.

    Args:
        simulation_id: ID of the simulation to cancel

    Returns:
        Cancellation status
    """
    try:
        result = await handler.cancel_simulation(simulation_id)
        return result
    except Exception as e:
        logger.error(f"Failed to cancel simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}/results")
async def get_simulation_results(
    simulation_id: str = Path(..., description="Simulation ID"),
) -> Dict[str, Any]:
    """Get simulation results and outcomes.

    Args:
        simulation_id: ID of the simulation

    Returns:
        Simulation results
    """
    try:
        result = await handler.get_simulation_results(simulation_id)
        return result
    except Exception as e:
        logger.error(f"Failed to get simulation results for {simulation_id}: {e}")
        raise HTTPException(status_code=404, detail=f"Simulation {simulation_id} results not found")


@router.post("/{simulation_id}/reports/generate")
async def generate_simulation_reports(
    simulation_id: str = Path(..., description="Simulation ID"),
    request: GenerateReportsRequest = None,
    background_tasks: BackgroundTasks = None,
) -> Dict[str, Any]:
    """Generate reports for a simulation.

    Args:
        simulation_id: ID of the simulation
        request: Report generation parameters
        background_tasks: FastAPI background tasks

    Returns:
        Report generation status
    """
    try:
        report_types = request.report_types if request else ["executive_summary"]

        if background_tasks:
            background_tasks.add_task(
                handler.generate_reports, simulation_id, report_types
            )

        return {
            "success": True,
            "message": f"Report generation started for simulation {simulation_id}",
            "simulation_id": simulation_id,
            "report_types": report_types,
        }
    except Exception as e:
        logger.error(f"Failed to generate reports for simulation {simulation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{simulation_id}/reports")
async def get_simulation_reports(
    simulation_id: str = Path(..., description="Simulation ID"),
) -> Dict[str, Any]:
    """Get available reports for a simulation.

    Args:
        simulation_id: ID of the simulation

    Returns:
        Available reports
    """
    try:
        result = await handler.get_simulation_reports(simulation_id)
        return result
    except Exception as e:
        logger.error(f"Failed to get reports for simulation {simulation_id}: {e}")
        raise HTTPException(status_code=404, detail=f"No reports found for simulation {simulation_id}")
