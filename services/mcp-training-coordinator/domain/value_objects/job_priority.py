"""Job Priority Value Object."""

from enum import Enum


class JobPriority(str, Enum):
    """
    Priority level for training jobs.
    
    Determines order of execution when multiple jobs are queued.
    """
    
    LOW = "low"
    """Low priority - process when resources available."""
    
    NORMAL = "normal"
    """Normal priority - standard processing."""
    
    HIGH = "high"
    """High priority - expedited processing."""
    
    URGENT = "urgent"
    """Urgent priority - immediate processing."""
    
    CRITICAL = "critical"
    """Critical priority - highest priority, pre-empt other jobs."""
    
    @property
    def numeric_value(self) -> int:
        """Get numeric value for sorting."""
        priority_values = {
            JobPriority.LOW: 1,
            JobPriority.NORMAL: 2,
            JobPriority.HIGH: 3,
            JobPriority.URGENT: 4,
            JobPriority.CRITICAL: 5,
        }
        return priority_values[self]
    
    def __lt__(self, other: "JobPriority") -> bool:
        """Compare priorities for sorting."""
        if not isinstance(other, JobPriority):
            return NotImplemented
        return self.numeric_value < other.numeric_value
    
    def __le__(self, other: "JobPriority") -> bool:
        """Less than or equal comparison."""
        return self < other or self == other
    
    def __gt__(self, other: "JobPriority") -> bool:
        """Greater than comparison."""
        return not self <= other
    
    def __ge__(self, other: "JobPriority") -> bool:
        """Greater than or equal comparison."""
        return not self < other

