"""Application handlers for Doc Store service.

Handlers process commands and queries, orchestrating business logic.
"""

from .document_handlers import (
    CreateDocumentHandler,
    UpdateDocumentHandler,
    DeleteDocumentHandler,
    GetDocumentHandler,
    SearchDocumentsHandler,
    ListDocumentsHandler,
    GetDocumentStatisticsHandler
)

__all__ = [
    "CreateDocumentHandler",
    "UpdateDocumentHandler",
    "DeleteDocumentHandler",
    "GetDocumentHandler",
    "SearchDocumentsHandler",
    "ListDocumentsHandler",
    "GetDocumentStatisticsHandler",
]
