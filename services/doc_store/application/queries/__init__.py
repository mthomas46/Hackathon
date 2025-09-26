"""Application queries for Doc Store service.

Queries represent read operations and data retrieval requests.
"""

from .document_queries import (
    GetDocumentQuery,
    SearchDocumentsQuery,
    ListDocumentsQuery,
    GetDocumentStatisticsQuery
)

__all__ = [
    "GetDocumentQuery",
    "SearchDocumentsQuery",
    "ListDocumentsQuery",
    "GetDocumentStatisticsQuery",
]
