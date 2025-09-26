"""Memory agent queries for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class GetMemoryByIdQuery(BaseModel):
    """Query to get memory by ID."""
    memory_id: str


class ListMemoriesQuery(BaseModel):
    """Query to list memories with filters."""
    user_id: str
    memory_type: Optional[str] = None
    limit: int = 50
    offset: int = 0


class SearchMemoriesQuery(BaseModel):
    """Query to search memories."""
    user_id: str
    query: str
    memory_type: Optional[str] = None
    limit: int = 50


class GetMemoryStatisticsQuery(BaseModel):
    """Query to get memory statistics."""
    user_id: str
