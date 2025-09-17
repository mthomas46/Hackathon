"""Query Processing Application Queries"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetQueryResultQuery:
    """Query to get query processing result."""
    query_id: str


@dataclass
class ListQueriesQuery:
    """Query to list processed queries."""
    status_filter: Optional[str] = None
    limit: int = 50
    offset: int = 0
