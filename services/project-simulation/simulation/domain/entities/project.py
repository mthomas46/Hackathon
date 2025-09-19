"""Project Aggregate - Domain Entity.

This module defines the Project aggregate, which is the root entity for
simulation projects in the domain-driven design architecture.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
from uuid import UUID, uuid4

from ..value_objects import ProjectType, ComplexityLevel, ProjectStatus
from ..events import ProjectCreated, ProjectStatusChanged, ProjectPhaseCompleted


@dataclass(frozen=True)
class ProjectId:
    """Value object for Project ID."""
    value: UUID = field(default_factory=uuid4)

    @classmethod
    def from_string(cls, value: str) -> ProjectId:
        """Create ProjectId from string."""
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class TeamMember:
    """Entity representing a team member."""
    id: str
    name: str
    role: str
    expertise_level: str
    communication_style: str
    work_style: str
    specialization: List[str] = field(default_factory=list)
    productivity_multiplier: float = 1.0

    def can_handle_task(self, task_type: str) -> bool:
        """Check if team member can handle a specific task type."""
        return task_type in self.specialization or self.expertise_level in ['expert', 'advanced', 'senior']

    def get_productivity_for_task(self, task_type: str) -> float:
        """Get productivity multiplier for a specific task."""
        if self.can_handle_task(task_type):
            return self.productivity_multiplier
        return self.productivity_multiplier * 0.7  # Reduced productivity for non-specialized work


@dataclass
class ProjectPhase:
    """Entity representing a project phase."""
    name: str
    duration_days: int
    deliverables: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    team_allocation: Dict[str, int] = field(default_factory=dict)
    status: str = "pending"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def start_phase(self, start_date: datetime) -> None:
        """Start the project phase."""
        self.status = "in_progress"
        self.start_date = start_date

    def complete_phase(self) -> None:
        """Complete the project phase."""
        self.status = "completed"
        self.end_date = datetime.now()

    def is_completed(self) -> bool:
        """Check if phase is completed."""
        return self.status == "completed"

    def get_duration_so_far(self) -> Optional[timedelta]:
        """Get duration since phase started."""
        if self.start_date:
            return datetime.now() - self.start_date
        return None


@dataclass
class Project:
    """Project Aggregate Root.

    This is the root entity for the Project aggregate, containing
    all project-related data and enforcing business rules.
    """
    id: ProjectId
    name: str
    description: str
    type: ProjectType
    team_size: int
    complexity: ComplexityLevel
    duration_weeks: int
    status: ProjectStatus = ProjectStatus.CREATED
    team_members: List[TeamMember] = field(default_factory=list)
    phases: List[ProjectPhase] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Domain events
    _domain_events: List[Any] = field(default_factory=list, init=False)

    def __post_init__(self):
        """Initialize project with default phases if none provided."""
        if not self.phases:
            self._initialize_default_phases()
        self._add_domain_event(ProjectCreated(
            project_id=str(self.id.value),
            project_name=self.name,
            project_type=self.type.value,
            complexity=self.complexity.value
        ))

    def _initialize_default_phases(self) -> None:
        """Initialize default project phases based on project type."""
        if self.type == ProjectType.WEB_APPLICATION:
            self.phases = [
                ProjectPhase(
                    name="planning",
                    duration_days=7,
                    deliverables=["requirements", "architecture_overview", "project_plan"],
                    team_allocation={"product_manager": 1, "technical_lead": 1}
                ),
                ProjectPhase(
                    name="design",
                    duration_days=10,
                    deliverables=["technical_design", "user_stories", "wireframes"],
                    dependencies=["planning"],
                    team_allocation={"designer": 1, "developer": 2, "technical_lead": 1}
                ),
                ProjectPhase(
                    name="development",
                    duration_days=21,
                    deliverables=["backend_api", "frontend_ui", "database_schema"],
                    dependencies=["design"],
                    team_allocation={"developer": 3, "technical_lead": 1}
                ),
                ProjectPhase(
                    name="testing",
                    duration_days=7,
                    deliverables=["test_cases", "test_results", "bug_reports"],
                    dependencies=["development"],
                    team_allocation={"qa_engineer": 2, "developer": 1}
                ),
                ProjectPhase(
                    name="deployment",
                    duration_days=3,
                    deliverables=["production_deployment", "documentation"],
                    dependencies=["testing"],
                    team_allocation={"devops_engineer": 1, "technical_lead": 1}
                )
            ]
        elif self.type == ProjectType.API_SERVICE:
            self.phases = [
                ProjectPhase(
                    name="requirements",
                    duration_days=5,
                    deliverables=["api_requirements", "security_requirements"],
                    team_allocation={"product_manager": 1, "technical_lead": 1}
                ),
                ProjectPhase(
                    name="design",
                    duration_days=8,
                    deliverables=["api_specification", "data_model", "architecture"],
                    dependencies=["requirements"],
                    team_allocation={"technical_lead": 1, "developer": 2}
                ),
                ProjectPhase(
                    name="implementation",
                    duration_days=15,
                    deliverables=["api_endpoints", "documentation", "tests"],
                    dependencies=["design"],
                    team_allocation={"developer": 3}
                ),
                ProjectPhase(
                    name="validation",
                    duration_days=4,
                    deliverables=["security_audit", "performance_test", "documentation_review"],
                    dependencies=["implementation"],
                    team_allocation={"qa_engineer": 1, "security_engineer": 1}
                )
            ]
        # Add more project types as needed...

    def add_team_member(self, member: TeamMember) -> None:
        """Add a team member to the project."""
        if len(self.team_members) >= self.team_size:
            raise ValueError(f"Project already has maximum team size of {self.team_size}")

        if any(m.id == member.id for m in self.team_members):
            raise ValueError(f"Team member with ID {member.id} already exists")

        self.team_members.append(member)
        self.updated_at = datetime.now()

    def remove_team_member(self, member_id: str) -> None:
        """Remove a team member from the project."""
        self.team_members = [m for m in self.team_members if m.id != member_id]
        self.updated_at = datetime.now()

    def start_phase(self, phase_name: str) -> None:
        """Start a project phase."""
        phase = self._get_phase(phase_name)

        # Check dependencies
        for dep in phase.dependencies:
            dep_phase = self._get_phase(dep)
            if not dep_phase.is_completed():
                raise ValueError(f"Cannot start phase {phase_name}: dependency {dep} not completed")

        phase.start_phase(datetime.now())
        self.updated_at = datetime.now()

    def complete_phase(self, phase_name: str) -> None:
        """Complete a project phase."""
        phase = self._get_phase(phase_name)
        phase.complete_phase()
        self.updated_at = datetime.now()

        # Find the phase number (index + 1)
        phase_number = self.phases.index(phase) + 1

        self._add_domain_event(ProjectPhaseCompleted(
            project_id=str(self.id.value),
            phase_name=phase_name,
            phase_number=phase_number,
            completion_percentage=100.0,
            duration_days=(phase.end_date - phase.start_date).days
        ))

    def update_status(self, new_status: ProjectStatus) -> None:
        """Update project status."""
        if self.status == new_status:
            return

        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()

        self._add_domain_event(ProjectStatusChanged(
            project_id=str(self.id.value),
            old_status=old_status.value,
            new_status=new_status.value,
            changed_by="system"
        ))

    def get_current_phase(self) -> Optional[ProjectPhase]:
        """Get the currently active phase."""
        for phase in self.phases:
            if phase.status == "in_progress":
                return phase
        return None

    def get_completed_phases(self) -> List[ProjectPhase]:
        """Get all completed phases."""
        return [phase for phase in self.phases if phase.is_completed()]

    def get_team_members_by_role(self, role: str) -> List[TeamMember]:
        """Get team members by role."""
        return [member for member in self.team_members if member.role == role]

    def calculate_progress_percentage(self) -> float:
        """Calculate overall project progress percentage."""
        if not self.phases:
            return 0.0

        completed_phases = len(self.get_completed_phases())
        return (completed_phases / len(self.phases)) * 100.0

    def get_estimated_completion_date(self) -> datetime:
        """Get estimated project completion date."""
        return self.created_at + timedelta(weeks=self.duration_weeks)

    def is_overdue(self) -> bool:
        """Check if project is overdue."""
        return datetime.now() > self.get_estimated_completion_date()

    def _get_phase(self, phase_name: str) -> ProjectPhase:
        """Get a phase by name."""
        for phase in self.phases:
            if phase.name == phase_name:
                return phase
        raise ValueError(f"Phase {phase_name} not found")

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
        return f"Project(id={self.id}, name='{self.name}', status={self.status.value})"

    def __repr__(self) -> str:
        return self.__str__()
