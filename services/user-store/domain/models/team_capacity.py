"""
Team Capacity Models
====================

Domain models for team capacity management, skills tracking,
and resource allocation.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import uuid


class ProficiencyLevel(Enum):
    """Skill proficiency levels."""
    BEGINNER = 1
    INTERMEDIATE = 2
    PROFICIENT = 3
    ADVANCED = 4
    EXPERT = 5


class MemberRole(Enum):
    """Team member roles."""
    DEVELOPER = "developer"
    SENIOR_DEVELOPER = "senior_developer"
    TECH_LEAD = "tech_lead"
    ARCHITECT = "architect"
    QA_ENGINEER = "qa_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    PRODUCT_MANAGER = "product_manager"
    DESIGNER = "designer"


class AssignmentStatus(Enum):
    """Task assignment status."""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Skill:
    """Represents a skill with proficiency level."""
    skill_name: str
    proficiency_level: ProficiencyLevel
    years_experience: float = 0.0
    last_used: Optional[date] = None
    certifications: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate skill data."""
        if self.years_experience < 0:
            raise ValueError("Years of experience cannot be negative")
        if self.proficiency_level.value > 5 or self.proficiency_level.value < 1:
            raise ValueError("Proficiency level must be between 1 and 5")
    
    def is_recent(self, months: int = 6) -> bool:
        """Check if skill was used recently."""
        if not self.last_used:
            return False
        
        from datetime import timedelta
        cutoff_date = date.today() - timedelta(days=months * 30)
        return self.last_used >= cutoff_date
    
    def proficiency_score(self) -> float:
        """Calculate overall proficiency score (0-1)."""
        # Base score from proficiency level
        base_score = self.proficiency_level.value / 5.0
        
        # Bonus for experience
        experience_bonus = min(self.years_experience / 10.0, 0.2)
        
        # Penalty for not using recently
        recency_penalty = 0.0 if self.is_recent() else 0.1
        
        return min(base_score + experience_bonus - recency_penalty, 1.0)


