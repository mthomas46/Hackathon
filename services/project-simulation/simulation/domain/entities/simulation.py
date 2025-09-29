"""Simulation Aggregate - Domain Entity.

This module defines the Simulation aggregate, which orchestrates the entire
simulation process and coordinates between Project, Timeline, and Team aggregates.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from enum import Enum

from .project import Project, ProjectId
from .timeline import Timeline, TimelineId
from .team import Team, TeamId
from ..value_objects import SimulationStatus, SimulationMetrics, DocumentType
from ..events import (SimulationStarted, SimulationCompleted, SimulationFailed,
                     DocumentGenerated, WorkflowExecuted)


@dataclass(frozen=True)
class SimulationId:
    """Value object for Simulation ID."""
    value: UUID = field(default_factory=uuid4)

    @classmethod
    def from_string(cls, value: str) -> SimulationId:
        """Create SimulationId from string."""
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)


class SimulationType(Enum):
    """Types of simulation scenarios."""
    FULL_PROJECT = "full_project"
    PHASE_FOCUS = "phase_focus"
    TEAM_DYNAMICS = "team_dynamics"
    DOCUMENT_GENERATION = "document_generation"
    WORKFLOW_EXECUTION = "workflow_execution"
    PERFORMANCE_TEST = "performance_test"


@dataclass
class SimulationConfiguration:
    """Configuration for simulation execution."""
    simulation_type: SimulationType
    include_document_generation: bool = True
    include_workflow_execution: bool = True
    include_team_dynamics: bool = True
    real_time_progress: bool = False
    max_execution_time_minutes: int = 60
    generate_realistic_delays: bool = True
    capture_metrics: bool = True
    enable_ecosystem_integration: bool = True

    def should_generate_documents(self) -> bool:
        """Check if document generation is enabled."""
        return self.include_document_generation

    def should_execute_workflows(self) -> bool:
        """Check if workflow execution is enabled."""
        return self.include_workflow_execution

    def should_simulate_team_dynamics(self) -> bool:
        """Check if team dynamics simulation is enabled."""
        return self.include_team_dynamics

    def get_max_execution_time(self) -> timedelta:
        """Get maximum execution time as timedelta."""
        return timedelta(minutes=self.max_execution_time_minutes)


@dataclass
class SimulationProgress:
    """Entity tracking simulation progress."""
    total_phases: int = 0
    completed_phases: int = 0
    current_phase: Optional[str] = None
    documents_generated: int = 0
    workflows_executed: int = 0
    start_time: Optional[datetime] = None
    estimated_completion_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None

    def update_phase_progress(self, phase_name: str, completed: bool = False) -> None:
        """Update phase progress."""
        self.current_phase = phase_name
        if completed and self.current_phase != phase_name:
            self.completed_phases += 1
        self.last_activity = datetime.now()

    def increment_documents(self, count: int = 1) -> None:
        """Increment document generation count."""
        self.documents_generated += count
        self.last_activity = datetime.now()

    def increment_workflows(self, count: int = 1) -> None:
        """Increment workflow execution count."""
        self.workflows_executed += count
        self.last_activity = datetime.now()

    def get_progress_percentage(self) -> float:
        """Get overall progress percentage."""
        if self.total_phases == 0:
            return 0.0
        return (self.completed_phases / self.total_phases) * 100.0

    def get_elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time since simulation started."""
        if not self.start_time:
            return None
        return datetime.now() - self.start_time

    def get_estimated_time_remaining(self) -> Optional[timedelta]:
        """Get estimated time remaining."""
        if not self.start_time or not self.estimated_completion_time:
            return None
        remaining = self.estimated_completion_time - datetime.now()
        return max(timedelta(0), remaining)


