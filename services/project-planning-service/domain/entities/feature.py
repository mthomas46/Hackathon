"""
Feature Entity - Core domain entity for project planning
=========================================================

Represents a software feature or user story in the planning domain.
Features are the fundamental units of work that get decomposed into
tasks and assigned to team members.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class FeatureStatus(Enum):
    """Feature development status enumeration."""
    DRAFT = "draft"
    ANALYZED = "analyzed"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class FeaturePriority(Enum):
    """Feature priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Feature:
    """
    Core domain entity representing a software feature.

    Features are high-level user stories or capabilities that need to be
    implemented. They get decomposed into specific tasks during planning.
    """

    id: str
    title: str
    description: str

    # Status and priority
    status: FeatureStatus = FeatureStatus.DRAFT
    priority: FeaturePriority = FeaturePriority.MEDIUM

    # Business context
    business_value: Optional[str] = None
    acceptance_criteria: List[str] = field(default_factory=list)

    # Technical details
    estimated_effort: Optional[float] = None  # Story points
    technical_complexity: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)

    # Planning metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None

    # AI analysis results
    ai_analysis: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)

    # Relationships
    roadmap_id: Optional[str] = None
    parent_feature_id: Optional[str] = None
    child_features: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate feature data after initialization."""
        if not self.title.strip():
            raise ValueError("Feature title cannot be empty")

        if not self.description.strip():
            raise ValueError("Feature description cannot be empty")

        # Ensure updated_at is always current
        self.updated_at = datetime.now()

    def update_status(self, new_status: FeatureStatus):
        """Update feature status with timestamp."""
        self.status = new_status
        self.updated_at = datetime.now()

    def add_acceptance_criterion(self, criterion: str):
        """Add acceptance criterion."""
        if criterion.strip():
            self.acceptance_criteria.append(criterion.strip())
            self.updated_at = datetime.now()

    def set_estimated_effort(self, effort: float):
        """Set estimated effort in story points."""
        if effort < 0:
            raise ValueError("Effort cannot be negative")
        self.estimated_effort = effort
        self.updated_at = datetime.now()

    def add_dependency(self, dependency_id: str):
        """Add feature dependency."""
        if dependency_id not in self.dependencies:
            self.dependencies.append(dependency_id)
            self.updated_at = datetime.now()

    def update_ai_analysis(self, analysis_data: Dict[str, Any]):
        """Update AI-powered analysis results."""
        self.ai_analysis.update(analysis_data)
        self.updated_at = datetime.now()

    def assess_risk(self, risk_data: Dict[str, Any]):
        """Update risk assessment data."""
        self.risk_assessment.update(risk_data)
        self.updated_at = datetime.now()

    @property
    def is_ready_for_planning(self) -> bool:
        """Check if feature is ready for detailed planning."""
        return (
            self.status in [FeatureStatus.DRAFT, FeatureStatus.ANALYZED] and
            self.description and
            self.acceptance_criteria
        )

    @property
    def completion_percentage(self) -> float:
        """Calculate feature completion percentage."""
        criteria = len(self.acceptance_criteria)
        if criteria == 0:
            return 0.0

        # Simple completion based on status
        status_weights = {
            FeatureStatus.DRAFT: 0.1,
            FeatureStatus.ANALYZED: 0.3,
            FeatureStatus.PLANNED: 0.5,
            FeatureStatus.IN_PROGRESS: 0.7,
            FeatureStatus.COMPLETED: 1.0,
            FeatureStatus.CANCELLED: 0.0
        }

        return status_weights.get(self.status, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert feature to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "business_value": self.business_value,
            "acceptance_criteria": self.acceptance_criteria,
            "estimated_effort": self.estimated_effort,
            "technical_complexity": self.technical_complexity,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
            "ai_analysis": self.ai_analysis,
            "risk_assessment": self.risk_assessment,
            "roadmap_id": self.roadmap_id,
            "parent_feature_id": self.parent_feature_id,
            "child_features": self.child_features,
            "is_ready_for_planning": self.is_ready_for_planning,
            "completion_percentage": self.completion_percentage
        }
