"""
Domain entities for recommendations.
Following DDD principles with clean, focused entities.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid


class RecommendationType(Enum):
    """Types of recommendations that can be generated."""
    CONSOLIDATION = "consolidation"
    DUPLICATE = "duplicate"
    OUTDATED = "outdated"
    QUALITY = "quality"
    CONTENT_GAP = "content_gap"
    STRUCTURAL_IMPROVEMENT = "structural_improvement"
    PRIORITY_REORDERING = "priority_reordering"


@dataclass
class Recommendation:
    """Represents a recommendation for document or content improvement."""
    type: RecommendationType
    description: str
    affected_documents: Optional[List[str]] = None
    confidence_score: float = 0.0
    priority: str = "medium"
    rationale: Optional[str] = None
    expected_impact: Optional[str] = None
    effort_level: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None
    age_days: Optional[int] = None  # For outdated document recommendations
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate recommendation data."""
        if not self.description or not self.description.strip():
            raise ValueError("Recommendation description cannot be empty")

        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")

        if self.priority not in ["low", "medium", "high", "critical"]:
            raise ValueError("Priority must be one of: low, medium, high, critical")

        if self.effort_level and self.effort_level not in ["low", "medium", "high"]:
            raise ValueError("Effort level must be one of: low, medium, high")

    def to_dict(self) -> dict:
        """Convert recommendation to dictionary representation."""
        return {
            "id": self.id,
            "type": self.type.value,
            "description": self.description,
            "affected_documents": self.affected_documents or [],
            "confidence_score": self.confidence_score,
            "priority": self.priority,
            "rationale": self.rationale,
            "expected_impact": self.expected_impact,
            "effort_level": self.effort_level,
            "tags": self.tags or [],
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Recommendation':
        """Create recommendation from dictionary representation."""
        return cls(
            type=RecommendationType(data["type"]),
            description=data["description"],
            affected_documents=data.get("affected_documents"),
            confidence_score=data.get("confidence_score", 0.0),
            priority=data.get("priority", "medium"),
            rationale=data.get("rationale"),
            expected_impact=data.get("expected_impact"),
            effort_level=data.get("effort_level"),
            tags=data.get("tags"),
            metadata=data.get("metadata"),
            id=data.get("id", str(uuid.uuid4()))
        )


@dataclass
class RecommendationBatch:
    """Represents a batch of recommendations for processing."""
    recommendations: List[Recommendation]
    source: str = "unknown"
    processing_time_seconds: float = 0.0
    total_confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def add_recommendation(self, recommendation: Recommendation) -> None:
        """Add a recommendation to the batch."""
        self.recommendations.append(recommendation)
        self._update_totals()

    def remove_recommendation(self, recommendation_id: str) -> bool:
        """Remove a recommendation from the batch."""
        original_length = len(self.recommendations)
        self.recommendations = [r for r in self.recommendations if r.id != recommendation_id]

        if len(self.recommendations) < original_length:
            self._update_totals()
            return True
        return False

    def get_recommendations_by_type(self, rec_type: RecommendationType) -> List[Recommendation]:
        """Get recommendations filtered by type."""
        return [r for r in self.recommendations if r.type == rec_type]

    def get_recommendations_by_priority(self, priority: str) -> List[Recommendation]:
        """Get recommendations filtered by priority."""
        return [r for r in self.recommendations if r.priority == priority]

    def sort_by_confidence(self, descending: bool = True) -> List[Recommendation]:
        """Sort recommendations by confidence score."""
        return sorted(
            self.recommendations,
            key=lambda r: r.confidence_score,
            reverse=descending
        )

    def sort_by_priority(self) -> List[Recommendation]:
        """Sort recommendations by priority (high to low)."""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(
            self.recommendations,
            key=lambda r: priority_order.get(r.priority, 2)
        )

    def _update_totals(self) -> None:
        """Update total confidence score."""
        if self.recommendations:
            self.total_confidence = sum(r.confidence_score for r in self.recommendations) / len(self.recommendations)
        else:
            self.total_confidence = 0.0

    def to_dict(self) -> dict:
        """Convert batch to dictionary representation."""
        return {
            "recommendations": [r.to_dict() for r in self.recommendations],
            "source": self.source,
            "processing_time_seconds": self.processing_time_seconds,
            "total_confidence": self.total_confidence,
            "recommendation_count": len(self.recommendations),
            "created_at": self.created_at.isoformat()
        }
