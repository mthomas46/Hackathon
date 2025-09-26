"""Document repository interface for DDD compliance."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..entities.document import Document


class DocumentRepository(ABC):
    """Abstract repository for document operations."""

    @abstractmethod
    async def save(self, document: Document) -> None:
        """Save a document."""
        pass

    @abstractmethod
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """Find document by ID."""
        pass

    @abstractmethod
    async def find_all(self, limit: int = 50, offset: int = 0) -> List[Document]:
        """Find all documents with pagination."""
        pass

    @abstractmethod
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None,
                    limit: int = 50) -> List[Document]:
        """Search documents by query and filters."""
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document by ID."""
        pass

    @abstractmethod
    async def exists(self, document_id: str) -> bool:
        """Check if document exists."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Count total documents."""
        pass

    @abstractmethod
    async def find_by_tags(self, tags: List[str], operator: str = "AND") -> List[Document]:
        """Find documents by tags."""
        pass
