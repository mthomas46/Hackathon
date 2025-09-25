"""
AuditResultDTO - Data Transfer Object

DTO for transferring audit result data between layers.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class AuditResultDTO:
    """Data Transfer Object for audit results.

    Used to transfer audit result data between application
    and presentation layers without exposing domain entities.
    """

    service_name: str
    overall_score: float
    grade: str
    dimensions: Dict[str, float]
    critical_issues_count: int
    recommendations: List[str]
    estimated_effort_days: float
    analysis_timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_domain(cls, analysis_result) -> 'AuditResultDTO':
        """Create DTO from domain AnalysisResult entity."""
        return cls(
            service_name=analysis_result.service_name,
            overall_score=analysis_result.overall_score,
            grade=analysis_result.grade,
            dimensions=analysis_result.dimensions,
            critical_issues_count=analysis_result.get_critical_issue_count(),
            recommendations=analysis_result.recommendations,
            estimated_effort_days=analysis_result.get_estimated_effort_days(),
            analysis_timestamp=analysis_result.analysis_timestamp,
            metadata=analysis_result.metadata,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "service_name": self.service_name,
            "overall_score": self.overall_score,
            "grade": self.grade,
            "dimensions": self.dimensions,
            "critical_issues_count": self.critical_issues_count,
            "recommendations": self.recommendations,
            "estimated_effort_days": self.estimated_effort_days,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "metadata": self.metadata or {},
        }
