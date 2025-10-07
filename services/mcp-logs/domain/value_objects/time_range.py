"""TimeRange Value Object."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TimeRange:
    """
    Time range value object.
    
    Immutable time range for queries.
    """
    
    start: datetime
    end: datetime
    
    def __post_init__(self):
        """Validate time range."""
        if self.start >= self.end:
            raise ValueError("Start time must be before end time")
    
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        return (self.end - self.start).total_seconds()
    
    def contains(self, timestamp: datetime) -> bool:
        """Check if timestamp is within range."""
        return self.start <= timestamp <= self.end