@dataclass
class TeamMember:
    """
    Represents a team member with skills, capacity, and workload.
    """
    id: str
    user_id: str
    team_id: str
    name: str
    role: MemberRole
    skills: Dict[str, Skill] = field(default_factory=dict)
    capacity_hours: int = 40  # Weekly capacity
    is_active: bool = True
    availability: float = 1.0  # 0.0-1.0 (percentage available)
    current_workload_hours: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate team member data."""
        if self.capacity_hours < 0:
            raise ValueError("Capacity hours cannot be negative")
        if not (0.0 <= self.availability <= 1.0):
            raise ValueError("Availability must be between 0 and 1")
        if self.current_workload_hours < 0:
            raise ValueError("Workload cannot be negative")
    
    @staticmethod
    def create(user_id: str, team_id: str, name: str, role: MemberRole) -> 'TeamMember':
        """Factory method to create a new team member."""
        return TeamMember(
            id=str(uuid.uuid4()),
            user_id=user_id,
            team_id=team_id,
            name=name,
            role=role
        )
    
    def add_skill(self, skill: Skill) -> None:
        """Add or update a skill."""
        self.skills[skill.skill_name] = skill
        self.updated_at = datetime.now()
    
    def remove_skill(self, skill_name: str) -> None:
        """Remove a skill."""
        if skill_name in self.skills:
            del self.skills[skill_name]
            self.updated_at = datetime.now()
    
    def has_skill(self, skill_name: str, min_proficiency: ProficiencyLevel = ProficiencyLevel.BEGINNER) -> bool:
        """Check if member has a skill at minimum proficiency."""
        if skill_name not in self.skills:
            return False
        return self.skills[skill_name].proficiency_level.value >= min_proficiency.value
    
    def get_skill_score(self, skill_name: str) -> float:
        """Get proficiency score for a skill (0-1, 0 if skill not present)."""
        if skill_name not in self.skills:
            return 0.0
        return self.skills[skill_name].proficiency_score()
    
    def available_capacity_hours(self) -> float:
        """Calculate available capacity in hours."""
        total_available = self.capacity_hours * self.availability
        return max(0.0, total_available - self.current_workload_hours)
    
    def capacity_utilization(self) -> float:
        """Calculate capacity utilization percentage (0-1)."""
        if self.capacity_hours == 0:
            return 0.0
        return min(self.current_workload_hours / self.capacity_hours, 1.0)
    
    def is_overloaded(self) -> bool:
        """Check if member is overloaded."""
        return self.current_workload_hours > (self.capacity_hours * self.availability)
    
    def is_available_for_hours(self, hours: float) -> bool:
        """Check if member has capacity for additional hours."""
        return self.available_capacity_hours() >= hours
    
    def assign_work(self, hours: float) -> None:
        """Assign work to member."""
        if hours < 0:
            raise ValueError("Cannot assign negative hours")
        self.current_workload_hours += hours
        self.updated_at = datetime.now()
    
    def complete_work(self, hours: float) -> None:
        """Mark work as complete and free up capacity."""
        if hours < 0:
            raise ValueError("Cannot complete negative hours")
        self.current_workload_hours = max(0.0, self.current_workload_hours - hours)
        self.updated_at = datetime.now()


@dataclass
class TaskAssignment:
    """Represents a task assigned to a team member."""
    id: str
    task_id: str
    member_id: str
    estimated_hours: float
    actual_hours: float = 0.0
    status: AssignmentStatus = AssignmentStatus.ASSIGNED
    assigned_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    confidence_score: float = 0.0  # Confidence in skill match (0-1)
    notes: str = ""
    
    def __post_init__(self):
        """Validate assignment data."""
        if self.estimated_hours < 0:
            raise ValueError("Estimated hours cannot be negative")
        if self.actual_hours < 0:
            raise ValueError("Actual hours cannot be negative")
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0 and 1")
    
    @staticmethod
    def create(task_id: str, member_id: str, estimated_hours: float, confidence_score: float = 0.0) -> 'TaskAssignment':
        """Factory method to create a new task assignment."""
        return TaskAssignment(
            id=str(uuid.uuid4()),
            task_id=task_id,
            member_id=member_id,
            estimated_hours=estimated_hours,
            confidence_score=confidence_score
        )
    
    def start(self) -> None:
        """Mark assignment as started."""
        if self.status != AssignmentStatus.ASSIGNED:
            raise ValueError(f"Cannot start assignment with status {self.status}")
        self.status = AssignmentStatus.IN_PROGRESS
        self.started_at = datetime.now()
    
    def complete(self, actual_hours: float) -> None:
        """Mark assignment as completed."""
        if self.status not in [AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot complete assignment with status {self.status}")
        self.status = AssignmentStatus.COMPLETED
        self.actual_hours = actual_hours
        self.completed_at = datetime.now()
    
    def block(self, notes: str = "") -> None:
        """Mark assignment as blocked."""
        self.status = AssignmentStatus.BLOCKED
        self.notes = notes
    
    def cancel(self, notes: str = "") -> None:
        """Cancel the assignment."""
        self.status = AssignmentStatus.CANCELLED
        self.notes = notes
        self.completed_at = datetime.now()
    
    def variance_hours(self) -> float:
        """Calculate variance between estimated and actual hours."""
        if self.status != AssignmentStatus.COMPLETED:
            return 0.0
        return self.actual_hours - self.estimated_hours
    
    def variance_percentage(self) -> float:
        """Calculate variance as percentage of estimate."""
        if self.estimated_hours == 0 or self.status != AssignmentStatus.COMPLETED:
            return 0.0
        return (self.variance_hours() / self.estimated_hours) * 100


@dataclass
class TeamCapacity:
    """Represents team capacity for a specific time period."""
    id: str
    team_id: str
    week_start: date
    available_hours: int = 0
    allocated_hours: int = 0
    blocked_hours: int = 0  # Hours blocked for meetings, etc.
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate capacity data."""
        if self.available_hours < 0:
            raise ValueError("Available hours cannot be negative")
        if self.allocated_hours < 0:
            raise ValueError("Allocated hours cannot be negative")
        if self.blocked_hours < 0:
            raise ValueError("Blocked hours cannot be negative")
    
    @staticmethod
    def create(team_id: str, week_start: date, available_hours: int) -> 'TeamCapacity':
        """Factory method to create a new team capacity record."""
        return TeamCapacity(
            id=str(uuid.uuid4()),
            team_id=team_id,
            week_start=week_start,
            available_hours=available_hours
        )
    
    def remaining_hours(self) -> int:
        """Calculate remaining capacity hours."""
        return max(0, self.available_hours - self.allocated_hours - self.blocked_hours)
    
    def utilization_percentage(self) -> float:
        """Calculate capacity utilization percentage (0-100)."""
        if self.available_hours == 0:
            return 0.0
        used_hours = self.allocated_hours + self.blocked_hours
        return (used_hours / self.available_hours) * 100
    
    def is_overallocated(self) -> bool:
        """Check if team is overallocated."""
        return (self.allocated_hours + self.blocked_hours) > self.available_hours
    
    def can_allocate_hours(self, hours: int) -> bool:
        """Check if team can allocate additional hours."""
        return self.remaining_hours() >= hours
    
    def allocate(self, hours: int) -> None:
        """Allocate hours to the team."""
        if hours < 0:
            raise ValueError("Cannot allocate negative hours")
        self.allocated_hours += hours
    
    def deallocate(self, hours: int) -> None:
        """Deallocate hours from the team."""
        if hours < 0:
            raise ValueError("Cannot deallocate negative hours")
        self.allocated_hours = max(0, self.allocated_hours - hours)


@dataclass
class TeamVelocity:
    """Tracks team velocity over time."""
    team_id: str
    sprint_name: str
    start_date: date
    end_date: date
    planned_story_points: int = 0
    completed_story_points: int = 0
    committed_hours: float = 0.0
    actual_hours: float = 0.0
    tasks_planned: int = 0
    tasks_completed: int = 0
    
    def __post_init__(self):
        """Validate velocity data."""
        if self.planned_story_points < 0:
            raise ValueError("Planned story points cannot be negative")
        if self.completed_story_points < 0:
            raise ValueError("Completed story points cannot be negative")
        if self.committed_hours < 0:
            raise ValueError("Committed hours cannot be negative")
        if self.actual_hours < 0:
            raise ValueError("Actual hours cannot be negative")
    
    def completion_rate(self) -> float:
        """Calculate story point completion rate (0-1)."""
        if self.planned_story_points == 0:
            return 0.0
        return min(self.completed_story_points / self.planned_story_points, 1.0)
    
    def task_completion_rate(self) -> float:
        """Calculate task completion rate (0-1)."""
        if self.tasks_planned == 0:
            return 0.0
        return min(self.tasks_completed / self.tasks_planned, 1.0)
    
    def hours_per_story_point(self) -> float:
        """Calculate average hours per story point."""
        if self.completed_story_points == 0:
            return 0.0
        return self.actual_hours / self.completed_story_points
    
    def efficiency_ratio(self) -> float:
        """Calculate efficiency (actual hours vs committed hours)."""
        if self.committed_hours == 0:
            return 0.0
        return self.actual_hours / self.committed_hours
    
    def is_successful_sprint(self, threshold: float = 0.8) -> bool:
        """Check if sprint met success threshold."""
        return self.completion_rate() >= threshold

