"""Document domain service for DDD compliance."""

from typing import List, Optional, Dict, Any
from ..entities.document import Document
from ..repositories.document_repository import DocumentRepository
from services.shared.infrastructure.utilities.logging_utils import (
    log_operation_start,
    log_operation_success,
    log_operation_error,
)


class DocumentService:
    """Domain service for document business logic."""

    def __init__(self, repository: DocumentRepository):
        self._repository = repository

    async def create_document(self, document_id: str, content: str,
                            metadata: Optional[Dict[str, Any]] = None,
                            tags: Optional[List[str]] = None) -> Document:
        """Create a new document with business logic validation and logging.

        Performs document creation with proper validation, metadata handling,
        and standardized logging for observability.

        Args:
            document_id: Unique identifier for the document
            content: Text content of the document
            metadata: Optional metadata dictionary (author, created_date, etc.)
            tags: Optional list of tags for categorization

        Returns:
            Document: The created and persisted document instance

        Raises:
            ValueError: If document validation fails
            Exception: If repository save operation fails

        Note:
            Error handling standardization: Uses consistent logging patterns
            with structured context across all services.
        """
        operation_name = "create_document"
        log_operation_start(operation_name, {
            "document_id": document_id,
            "content_length": len(content),
            "metadata_keys": list(metadata.keys()) if metadata else [],
            "tags_count": len(tags) if tags else 0
        })

        try:
            document = Document(
                id=document_id,
                content=content,
                metadata=metadata or {},
                tags=tags or []
            )
            await self._repository.save(document)

            log_operation_success(operation_name, {
                "document_id": document_id,
                "final_tags_count": len(document.tags)
            })
            return document

        except Exception as e:
            log_operation_error(operation_name, e, {
                "document_id": document_id,
                "error_type": type(e).__name__
            })
            raise

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
        """Add tags to an existing document.

        Args:
            document_id: Unique identifier of the document to tag
            tags: List of tag strings to add to the document

        Returns:
            bool: True if tagging was successful, False if document not found
        """
        document = await self._repository.find_by_id(document_id)
        if not document:
            return False

        document.add_tags(tags)
        await self._repository.save(document)
        return True

    async def search_documents(self, query: str, filters: Optional[Dict[str, Any]] = None,
                             limit: int = 50) -> List[Document]:
        """Search documents using text query and optional filters.

        Args:
            query: Search query string to match against document content
            filters: Optional dictionary of filter criteria (tags, metadata, etc.)
            limit: Maximum number of results to return (default: 50)

        Returns:
            List[Document]: List of documents matching the search criteria
        """
        return await self._repository.search(query, filters, limit)

    async def get_document_statistics(self) -> Dict[str, Any]:
        """Get comprehensive document collection statistics.

        Returns:
            Dict[str, Any]: Statistics including total count, and other
                           business-relevant metrics about the document collection
        """
        total_count = await self._repository.count()
        # Additional business logic for statistics could go here
        return {
            "total_documents": total_count,
            "status": "active"
        }
