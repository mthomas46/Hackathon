"""Recommendation domain entity.

This module contains the Recommendation entity for AI-powered recommendations
in the summarizer-hub domain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from enum import Enum


class RecommendationType(Enum):
    """Enumeration of recommendation types."""
    CONTENT_IMPROVEMENT = "content_improvement"
    STRUCTURAL_CHANGE = "structural_change"
    TECHNICAL_ENHANCEMENT = "technical_enhancement"
    BUSINESS_IMPACT = "business_impact"
    COMPLIANCE_UPDATE = "compliance_update"


class RecommendationPriority(Enum):
    """Enumeration of recommendation priorities."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class RecommendationId:
    """Value object for Recommendation ID."""
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Recommendation ID cannot be empty")

    @classmethod
    def generate(cls) -> 'RecommendationId':
        """Generate a new RecommendationId."""
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass
class Recommendation:
    """Recommendation entity.

    Represents an AI-generated recommendation for document improvement
    or analysis insights.
    """

    id: RecommendationId
    document_id: str
    title: str
    description: str
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    confidence_score: float
    impact_score: float
    implementation_effort: str  # "low", "medium", "high"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    implemented: bool = False
    implemented_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.title or not self.title.strip():
            raise ValueError("Recommendation title cannot be empty")

        if not self.description or not self.description.strip():
            raise ValueError("Recommendation description cannot be empty")

        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")

        if not (0.0 <= self.impact_score <= 1.0):
            raise ValueError("Impact score must be between 0.0 and 1.0")

        if self.implementation_effort not in ["low", "medium", "high"]:
            raise ValueError("Implementation effort must be 'low', 'medium', or 'high'")

        if not self.document_id:
            raise ValueError("Document ID is required")

    def mark_implemented(self) -> None:
        """Mark the recommendation as implemented."""
        self.implemented = True
        self.implemented_at = datetime.now()

    def update_priority(self, new_priority: RecommendationPriority) -> None:
        """Update the recommendation priority."""
        self.priority = new_priority

    def add_tag(self, tag: str) -> None:
        """Add a tag to the recommendation."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the recommendation."""
        if tag in self.tags:
            self.tags.remove(tag)

    def get_business_value(self) -> float:
        """Calculate business value based on impact and confidence."""
        return self.impact_score * self.confidence_score

    def is_high_impact(self) -> bool:
        """Check if recommendation has high business impact."""
        return self.impact_score >= 0.8 and self.priority in [RecommendationPriority.HIGH, RecommendationPriority.CRITICAL]

    def get_implementation_complexity_score(self) -> float:
        """Get a numerical score for implementation complexity."""
        effort_scores = {"low": 0.3, "medium": 0.6, "high": 0.9}
        return effort_scores[self.implementation_effort]

    @classmethod
    def create(
        cls,
        document_id: str,
        title: str,
        description: str,
        recommendation_type: RecommendationType,
        priority: RecommendationPriority,
        confidence_score: float,
        impact_score: float,
        implementation_effort: str = "medium",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> 'Recommendation':
        """Factory method to create a new recommendation."""
        recommendation_id = RecommendationId.generate()

        return cls(
            id=recommendation_id,
            document_id=document_id,
            title=title.strip(),
            description=description.strip(),
            recommendation_type=recommendation_type,
            priority=priority,
            confidence_score=confidence_score,
            impact_score=impact_score,
            implementation_effort=implementation_effort,
            tags=tags or [],
            metadata=metadata or {},
        )
