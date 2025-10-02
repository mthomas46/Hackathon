"""Simulation Queries.

Query objects for simulation read operations following CQRS principles.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ListSimulationsQuery:
    """Query to list simulations with filtering and pagination."""

    user_id: Optional[str] = None
    status: Optional[str] = None
    simulation_type: Optional[str] = None
    limit: int = 50
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"

    def __post_init__(self):
        """Validate query parameters."""
        if self.limit < 1 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")
        if self.sort_order not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        if self.sort_by not in ["created_at", "name", "status", "updated_at"]:
            raise ValueError("Invalid sort field")


@dataclass
class GetSimulationQuery:
    """Query to get a specific simulation."""

    simulation_id: str
    include_details: bool = True

    def __post_init__(self):
        """Validate query data."""
        if not self.simulation_id:
            raise ValueError("Simulation ID is required")


@dataclass
class GetSimulationProgressQuery:
    """Query to get simulation execution progress."""

    simulation_id: str
    include_logs: bool = False
    log_limit: int = 100

    def __post_init__(self):
        """Validate query data."""
        if not self.simulation_id:
            raise ValueError("Simulation ID is required")
        if self.log_limit < 0 or self.log_limit > 1000:
            raise ValueError("Log limit must be between 0 and 1000")
