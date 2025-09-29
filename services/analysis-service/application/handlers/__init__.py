"""Application layer handlers."""

from .commands import (
    CreateDocumentCommand,
    UpdateDocumentCommand,
    PerformAnalysisCommand,
    CreateFindingCommand,
    UpdateFindingCommand,
    DeleteDocumentCommand
)
from .command_handlers import (
    CreateDocumentCommandHandler,
    UpdateDocumentCommandHandler,
    PerformAnalysisCommandHandler,
    CreateFindingCommandHandler,
    UpdateFindingCommandHandler,
    DeleteDocumentCommandHandler
)
from .queries import (
    GetDocumentQuery,
    GetDocumentsQuery,
    GetAnalysisQuery,
    GetAnalysesQuery,
    GetFindingQuery,
    GetFindingsQuery,
    GetStatisticsQuery
)
from .query_handlers import (
    GetDocumentQueryHandler,
    GetDocumentsQueryHandler,
    GetAnalysisQueryHandler,
    GetAnalysesQueryHandler,
    GetFindingQueryHandler,
    GetFindingsQueryHandler,
    GetStatisticsQueryHandler
)

__all__ = [
    # Commands
    'CreateDocumentCommand',
    'UpdateDocumentCommand',
    'PerformAnalysisCommand',
    'CreateFindingCommand',
    'UpdateFindingCommand',
    'DeleteDocumentCommand',
    # Command Handlers
    'CreateDocumentCommandHandler',
    'UpdateDocumentCommandHandler',
    'PerformAnalysisCommandHandler',
    'CreateFindingCommandHandler',
    'UpdateFindingCommandHandler',
    'DeleteDocumentCommandHandler',
    # Queries
    'GetDocumentQuery',
    'GetDocumentsQuery',
    'GetAnalysisQuery',
    'GetAnalysesQuery',
    'GetFindingQuery',
    'GetFindingsQuery',
    'GetStatisticsQuery',
    # Query Handlers
    'GetDocumentQueryHandler',
    'GetDocumentsQueryHandler',
    'GetAnalysisQueryHandler',
    'GetAnalysesQueryHandler',
    'GetFindingQueryHandler',
    'GetFindingsQueryHandler',
    'GetStatisticsQueryHandler'
]
