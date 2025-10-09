"""Severity value object."""

from enum import Enum


class Severity(Enum):
    """Severity levels for issues and findings."""
    
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    WARNING = 3  # Alias for MEDIUM
    LOW = 2
    INFO = 1
    
    def __lt__(self, other):
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value < other.value
    
    def __le__(self, other):
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value <= other.value
    
    def __gt__(self, other):
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value > other.value
    
    def __ge__(self, other):
        """Compare severity levels."""
        if not isinstance(other, Severity):
            return NotImplemented
        return self.value >= other.value

