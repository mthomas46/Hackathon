"""Document repository infrastructure."""

from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod

from ...domain.entities.document import Document


class DocumentRepository(ABC):
    """Abstract base class for document repositories.

    Defines the interface for document persistence operations.
    """

    @abstractmethod
    async def save(self, document: Document) -> None:
        """Save a document to the repository."""
        pass

    @abstractmethod
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """Find a document by its ID."""
        pass

    @abstractmethod
    async def find_by_source(self, source_type: str, source_id: str) -> List[Document]:
        """Find documents by source type and source ID."""
        pass

    @abstractmethod
    async def find_by_tags(self, tags: List[str]) -> List[Document]:
        """Find documents that have any of the specified tags."""
        pass

    @abstractmethod
    async def update(self, document: Document) -> None:
        """Update an existing document."""
        pass

    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document by ID."""
        pass

    @abstractmethod
    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Search documents by content and filters."""
        pass

    @abstractmethod
    async def get_recent(self, limit: int = 10) -> List[Document]:
        """Get recently fetched documents."""
        pass


class InMemoryDocumentRepository(DocumentRepository):
    """In-memory implementation of document repository for testing and development."""

    def __init__(self):
        """Initialize the in-memory repository."""
        self._documents: Dict[str, Document] = {}
        self._source_index: Dict[str, List[str]] = {}  # source_key -> [document_ids]
        self._tag_index: Dict[str, List[str]] = {}     # tag -> [document_ids]

    async def save(self, document: Document) -> None:
        """Save a document to memory."""
        self._documents[document.id] = document

        # Update source index
        source_key = f"{document.source_type}:{document.source_id}"
        if source_key not in self._source_index:
            self._source_index[source_key] = []
        if document.id not in self._source_index[source_key]:
            self._source_index[source_key].append(document.id)

        # Update tag index
        for tag in document.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            if document.id not in self._tag_index[tag]:
                self._tag_index[tag].append(document.id)

    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """Find a document by ID."""
        return self._documents.get(document_id)

    async def find_by_source(self, source_type: str, source_id: str) -> List[Document]:
        """Find documents by source."""
        source_key = f"{source_type}:{source_id}"
        document_ids = self._source_index.get(source_key, [])
        return [self._documents[doc_id] for doc_id in document_ids if doc_id in self._documents]

    async def find_by_tags(self, tags: List[str]) -> List[Document]:
        """Find documents by tags."""
        document_ids = set()
        for tag in tags:
            document_ids.update(self._tag_index.get(tag, []))

        return [self._documents[doc_id] for doc_id in document_ids if doc_id in self._documents]

    async def update(self, document: Document) -> None:
        """Update a document."""
        if document.id in self._documents:
            await self.save(document)  # Re-save to update indexes

    async def delete(self, document_id: str) -> bool:
        """Delete a document."""
        if document_id in self._documents:
            document = self._documents[document_id]

            # Remove from indexes
            source_key = f"{document.source_type}:{document.source_id}"
            if source_key in self._source_index:
                self._source_index[source_key] = [
                    doc_id for doc_id in self._source_index[source_key] if doc_id != document_id
                ]

            for tag in document.tags:
                if tag in self._tag_index:
                    self._tag_index[tag] = [
                        doc_id for doc_id in self._tag_index[tag] if doc_id != document_id
                    ]

            del self._documents[document_id]
            return True
        return False

    async def search(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        """Simple text search in documents."""
        query_lower = query.lower()
        results = []

        for document in self._documents.values():
            # Apply text search
            text_match = (
                query_lower in document.title.lower() or
                query_lower in document.content.lower()
            )

            if not text_match:
                continue

            # Apply filters
            if filters:
                if not self._matches_filters(document, filters):
                    continue

            results.append(document)

        return results

    async def get_recent(self, limit: int = 10) -> List[Document]:
        """Get recently fetched documents."""
        sorted_docs = sorted(
            self._documents.values(),
            key=lambda d: d.fetched_at,
            reverse=True
        )
        return sorted_docs[:limit]

    def _matches_filters(self, document: Document, filters: Dict[str, Any]) -> bool:
        """Check if document matches the given filters."""
        for key, value in filters.items():
            if key == "source_type" and document.source_type != value:
                return False
            elif key == "source_id" and document.source_id != value:
                return False
            elif key == "status" and document.status != value:
                return False
            elif key == "tags":
                if not any(tag in document.tags for tag in value):
                    return False
            elif key == "author" and document.author != value:
                return False

        return True

    def clear(self) -> None:
        """Clear all documents (for testing)."""
        self._documents.clear()
        self._source_index.clear()
        self._tag_index.clear()
