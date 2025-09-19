"""Domain Events - Cross-Bounded Context Communication.

This module defines domain events following Domain Driven Design principles.
Domain events represent significant business events that may trigger
actions in other bounded contexts.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod


@dataclass(frozen=True, kw_only=True)
class DomainEvent(ABC):
    """Base class for all domain events."""
    event_id: str = field(init=False)
    event_type: str = field(init=False)
    event_version: int = 1
    occurred_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        # Set event_id and event_type based on class name
        object.__setattr__(self, 'event_id', f"{self.__class__.__name__}_{datetime.now().timestamp()}")
        object.__setattr__(self, 'event_type', self.__class__.__name__)
        # Set default values for optional fields
        if not hasattr(self, 'event_version'):
            object.__setattr__(self, 'event_version', 1)
        if not hasattr(self, 'occurred_at'):
            object.__setattr__(self, 'occurred_at', datetime.now())

    @abstractmethod
    def get_aggregate_id(self) -> str:
        """Get the aggregate ID this event relates to."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result = {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "occurred_at": self.occurred_at.isoformat(),
            "event_version": self.event_version,
        }

        # Add other fields, converting datetime objects to ISO strings
        for k, v in self.__dict__.items():
            if k not in ['event_id', 'event_type', 'occurred_at', 'event_version']:
                if isinstance(v, datetime):
                    result[k] = v.isoformat()
                else:
                    result[k] = v

        return result


# Project Aggregate Events

@dataclass(frozen=True)
class ProjectCreated(DomainEvent):
    """Event fired when a new project is created."""
    project_id: str
    project_name: str
    project_type: str
    complexity: str

    def get_aggregate_id(self) -> str:
        return self.project_id


@dataclass(frozen=True)
class ProjectStatusChanged(DomainEvent):
    """Event fired when project status changes."""
    project_id: str
    old_status: str
    new_status: str
    changed_by: str

    def get_aggregate_id(self) -> str:
        return self.project_id


@dataclass(frozen=True)
class ProjectPhaseCompleted(DomainEvent):
    """Event fired when a project phase is completed."""
    project_id: str
    phase_name: str
    phase_number: int
    completion_percentage: float
    duration_days: int

    def get_aggregate_id(self) -> str:
        return self.project_id


@dataclass(frozen=True)
class TeamMemberAdded(DomainEvent):
    """Event fired when a team member is added to a project."""
    team_id: str
    project_id: str
    member_id: str
    member_name: str
    role: str
    skills: List[str]
    experience_years: int
    productivity_factor: float

    def get_aggregate_id(self) -> str:
        return self.project_id


@dataclass(frozen=True)
class TeamMemberRemoved(DomainEvent):
    """Event fired when a team member is removed from a project."""
    team_id: str
    project_id: str
    member_id: str
    member_name: str
    removal_reason: str
    removal_date: datetime
    replacement_planned: bool

    def get_aggregate_id(self) -> str:
        return self.project_id


# Simulation Aggregate Events

@dataclass(frozen=True)
class SimulationStarted(DomainEvent):
    """Event fired when a simulation starts."""
    simulation_id: str
    project_id: str
    scenario_type: str
    estimated_duration_hours: int

    def get_aggregate_id(self) -> str:
        return self.simulation_id


@dataclass(frozen=True)
class SimulationCompleted(DomainEvent):
    """Event fired when a simulation completes."""
    simulation_id: str
    project_id: str
    status: str
    metrics: Dict[str, Any]
    total_duration_hours: float

    def get_aggregate_id(self) -> str:
        return self.simulation_id


@dataclass(frozen=True)
class SimulationFailed(DomainEvent):
    """Event fired when a simulation fails."""
    simulation_id: str
    project_id: str
    failure_reason: str
    failure_time: datetime

    def get_aggregate_id(self) -> str:
        return self.simulation_id


@dataclass(frozen=True)
class DocumentGenerated(DomainEvent):
    """Event fired when a document is generated."""
    document_id: str
    project_id: str
    simulation_id: str
    document_type: str
    title: str
    content_hash: str
    metadata: Dict[str, Any]

    def get_aggregate_id(self) -> str:
        return self.simulation_id


@dataclass(frozen=True)
class WorkflowExecuted(DomainEvent):
    """Event fired when a workflow is executed."""
    workflow_id: str
    simulation_id: str
    workflow_type: str
    parameters: Dict[str, Any]
    results: Dict[str, Any]
    execution_time_seconds: float

    def get_aggregate_id(self) -> str:
        return self.simulation_id


# Timeline Aggregate Events

@dataclass(frozen=True)
class PhaseStarted(DomainEvent):
    """Event fired when a timeline phase starts."""
    timeline_id: str
    project_id: str
    phase_name: str
    start_date: datetime

    def get_aggregate_id(self) -> str:
        return self.timeline_id


