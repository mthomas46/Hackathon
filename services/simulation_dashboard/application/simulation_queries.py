"""Simulation Query Handlers.

Application layer handlers for processing simulation queries (read operations).
Following CQRS pattern for clear separation of concerns.
"""

import logging
from typing import List, Optional

from .queries.simulation_queries import (
    ListSimulationsQuery,
    GetSimulationQuery,
    GetSimulationProgressQuery,
)
from ..domain.entities.simulation import Simulation
from ..domain.services.simulation_service import SimulationService
from ..infrastructure.repositories.simulation_repository import SimulationRepository

logger = logging.getLogger(__name__)


class ListSimulationsQueryHandler:
    """Handler for listing simulations with filtering."""

    def __init__(self, repository: SimulationRepository):
        self.repository = repository

    async def handle(self, query: ListSimulationsQuery) -> List[Simulation]:
        """Handle list simulations query."""
        try:
            logger.info(f"Listing simulations with filters: user_id={query.user_id}, status={query.status}")

            # Get simulations from repository with filters
            simulations = await self.repository.list_simulations(
                user_id=query.user_id,
                status=query.status,
                simulation_type=query.simulation_type,
                limit=query.limit,
                offset=query.offset,
                sort_by=query.sort_by,
                sort_order=query.sort_order,
            )

            logger.info(f"Found {len(simulations)} simulations")
            return simulations

        except Exception as e:
            logger.error(f"Failed to list simulations: {e}")
            raise


class GetSimulationQueryHandler:
    """Handler for getting a specific simulation."""

    def __init__(self, repository: SimulationRepository):
        self.repository = repository

    async def handle(self, query: GetSimulationQuery) -> Optional[Simulation]:
        """Handle get simulation query."""
        try:
            logger.info(f"Getting simulation: {query.simulation_id}")

            simulation = await self.repository.get_by_id(query.simulation_id)

            if simulation:
                logger.info(f"Simulation found: {query.simulation_id}")
            else:
                logger.warning(f"Simulation not found: {query.simulation_id}")

            return simulation

        except Exception as e:
            logger.error(f"Failed to get simulation {query.simulation_id}: {e}")
            raise


class GetSimulationProgressQueryHandler:
    """Handler for getting simulation progress."""

    def __init__(self, simulation_service: SimulationService, repository: SimulationRepository):
        self.simulation_service = simulation_service
        self.repository = repository

    async def handle(self, query: GetSimulationProgressQuery) -> dict:
        """Handle get simulation progress query."""
        try:
            logger.info(f"Getting simulation progress: {query.simulation_id}")

            # Get simulation
            simulation = await self.repository.get_by_id(query.simulation_id)
            if not simulation:
                raise ValueError(f"Simulation not found: {query.simulation_id}")

            # Get progress from domain service
            progress = await self.simulation_service.get_simulation_progress(
                simulation, include_logs=query.include_logs, log_limit=query.log_limit
            )

            logger.info(f"Retrieved progress for simulation: {query.simulation_id}")
            return progress

        except Exception as e:
            logger.error(f"Failed to get simulation progress {query.simulation_id}: {e}")
            raise
