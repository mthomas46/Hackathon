"""Confidence Level Value Object."""

from enum import Enum


class ConfidenceLevel(str, Enum):
    """
    Confidence level for query interpretation results.
    
    Indicates how certain the interpreter is about its analysis.
    """
    
    VERY_HIGH = "very_high"    # 0.9-1.0
    HIGH = "high"              # 0.75-0.9
    MEDIUM = "medium"          # 0.5-0.75
    LOW = "low"                # 0.25-0.5
    VERY_LOW = "very_low"      # 0.0-0.25
    
    @property
    def min_score(self) -> float:
        """Get minimum confidence score for this level."""
        scores = {
            ConfidenceLevel.VERY_HIGH: 0.9,
            ConfidenceLevel.HIGH: 0.75,
            ConfidenceLevel.MEDIUM: 0.5,
            ConfidenceLevel.LOW: 0.25,
            ConfidenceLevel.VERY_LOW: 0.0,
        }
        return scores.get(self, 0.0)
    
    @property
    def max_score(self) -> float:
        """Get maximum confidence score for this level."""
        scores = {
            ConfidenceLevel.VERY_HIGH: 1.0,
            ConfidenceLevel.HIGH: 0.9,
            ConfidenceLevel.MEDIUM: 0.75,
            ConfidenceLevel.LOW: 0.5,
            ConfidenceLevel.VERY_LOW: 0.25,
        }
        return scores.get(self, 1.0)
    
    @property
    def requires_human_review(self) -> bool:
        """Check if this confidence level requires human review."""
        return self in {
            ConfidenceLevel.LOW,
            ConfidenceLevel.VERY_LOW,
        }
    
    @property
    def can_auto_execute(self) -> bool:
        """Check if queries with this confidence can auto-execute."""
        return self in {
            ConfidenceLevel.VERY_HIGH,
            ConfidenceLevel.HIGH,
        }
    
    @classmethod
    def from_score(cls, score: float) -> "ConfidenceLevel":
        """
        Convert a numeric confidence score (0.0-1.0) to a ConfidenceLevel.
        
        Args:
            score: Confidence score between 0.0 and 1.0
        
        Returns:
            Appropriate ConfidenceLevel
        """
        if score >= 0.9:
            return cls.VERY_HIGH
        elif score >= 0.75:
            return cls.HIGH
        elif score >= 0.5:
            return cls.MEDIUM
        elif score >= 0.25:
            return cls.LOW
        else:
            return cls.VERY_LOW
    
    def to_score_range(self) -> tuple[float, float]:
        """
        Get the score range for this confidence level.
        
        Returns:
            Tuple of (min_score, max_score)
        """
        return (self.min_score, self.max_score)
    
    def __lt__(self, other: "ConfidenceLevel") -> bool:
        """Compare confidence levels (lower confidence < higher confidence)."""
        if not isinstance(other, ConfidenceLevel):
            return NotImplemented
        return self.min_score < other.min_score
    
    def __le__(self, other: "ConfidenceLevel") -> bool:
        """Less than or equal comparison."""
        if not isinstance(other, ConfidenceLevel):
            return NotImplemented
        return self.min_score <= other.min_score
    
    def __gt__(self, other: "ConfidenceLevel") -> bool:
        """Greater than comparison."""
        if not isinstance(other, ConfidenceLevel):
            return NotImplemented
        return self.min_score > other.min_score
    
    def __ge__(self, other: "ConfidenceLevel") -> bool:
        """Greater than or equal comparison."""
        if not isinstance(other, ConfidenceLevel):
            return NotImplemented
        return self.min_score >= other.min_score

