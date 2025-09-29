"""Infrastructure Application Queries"""

from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class GetSagaQuery:
    """Query to get a saga by ID."""
    saga_id: str


@dataclass
class ListSagasQuery:
    """Query to list sagas with filters."""
    status_filter: Optional[str] = None
    saga_type_filter: Optional[str] = None
    correlation_id_filter: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetTraceQuery:
    """Query to get a trace by ID."""
    trace_id: str


@dataclass
class ListTracesQuery:
    """Query to list traces with filters."""
    service_filter: Optional[str] = None
    operation_filter: Optional[str] = None
    start_time_after: Optional[str] = None
    start_time_before: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetDLQStatsQuery:
    """Query to get DLQ statistics."""
    time_range_hours: Optional[int] = 24


@dataclass
class ListDLQEventsQuery:
    """Query to list DLQ events."""
    event_type_filter: Optional[str] = None
    service_filter: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class GetEventStreamStatsQuery:
    """Query to get event stream statistics."""
    time_range_hours: Optional[int] = 24


@dataclass
class ListEventStreamQuery:
    """Query to list events from the stream."""
    event_type_filter: Optional[str] = None
    correlation_id_filter: Optional[str] = None
    time_after: Optional[str] = None
    limit: int = 50
    offset: int = 0
