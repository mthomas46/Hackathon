"""Simulation domain events for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class SimulationStartedEvent(BaseModel):
    """Event fired when a simulation starts."""
    simulation_id: str
    project_type: str
    team_size: int
    started_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class SimulationCompletedEvent(BaseModel):
    """Event fired when a simulation completes."""
    simulation_id: str
    completed_at: datetime
    final_status: str
    metrics: Dict[str, Any]


class SimulationPausedEvent(BaseModel):
    """Event fired when a simulation is paused."""
    simulation_id: str
    paused_at: datetime
    reason: Optional[str] = None


class SimulationResumedEvent(BaseModel):
    """Event fired when a simulation is resumed."""
    simulation_id: str
    resumed_at: datetime


class TeamAssignmentChangedEvent(BaseModel):
    """Event fired when team assignments change."""
    simulation_id: str
    team_member_id: str
    new_role: str
    changed_at: datetime
