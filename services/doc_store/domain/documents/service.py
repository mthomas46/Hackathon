"""Document service for business logic operations.

Handles document validation, processing, and business rules.
"""
import uuid
from typing import Dict, Any, Optional
from services.shared.envelopes import DocumentEnvelope
from ...core.entities import Document
from .repository import DocumentRepository


class DocumentService:
    """Service for document business logic."""

    def __init__(self):
        self.repository = DocumentRepository()

    def create_document(self, content: str, metadata: Optional[Dict[str, Any]] = None,
                       document_id: Optional[str] = None, correlation_id: Optional[str] = None) -> Document:
        """Create a new document with validation."""
        # Validate content
        if not content or not content.strip():
            raise ValueError("Document content cannot be empty")

        # Generate ID if not provided
        if not document_id:
            document_id = str(uuid.uuid4())

        # Calculate content hash
        content_hash = self.repository.calculate_content_hash(content)

        # Check for duplicates
        existing = self.repository.get_by_content_hash(content_hash)
        if existing:
            # Return existing document if content is identical
            return existing

        # Create document entity
        document = Document(
            id=document_id,
            content=content,
            content_hash=content_hash,
            metadata=metadata or {},
            correlation_id=correlation_id
        )

        # Validate metadata
        self._validate_metadata(document.metadata)

        # Save to repository
        self.repository.save(document)

        return document

    def get_document(self, document_id: str) -> Optional[Document]:
        """Get document by ID."""
        return self.repository.get_by_id(document_id)

    def update_metadata(self, document_id: str, metadata: Dict[str, Any]) -> None:
        """Update document metadata."""
        # Validate the document exists
        document = self.repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Validate metadata
        self._validate_metadata(metadata)

        # Update in repository
        self.repository.update_metadata(document_id, metadata)

    def list_documents(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List documents with pagination."""
        documents = self.repository.list_documents(limit, offset)

        return {
            "items": documents,
            "total": len(documents),
            "has_more": len(documents) == limit,
            "limit": limit,
            "offset": offset
        }

    def search_documents(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Search documents by content."""
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")

        results = self.repository.search_documents(query.strip(), limit)

        return {
            "items": results,
            "total": len(results),
            "query": query,
            "limit": limit
        }

    def get_quality_metrics(self, limit: int = 1000) -> Dict[str, Any]:
        """Get document quality metrics."""
        metrics = self.repository.get_quality_metrics(limit)

        # Aggregate quality statistics
        total = len(metrics)
        stale_count = sum(1 for m in metrics if 'stale' in m.get('flags', []))
        redundant_count = sum(1 for m in metrics if 'redundant' in m.get('flags', []))

        return {
            "items": metrics,
            "total": total,
            "stale_count": stale_count,
            "redundant_count": redundant_count,
            "stale_percentage": (stale_count / total * 100) if total > 0 else 0,
            "redundant_percentage": (redundant_count / total * 100) if total > 0 else 0
        }

    def get_related_documents(self, correlation_id: str) -> List[Dict[str, Any]]:
        """Get documents by correlation ID."""
        return self.repository.get_documents_by_correlation_id(correlation_id)

    def delete_document(self, document_id: str) -> None:
        """Delete document by ID."""
        # Validate the document exists
        document = self.repository.get_by_id(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Delete from repository
        self.repository.delete_document(document_id)

    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """Validate document metadata."""
        if not isinstance(metadata, dict):
            raise ValueError("Metadata must be a dictionary")

        # Check for reserved keys
        reserved_keys = {'id', 'content', 'content_hash', 'created_at', 'updated_at'}
        for key in reserved_keys:
            if key in metadata:
                raise ValueError(f"Metadata cannot contain reserved key: {key}")

        # Validate specific metadata fields if present
        if 'views' in metadata and not isinstance(metadata['views'], int):
            raise ValueError("Views must be an integer")

        if 'unique_views' in metadata and not isinstance(metadata['unique_views'], int):
            raise ValueError("Unique views must be an integer")

        if 'watchers' in metadata and not isinstance(metadata['watchers'], int):
            raise ValueError("Watchers must be an integer")
