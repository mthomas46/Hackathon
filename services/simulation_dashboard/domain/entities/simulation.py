"""Simulation domain entity."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from services.shared.domain import BaseEntity


class SimulationStatus(Enum):
    """Simulation status enumeration."""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationType(Enum):
    """Simulation type enumeration."""
    PROJECT_SIMULATION = "project_simulation"
    RISK_ANALYSIS = "risk_analysis"
    RESOURCE_OPTIMIZATION = "resource_optimization"
    BUDGET_PLANNING = "budget_planning"
    TEAM_OPTIMIZATION = "team_optimization"


@dataclass
class Simulation(BaseEntity):
    """Domain entity representing a simulation."""

    id: str
    name: str
    description: Optional[str] = None
    simulation_type: SimulationType = SimulationType.PROJECT_SIMULATION
    status: SimulationStatus = SimulationStatus.CREATED
    configuration: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    progress_percentage: float = 0.0
    estimated_completion_time: Optional[datetime] = None
    actual_completion_time: Optional[datetime] = None
    error_message: Optional[str] = None
    created_by: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Post initialization validation."""
        if not self.id:
            raise ValueError("Simulation ID cannot be empty")
        if not self.name:
            raise ValueError("Simulation name cannot be empty")
        if not isinstance(self.progress_percentage, (int, float)):
            raise ValueError("Progress percentage must be numeric")
        if not 0 <= self.progress_percentage <= 100:
            raise ValueError("Progress percentage must be between 0 and 100")

    def start_simulation(self) -> None:
        """Start the simulation."""
        if self.status != SimulationStatus.CREATED:
            raise ValueError(f"Cannot start simulation in {self.status.value} status")
        self.status = SimulationStatus.RUNNING
        self.updated_at = datetime.utcnow()

    def pause_simulation(self) -> None:
        """Pause the simulation."""
        if self.status != SimulationStatus.RUNNING:
            raise ValueError(f"Cannot pause simulation in {self.status.value} status")
        self.status = SimulationStatus.PAUSED
        self.updated_at = datetime.utcnow()

    def resume_simulation(self) -> None:
        """Resume the simulation."""
        if self.status != SimulationStatus.PAUSED:
            raise ValueError(f"Cannot resume simulation in {self.status.value} status")
        self.status = SimulationStatus.RUNNING
        self.updated_at = datetime.utcnow()

    def complete_simulation(self, results: Dict[str, Any]) -> None:
        """Complete the simulation with results."""
        if self.status not in [SimulationStatus.RUNNING, SimulationStatus.PAUSED]:
            raise ValueError(f"Cannot complete simulation in {self.status.value} status")
        self.status = SimulationStatus.COMPLETED
        self.results = results
        self.progress_percentage = 100.0
        self.actual_completion_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail_simulation(self, error_message: str) -> None:
        """Mark simulation as failed."""
        self.status = SimulationStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.utcnow()

    def cancel_simulation(self) -> None:
        """Cancel the simulation."""
        if self.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED]:
            raise ValueError(f"Cannot cancel simulation in {self.status.value} status")
        self.status = SimulationStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    def update_progress(self, percentage: float, message: Optional[str] = None) -> None:
        """Update simulation progress."""
        if not 0 <= percentage <= 100:
            raise ValueError("Progress percentage must be between 0 and 100")
        self.progress_percentage = percentage
        if message:
            self.results["last_progress_message"] = message
        self.updated_at = datetime.utcnow()

    def is_running(self) -> bool:
        """Check if simulation is currently running."""
        return self.status == SimulationStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if simulation is completed."""
        return self.status == SimulationStatus.COMPLETED

    def is_failed(self) -> bool:
        """Check if simulation has failed."""
        return self.status == SimulationStatus.FAILED

    def get_duration_seconds(self) -> Optional[float]:
        """Get simulation duration in seconds."""
        if not self.actual_completion_time or not self.created_at:
            return None
        duration = self.actual_completion_time - self.created_at
        return duration.total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert simulation to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "simulation_type": self.simulation_type.value,
            "status": self.status.value,
            "configuration": self.configuration,
            "parameters": self.parameters,
            "results": self.results,
            "progress_percentage": self.progress_percentage,
            "estimated_completion_time": self.estimated_completion_time.isoformat() if self.estimated_completion_time else None,
            "actual_completion_time": self.actual_completion_time.isoformat() if self.actual_completion_time else None,
            "error_message": self.error_message,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags
        }