@dataclass(frozen=True)
class PhaseDelayed(DomainEvent):
    """Event fired when a timeline phase is delayed."""
    timeline_id: str
    project_id: str
    phase_name: str
    original_end_date: datetime
    new_end_date: datetime
    delay_reason: str

    def get_aggregate_id(self) -> str:
        return self.timeline_id


@dataclass(frozen=True)
class MilestoneAchieved(DomainEvent):
    """Event fired when a milestone is achieved."""
    timeline_id: str
    project_id: str
    milestone_name: str
    achieved_date: datetime

    def get_aggregate_id(self) -> str:
        return self.timeline_id


# Integration Events (Cross-Bounded Context)

@dataclass(frozen=True)
class EcosystemServiceHealthChanged(DomainEvent):
    """Event fired when ecosystem service health changes."""
    service_name: str
    old_status: str
    new_status: str
    response_time_ms: Optional[float]
    affected_simulations: List[str]

    def get_aggregate_id(self) -> str:
        return self.service_name


@dataclass(frozen=True)
class DocumentAnalysisCompleted(DomainEvent):
    """Event fired when document analysis is completed."""
    document_id: str
    analysis_type: str
    confidence_score: float
    insights_found: int
    processing_time_seconds: float

    def get_aggregate_id(self) -> str:
        return self.document_id


@dataclass(frozen=True)
class WorkflowOrchestrationCompleted(DomainEvent):
    """Event fired when workflow orchestration is completed."""
    workflow_id: str
    orchestration_type: str
    services_involved: List[str]
    total_execution_time_seconds: float
    success: bool

    def get_aggregate_id(self) -> str:
        return self.workflow_id


@dataclass(frozen=True)
class NotificationSent(DomainEvent):
    """Event fired when a notification is sent."""
    notification_id: str
    recipient: str
    notification_type: str
    priority: str
    sent_at: datetime

    def get_aggregate_id(self) -> str:
        return self.notification_id


@dataclass(frozen=True)
class AnalyticsDataGenerated(DomainEvent):
    """Event fired when analytics data is generated."""
    analytics_id: str
    data_type: str
    records_generated: int
    time_range_days: int
    processing_time_seconds: float

    def get_aggregate_id(self) -> str:
        return self.analytics_id


@dataclass(frozen=True)
class ConfigurationChanged(DomainEvent):
    """Event fired when system configuration changes."""
    config_id: str
    config_type: str
    changed_by: str
    change_description: str
    affected_services: List[str]

    def get_aggregate_id(self) -> str:
        return self.config_id


@dataclass(frozen=True)
class TimelineEventOccurred(DomainEvent):
    """Event fired when a timeline event occurs."""
    simulation_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any]

    def get_aggregate_id(self) -> str:
        return self.simulation_id


# Event Registry for Serialization
EVENT_TYPES = {
    # Project Events
    "ProjectCreated": ProjectCreated,
    "ProjectStatusChanged": ProjectStatusChanged,
    "ProjectPhaseCompleted": ProjectPhaseCompleted,
    "TeamMemberAdded": TeamMemberAdded,
    "TeamMemberRemoved": TeamMemberRemoved,

    # Simulation Events
    "SimulationStarted": SimulationStarted,
    "SimulationCompleted": SimulationCompleted,
    "SimulationFailed": SimulationFailed,
    "DocumentGenerated": DocumentGenerated,
    "WorkflowExecuted": WorkflowExecuted,

    # Timeline Events
    "PhaseStarted": PhaseStarted,
    "PhaseDelayed": PhaseDelayed,
    "MilestoneAchieved": MilestoneAchieved,

    # Integration Events
    "EcosystemServiceHealthChanged": EcosystemServiceHealthChanged,
    "DocumentAnalysisCompleted": DocumentAnalysisCompleted,
    "WorkflowOrchestrationCompleted": WorkflowOrchestrationCompleted,
    "NotificationSent": NotificationSent,
    "AnalyticsDataGenerated": AnalyticsDataGenerated,
    "ConfigurationChanged": ConfigurationChanged,
    "TimelineEventOccurred": TimelineEventOccurred,
}


def event_from_dict(data: Dict[str, Any]) -> DomainEvent:
    """Deserialize event from dictionary."""
    event_type = data.get("event_type")
    if not event_type or event_type not in EVENT_TYPES:
        raise ValueError(f"Unknown event type: {event_type}")

    # Remove metadata fields before creating event
    event_data = {k: v for k, v in data.items()
                  if k not in ["event_id", "event_type", "occurred_at", "event_version"]}

    # Convert occurred_at back to datetime
    if "occurred_at" in data:
        event_data["occurred_at"] = datetime.fromisoformat(data["occurred_at"])

    return EVENT_TYPES[event_type](**event_data)
