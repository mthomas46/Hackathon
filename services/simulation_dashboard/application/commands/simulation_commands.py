"""Simulation Commands.

Command objects for simulation operations following CQRS principles.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class CreateSimulationCommand:
    """Command to create a new simulation."""

    name: str
    description: Optional[str] = None
    simulation_type: str = "standard"
    parameters: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate command data."""
        if not self.name or not self.name.strip():
            raise ValueError("Simulation name is required")
        if self.parameters is None:
            self.parameters = {}
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UpdateSimulationCommand:
    """Command to update an existing simulation."""

    simulation_id: str
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate command data."""
        if not self.simulation_id:
            raise ValueError("Simulation ID is required")


@dataclass
class DeleteSimulationCommand:
    """Command to delete a simulation."""

    simulation_id: str
    user_id: Optional[str] = None

    def __post_init__(self):
        """Validate command data."""
        if not self.simulation_id:
            raise ValueError("Simulation ID is required")


@dataclass
class StartSimulationCommand:
    """Command to start a simulation."""

    simulation_id: str
    user_id: Optional[str] = None
    execution_parameters: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate command data."""
        if not self.simulation_id:
            raise ValueError("Simulation ID is required")
        if self.execution_parameters is None:
            self.execution_parameters = {}


@dataclass
class StopSimulationCommand:
    """Command to stop a running simulation."""

    simulation_id: str
    user_id: Optional[str] = None
    reason: Optional[str] = None

    def __post_init__(self):
        """Validate command data."""
        if not self.simulation_id:
            raise ValueError("Simulation ID is required")
