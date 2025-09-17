"""Report Type Value Object"""

from enum import Enum


class ReportType(Enum):
    """Enumeration of supported report types."""

    SUMMARY = "summary"
    DETAILED = "detailed"
    METRICS = "metrics"
    AUDIT = "audit"
    PR_CONFIDENCE = "pr_confidence"
    LIFE_OF_TICKET = "life_of_ticket"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"

    @property
    def description(self) -> str:
        """Get a human-readable description of the report type."""
        descriptions = {
            ReportType.SUMMARY: "High-level summary with key metrics",
            ReportType.DETAILED: "Comprehensive report with full details",
            ReportType.METRICS: "Focused on quantitative metrics and KPIs",
            ReportType.AUDIT: "Compliance and audit trail information",
            ReportType.PR_CONFIDENCE: "Pull request confidence analysis",
            ReportType.LIFE_OF_TICKET: "End-to-end ticket lifecycle analysis",
            ReportType.COMPLIANCE: "Regulatory compliance assessment",
            ReportType.PERFORMANCE: "System performance and efficiency metrics"
        }
        return descriptions[self]

    @property
    def requires_ai(self) -> bool:
        """Check if this report type requires AI processing."""
        return self in (ReportType.PR_CONFIDENCE, ReportType.LIFE_OF_TICKET)

    def __str__(self) -> str:
        return self.value
