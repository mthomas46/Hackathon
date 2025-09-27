"""Severity level value object."""

from enum import Enum
from typing import Optional


class SeverityLevel(Enum):
    """Enumeration of severity levels for issues and findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @classmethod
    def from_string(cls, value: str) -> Optional['SeverityLevel']:
        """Create severity level from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        display_names = {
            "critical": "Critical",
            "high": "High",
            "medium": "Medium",
            "low": "Low",
            "info": "Informational",
        }
        return display_names.get(self.value, self.value.title())

    def get_numeric_value(self) -> int:
        """Get numeric value for severity (higher = more severe)."""
        numeric_values = {
            "critical": 5,
            "high": 4,
            "medium": 3,
            "low": 2,
            "info": 1,
        }
        return numeric_values.get(self.value, 0)

    def is_security_relevant(self) -> bool:
        """Check if this severity level is relevant for security issues."""
        return self in [self.CRITICAL, self.HIGH, self.MEDIUM]

    def requires_immediate_attention(self) -> bool:
        """Check if this severity requires immediate attention."""
        return self in [self.CRITICAL, self.HIGH]

    def get_response_time_hours(self) -> int:
        """Get recommended response time in hours based on severity."""
        response_times = {
            "critical": 1,   # 1 hour
            "high": 4,       # 4 hours
            "medium": 24,    # 24 hours
            "low": 168,      # 1 week
            "info": 0,       # No specific timeline
        }
        return response_times.get(self.value, 0)

    def get_cvss_score_range(self) -> tuple[float, float]:
        """Get typical CVSS score range for this severity level."""
        score_ranges = {
            "critical": (9.0, 10.0),
            "high": (7.0, 8.9),
            "medium": (4.0, 6.9),
            "low": (0.1, 3.9),
            "info": (0.0, 0.0),
        }
        return score_ranges.get(self.value, (0.0, 0.0))

    def __lt__(self, other: 'SeverityLevel') -> bool:
        """Less than comparison based on numeric value."""
        if isinstance(other, SeverityLevel):
            return self.get_numeric_value() < other.get_numeric_value()
        return NotImplemented

    def __le__(self, other: 'SeverityLevel') -> bool:
        """Less than or equal comparison."""
        if isinstance(other, SeverityLevel):
            return self.get_numeric_value() <= other.get_numeric_value()
        return NotImplemented

    def __gt__(self, other: 'SeverityLevel') -> bool:
        """Greater than comparison."""
        if isinstance(other, SeverityLevel):
            return self.get_numeric_value() > other.get_numeric_value()
        return NotImplemented

    def __ge__(self, other: 'SeverityLevel') -> bool:
        """Greater than or equal comparison."""
        if isinstance(other, SeverityLevel):
            return self.get_numeric_value() >= other.get_numeric_value()
        return NotImplemented
