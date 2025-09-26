"""Document domain service for DDD compliance."""

from typing import List, Optional, Dict, Any
from ..entities.document import Document
from ..repositories.document_repository import DocumentRepository


class DocumentService:
    """Domain service for document business logic."""

    def __init__(self, repository: DocumentRepository):
        self._repository = repository

    async def create_document(self, document_id: str, content: str,
                            metadata: Optional[Dict[str, Any]] = None,
                            tags: Optional[List[str]] = None) -> Document:
        """Create a new document."""
        document = Document(
            id=document_id,
            content=content,
            metadata=metadata or {},
            tags=tags or []
        )
        await self._repository.save(document)
        return document

    async def update_document(self, document_id: str, content: Optional[str] = None,
                            metadata: Optional[Dict[str, Any]] = None,
                            tags: Optional[List[str]] = None) -> Optional[Document]:
        """Update an existing document."""
        document = await self._repository.find_by_id(document_id)
        if not document:
            return None

        if content is not None:
            document.update_content(content)
        if metadata:
            document.update_metadata(metadata)
        if tags:
            document.add_tags(tags)

        await self._repository.save(document)
        return document

    async def tag_document(self, document_id: str, tags: List[str]) -> bool:
        """Add tags to a document."""
        document = await self._repository.find_by_id(document_id)
        if not document:
            return False

        document.add_tags(tags)
        await self._repository.save(document)
        return True

    async def search_documents(self, query: str, filters: Optional[Dict[str, Any]] = None,
                             limit: int = 50) -> List[Document]:
        """Search documents with business logic."""
        return await self._repository.search(query, filters, limit)

    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get document statistics."""
        total_count = await self._repository.count()
        # Additional business logic for statistics could go here
        return {
            "total_documents": total_count,
            "status": "active"
        }
