"""SearchQuery Value Object."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class SearchQuery:
    """
    Search query value object.
    
    Immutable search query configuration.
    """
    
    query_string: str
    service: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    tags: tuple = ()
    limit: int = 100
    offset: int = 0
    sort_by: str = "timestamp"
    sort_order: str = "desc"
    
    def __post_init__(self):
        """Validate search query."""
        if self.limit < 1:
            raise ValueError("Limit must be at least 1")
        if self.limit > 10000:
            raise ValueError("Limit cannot exceed 10000")
        if self.offset < 0:
            raise ValueError("Offset must be non-negative")
        if self.sort_order not in ("asc", "desc"):
            raise ValueError("Sort order must be 'asc' or 'desc'")

