"""Application layer handlers."""

from .command_handlers import (
    CreateDocumentCommandHandler,
    CreateFindingCommandHandler,
    DeleteDocumentCommandHandler,
    PerformAnalysisCommandHandler,
    UpdateDocumentCommandHandler,
    UpdateFindingCommandHandler,
)
from .commands import (
    CreateDocumentCommand,
    CreateFindingCommand,
    DeleteDocumentCommand,
    PerformAnalysisCommand,
    UpdateDocumentCommand,
    UpdateFindingCommand,
)
from .queries import (
    GetAnalysesQuery,
    GetAnalysisQuery,
    GetDocumentQuery,
    GetDocumentsQuery,
    GetFindingQuery,
    GetFindingsQuery,
    GetStatisticsQuery,
)
from .query_handlers import (
    GetAnalysesQueryHandler,
    GetAnalysisQueryHandler,
    GetDocumentQueryHandler,
    GetDocumentsQueryHandler,
    GetFindingQueryHandler,
    GetFindingsQueryHandler,
    GetStatisticsQueryHandler,
)

__all__ = [
    # Commands
    "CreateDocumentCommand",
    "UpdateDocumentCommand",
    "PerformAnalysisCommand",
    "CreateFindingCommand",
    "UpdateFindingCommand",
    "DeleteDocumentCommand",
    # Command Handlers
    "CreateDocumentCommandHandler",
    "UpdateDocumentCommandHandler",
    "PerformAnalysisCommandHandler",
    "CreateFindingCommandHandler",
    "UpdateFindingCommandHandler",
    "DeleteDocumentCommandHandler",
    # Queries
    "GetDocumentQuery",
    "GetDocumentsQuery",
    "GetAnalysisQuery",
    "GetAnalysesQuery",
    "GetFindingQuery",
    "GetFindingsQuery",
    "GetStatisticsQuery",
    # Query Handlers
    "GetDocumentQueryHandler",
    "GetDocumentsQueryHandler",
    "GetAnalysisQueryHandler",
    "GetAnalysesQueryHandler",
    "GetFindingQueryHandler",
    "GetFindingsQueryHandler",
    "GetStatisticsQueryHandler",
]
