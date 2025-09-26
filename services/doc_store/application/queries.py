"""Document store queries for CQRS pattern compliance."""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel


class GetDocumentByIdQuery(BaseModel):
    """Query to get document by ID."""
    document_id: str


class ListDocumentsQuery(BaseModel):
    """Query to list documents with pagination."""
    page: int = 1
    size: int = 50
    sort_by: str = "created_at"
    sort_order: str = "desc"
    filters: Optional[Dict[str, Any]] = None


class SearchDocumentsQuery(BaseModel):
    """Query to search documents."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 50
    offset: int = 0


class GetDocumentMetadataQuery(BaseModel):
    """Query to get document metadata."""
    document_id: str


class GetDocumentsByTagsQuery(BaseModel):
    """Query to get documents by tags."""
    tags: List[str]
    operator: str = "AND"  # AND, OR


class GetDocumentStatisticsQuery(BaseModel):
    """Query to get document statistics."""
    time_range: Optional[str] = None
