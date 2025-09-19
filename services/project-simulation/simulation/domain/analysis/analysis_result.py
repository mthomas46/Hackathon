"""
Domain entities for analysis results.
Following DDD principles with clean, focused entities.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime
from enum import Enum


class AnalysisType(Enum):
    """Types of analysis that can be performed."""
    DOCUMENT_ANALYSIS = "document_analysis"
    TIMELINE_ANALYSIS = "timeline_analysis"
    TEAM_DYNAMICS = "team_dynamics"
    RISK_ASSESSMENT = "risk_assessment"
    COST_BENEFIT_ANALYSIS = "cost_benefit_analysis"


@dataclass
class AnalysisResult:
    """Represents the result of an analysis operation."""
    simulation_id: str
    analysis_type: AnalysisType
    findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    confidence_score: float = 0.0
    analyzed_at: datetime = field(default_factory=datetime.now)
    processing_time_seconds: float = 0.0

    def add_finding(self, finding: str) -> None:
        """Add a finding to the analysis result."""
        self.findings.append(finding)

    def add_recommendation(self, recommendation: str) -> None:
        """Add a recommendation to the analysis result."""
        self.recommendations.append(recommendation)

    def add_metric(self, key: str, value: Any) -> None:
        """Add a metric to the analysis result."""
        self.metrics[key] = value

    def add_insight(self, insight: str) -> None:
        """Add an insight to the analysis result."""
        self.insights.append(insight)

    def calculate_confidence(self) -> float:
        """Calculate confidence score based on available data."""
        # Simple confidence calculation based on data completeness
        data_points = len(self.findings) + len(self.metrics) + len(self.insights)
        if data_points == 0:
            return 0.0
        elif data_points < 3:
            return 0.5
        elif data_points < 6:
            return 0.7
        else:
            return 0.9
