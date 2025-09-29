"""In-Memory Document Repository Implementation.

This module provides an in-memory implementation of the document repository
for development and testing purposes.
"""

from typing import Dict, List, Optional
from ..domain.repositories.document_repository import IDocumentRepository
from ..domain.entities.document import Document, DocumentId


class InMemoryDocumentRepository(IDocumentRepository):
    """In-memory implementation of document repository."""

    def __init__(self):
        """Initialize the repository."""
        self._documents: Dict[str, Document] = {}

    async def save(self, document: Document) -> None:
        """Save a document."""
        self._documents[document.id.value] = document

    async def get_by_id(self, document_id: DocumentId) -> Optional[Document]:
        """Get a document by ID."""
        return self._documents.get(document_id.value)

    async def get_by_id_str(self, document_id: str) -> Optional[Document]:
        """Get a document by ID string."""
        return self._documents.get(document_id)

    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """List all documents with pagination."""
        documents = list(self._documents.values())
        return documents[offset:offset + limit]

    async def find_by_source(self, source: str) -> List[Document]:
        """Find documents by source."""
        return [
            doc for doc in self._documents.values()
            if doc.metadata.source == source
        ]

    async def find_by_author(self, author: str) -> List[Document]:
        """Find documents by author."""
        return [
            doc for doc in self._documents.values()
            if doc.metadata.author == author
        ]

    async def find_by_tags(self, tags: List[str]) -> List[Document]:
        """Find documents by tags."""
        return [
            doc for doc in self._documents.values()
            if any(tag in doc.metadata.tags for tag in tags)
        ]

    async def update(self, document: Document) -> None:
        """Update a document."""
        self._documents[document.id.value] = document

    async def delete(self, document_id: DocumentId) -> None:
        """Delete a document."""
        self._documents.pop(document_id.value, None)

    async def exists(self, document_id: DocumentId) -> bool:
        """Check if a document exists."""
        return document_id.value in self._documents

    async def count(self) -> int:
        """Count total documents."""
        return len(self._documents)
