"""
Roadmap Entity - Development timeline and release planning
==========================================================

Represents a development roadmap containing multiple features and tasks
organized into releases and sprints with timeline planning and dependencies.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum


class RoadmapStatus(Enum):
    """Roadmap planning status."""
    PLANNING = "planning"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ReleaseStatus(Enum):
    """Release status within roadmap."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    RELEASED = "released"
    CANCELLED = "cancelled"


class SprintStatus(Enum):
    """Sprint status."""
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Sprint:
    """Sprint within a roadmap."""
    
    # Required fields
    id: str
    name: str
    start_date: datetime
    end_date: datetime
    capacity: float  # Story points capacity
    
    # Optional fields with defaults
    status: SprintStatus = SprintStatus.PLANNED
    allocated: float = 0.0  # Story points allocated
    feature_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def remaining_capacity(self) -> float:
        """Calculate remaining capacity."""
        return max(0.0, self.capacity - self.allocated)
    
    def is_full(self) -> bool:
        """Check if sprint is at capacity."""
        return self.allocated >= self.capacity
    
    def duration_days(self) -> int:
        """Calculate sprint duration in days."""
        return (self.end_date - self.start_date).days + 1


@dataclass
class Release:
    """Release milestone within a roadmap."""

    id: str
    name: str
    description: Optional[str] = None
    status: ReleaseStatus = ReleaseStatus.PLANNED

    # Timeline
    planned_release_date: Optional[datetime] = None
    actual_release_date: Optional[datetime] = None

    # Content
    feature_ids: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate release data."""
        if not self.name.strip():
            raise ValueError("Release name cannot be empty")

        self.updated_at = datetime.now()

    def add_feature(self, feature_id: str):
        """Add feature to this release."""
        if feature_id not in self.feature_ids:
            self.feature_ids.append(feature_id)
            self.updated_at = datetime.now()

    def remove_feature(self, feature_id: str):
        """Remove feature from this release."""
        if feature_id in self.feature_ids:
            self.feature_ids.remove(feature_id)
            self.updated_at = datetime.now()

    def mark_released(self, actual_date: Optional[datetime] = None):
        """Mark release as completed."""
        self.status = ReleaseStatus.RELEASED
        self.actual_release_date = actual_date or datetime.now()
        self.updated_at = datetime.now()

    @property
    def is_overdue(self) -> bool:
        """Check if release is overdue."""
        if not self.planned_release_date:
            return False
        return datetime.now() > self.planned_release_date and self.status != ReleaseStatus.RELEASED


@dataclass
class Roadmap:
    """
    Development roadmap entity.

    Roadmaps organize features into releases and sprints with timeline
    planning, resource allocation, and progress tracking.
    """

    # Required fields
    id: str
    name: str
    created_by: str
    
    # Optional fields
    description: Optional[str] = None

    # Status and timeline
    status: RoadmapStatus = RoadmapStatus.PLANNING
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Content
    feature_ids: List[str] = field(default_factory=list)
    releases: List[Release] = field(default_factory=list)

    # Team and capacity
    team_capacity: Dict[str, float] = field(default_factory=dict)  # user_id -> capacity (hours/week)
    sprint_duration_days: int = 14  # Default 2 weeks

    # Progress tracking
    total_story_points: Optional[float] = None
    completed_story_points: float = 0.0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # AI analysis
    ai_insights: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate roadmap data after initialization."""
        if not self.name.strip():
            raise ValueError("Roadmap name cannot be empty")

        # Set default dates if not provided
        if not self.start_date:
            self.start_date = datetime.now()
        if not self.end_date:
            # Default to 3 months from start
            self.end_date = self.start_date + timedelta(days=90)

        self.updated_at = datetime.now()

    def update_status(self, new_status: RoadmapStatus):
        """Update roadmap status."""
        self.status = new_status
        self.updated_at = datetime.now()

    def add_feature(self, feature_id: str, release_id: Optional[str] = None):
        """Add feature to roadmap."""
        if feature_id not in self.feature_ids:
            self.feature_ids.append(feature_id)
            self.updated_at = datetime.now()

        # Add to specific release if provided
        if release_id:
            release = self.get_release(release_id)
            if release:
                release.add_feature(feature_id)

    def remove_feature(self, feature_id: str):
        """Remove feature from roadmap."""
        if feature_id in self.feature_ids:
            self.feature_ids.remove(feature_id)
            self.updated_at = datetime.now()

        # Remove from all releases
        for release in self.releases:
            release.remove_feature(feature_id)

    def add_release(self, release: Release):
        """Add release to roadmap."""
        # Check for duplicate IDs
        if any(r.id == release.id for r in self.releases):
            raise ValueError(f"Release with ID {release.id} already exists")

        self.releases.append(release)
        self.updated_at = datetime.now()

    def get_release(self, release_id: str) -> Optional[Release]:
        """Get release by ID."""
        return next((r for r in self.releases if r.id == release_id), None)

    def set_team_capacity(self, user_id: str, capacity_hours: float):
        """Set team member capacity."""
        if capacity_hours < 0:
            raise ValueError("Capacity cannot be negative")

        self.team_capacity[user_id] = capacity_hours
        self.updated_at = datetime.now()

    def calculate_total_capacity(self) -> float:
        """Calculate total team capacity in hours."""
        return sum(self.team_capacity.values())

    def estimate_completion_date(self) -> Optional[datetime]:
        """Estimate roadmap completion date based on capacity and story points."""
        if not self.total_story_points or not self.team_capacity:
            return None

        # Simple estimation: story points / (capacity per week * weeks per story point)
        # This is a rough estimate - real implementation would be more sophisticated
        total_capacity_per_week = self.calculate_total_capacity()
        if total_capacity_per_week == 0:
            return None

        # Assume 1 story point = 1 week for 1 developer
        weeks_needed = self.total_story_points / total_capacity_per_week
        days_needed = weeks_needed * 7

        return self.start_date + timedelta(days=days_needed) if self.start_date else None

    def update_progress(self, completed_points: float):
        """Update roadmap progress."""
        self.completed_story_points = max(0, completed_points)
        self.updated_at = datetime.now()

    @property
    def progress_percentage(self) -> float:
        """Calculate roadmap completion percentage."""
        if not self.total_story_points or self.total_story_points == 0:
            return 0.0
        return min(100.0, (self.completed_story_points / self.total_story_points) * 100)

    @property
    def is_on_track(self) -> bool:
        """Check if roadmap is on track for completion."""
        if not self.end_date:
            return True

        estimated_completion = self.estimate_completion_date()
        if not estimated_completion:
            return True

        return estimated_completion <= self.end_date

    @property
    def overdue_releases(self) -> List[Release]:
        """Get list of overdue releases."""
        return [r for r in self.releases if r.is_overdue]

    def to_dict(self) -> Dict[str, Any]:
        """Convert roadmap to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "feature_ids": self.feature_ids,
            "releases": [r.__dict__ for r in self.releases],
            "team_capacity": self.team_capacity,
            "sprint_duration_days": self.sprint_duration_days,
            "total_story_points": self.total_story_points,
            "completed_story_points": self.completed_story_points,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "ai_insights": self.ai_insights,
            "risk_assessment": self.risk_assessment,
            "progress_percentage": self.progress_percentage,
            "is_on_track": self.is_on_track,
            "total_capacity": self.calculate_total_capacity(),
            "estimated_completion_date": self.estimate_completion_date().isoformat() if self.estimate_completion_date() else None
        }
