"""Confidence Level Value Object"""

from enum import Enum


class ConfidenceLevel(Enum):
    """Enumeration of confidence assessment levels."""

    CRITICAL = "critical"  # < 25% - Major concerns, do not approve
    LOW = "low"          # 25-50% - Significant issues, requires review
    MEDIUM = "medium"    # 50-75% - Moderate confidence, consider carefully
    HIGH = "high"        # 75-90% - Good confidence, minor concerns
    EXCELLENT = "excellent"  # 90%+ - High confidence, ready for approval

    @property
    def numeric_range(self) -> tuple[float, float]:
        """Get the numeric range for this confidence level."""
        ranges = {
            ConfidenceLevel.CRITICAL: (0.0, 0.25),
            ConfidenceLevel.LOW: (0.25, 0.50),
            ConfidenceLevel.MEDIUM: (0.50, 0.75),
            ConfidenceLevel.HIGH: (0.75, 0.90),
            ConfidenceLevel.EXCELLENT: (0.90, 1.0)
        }
        return ranges[self]

    @property
    def color_code(self) -> str:
        """Get the color code for UI display."""
        colors = {
            ConfidenceLevel.CRITICAL: "#dc3545",    # Red
            ConfidenceLevel.LOW: "#fd7e14",         # Orange
            ConfidenceLevel.MEDIUM: "#ffc107",      # Yellow
            ConfidenceLevel.HIGH: "#28a745",        # Green
            ConfidenceLevel.EXCELLENT: "#20c997"    # Teal
        }
        return colors[self]

    @property
    def risk_level(self) -> str:
        """Get the associated risk level."""
        risk_levels = {
            ConfidenceLevel.CRITICAL: "high",
            ConfidenceLevel.LOW: "high",
            ConfidenceLevel.MEDIUM: "medium",
            ConfidenceLevel.HIGH: "low",
            ConfidenceLevel.EXCELLENT: "minimal"
        }
        return risk_levels[self]

    @classmethod
    def from_score(cls, score: float) -> 'ConfidenceLevel':
        """Determine confidence level from numeric score (0.0 to 1.0)."""
        if not 0.0 <= score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")

        for level in cls:
            min_score, max_score = level.numeric_range
            if min_score <= score < max_score:
                return level

        # Handle edge case of perfect score
        return ConfidenceLevel.EXCELLENT

    def __str__(self) -> str:
        return self.value
