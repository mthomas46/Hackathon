"""Frontend queries for CQRS pattern compliance."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GetUIStateQuery(BaseModel):
    """Query to get UI state."""
    user_id: str


class GetUserInteractionsQuery(BaseModel):
    """Query to get user interactions."""
    user_id: str
    limit: int = 50
    interaction_type: Optional[str] = None


class GetUIStatisticsQuery(BaseModel):
    """Query to get UI statistics."""
    time_range: str = "24h"
