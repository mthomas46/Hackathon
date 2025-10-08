"""Dependency injection container for Doc Store service.

Provides centralized dependency management and injection for all service components.
"""

from typing import Optional

from services.doc_store.domain.documents.repository import DocumentRepository  # ✅ FIX: Use correct repository with tags
from services.doc_store.db.connection import get_document_connection_string
from services.doc_store.application.handlers.document_handlers import DocumentHandlers
from services.doc_store.domain.documents.service import DocumentService


class DocStoreContainer:
    """Dependency injection container for Doc Store service."""

    def __init__(self):
        """Initialize container with service dependencies."""
        self._document_repository: Optional[DocumentRepository] = None
        self._document_service: Optional[DocumentService] = None
        self._document_handlers: Optional[DocumentHandlers] = None

    @property
    def document_repository(self) -> DocumentRepository:
        """Get or create document repository."""
        if self._document_repository is None:
            self._document_repository = DocumentRepository(
                get_document_connection_string()
            )
        return self._document_repository

    @property
    def document_service(self) -> DocumentService:
        """Get or create document service."""
        if self._document_service is None:
            self._document_service = DocumentService(self.document_repository)
        return self._document_service

    @property
    def document_handlers(self) -> DocumentHandlers:
        """Get or create document handlers."""
        if self._document_handlers is None:
            self._document_handlers = DocumentHandlers(self.document_service)
        return self._document_handlers


# Global container instance
container = DocStoreContainer()
