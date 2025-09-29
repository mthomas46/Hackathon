"""Document Repository Interface.

This module defines the contract for document data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.document import Document, DocumentId


class IDocumentRepository(ABC):
    """Interface for document repository operations."""

    @abstractmethod
    async def save(self, document: Document) -> None:
        """Save a document."""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: DocumentId) -> Optional[Document]:
        """Get a document by ID."""
        pass

    @abstractmethod
    async def get_by_id_str(self, document_id: str) -> Optional[Document]:
        """Get a document by ID string."""
        pass

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """List all documents with pagination."""
        pass

    @abstractmethod
    async def find_by_source(self, source: str) -> List[Document]:
        """Find documents by source."""
        pass

    @abstractmethod
    async def find_by_author(self, author: str) -> List[Document]:
        """Find documents by author."""
        pass

    @abstractmethod
    async def find_by_tags(self, tags: List[str]) -> List[Document]:
        """Find documents by tags."""
        pass

    @abstractmethod
    async def update(self, document: Document) -> None:
        """Update a document."""
        pass

    @abstractmethod
    async def delete(self, document_id: DocumentId) -> None:
        """Delete a document."""
        pass

    @abstractmethod
    async def exists(self, document_id: DocumentId) -> bool:
        """Check if a document exists."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total documents."""
        pass
