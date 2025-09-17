"""Query Confidence Value Object"""

from enum import Enum


class QueryConfidence(Enum):
    """Enumeration of query interpretation confidence levels."""

    VERY_LOW = "very_low"      # < 30% - High uncertainty, requires clarification
    LOW = "low"               # 30-50% - Moderate uncertainty, suggest alternatives
    MEDIUM = "medium"         # 50-70% - Reasonable confidence, proceed with caution
    HIGH = "high"            # 70-85% - Good confidence, proceed normally
    VERY_HIGH = "very_high"  # 85%+ - High confidence, execute directly

    @property
    def numeric_range(self) -> tuple[float, float]:
        """Get the numeric range for this confidence level."""
        ranges = {
            QueryConfidence.VERY_LOW: (0.0, 0.3),
            QueryConfidence.LOW: (0.3, 0.5),
            QueryConfidence.MEDIUM: (0.5, 0.7),
            QueryConfidence.HIGH: (0.7, 0.85),
            QueryConfidence.VERY_HIGH: (0.85, 1.0)
        }
        return ranges[self]

    @property
    def requires_clarification(self) -> bool:
        """Check if this confidence level requires user clarification."""
        return self in (QueryConfidence.VERY_LOW, QueryConfidence.LOW)

    @property
    def can_auto_execute(self) -> bool:
        """Check if query can be automatically executed at this confidence level."""
        return self == QueryConfidence.VERY_HIGH

    @property
    def should_suggest_alternatives(self) -> bool:
        """Check if alternatives should be suggested."""
        return self in (QueryConfidence.LOW, QueryConfidence.MEDIUM)

    @property
    def risk_level(self) -> str:
        """Get associated risk level."""
        risk_levels = {
            QueryConfidence.VERY_LOW: "high",
            QueryConfidence.LOW: "high",
            QueryConfidence.MEDIUM: "medium",
            QueryConfidence.HIGH: "low",
            QueryConfidence.VERY_HIGH: "minimal"
        }
        return risk_levels[self]

    @classmethod
    def from_score(cls, score: float) -> 'QueryConfidence':
        """Determine confidence level from numeric score (0.0 to 1.0)."""
        if not 0.0 <= score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")

        for level in cls:
            min_score, max_score = level.numeric_range
            if min_score <= score < max_score:
                return level

        # Handle edge case of perfect score
        return QueryConfidence.VERY_HIGH

    def __str__(self) -> str:
        return self.value.replace('_', ' ').title()
