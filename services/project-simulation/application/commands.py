"""Simulation commands for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class StartSimulationCommand(BaseModel):
    """Command to start a new simulation."""
    simulation_id: str
    project_type: str
    team_size: int
    duration_weeks: int
    configuration: Optional[Dict[str, Any]] = None


class StopSimulationCommand(BaseModel):
    """Command to stop a running simulation."""
    simulation_id: str
    reason: Optional[str] = None


class UpdateSimulationCommand(BaseModel):
    """Command to update simulation parameters."""
    simulation_id: str
    updates: Dict[str, Any]


class PauseSimulationCommand(BaseModel):
    """Command to pause a simulation."""
    simulation_id: str


class ResumeSimulationCommand(BaseModel):
    """Command to resume a paused simulation."""
    simulation_id: str
