"""
GetAuditHistoryQuery - Query Object

Represents a request to retrieve audit history for a service.
Following CQRS query pattern for read operations.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetAuditHistoryQuery:
    """Query to retrieve audit history for a service.

    This query represents the user's intention to read
    the audit history of a specific service.
    """

    service_name: str
    limit: Optional[int] = None
    include_failed_audits: bool = True

    def __post_init__(self):
        """Validate query parameters."""
        if not self.service_name:
            raise ValueError("Service name is required")

        if self.limit is not None and self.limit <= 0:
            raise ValueError("Limit must be a positive number")

        if self.limit is not None and self.limit > 100:
            raise ValueError("Limit cannot exceed 100")

    def get_effective_limit(self) -> int:
        """Get the effective limit for the query."""
        return self.limit or 10  # Default to last 10 audits
