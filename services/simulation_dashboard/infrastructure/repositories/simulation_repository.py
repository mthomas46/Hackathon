"""Simulation Repository.

Data access layer for simulation entities.
"""

from typing import Optional, List
from ...domain.entities.simulation import Simulation


class SimulationRepository:
    """Repository for simulation data access."""

    def __init__(self):
        # TODO: Initialize database connection or in-memory storage
        self._simulations = {}

    def save(self, simulation: Simulation) -> Simulation:
        """Save a simulation."""
        self._simulations[simulation.id] = simulation
        return simulation

    def find_by_id(self, simulation_id: str) -> Optional[Simulation]:
        """Find a simulation by ID."""
        return self._simulations.get(simulation_id)

    def find_all(self) -> List[Simulation]:
        """Find all simulations."""
        return list(self._simulations.values())

    def delete(self, simulation_id: str) -> bool:
        """Delete a simulation by ID."""
        if simulation_id in self._simulations:
            del self._simulations[simulation_id]
            return True
        return False

    def exists(self, simulation_id: str) -> bool:
        """Check if a simulation exists."""
        return simulation_id in self._simulations
