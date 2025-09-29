"""Document Handler - Application Layer.

This module contains application layer handlers for document operations,
implementing use cases and coordinating between presentation and domain layers.
"""

import logging
from typing import Any, Dict, List, Optional

from ...domain.entities.document import Document
from ...domain.services.summarization_service import SummarizationService
from ...infrastructure.repositories.in_memory_document_repository import InMemoryDocumentRepository

logger = logging.getLogger(__name__)


class DocumentHandler:
    """Application handler for document operations."""

    def __init__(self):
        """Initialize the document handler."""
        self.domain_service = SummarizationService()
        self.repository = InMemoryDocumentRepository()

    async def create_document(
        self,
        content: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        author: Optional[str] = None,
        language: str = "en",
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new document.

        Args:
            content: Document content
            title: Optional document title
            source: Optional document source
            author: Optional document author
            language: Document language
            tags: Optional document tags

        Returns:
            Created document data
        """
        try:
            # Create document entity
            document = Document.create(
                content=content,
                title=title,
                source=source,
                author=author,
                language=language,
                tags=tags,
            )

            # Save to repository
            await self.repository.save(document)

            logger.info(f"Created document: {document.id.value}")
            return {
                "document_id": document.id.value,
                "title": document.title,
                "created_at": document.created_at.isoformat(),
                "word_count": document.get_word_count(),
            }

        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise

    async def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get a document by ID.

        Args:
            document_id: Document ID

        Returns:
            Document data
        """
        try:
            document = await self.repository.get_by_id_str(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")

            return {
                "id": document.id.value,
                "title": document.title,
                "content": document.content,
                "metadata": {
                    "source": document.metadata.source,
                    "author": document.metadata.author,
                    "language": document.metadata.language,
                    "word_count": document.get_word_count(),
                    "tags": document.metadata.tags,
                },
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise

    async def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        source_filter: Optional[str] = None,
        author_filter: Optional[str] = None,
        tags_filter: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """List documents with optional filtering.

        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            source_filter: Filter by source
            author_filter: Filter by author
            tags_filter: Filter by tags

        Returns:
            List of documents
        """
        try:
            # Apply filters
            if source_filter:
                documents = await self.repository.find_by_source(source_filter)
            elif author_filter:
                documents = await self.repository.find_by_author(author_filter)
            elif tags_filter:
                documents = await self.repository.find_by_tags(tags_filter)
            else:
                documents = await self.repository.list_all(limit + offset)

            # Apply pagination
            documents = documents[offset:offset + limit]

            return {
                "documents": [
                    {
                        "id": doc.id.value,
                        "title": doc.title,
                        "source": doc.metadata.source,
                        "author": doc.metadata.author,
                        "created_at": doc.created_at.isoformat(),
                        "word_count": doc.get_word_count(),
                        "tags": doc.metadata.tags[:3],  # First 3 tags
                    }
                    for doc in documents
                ],
                "total_count": await self.repository.count(),
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise

    async def update_document(
        self,
        document_id: str,
        content: Optional[str] = None,
        title: Optional[str] = None,
        **metadata_updates
    ) -> Dict[str, Any]:
        """Update a document.

        Args:
            document_id: Document ID
            content: New content
            title: New title
            metadata_updates: Metadata updates

        Returns:
            Updated document data
        """
        try:
            document = await self.repository.get_by_id_str(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Update content if provided
            if content:
                document.update_content(content, title)

            # Update metadata
            if metadata_updates:
                document.update_metadata(**metadata_updates)

            # Save updated document
            await self.repository.update(document)

            logger.info(f"Updated document: {document_id}")
            return {
                "document_id": document_id,
                "updated_at": document.updated_at.isoformat(),
                "version": document.version,
            }

        except Exception as e:
            logger.error(f"Failed to update document {document_id}: {e}")
            raise

    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        """Delete a document.

        Args:
            document_id: Document ID to delete

        Returns:
            Deletion result
        """
        try:
            document = await self.repository.get_by_id_str(document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")

            await self.repository.delete(document.id)

            logger.info(f"Deleted document: {document_id}")
            return {
                "document_id": document_id,
                "deleted": True,
                "message": "Document deleted successfully"
            }

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