@dataclass
class SimulationResult:
    """Entity representing simulation results."""
    success: bool
    execution_time_seconds: float
    metrics: SimulationMetrics
    documents_created: List[Dict[str, Any]] = field(default_factory=list)
    workflows_executed: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        """Add an error to the results."""
        self.errors.append(error)

    def add_warning(self, warning: str) -> None:
        """Add a warning to the results."""
        self.warnings.append(warning)

    def add_insight(self, insight: str) -> None:
        """Add an insight to the results."""
        self.insights.append(insight)

    def add_document_created(self, doc_info: Dict[str, Any]) -> None:
        """Add information about a created document."""
        self.documents_created.append(doc_info)

    def add_workflow_executed(self, workflow_info: Dict[str, Any]) -> None:
        """Add information about an executed workflow."""
        self.workflows_executed.append(workflow_info)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of simulation results."""
        return {
            "success": self.success,
            "execution_time_seconds": self.execution_time_seconds,
            "total_documents": len(self.documents_created),
            "total_workflows": len(self.workflows_executed),
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "total_insights": len(self.insights),
            "metrics": self.metrics
        }


@dataclass
class Simulation:
    """Simulation Aggregate Root.

    This is the root entity for the Simulation aggregate, orchestrating
    the entire simulation process and coordinating between all aggregates.
    """
    id: SimulationId
    project_id: str
    configuration: SimulationConfiguration
    status: SimulationStatus = SimulationStatus.CREATED
    progress: SimulationProgress = field(default_factory=SimulationProgress)
    result: Optional[SimulationResult] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Domain events
    _domain_events: List[Any] = field(default_factory=list, init=False)

    def start_simulation(self) -> None:
        """Start the simulation execution."""
        if self.status != SimulationStatus.CREATED:
            raise ValueError(f"Cannot start simulation in status: {self.status.value}")

        self.status = SimulationStatus.STARTING
        self.started_at = datetime.now()
        self.progress.start_time = self.started_at

        # Estimate completion time
        self.progress.estimated_completion_time = (
            self.started_at + self.configuration.get_max_execution_time()
        )

        self._add_domain_event(SimulationStarted(
            simulation_id=str(self.id.value),
            project_id=self.project_id,
            scenario_type=self.configuration.simulation_type.value,
            start_time=self.started_at
        ))

        self.status = SimulationStatus.RUNNING

    def update_progress(self, phase_name: str, documents_count: int = 0,
                       workflows_count: int = 0, completed: bool = False) -> None:
        """Update simulation progress."""
        self.progress.update_phase_progress(phase_name, completed)
        self.progress.increment_documents(documents_count)
        self.progress.increment_workflows(workflows_count)

    def record_document_generation(self, document_type: DocumentType,
                                 title: str, word_count: int) -> None:
        """Record a document generation event."""
        self.progress.increment_documents()

        self._add_domain_event(DocumentGenerated(
            simulation_id=str(self.id.value),
            document_id=f"doc_{datetime.now().timestamp()}",
            document_type=document_type.value,
            title=title,
            word_count=word_count
        ))

    def record_workflow_execution(self, workflow_type: str,
                                execution_time_seconds: float,
                                success: bool) -> None:
        """Record a workflow execution event."""
        self.progress.increment_workflows()

        self._add_domain_event(WorkflowExecuted(
            simulation_id=str(self.id.value),
            workflow_id=f"workflow_{datetime.now().timestamp()}",
            workflow_type=workflow_type,
            execution_time_seconds=execution_time_seconds,
            success=success
        ))

    def complete_simulation(self, success: bool, execution_time: float,
                          metrics: SimulationMetrics) -> None:
        """Complete the simulation."""
        self.status = SimulationStatus.COMPLETED if success else SimulationStatus.FAILED
        self.completed_at = datetime.now()
        self.result = SimulationResult(
            success=success,
            execution_time_seconds=execution_time,
            metrics=metrics
        )

        self._add_domain_event(SimulationCompleted(
            simulation_id=str(self.id.value),
            project_id=self.project_id,
            end_time=self.completed_at,
            success=success,
            metrics=metrics.__dict__ if metrics else {}
        ))

    def fail_simulation(self, failure_reason: str) -> None:
        """Mark simulation as failed."""
        self.status = SimulationStatus.FAILED
        self.completed_at = datetime.now()

        if self.result:
            self.result.add_error(failure_reason)

        self._add_domain_event(SimulationFailed(
            simulation_id=str(self.id.value),
            project_id=self.project_id,
            failure_reason=failure_reason,
            failure_time=self.completed_at
        ))

    def pause_simulation(self) -> None:
        """Pause the simulation."""
        if self.status == SimulationStatus.RUNNING:
            self.status = SimulationStatus.PAUSED

    def resume_simulation(self) -> None:
        """Resume the simulation."""
        if self.status == SimulationStatus.PAUSED:
            self.status = SimulationStatus.RUNNING

    def cancel_simulation(self) -> None:
        """Cancel the simulation."""
        self.status = SimulationStatus.CANCELLED
        self.completed_at = datetime.now()

    def is_running(self) -> bool:
        """Check if simulation is currently running."""
        return self.status == SimulationStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if simulation is completed."""
        return self.status in [SimulationStatus.COMPLETED, SimulationStatus.FAILED, SimulationStatus.CANCELLED]

    def get_elapsed_time(self) -> Optional[timedelta]:
        """Get elapsed time since simulation started."""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return end_time - self.started_at

    def get_progress_percentage(self) -> float:
        """Get overall simulation progress percentage."""
        return self.progress.get_progress_percentage()

    def is_within_time_limit(self) -> bool:
        """Check if simulation is within time limits."""
        elapsed = self.get_elapsed_time()
        if not elapsed:
            return True
        return elapsed <= self.configuration.get_max_execution_time()

    def should_continue(self) -> bool:
        """Check if simulation should continue running."""
        return (self.is_running() and
                self.is_within_time_limit() and
                not self.is_completed())

    def get_simulation_summary(self) -> Dict[str, Any]:
        """Get a summary of the simulation."""
        return {
            "id": str(self.id.value),
            "project_id": self.project_id,
            "status": self.status.value,
            "type": self.configuration.simulation_type.value,
            "progress": self.get_progress_percentage(),
            "elapsed_time": self.get_elapsed_time(),
            "documents_generated": self.progress.documents_generated,
            "workflows_executed": self.progress.workflows_executed,
            "result": self.result.get_summary() if self.result else None
        }

    def _add_domain_event(self, event: Any) -> None:
        """Add a domain event."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List[Any]:
        """Get all domain events."""
        return self._domain_events.copy()

    def clear_domain_events(self) -> None:
        """Clear all domain events."""
        self._domain_events.clear()

    def __str__(self) -> str:
        return (f"Simulation(id={self.id}, project_id={self.project_id}, "
                f"status={self.status.value}, progress={self.get_progress_percentage():.1f}%)")

    def __repr__(self) -> str:
        return self.__str__()
