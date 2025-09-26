"""Document store commands for CQRS pattern compliance."""

from typing import Any, Dict, Optional, List
from pydantic import BaseModel


class StoreDocumentCommand(BaseModel):
    """Command to store a new document."""
    document_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class UpdateDocumentCommand(BaseModel):
    """Command to update an existing document."""
    document_id: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class DeleteDocumentCommand(BaseModel):
    """Command to delete a document."""
    document_id: str


class TagDocumentCommand(BaseModel):
    """Command to tag a document."""
    document_id: str
    tags: List[str]


class BulkStoreDocumentsCommand(BaseModel):
    """Command to store multiple documents."""
    documents: List[Dict[str, Any]]


class SearchDocumentsCommand(BaseModel):
    """Command to search documents."""
    query: str
    filters: Optional[Dict[str, Any]] = None
    limit: int = 50
