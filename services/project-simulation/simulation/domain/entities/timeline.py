"""Timeline Aggregate - Domain Entity.

This module defines the Timeline aggregate, which manages project phases,
milestones, and timeline progression in the domain-driven design architecture.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4

from ..value_objects import Duration, Percentage
from ..events import PhaseStarted, PhaseDelayed, MilestoneAchieved


@dataclass(frozen=True)
class TimelineId:
    """Value object for Timeline ID."""
    value: UUID = field(default_factory=uuid4)

    @classmethod
    def from_string(cls, value: str) -> TimelineId:
        """Create TimelineId from string."""
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)


@dataclass
class Milestone:
    """Entity representing a project milestone."""
    id: str
    name: str
    description: str
    due_date: datetime
    achieved_date: Optional[datetime] = None
    status: str = "pending"
    dependencies: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)

    def achieve_milestone(self, achieved_date: Optional[datetime] = None) -> None:
        """Mark milestone as achieved."""
        self.status = "achieved"
        self.achieved_date = achieved_date or datetime.now()

    def is_achieved(self) -> bool:
        """Check if milestone is achieved."""
        return self.status == "achieved"

    def is_overdue(self) -> bool:
        """Check if milestone is overdue."""
        return datetime.now() > self.due_date and not self.is_achieved()

    def get_days_overdue(self) -> int:
        """Get number of days milestone is overdue."""
        if not self.is_overdue():
            return 0
        return (datetime.now() - self.due_date).days

    def can_be_achieved(self, achieved_milestones: List[str]) -> bool:
        """Check if milestone can be achieved (all dependencies met)."""
        return all(dep in achieved_milestones for dep in self.dependencies)


@dataclass
class TimelinePhase:
    """Enhanced entity representing a timeline phase with detailed tracking."""
    id: str
    name: str
    display_name: str
    description: str
    planned_duration: Duration
    actual_duration: Optional[Duration] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    planned_end_date: Optional[datetime] = None
    status: str = "pending"
    progress_percentage: Percentage = field(default_factory=lambda: Percentage(0))
    dependencies: List[str] = field(default_factory=list)
    milestones: List[Milestone] = field(default_factory=list)
    team_allocation: Dict[str, int] = field(default_factory=dict)
    risk_level: str = "low"
    blockers: List[str] = field(default_factory=list)

    def start_phase(self, start_date: Optional[datetime] = None) -> None:
        """Start the timeline phase."""
        self.status = "in_progress"
        self.start_date = start_date or datetime.now()
        self.planned_end_date = self.start_date + timedelta(days=self.planned_duration.total_days)

    def update_progress(self, progress: Percentage) -> None:
        """Update phase progress percentage."""
        self.progress_percentage = progress

    def complete_phase(self, end_date: Optional[datetime] = None) -> None:
        """Complete the timeline phase."""
        self.status = "completed"
        self.end_date = end_date or datetime.now()
        self.actual_duration = Duration(
            weeks=int((self.end_date - self.start_date).days // 7),
            days=(self.end_date - self.start_date).days % 7
        )
        self.progress_percentage = Percentage(100)

    def delay_phase(self, delay_days: int, reason: str) -> None:
        """Delay the phase by specified days."""
        if self.planned_end_date:
            self.planned_end_date += timedelta(days=delay_days)
            self.blockers.append(f"Delay: {reason} (+{delay_days} days)")

    def add_milestone(self, milestone: Milestone) -> None:
        """Add a milestone to this phase."""
        self.milestones.append(milestone)

    def get_achieved_milestones(self) -> List[Milestone]:
        """Get all achieved milestones in this phase."""
        return [m for m in self.milestones if m.is_achieved()]

    def get_overdue_milestones(self) -> List[Milestone]:
        """Get all overdue milestones in this phase."""
        return [m for m in self.milestones if m.is_overdue()]

    def is_on_track(self) -> bool:
        """Check if phase is on track (within planned duration)."""
        if not self.start_date or not self.planned_end_date:
            return True
        return datetime.now() <= self.planned_end_date

    def get_days_remaining(self) -> int:
        """Get days remaining until planned end date."""
        if not self.planned_end_date:
            return 0
        remaining = (self.planned_end_date - datetime.now()).days
        return max(0, remaining)

    def get_days_delayed(self) -> int:
        """Get number of days phase is delayed."""
        if not self.planned_end_date or self.status == "completed":
            return 0
        delay = (datetime.now() - self.planned_end_date).days
        return max(0, delay)

    def can_start(self, completed_phases: List[str]) -> bool:
        """Check if phase can start (all dependencies met)."""
        return all(dep in completed_phases for dep in self.dependencies)


@dataclass
class Timeline:
    """Timeline Aggregate Root.

    This is the root entity for the Timeline aggregate, managing project phases,
    milestones, and overall timeline progression.
    """
    id: TimelineId
    project_id: str
    phases: List[TimelinePhase] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Domain events
    _domain_events: List[Any] = field(default_factory=list, init=False)

    def add_phase(self, phase: TimelinePhase) -> None:
        """Add a phase to the timeline."""
        if any(p.id == phase.id for p in self.phases):
            raise ValueError(f"Phase with ID {phase.id} already exists")

        self.phases.append(phase)
        self.updated_at = datetime.now()

    def start_phase(self, phase_id: str, start_date: Optional[datetime] = None) -> None:
        """Start a timeline phase."""
        phase = self._get_phase(phase_id)

        # Check dependencies
        completed_phase_ids = [p.id for p in self.phases if p.status == "completed"]
        if not phase.can_start(completed_phase_ids):
            raise ValueError(f"Cannot start phase {phase_id}: dependencies not met")

        phase.start_phase(start_date)
        self.updated_at = datetime.now()

        self._add_domain_event(PhaseStarted(
            timeline_id=str(self.id.value),
            project_id=self.project_id,
            phase_name=phase.name,
            start_date=phase.start_date
        ))

    def complete_phase(self, phase_id: str, end_date: Optional[datetime] = None) -> None:
        """Complete a timeline phase."""
        phase = self._get_phase(phase_id)
        phase.complete_phase(end_date)
        self.updated_at = datetime.now()

    def delay_phase(self, phase_id: str, delay_days: int, reason: str) -> None:
        """Delay a timeline phase."""
        phase = self._get_phase(phase_id)
        old_end_date = phase.planned_end_date

        phase.delay_phase(delay_days, reason)
        self.updated_at = datetime.now()

        if old_end_date and phase.planned_end_date:
            self._add_domain_event(PhaseDelayed(
                timeline_id=str(self.id.value),
                project_id=self.project_id,
                phase_name=phase.name,
                original_end_date=old_end_date,
                new_end_date=phase.planned_end_date,
                delay_reason=reason
            ))

    def add_milestone(self, phase_id: str, milestone: Milestone) -> None:
        """Add a milestone to a specific phase."""
        phase = self._get_phase(phase_id)
        phase.add_milestone(milestone)
        self.updated_at = datetime.now()

    def achieve_milestone(self, phase_id: str, milestone_id: str, achieved_date: Optional[datetime] = None) -> None:
        """Achieve a milestone."""
        phase = self._get_phase(phase_id)
        milestone = self._get_milestone(phase, milestone_id)

        # Check milestone dependencies
        achieved_milestone_ids = [m.id for p in self.phases for m in p.get_achieved_milestones()]
        if not milestone.can_be_achieved(achieved_milestone_ids):
            raise ValueError(f"Cannot achieve milestone {milestone_id}: dependencies not met")

        milestone.achieve_milestone(achieved_date)
        self.updated_at = datetime.now()

        self._add_domain_event(MilestoneAchieved(
            timeline_id=str(self.id.value),
            project_id=self.project_id,
            milestone_name=milestone.name,
            achieved_date=milestone.achieved_date
        ))

    def get_current_phase(self) -> Optional[TimelinePhase]:
        """Get the currently active phase."""
        for phase in self.phases:
            if phase.status == "in_progress":
                return phase
        return None

    def get_completed_phases(self) -> List[TimelinePhase]:
        """Get all completed phases."""
        return [phase for phase in self.phases if phase.status == "completed"]

    def get_overdue_phases(self) -> List[TimelinePhase]:
        """Get all overdue phases."""
        return [phase for phase in self.phases if not phase.is_on_track() and phase.status != "completed"]

    def get_overall_progress(self) -> Percentage:
        """Calculate overall timeline progress."""
        if not self.phases:
            return Percentage(0)

        total_weight = sum(phase.planned_duration.total_days for phase in self.phases)
        if total_weight == 0:
            return Percentage(0)

        weighted_progress = sum(
            phase.planned_duration.total_days * phase.progress_percentage.value
            for phase in self.phases
        )

        return Percentage(weighted_progress / total_weight)

    def get_projected_completion_date(self) -> Optional[datetime]:
        """Get projected completion date based on current progress."""
        current_phase = self.get_current_phase()
        if not current_phase or not current_phase.start_date:
            return None

        # Calculate remaining work
        remaining_phases = [p for p in self.phases if p.status != "completed"]
        remaining_days = sum(p.planned_duration.total_days for p in remaining_phases)

        # Estimate based on current phase progress
        if current_phase.progress_percentage.value > 0:
            days_per_percent = current_phase.planned_duration.total_days / 100
            remaining_current_phase = days_per_percent * (100 - current_phase.progress_percentage.value)
            remaining_days += remaining_current_phase

        return datetime.now() + timedelta(days=remaining_days)

    def get_critical_path(self) -> List[TimelinePhase]:
        """Get the critical path (longest chain of dependent phases)."""
        # Simple implementation - return phases sorted by dependencies
        # In a real implementation, this would calculate the actual critical path
        return sorted(self.phases, key=lambda p: len(p.dependencies), reverse=True)

    def get_all_milestones(self) -> List[Milestone]:
        """Get all milestones across all phases."""
        milestones = []
        for phase in self.phases:
            milestones.extend(phase.milestones)
        return milestones

    def get_overdue_milestones(self) -> List[Milestone]:
        """Get all overdue milestones across all phases."""
        overdue = []
        for phase in self.phases:
            overdue.extend(phase.get_overdue_milestones())
        return overdue

    def get_upcoming_milestones(self, days_ahead: int = 7) -> List[Milestone]:
        """Get milestones due within the specified days."""
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        upcoming = []
        for phase in self.phases:
            for milestone in phase.milestones:
                if (not milestone.is_achieved() and
                    milestone.due_date <= cutoff_date):
                    upcoming.append(milestone)
        return sorted(upcoming, key=lambda m: m.due_date)

    def _get_phase(self, phase_id: str) -> TimelinePhase:
        """Get a phase by ID."""
        for phase in self.phases:
            if phase.id == phase_id:
                return phase
        raise ValueError(f"Phase {phase_id} not found")

    def _get_milestone(self, phase: TimelinePhase, milestone_id: str) -> Milestone:
        """Get a milestone by ID from a specific phase."""
        for milestone in phase.milestones:
            if milestone.id == milestone_id:
                return milestone
        raise ValueError(f"Milestone {milestone_id} not found in phase {phase.id}")

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
        return f"Timeline(id={self.id}, project_id={self.project_id}, phases={len(self.phases)})"

    def __repr__(self) -> str:
        return self.__str__()
