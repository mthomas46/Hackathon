"""Simulation Command Handlers.

Application layer handlers for processing simulation commands.
These handlers orchestrate domain services and manage business logic.
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from ...domain.entities.simulation import Simulation, SimulationStatus
from ...domain.services.simulation_service import SimulationService
from ...infrastructure.repositories.simulation_repository import SimulationRepository

from ..commands.simulation_commands import (
    CreateSimulationCommand,
    UpdateSimulationCommand,
    DeleteSimulationCommand,
    StartSimulationCommand,
    StopSimulationCommand,
)

logger = logging.getLogger(__name__)


class CreateSimulationHandler:
    """Handler for creating new simulations."""

    def __init__(self, simulation_service: SimulationService, repository: SimulationRepository):
        self.simulation_service = simulation_service
        self.repository = repository

    async def handle(self, command: CreateSimulationCommand) -> Simulation:
        """Handle create simulation command."""
        try:
            logger.info(f"Creating simulation: {command.name}")

            # Create simulation entity
            simulation = Simulation(
                id=None,  # Will be set by repository
                name=command.name,
                description=command.description,
                simulation_type=command.simulation_type,
                parameters=command.parameters or {},
                status=SimulationStatus.CREATED,
                user_id=command.user_id,
                metadata=command.metadata or {},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            # Validate simulation using domain service
            await self.simulation_service.validate_simulation(simulation)

            # Save to repository
            created_simulation = await self.repository.save(simulation)

            logger.info(f"Simulation created successfully: {created_simulation.id}")
            return created_simulation

        except Exception as e:
            logger.error(f"Failed to create simulation: {e}")
            raise


class UpdateSimulationHandler:
    """Handler for updating existing simulations."""

    def __init__(self, simulation_service: SimulationService, repository: SimulationRepository):
        self.simulation_service = simulation_service
        self.repository = repository

    async def handle(self, command: UpdateSimulationCommand) -> Simulation:
        """Handle update simulation command."""
        try:
            logger.info(f"Updating simulation: {command.simulation_id}")

            # Get existing simulation
            simulation = await self.repository.get_by_id(command.simulation_id)
            if not simulation:
                raise ValueError(f"Simulation not found: {command.simulation_id}")

            # Update fields if provided
            if command.name is not None:
                simulation.name = command.name
            if command.description is not None:
                simulation.description = command.description
            if command.parameters is not None:
                simulation.parameters.update(command.parameters)
            if command.metadata is not None:
                simulation.metadata.update(command.metadata)

            simulation.updated_at = datetime.now(timezone.utc)

            # Validate updated simulation
            await self.simulation_service.validate_simulation(simulation)

            # Save changes
            updated_simulation = await self.repository.save(simulation)

            logger.info(f"Simulation updated successfully: {command.simulation_id}")
            return updated_simulation

        except Exception as e:
            logger.error(f"Failed to update simulation {command.simulation_id}: {e}")
            raise


class DeleteSimulationHandler:
    """Handler for deleting simulations."""

    def __init__(self, repository: SimulationRepository):
        self.repository = repository

    async def handle(self, command: DeleteSimulationCommand) -> bool:
        """Handle delete simulation command."""
        try:
            logger.info(f"Deleting simulation: {command.simulation_id}")

            # Check if simulation exists and can be deleted
            simulation = await self.repository.get_by_id(command.simulation_id)
            if not simulation:
                raise ValueError(f"Simulation not found: {command.simulation_id}")

            # Only allow deletion of non-running simulations
            if simulation.status == SimulationStatus.RUNNING:
                raise ValueError(f"Cannot delete running simulation: {command.simulation_id}")

            # Delete from repository
            success = await self.repository.delete(command.simulation_id)

            if success:
                logger.info(f"Simulation deleted successfully: {command.simulation_id}")
            else:
                logger.warning(f"Simulation deletion failed: {command.simulation_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to delete simulation {command.simulation_id}: {e}")
            raise


class StartSimulationHandler:
    """Handler for starting simulations."""

    def __init__(self, simulation_service: SimulationService, repository: SimulationRepository):
        self.simulation_service = simulation_service
        self.repository = repository

    async def handle(self, command: StartSimulationCommand) -> Simulation:
        """Handle start simulation command."""
        try:
            logger.info(f"Starting simulation: {command.simulation_id}")

            # Get simulation
            simulation = await self.repository.get_by_id(command.simulation_id)
            if not simulation:
                raise ValueError(f"Simulation not found: {command.simulation_id}")

            # Start simulation using domain service
            started_simulation = await self.simulation_service.start_simulation(
                simulation, command.execution_parameters or {}
            )

            # Save updated simulation
            await self.repository.save(started_simulation)

            logger.info(f"Simulation started successfully: {command.simulation_id}")
            return started_simulation

        except Exception as e:
            logger.error(f"Failed to start simulation {command.simulation_id}: {e}")
            raise


class StopSimulationHandler:
    """Handler for stopping simulations."""

    def __init__(self, simulation_service: SimulationService, repository: SimulationRepository):
        self.simulation_service = simulation_service
        self.repository = repository

    async def handle(self, command: StopSimulationCommand) -> Simulation:
        """Handle stop simulation command."""
        try:
            logger.info(f"Stopping simulation: {command.simulation_id}")

            # Get simulation
            simulation = await self.repository.get_by_id(command.simulation_id)
            if not simulation:
                raise ValueError(f"Simulation not found: {command.simulation_id}")

            # Stop simulation using domain service
            stopped_simulation = await self.simulation_service.stop_simulation(
                simulation, command.reason
            )

            # Save updated simulation
            await self.repository.save(stopped_simulation)

            logger.info(f"Simulation stopped successfully: {command.simulation_id}")
            return stopped_simulation

        except Exception as e:
            logger.error(f"Failed to stop simulation {command.simulation_id}: {e}")
            raise
