"""Log collector queries for CQRS pattern compliance."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GetLogByIdQuery(BaseModel):
    """Query to get log by ID."""
    log_id: str


class ListLogsQuery(BaseModel):
    """Query to list logs with filters."""
    service: Optional[str] = None
    level: Optional[str] = None
    limit: int = 50
    offset: int = 0


class SearchLogsQuery(BaseModel):
    """Query to search logs."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 50


class GetLogStatisticsQuery(BaseModel):
    """Query to get log statistics."""
    time_range: str = "24h"
