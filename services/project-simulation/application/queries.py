"""Simulation queries for CQRS pattern compliance."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GetSimulationStatusQuery(BaseModel):
    """Query to get simulation status."""
    simulation_id: str


class ListSimulationsQuery(BaseModel):
    """Query to list simulations with filters."""
    status: Optional[str] = None
    project_type: Optional[str] = None
    limit: int = 50
    offset: int = 0


class GetSimulationDetailsQuery(BaseModel):
    """Query to get detailed simulation information."""
    simulation_id: str
    include_history: bool = False


class GetSimulationMetricsQuery(BaseModel):
    """Query to get simulation performance metrics."""
    simulation_id: str
    metric_types: List[str]


class GetTeamPerformanceQuery(BaseModel):
    """Query to get team performance data."""
    simulation_id: str
    team_member_id: Optional[str] = None
