"""Query bus for CQRS pattern."""

from typing import Dict, Type, Any
from abc import ABC, abstractmethod

from ..handlers.query_handlers import (
    GetDocumentQueryHandler,
    GetDocumentsQueryHandler,
    GetAnalysisQueryHandler,
    GetAnalysesQueryHandler,
    GetFindingQueryHandler,
    GetFindingsQueryHandler,
    GetStatisticsQueryHandler
)
from ..handlers.queries import (
    GetDocumentQuery,
    GetDocumentsQuery,
    GetAnalysisQuery,
    GetAnalysesQuery,
    GetFindingQuery,
    GetFindingsQuery,
    GetStatisticsQuery
)


class QueryBus:
    """Query bus for dispatching queries to handlers."""

    def __init__(self):
        """Initialize query bus with empty handler registry."""
        self._handlers: Dict[Type, Any] = {}

    def register_handler(self, query_type: Type, handler: Any) -> None:
        """Register a query handler."""
        self._handlers[query_type] = handler

    async def ask(self, query: Any) -> Any:
        """Ask a query to its handler."""
        query_type = type(query)

        if query_type not in self._handlers:
            raise ValueError(f"No handler registered for query: {query_type.__name__}")

        handler = self._handlers[query_type]
        return await handler.handle(query)

    def register_default_handlers(self,
                                  get_document_handler: GetDocumentQueryHandler,
                                  get_documents_handler: GetDocumentsQueryHandler,
                                  get_analysis_handler: GetAnalysisQueryHandler,
                                  get_analyses_handler: GetAnalysesQueryHandler,
                                  get_finding_handler: GetFindingQueryHandler,
                                  get_findings_handler: GetFindingsQueryHandler,
                                  get_statistics_handler: GetStatisticsQueryHandler) -> None:
        """Register all default query handlers."""
        self.register_handler(GetDocumentQuery, get_document_handler)
        self.register_handler(GetDocumentsQuery, get_documents_handler)
        self.register_handler(GetAnalysisQuery, get_analysis_handler)
        self.register_handler(GetAnalysesQuery, get_analyses_handler)
        self.register_handler(GetFindingQuery, get_finding_handler)
        self.register_handler(GetFindingsQuery, get_findings_handler)
        self.register_handler(GetStatisticsQuery, get_statistics_handler)

    def get_registered_queries(self) -> list[str]:
        """Get list of registered query types."""
        return [query.__name__ for query in self._handlers.keys()]

    def has_handler(self, query_type: Type) -> bool:
        """Check if a handler is registered for the query type."""
        return query_type in self._handlers
