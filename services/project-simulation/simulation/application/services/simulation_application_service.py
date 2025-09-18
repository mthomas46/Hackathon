"""Application Services - Use Case Orchestration.

This module provides application services that orchestrate domain services
to fulfill high-level use cases following CQRS and Clean Architecture patterns.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime

from ...domain.services.project_simulation_service import ProjectSimulationService
from ...infrastructure.logging import SimulationLogger
from ...presentation.websockets.simulation_websocket import (
    notify_simulation_progress,
    notify_simulation_event
)
from ...domain.value_objects import SimulationType, SimulationStatus


class SimulationApplicationService:
    """Application service for simulation use cases.

    This service orchestrates domain services to fulfill high-level
    business use cases while maintaining clean architecture principles.
    """

    def __init__(self,
                 project_simulation_service: ProjectSimulationService,
                 logger: SimulationLogger):
        """Initialize application service."""
        self._domain_service = project_simulation_service
        self._logger = logger

    async def create_simulation(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project simulation."""
        correlation_id = self._logger._logger._logger.extra.get('correlation_id', 'unknown')

        try:
            self._logger.info(
                "Creating new simulation",
                operation="create_simulation",
                project_name=request.get("name", "unknown"),
                correlation_id=correlation_id
            )

            start_time = datetime.now()

            # Create simulation through domain service
            simulation_id = await self._domain_service.create_project_simulation(request)

            duration = (datetime.now() - start_time).total_seconds()

            self._logger.log_performance(
                operation="create_simulation",
                duration=duration,
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Notify WebSocket clients about new simulation
            try:
                await notify_simulation_progress(simulation_id, {
                    "progress_percentage": 0.0,
                    "current_phase": "Initialization",
                    "status": "created",
                    "message": "Simulation created successfully"
                })
            except Exception as ws_error:
                self._logger.warning(
                    "Failed to send WebSocket notification for simulation creation",
                    error=str(ws_error),
                    simulation_id=simulation_id
                )

            return {
                "success": True,
                "simulation_id": simulation_id,
                "message": "Simulation created successfully",
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            self._logger.error(
                "Failed to create simulation",
                error=str(e),
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create simulation"
            }

    async def execute_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Execute a simulation."""
        correlation_id = self._logger._logger._logger.extra.get('correlation_id', 'unknown')

        try:
            self._logger.info(
                "Executing simulation",
                operation="execute_simulation",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Execute simulation through domain service
            result = await self._domain_service.execute_simulation(simulation_id)

            self._logger.info(
                "Simulation execution completed",
                operation="execute_simulation",
                simulation_id=simulation_id,
                success=result.get("success", False),
                duration=result.get("execution_time_seconds", 0),
                correlation_id=correlation_id
            )

            # Notify WebSocket clients about execution start
            try:
                await notify_simulation_progress(simulation_id, {
                    "progress_percentage": 10.0,
                    "current_phase": "Execution",
                    "status": "running",
                    "message": "Simulation execution started",
                    "execution_time_seconds": result.get("execution_time_seconds", 0)
                })
            except Exception as ws_error:
                self._logger.warning(
                    "Failed to send WebSocket notification for simulation execution",
                    error=str(ws_error),
                    simulation_id=simulation_id
                )

            return result

        except Exception as e:
            self._logger.error(
                "Failed to execute simulation",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": str(e),
                "message": "Failed to execute simulation"
            }

    async def get_simulation_status(self, simulation_id: str) -> Dict[str, Any]:
        """Get simulation status."""
        correlation_id = self._logger._logger._logger.extra.get('correlation_id', 'unknown')

        try:
            self._logger.debug(
                "Getting simulation status",
                operation="get_simulation_status",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Get simulation from repository
            from ...infrastructure.di_container import get_simulation_container
            simulation_repo = get_simulation_container().simulation_repository
            simulation = simulation_repo.find_by_id(simulation_id)

            if not simulation:
                return {
                    "success": False,
                    "error": "Simulation not found",
                    "simulation_id": simulation_id
                }

            return {
                "success": True,
                "simulation_id": simulation_id,
                "status": simulation.status.value,
                "progress": simulation.get_progress_percentage(),
                "created_at": simulation.created_at.isoformat(),
                "started_at": simulation.started_at.isoformat() if simulation.started_at else None,
                "completed_at": simulation.completed_at.isoformat() if simulation.completed_at else None,
                "result": simulation.result.get_summary() if simulation.result else None
            }

        except Exception as e:
            self._logger.error(
                "Failed to get simulation status",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": str(e)
            }

    async def list_simulations(self, status_filter: Optional[str] = None,
                              limit: int = 50) -> Dict[str, Any]:
        """List simulations with optional filtering."""
        correlation_id = self._logger._logger._logger.extra.get('correlation_id', 'unknown')

        try:
            self._logger.debug(
                "Listing simulations",
                operation="list_simulations",
                status_filter=status_filter,
                limit=limit,
                correlation_id=correlation_id
            )

            # Get simulations from repository
            from ...infrastructure.di_container import get_simulation_container
            simulation_repo = get_simulation_container().simulation_repository

            if status_filter:
                simulations = simulation_repo.find_by_status(status_filter)
            else:
                simulations = simulation_repo.find_recent(limit)

            # Convert to response format
            simulation_list = []
            for sim in simulations[:limit]:
                simulation_list.append({
                    "id": str(sim.id.value),
                    "project_id": sim.project_id,
                    "status": sim.status.value,
                    "progress": sim.get_progress_percentage(),
                    "created_at": sim.created_at.isoformat(),
                    "started_at": sim.started_at.isoformat() if sim.started_at else None,
                    "completed_at": sim.completed_at.isoformat() if sim.completed_at else None
                })

            return {
                "success": True,
                "simulations": simulation_list,
                "total": len(simulation_list),
                "filter": status_filter
            }

        except Exception as e:
            self._logger.error(
                "Failed to list simulations",
                error=str(e),
                status_filter=status_filter,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "error": str(e),
                "simulations": [],
                "total": 0
            }

    async def cancel_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Cancel a running simulation."""
        correlation_id = self._logger._logger._logger.extra.get('correlation_id', 'unknown')

        try:
            self._logger.info(
                "Cancelling simulation",
                operation="cancel_simulation",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Get simulation from repository
            from ...infrastructure.di_container import get_simulation_container
            simulation_repo = get_simulation_container().simulation_repository
            simulation = simulation_repo.find_by_id(simulation_id)

            if not simulation:
                return {
                    "success": False,
                    "error": "Simulation not found",
                    "simulation_id": simulation_id
                }

            if simulation.is_completed():
                return {
                    "success": False,
                    "error": "Simulation is already completed",
                    "simulation_id": simulation_id,
                    "status": simulation.status.value
                }

            # Cancel simulation
            simulation.cancel_simulation()
            simulation_repo.save(simulation)

            self._logger.info(
                "Simulation cancelled successfully",
                operation="cancel_simulation",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            return {
                "success": True,
                "simulation_id": simulation_id,
                "message": "Simulation cancelled successfully",
                "cancelled_at": datetime.now().isoformat()
            }

        except Exception as e:
            self._logger.error(
                "Failed to cancel simulation",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": str(e)
            }

    async def get_simulation_results(self, simulation_id: str) -> Dict[str, Any]:
        """Get detailed simulation results."""
        correlation_id = self._logger._logger._logger.extra.get('correlation_id', 'unknown')

        try:
            self._logger.debug(
                "Getting simulation results",
                operation="get_simulation_results",
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )

            # Get simulation from repository
            from ...infrastructure.di_container import get_simulation_container
            simulation_repo = get_simulation_container().simulation_repository
            simulation = simulation_repo.find_by_id(simulation_id)

            if not simulation:
                return {
                    "success": False,
                    "error": "Simulation not found",
                    "simulation_id": simulation_id
                }

            if not simulation.result:
                return {
                    "success": False,
                    "error": "Simulation has no results yet",
                    "simulation_id": simulation_id,
                    "status": simulation.status.value
                }

            return {
                "success": True,
                "simulation_id": simulation_id,
                "results": simulation.result.get_summary(),
                "documents_created": simulation.result.documents_created,
                "workflows_executed": simulation.result.workflows_executed,
                "insights": simulation.result.insights,
                "errors": simulation.result.errors,
                "warnings": simulation.result.warnings
            }

        except Exception as e:
            self._logger.error(
                "Failed to get simulation results",
                error=str(e),
                simulation_id=simulation_id,
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "simulation_id": simulation_id,
                "error": str(e)
            }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        correlation_id = self._logger._logger._logger.extra.get('correlation_id', 'unknown')

        try:
            from ...infrastructure.di_container import get_simulation_container
            health_manager = get_simulation_container().health_manager

            health_status = await health_manager.simulation_health()

            return {
                "success": True,
                "health": health_status
            }

        except Exception as e:
            self._logger.error(
                "Failed to get health status",
                error=str(e),
                correlation_id=correlation_id
            )
            return {
                "success": False,
                "error": str(e)
            }
