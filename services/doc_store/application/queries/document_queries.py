"""Document queries for Doc Store application layer.

Query objects that represent read operations on documents.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class GetDocumentQuery:
    """Query to retrieve a single document by ID."""

    document_id: str

    def __post_init__(self):
        """Validate query data."""
        if not self.document_id or not self.document_id.strip():
            raise ValueError("Document ID cannot be empty")


@dataclass
class SearchDocumentsQuery:
    """Query to search documents by content and filters."""

    query: str
    filters: Optional[Dict[str, str]] = None
    limit: int = 50
    offset: int = 0

    def __post_init__(self):
        """Validate query data."""
        if not self.query or not self.query.strip():
            raise ValueError("Search query cannot be empty")
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")


@dataclass
class ListDocumentsQuery:
    """Query to list documents with pagination."""

    limit: int = 50
    offset: int = 0
    sort_by: str = "created_at"
    sort_order: str = "desc"

    def __post_init__(self):
        """Validate query data."""
        if self.limit < 1 or self.limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        if self.offset < 0:
            raise ValueError("Offset cannot be negative")
        if self.sort_order not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        if self.sort_by not in ["created_at", "updated_at", "id"]:
            raise ValueError("Sort by must be one of: created_at, updated_at, id")


@dataclass
class GetDocumentStatisticsQuery:
    """Query to get document statistics and metrics."""

    include_tags: bool = True
    include_metadata: bool = True

    def __post_init__(self):
        """Validate query data."""
        # No validation needed for this simple query
        pass
