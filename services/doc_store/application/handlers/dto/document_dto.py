"""Data Transfer Objects for document operations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class DocumentDto(BaseModel):
    """DTO for document data."""
    id: str
    content: str
    metadata: Dict[str, Any]
    tags: List[str]
    created_at: datetime
    updated_at: datetime


class DocumentSearchResultDto(BaseModel):
    """DTO for search operation results."""
    documents: List[DocumentDto]
    total_count: int
    query: str
    search_duration_ms: int


class DocumentStatisticsDto(BaseModel):
    """DTO for document statistics."""
    total_documents: int
    documents_by_type: Dict[str, int]
    total_tags: int
    average_document_size: int
    last_updated: datetime


class DocumentUpdateDto(BaseModel):
    """DTO for document update operations."""
    document_id: str
    updates: Dict[str, Any]
    updated_at: datetime
