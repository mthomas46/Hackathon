"""
GetAuditTrendsQuery - Query Object

Represents a request to retrieve audit trends for a service.
Following CQRS query pattern for read operations.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetAuditTrendsQuery:
    """Query to retrieve audit trends for a service.

    This query represents the user's intention to analyze
    audit trends over time for a specific service.
    """

    service_name: str
    time_window_days: Optional[int] = None
    include_forecast: bool = False

    def __post_init__(self):
        """Validate query parameters."""
        if not self.service_name:
            raise ValueError("Service name is required")

        if self.time_window_days is not None:
            if self.time_window_days <= 0:
                raise ValueError("Time window must be a positive number")
            if self.time_window_days > 365:
                raise ValueError("Time window cannot exceed 365 days")

    def get_effective_time_window(self) -> int:
        """Get the effective time window in days."""
        return self.time_window_days or 30  # Default to last 30 days
