"""Document store domain events for CQRS pattern compliance."""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from datetime import datetime


class DocumentStoredEvent(BaseModel):
    """Event fired when a document is stored."""
    document_id: str
    content_size: int
    tags: List[str]
    stored_at: datetime


class DocumentUpdatedEvent(BaseModel):
    """Event fired when a document is updated."""
    document_id: str
    updates: Dict[str, Any]
    updated_at: datetime


class DocumentDeletedEvent(BaseModel):
    """Event fired when a document is deleted."""
    document_id: str
    deleted_at: datetime


class DocumentTaggedEvent(BaseModel):
    """Event fired when a document is tagged."""
    document_id: str
    tags_added: List[str]
    tagged_at: datetime


class DocumentsBulkStoredEvent(BaseModel):
    """Event fired when multiple documents are stored."""
    document_count: int
    total_size: int
    stored_at: datetime


class DocumentSearchedEvent(BaseModel):
    """Event fired when a document search is performed."""
    query: str
    results_count: int
    search_duration_ms: int
    searched_at: datetime
