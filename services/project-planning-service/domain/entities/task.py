"""
Task Entity - Implementation task for feature development
=========================================================

Represents a specific, actionable task that contributes to feature completion.
Tasks are assigned to team members and have concrete deliverables.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class TaskStatus(Enum):
    """Task execution status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskType(Enum):
    """Type of development task."""
    ANALYSIS = "analysis"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEPLOYMENT = "deployment"
    REVIEW = "review"


@dataclass
class Task:
    """
    Implementation task entity.

    Tasks represent specific, actionable work items that contribute
    to feature completion. They have clear deliverables and assignments.
    """

    # Required fields
    id: str
    title: str
    description: str
    task_type: TaskType
    feature_id: str  # Parent feature
    created_by: str

    # Status and assignment
    status: TaskStatus = TaskStatus.TODO
    assigned_to: Optional[str] = None  # User ID
    assigned_by: Optional[str] = None  # User ID

    # Estimation and tracking
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)  # Task IDs this task depends on
    story_points: Optional[float] = None

    # Scheduling
    planned_start: Optional[datetime] = None
    planned_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None

    # Relationships
    depends_on: List[str] = field(default_factory=list)  # Task IDs
    blocks: List[str] = field(default_factory=list)  # Task IDs

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Additional context
    tags: List[str] = field(default_factory=list)
    attachments: List[str] = field(default_factory=list)  # File URLs/IDs
    comments: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Validate task data after initialization."""
        if not self.title.strip():
            raise ValueError("Task title cannot be empty")

        if not self.description.strip():
            raise ValueError("Task description cannot be empty")

        if not self.feature_id:
            raise ValueError("Task must be associated with a feature")

        # Ensure updated_at is always current
        self.updated_at = datetime.now()

    def update_status(self, new_status: TaskStatus, updated_by: str):
        """Update task status with audit trail."""
        old_status = self.status
        self.status = new_status
        self.updated_at = datetime.now()

        # Add status change comment
        self.add_comment(
            f"Status changed from {old_status.value} to {new_status.value}",
            updated_by,
            "status_change"
        )

        # Set actual timestamps
        if new_status == TaskStatus.IN_PROGRESS and not self.actual_start:
            self.actual_start = datetime.now()
        elif new_status == TaskStatus.DONE and not self.actual_end:
            self.actual_end = datetime.now()

    def assign_to(self, user_id: str, assigned_by: str):
        """Assign task to a user."""
        old_assignee = self.assigned_to
        self.assigned_to = user_id
        self.assigned_by = assigned_by
        self.updated_at = datetime.now()

        # Add assignment comment
        if old_assignee:
            self.add_comment(
                f"Reassigned from {old_assignee} to {user_id}",
                assigned_by,
                "assignment"
            )
        else:
            self.add_comment(
                f"Assigned to {user_id}",
                assigned_by,
                "assignment"
            )

    def set_estimate(self, hours: float, story_points: Optional[float] = None):
        """Set time estimate for the task."""
        if hours < 0:
            raise ValueError("Hours cannot be negative")

        self.estimated_hours = hours
        if story_points is not None:
            if story_points < 0:
                raise ValueError("Story points cannot be negative")
            self.story_points = story_points

        self.updated_at = datetime.now()

    def log_time(self, hours: float, user_id: str):
        """Log actual time spent on the task."""
        if hours < 0:
            raise ValueError("Logged hours cannot be negative")

        self.actual_hours = (self.actual_hours or 0) + hours
        self.updated_at = datetime.now()

        self.add_comment(
            f"Logged {hours} hours (total: {self.actual_hours})",
            user_id,
            "time_log"
        )

    def add_dependency(self, task_id: str):
        """Add task dependency."""
        if task_id not in self.depends_on:
            self.depends_on.append(task_id)
            self.updated_at = datetime.now()

    def add_comment(self, content: str, author_id: str, comment_type: str = "general"):
        """Add a comment to the task."""
        comment = {
            "id": f"comment_{len(self.comments)}",
            "content": content,
            "author_id": author_id,
            "timestamp": datetime.now().isoformat(),
            "type": comment_type
        }
        self.comments.append(comment)
        self.updated_at = datetime.now()

    @property
    def is_overdue(self) -> bool:
        """Check if task is overdue."""
        if not self.planned_end:
            return False
        return datetime.now() > self.planned_end and self.status != TaskStatus.DONE

    @property
    def time_spent_ratio(self) -> Optional[float]:
        """Calculate ratio of actual to estimated time."""
        if not self.estimated_hours or not self.actual_hours:
            return None
        return self.actual_hours / self.estimated_hours

    @property
    def completion_percentage(self) -> float:
        """Calculate task completion percentage."""
        if self.status == TaskStatus.DONE:
            return 1.0
        elif self.status == TaskStatus.IN_PROGRESS:
            return 0.5
        elif self.status == TaskStatus.REVIEW:
            return 0.8
        elif self.status == TaskStatus.BLOCKED:
            return 0.0
        else:
            return 0.0

    def can_start(self) -> bool:
        """Check if task can be started (dependencies satisfied)."""
        # This would need to check if all dependent tasks are complete
        # For now, return True if no dependencies
        return len(self.depends_on) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "assigned_by": self.assigned_by,
            "estimated_hours": self.estimated_hours,
            "actual_hours": self.actual_hours,
            "story_points": self.story_points,
            "planned_start": self.planned_start.isoformat() if self.planned_start else None,
            "planned_end": self.planned_end.isoformat() if self.planned_end else None,
            "actual_start": self.actual_start.isoformat() if self.actual_start else None,
            "actual_end": self.actual_end.isoformat() if self.actual_end else None,
            "feature_id": self.feature_id,
            "depends_on": self.depends_on,
            "blocks": self.blocks,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "tags": self.tags,
            "attachments": self.attachments,
            "comments": self.comments,
            "is_overdue": self.is_overdue,
            "time_spent_ratio": self.time_spent_ratio,
            "completion_percentage": self.completion_percentage,
            "can_start": self.can_start
        }
