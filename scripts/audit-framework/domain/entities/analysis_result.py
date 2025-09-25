"""
AnalysisResult Domain Entity

Represents the result of an audit analysis with business logic and validation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum


class AuditGrade(Enum):
    """Audit grade enumeration based on score ranges."""
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class AnalysisResult:
    """Domain entity representing the result of an audit analysis.

    This entity contains all analysis results with business logic for
    score calculation, grading, and result interpretation.
    """

    service_name: str
    overall_score: float
    dimensions: Dict[str, float]
    architecture: Dict[str, Any]
    code_quality: Dict[str, Any]
    performance: Dict[str, Any]
    maintainability: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)
    critical_issues: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    analysis_timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Apply business rules and validations."""
        self._validate_scores()
        self._calculate_grade()

    def _validate_scores(self) -> None:
        """Validate that all scores are within valid ranges."""
        if not (0.0 <= self.overall_score <= 100.0):
            raise ValueError("Overall score must be between 0.0 and 100.0")

        for dimension, score in self.dimensions.items():
            if not (0.0 <= score <= 100.0):
                raise ValueError(f"Dimension '{dimension}' score must be between 0.0 and 100.0")

    def _calculate_grade(self) -> None:
        """Calculate letter grade based on overall score."""
        if self.overall_score >= 95:
            self.grade = AuditGrade.A_PLUS.value
        elif self.overall_score >= 90:
            self.grade = AuditGrade.A.value
        elif self.overall_score >= 85:
            self.grade = AuditGrade.B_PLUS.value
        elif self.overall_score >= 80:
            self.grade = AuditGrade.B.value
        elif self.overall_score >= 75:
            self.grade = AuditGrade.C_PLUS.value
        elif self.overall_score >= 70:
            self.grade = AuditGrade.C.value
        elif self.overall_score >= 60:
            self.grade = AuditGrade.D.value
        else:
            self.grade = AuditGrade.F.value

    @property
    def grade(self) -> str:
        """Get the audit grade."""
        return getattr(self, '_grade', AuditGrade.F.value)

    @grade.setter
    def grade(self, value: str) -> None:
        """Set the audit grade."""
        if value not in [grade.value for grade in AuditGrade]:
            raise ValueError(f"Invalid grade: {value}")
        self._grade = value

    def is_passing(self, threshold: float = 70.0) -> bool:
        """Check if the audit result is passing."""
        return self.overall_score >= threshold

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return len(self.critical_issues) > 0

    def get_critical_issue_count(self) -> int:
        """Get the number of critical issues."""
        return len(self.critical_issues)

    def get_high_priority_recommendations(self) -> List[str]:
        """Get recommendations that should be addressed immediately."""
        # Filter recommendations based on keywords indicating high priority
        high_priority_keywords = [
            "critical", "immediately", "urgent", "security", "fix",
            "🚨", "⚠️", "high-priority", "blocking"
        ]

        return [
            rec for rec in self.recommendations
            if any(keyword.lower() in rec.lower() for keyword in high_priority_keywords)
        ]

    def get_dimension_score(self, dimension: str) -> float:
        """Get score for a specific dimension."""
        return self.dimensions.get(dimension, 0.0)

    def get_weakest_dimensions(self, threshold: float = 70.0) -> List[str]:
        """Get dimensions that scored below the threshold."""
        return [
            dimension for dimension, score in self.dimensions.items()
            if score < threshold
        ]

    def get_estimated_effort_days(self) -> float:
        """Estimate effort required to address issues (in days)."""
        # Simple heuristic based on critical issues and weak dimensions
        base_effort = len(self.critical_issues) * 2  # 2 days per critical issue
        weak_dimensions = len(self.get_weakest_dimensions())

        # Add effort for weak dimensions
        dimension_effort = weak_dimensions * 1.5

        return round(base_effort + dimension_effort, 1)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "service_name": self.service_name,
            "overall_score": self.overall_score,
            "grade": self.grade,
            "dimensions": self.dimensions,
            "architecture": self.architecture,
            "code_quality": self.code_quality,
            "performance": self.performance,
            "maintainability": self.maintainability,
            "recommendations": self.recommendations,
            "critical_issues": self.critical_issues,
            "critical_issues_count": self.get_critical_issue_count(),
            "estimated_effort_days": self.get_estimated_effort_days(),
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalysisResult':
        """Create AnalysisResult from dictionary."""
        # Handle timestamp conversion
        analysis_timestamp = datetime.fromisoformat(data["analysis_timestamp"])

        return cls(
            service_name=data["service_name"],
            overall_score=data["overall_score"],
            dimensions=data["dimensions"],
            architecture=data["architecture"],
            code_quality=data["code_quality"],
            performance=data["performance"],
            maintainability=data["maintainability"],
            recommendations=data.get("recommendations", []),
            critical_issues=data.get("critical_issues", []),
            metadata=data.get("metadata", {}),
            analysis_timestamp=analysis_timestamp,
        )
