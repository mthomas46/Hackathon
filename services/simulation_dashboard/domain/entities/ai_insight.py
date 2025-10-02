"""AI Insight domain entity."""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from services.shared.domain import BaseEntity


class InsightType(Enum):
    """AI insight type enumeration."""
    PREDICTIVE = "predictive"
    DIAGNOSTIC = "diagnostic"
    PRESCRIPTIVE = "prescriptive"
    DESCRIPTIVE = "descriptive"
    ANOMALY = "anomaly"
    TREND = "trend"


class InsightSeverity(Enum):
    """Insight severity enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AIInsight(BaseEntity):
    """Domain entity representing an AI-generated insight."""

    id: str
    title: str
    description: str
    insight_type: InsightType = InsightType.DESCRIPTIVE
    severity: InsightSeverity = InsightSeverity.MEDIUM
    confidence_score: float = 0.0
    data_source: str = ""
    simulation_id: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    is_actionable: bool = False
    action_taken: bool = False
    action_timestamp: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Post initialization validation."""
        if not self.id:
            raise ValueError("AI Insight ID cannot be empty")
        if not self.title:
            raise ValueError("AI Insight title cannot be empty")
        if not self.description:
            raise ValueError("AI Insight description cannot be empty")
        if not isinstance(self.confidence_score, (int, float)):
            raise ValueError("Confidence score must be numeric")
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")

    def mark_action_taken(self) -> None:
        """Mark the insight as having an action taken."""
        self.action_taken = True
        self.action_timestamp = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_confidence(self, new_score: float) -> None:
        """Update the confidence score."""
        if not 0 <= new_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")
        self.confidence_score = new_score
        self.updated_at = datetime.utcnow()

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation."""
        if recommendation not in self.recommendations:
            self.recommendations.append(recommendation)
            self.updated_at = datetime.utcnow()

    def remove_recommendation(self, recommendation: str) -> None:
        """Remove a recommendation."""
        if recommendation in self.recommendations:
            self.recommendations.remove(recommendation)
            self.updated_at = datetime.utcnow()

    def is_high_confidence(self) -> bool:
        """Check if insight has high confidence."""
        return self.confidence_score >= 0.8

    def is_critical_severity(self) -> bool:
        """Check if insight has critical severity."""
        return self.severity == InsightSeverity.CRITICAL

    def requires_attention(self) -> bool:
        """Check if insight requires attention."""
        return (self.is_critical_severity() or
                (self.is_high_confidence() and self.severity in [InsightSeverity.HIGH, InsightSeverity.CRITICAL]))

    def get_priority_score(self) -> float:
        """Calculate priority score based on severity and confidence."""
        severity_weights = {
            InsightSeverity.LOW: 0.25,
            InsightSeverity.MEDIUM: 0.5,
            InsightSeverity.HIGH: 0.75,
            InsightSeverity.CRITICAL: 1.0
        }
        return severity_weights[self.severity] * self.confidence_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert AI insight to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "insight_type": self.insight_type.value,
            "severity": self.severity.value,
            "confidence_score": self.confidence_score,
            "data_source": self.data_source,
            "simulation_id": self.simulation_id,
            "metrics": self.metrics,
            "recommendations": self.recommendations,
            "supporting_data": self.supporting_data,
            "is_actionable": self.is_actionable,
            "action_taken": self.action_taken,
            "action_timestamp": self.action_timestamp.isoformat() if self.action_timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags
        }
