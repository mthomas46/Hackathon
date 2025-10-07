"""SyncSchedule Value Object."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SyncSchedule:
    """
    Synchronization schedule value object.
    
    Immutable schedule configuration for sync jobs.
    """
    
    cron_expression: str
    timezone: str = "UTC"
    enabled: bool = True
    max_retries: int = 3
    retry_delay_seconds: int = 60
    
    def __post_init__(self):
        """Validate schedule."""
        if not self.cron_expression:
            raise ValueError("Cron expression is required")
        
        # Basic validation of cron format (5 or 6 fields)
        fields = self.cron_expression.strip().split()
        if len(fields) not in (5, 6):
            raise ValueError("Invalid cron expression format")
        
        if self.max_retries < 0:
            raise ValueError("Max retries must be non-negative")
        if self.retry_delay_seconds <= 0:
            raise ValueError("Retry delay must be positive")
    
    def is_active(self) -> bool:
        """Check if schedule is active."""
        return self.enabled

