"""Team Aggregate - Domain Entity.

This module defines the Team aggregate, which manages team members,
roles, and team dynamics in the domain-driven design architecture.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from enum import Enum

from ..value_objects import Money, Percentage
from ..events import TeamMemberAdded, TeamMemberRemoved


@dataclass(frozen=True)
class TeamId:
    """Value object for Team ID."""
    value: UUID = field(default_factory=uuid4)

    @classmethod
    def from_string(cls, value: str) -> TeamId:
        """Create TeamId from string."""
        return cls(UUID(value))

    def __str__(self) -> str:
        return str(self.value)


class ExpertiseLevel(Enum):
    """Team member expertise levels."""
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    ADVANCED = "advanced"
    EXPERT = "expert"
    LEAD = "lead"


class CommunicationStyle(Enum):
    """Team member communication styles."""
    DIRECT = "direct"
    COLLABORATIVE = "collaborative"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"
    SUPPORTIVE = "supportive"


class WorkStyle(Enum):
    """Team member work styles."""
    INDEPENDENT = "independent"
    TEAM_PLAYER = "team_player"
    MENTOR = "mentor"
    INNOVATOR = "innovator"
    EXECUTOR = "executor"


class MoraleLevel(Enum):
    """Team morale levels."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class BurnoutRisk(Enum):
    """Team burnout risk levels."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TeamRole:
    """Entity representing a team role."""
    name: str
    description: str
    required_expertise: ExpertiseLevel
    responsibilities: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)
    salary_range: Optional[Dict[str, Money]] = None

    def matches_member(self, member: TeamMemberEntity) -> bool:
        """Check if a team member matches this role."""
        return (member.expertise_level == self.required_expertise or
                member.expertise_level.value >= self.required_expertise.value)

    def get_salary_range_text(self) -> str:
        """Get salary range as formatted text."""
        if not self.salary_range:
            return "Not specified"
        min_salary = self.salary_range.get("min")
        max_salary = self.salary_range.get("max")
        if min_salary and max_salary:
            return f"{min_salary} - {max_salary}"
        return "Not specified"


@dataclass
class TeamMemberEntity:
    """Entity representing a team member with enhanced attributes."""
    id: str
    name: str
    email: str
    role: str
    expertise_level: ExpertiseLevel
    communication_style: CommunicationStyle
    work_style: WorkStyle
    specialization: List[str] = field(default_factory=list)
    productivity_multiplier: float = 1.0
    morale_level: Percentage = field(default_factory=lambda: Percentage(80))
    burnout_risk: Percentage = field(default_factory=lambda: Percentage(20))
    joined_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)

    def can_handle_task(self, task_type: str, complexity: str = "medium") -> bool:
        """Check if team member can handle a specific task."""
        # Basic skill check
        has_skill = task_type in self.specialization

        # Expertise level check based on complexity
        complexity_levels = {"simple": 1, "medium": 2, "complex": 3}
        required_level = complexity_levels.get(complexity, 2)
        expertise_levels = {
            ExpertiseLevel.JUNIOR: 1,
            ExpertiseLevel.MID_LEVEL: 2,
            ExpertiseLevel.SENIOR: 3,
            ExpertiseLevel.EXPERT: 4,
            ExpertiseLevel.LEAD: 5
        }
        has_expertise = expertise_levels[self.expertise_level] >= required_level

        return has_skill or has_expertise

    def get_productivity_for_task(self, task_type: str, complexity: str = "medium") -> float:
        """Get productivity multiplier for a specific task."""
        base_productivity = self.productivity_multiplier

        # Adjust for task fit
        if self.can_handle_task(task_type, complexity):
            task_fit_bonus = 1.2
        else:
            task_fit_penalty = 0.8

        # Adjust for morale
        morale_multiplier = self.morale_level.to_fraction()

        # Adjust for burnout risk
        burnout_penalty = 1 - (self.burnout_risk.to_fraction() * 0.3)

        return base_productivity * task_fit_bonus * morale_multiplier * burnout_penalty

    def update_morale(self, change: float) -> None:
        """Update morale level."""
        new_level = self.morale_level.value + change
        new_level = max(0, min(100, new_level))  # Clamp between 0-100
        self.morale_level = Percentage(new_level)

    def update_burnout_risk(self, change: float) -> None:
        """Update burnout risk level."""
        new_risk = self.burnout_risk.value + change
        new_risk = max(0, min(100, new_risk))  # Clamp between 0-100
        self.burnout_risk = Percentage(new_risk)

    def is_high_performer(self) -> bool:
        """Check if member is a high performer."""
        return (self.productivity_multiplier >= 1.2 and
                self.morale_level.value >= 70 and
                self.burnout_risk.value <= 30)

    def needs_attention(self) -> bool:
        """Check if member needs attention (low morale or high burnout risk)."""
        return (self.morale_level.value < 50 or
                self.burnout_risk.value > 60)

    def get_days_since_active(self) -> int:
        """Get days since last active."""
        return (datetime.now() - self.last_active).days

    def mark_active(self) -> None:
        """Mark member as active."""
        self.last_active = datetime.now()


@dataclass
class TeamDynamics:
    """Entity representing team dynamics and relationships."""
    communication_score: Percentage = field(default_factory=lambda: Percentage(75))
    collaboration_score: Percentage = field(default_factory=lambda: Percentage(70))
    conflict_resolution_score: Percentage = field(default_factory=lambda: Percentage(65))
    trust_level: Percentage = field(default_factory=lambda: Percentage(80))
    last_assessment: datetime = field(default_factory=datetime.now)

    def update_scores(self, communication: float, collaboration: float,
                     conflict_resolution: float, trust: float) -> None:
        """Update all dynamic scores."""
        self.communication_score = Percentage(communication)
        self.collaboration_score = Percentage(collaboration)
        self.conflict_resolution_score = Percentage(conflict_resolution)
        self.trust_level = Percentage(trust)
        self.last_assessment = datetime.now()

    def get_overall_health(self) -> Percentage:
        """Get overall team health score."""
        scores = [
            self.communication_score.value,
            self.collaboration_score.value,
            self.conflict_resolution_score.value,
            self.trust_level.value
        ]
        return Percentage(sum(scores) / len(scores))

    def needs_improvement(self) -> bool:
        """Check if team dynamics need improvement."""
        return self.get_overall_health().value < 60


@dataclass
class Team:
    """Team Aggregate Root.

    This is the root entity for the Team aggregate, managing team members,
    roles, and team dynamics.
    """
    id: TeamId
    project_id: str
    name: str
    max_size: int
    members: List[TeamMemberEntity] = field(default_factory=list)
    roles: List[TeamRole] = field(default_factory=list)
    dynamics: TeamDynamics = field(default_factory=TeamDynamics)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Domain events
    _domain_events: List[Any] = field(default_factory=list, init=False)

    def add_member(self, member: TeamMemberEntity) -> None:
        """Add a member to the team."""
        if len(self.members) >= self.max_size:
            raise ValueError(f"Team already has maximum size of {self.max_size}")

        if any(m.id == member.id for m in self.members):
            raise ValueError(f"Team member with ID {member.id} already exists")

        if any(m.email == member.email for m in self.members):
            raise ValueError(f"Team member with email {member.email} already exists")

        self.members.append(member)
        self.updated_at = datetime.now()

        self._add_domain_event(TeamMemberAdded(
            project_id=self.project_id,
            member_id=member.id,
            member_name=member.name,
            role=member.role
        ))

    def remove_member(self, member_id: str) -> None:
        """Remove a member from the team."""
        member = self._get_member(member_id)
        self.members = [m for m in self.members if m.id != member_id]
        self.updated_at = datetime.now()

        self._add_domain_event(TeamMemberRemoved(
            project_id=self.project_id,
            member_id=member.id,
            member_name=member.name
        ))

    def add_role(self, role: TeamRole) -> None:
        """Add a role to the team."""
        if any(r.name == role.name for r in self.roles):
            raise ValueError(f"Role {role.name} already exists")
        self.roles.append(role)
        self.updated_at = datetime.now()

    def assign_role_to_member(self, member_id: str, role_name: str) -> None:
        """Assign a role to a team member."""
        member = self._get_member(member_id)
        role = self._get_role(role_name)

        if not role.matches_member(member):
            raise ValueError(f"Member {member.name} does not match requirements for role {role_name}")

        member.role = role_name
        self.updated_at = datetime.now()

    def get_members_by_role(self, role_name: str) -> List[TeamMemberEntity]:
        """Get all members with a specific role."""
        return [member for member in self.members if member.role == role_name]

    def get_members_by_expertise(self, expertise: ExpertiseLevel) -> List[TeamMemberEntity]:
        """Get all members with a specific expertise level."""
        return [member for member in self.members if member.expertise_level == expertise]

    def get_high_performers(self) -> List[TeamMemberEntity]:
        """Get all high-performing team members."""
        return [member for member in self.members if member.is_high_performer()]

    def get_members_needing_attention(self) -> List[TeamMemberEntity]:
        """Get members who need attention (low morale, high burnout risk)."""
        return [member for member in self.members if member.needs_attention()]

    def update_member_morale(self, member_id: str, morale_change: float) -> None:
        """Update a member's morale level."""
        member = self._get_member(member_id)
        member.update_morale(morale_change)
        self.updated_at = datetime.now()

    def update_member_burnout_risk(self, member_id: str, burnout_change: float) -> None:
        """Update a member's burnout risk level."""
        member = self._get_member(member_id)
        member.update_burnout_risk(burnout_change)
        self.updated_at = datetime.now()

    def assess_team_dynamics(self) -> None:
        """Assess and update team dynamics."""
        if not self.members:
            return

        # Simple assessment algorithm
        avg_morale = sum(m.morale_level.value for m in self.members) / len(self.members)
        avg_burnout = sum(m.burnout_risk.value for m in self.members) / len(self.members)

        # Communication score based on diversity and collaboration styles
        communication_styles = [m.communication_style for m in self.members]
        communication_diversity = len(set(communication_styles)) / len(communication_styles)
        communication_score = 100 - (communication_diversity * 20)  # Less diversity = better communication

        # Collaboration score based on work styles
        team_players = sum(1 for m in self.members if m.work_style == WorkStyle.TEAM_PLAYER)
        collaboration_score = (team_players / len(self.members)) * 100

        # Conflict resolution based on supportive members
        supportive_members = sum(1 for m in self.members if m.communication_style == CommunicationStyle.SUPPORTIVE)
        conflict_resolution_score = (supportive_members / len(self.members)) * 100

        # Trust level based on overall team health
        trust_score = (avg_morale + (100 - avg_burnout)) / 2

        self.dynamics.update_scores(
            communication_score,
            collaboration_score,
            conflict_resolution_score,
            trust_score
        )
        self.updated_at = datetime.now()

    def get_team_productivity(self) -> float:
        """Calculate overall team productivity."""
        if not self.members:
            return 0.0

        total_productivity = sum(member.productivity_multiplier for member in self.members)
        return total_productivity / len(self.members)

    def get_team_morale(self) -> Percentage:
        """Get average team morale."""
        if not self.members:
            return Percentage(0)

        avg_morale = sum(m.morale_level.value for m in self.members) / len(self.members)
        return Percentage(avg_morale)

    def get_team_burnout_risk(self) -> Percentage:
        """Get average team burnout risk."""
        if not self.members:
            return Percentage(0)

        avg_burnout = sum(m.burnout_risk.value for m in self.members) / len(self.members)
        return Percentage(avg_burnout)

    def is_team_healthy(self) -> bool:
        """Check if the team is healthy overall."""
        return (self.get_team_morale().value >= 60 and
                self.get_team_burnout_risk().value <= 40 and
                self.dynamics.get_overall_health().value >= 65)

    def get_optimal_team_size(self) -> int:
        """Get optimal team size based on current dynamics."""
        base_size = 5
        health_adjustment = int(self.dynamics.get_overall_health().value / 20) - 2  # -2 to +3
        return max(3, min(15, base_size + health_adjustment))

    def _get_member(self, member_id: str) -> TeamMemberEntity:
        """Get a team member by ID."""
        for member in self.members:
            if member.id == member_id:
                return member
        raise ValueError(f"Team member {member_id} not found")

    def _get_role(self, role_name: str) -> TeamRole:
        """Get a role by name."""
        for role in self.roles:
            if role.name == role_name:
                return role
        raise ValueError(f"Role {role_name} not found")

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
        return f"Team(id={self.id}, name='{self.name}', members={len(self.members)}/{self.max_size})"

    def __repr__(self) -> str:
        return self.__str__()
