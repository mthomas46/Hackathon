"""Document repository implementation."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from ...domain.entities import Document, DocumentId


class DocumentRepository(ABC):
    """Abstract repository for document entities."""

    @abstractmethod
    async def save(self, document: Document) -> None:
        """Save a document."""
        pass

    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        pass

    @abstractmethod
    async def get_all(self) -> List[Document]:
        """Get all documents."""
        pass

    @abstractmethod
    async def get_by_author(self, author: str) -> List[Document]:
        """Get documents by author."""
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document."""
        pass


class InMemoryDocumentRepository(DocumentRepository):
    """In-memory implementation of document repository."""

    def __init__(self):
        """Initialize repository with empty storage."""
        self._documents: Dict[str, Document] = {}

    async def save(self, document: Document) -> None:
        """Save a document to memory."""
        self._documents[document.id.value] = document

    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get document by ID from memory."""
        return self._documents.get(document_id)

    async def get_all(self) -> List[Document]:
        """Get all documents from memory."""
        return list(self._documents.values())

    async def get_by_author(self, author: str) -> List[Document]:
        """Get documents by author from memory."""
        return [
            doc for doc in self._documents.values()
            if doc.metadata.author and doc.metadata.author.lower() == author.lower()
        ]

    async def delete(self, document_id: str) -> bool:
        """Delete a document from memory."""
        if document_id in self._documents:
            del self._documents[document_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all documents (for testing)."""
        self._documents.clear()
