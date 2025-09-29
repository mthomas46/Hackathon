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
    intent_filter: Optional[str] = None
    status_filter: Optional[str] = None
    page: int = 1
    page_size: int = 20
    limit: int = 50
    offset: int = 0
