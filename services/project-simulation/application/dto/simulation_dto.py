"""Data Transfer Objects for simulation operations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class SimulationDto(BaseModel):
    """DTO for simulation data transfer."""
    id: str
    project_type: str
    team_size: int
    duration_weeks: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class SimulationSummaryDto(BaseModel):
    """DTO for simulation summary data."""
    simulation_id: str
    total_tasks: int
    completed_tasks: int
    progress_percentage: float
    estimated_completion: Optional[datetime] = None
    key_metrics: Dict[str, Any]


class TeamMemberDto(BaseModel):
    """DTO for team member data."""
    id: str
    name: str
    role: str
    expertise: List[str]
    performance_score: Optional[float] = None


class ProjectMetricsDto(BaseModel):
    """DTO for project metrics data."""
    simulation_id: str
    velocity: float
    quality_score: float
    risk_level: str
    timeline_adherence: float
    resource_utilization: float
