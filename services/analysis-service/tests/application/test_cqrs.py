"""Tests for CQRS Implementation - Command and Query Handlers."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any, List
from uuid import uuid4

from ...application.cqrs.command_bus import CommandBus
from ...application.cqrs.query_bus import QueryBus
from ...application.handlers.commands import (
    CreateDocumentCommand, UpdateDocumentCommand, DeleteDocumentCommand,
    PerformAnalysisCommand, CancelAnalysisCommand
)
from ...application.handlers.queries import (
    GetDocumentQuery, GetDocumentsQuery, GetAnalysisQuery,
    GetFindingsQuery, GetDocumentHistoryQuery
)
from ...application.handlers.command_handlers import (
    CreateDocumentCommandHandler, UpdateDocumentCommandHandler,
    DeleteDocumentCommandHandler, PerformAnalysisCommandHandler
)
from ...application.handlers.query_handlers import (
    GetDocumentQueryHandler, GetDocumentsQueryHandler,
    GetAnalysisQueryHandler, GetFindingsQueryHandler
)

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType


class TestCommandBus:
    """Test cases for CommandBus."""

    def test_command_bus_creation(self):
        """Test creating command bus."""
        bus = CommandBus()
        assert bus is not None
        assert len(bus._handlers) == 0

    @pytest.mark.asyncio
    async def test_register_and_execute_command(self):
        """Test registering and executing commands."""
        bus = CommandBus()

        # Mock command handler
        mock_handler = Mock()
        mock_handler.handle = AsyncMock(return_value={'result': 'success'})

        # Register handler
        bus.register_handler('CreateDocumentCommand', mock_handler)

        # Execute command
        command = Mock()
        command.__class__.__name__ = 'CreateDocumentCommand'

        result = await bus.execute(command)

        # Assert
        assert result == {'result': 'success'}
        mock_handler.handle.assert_called_once_with(command)

    @pytest.mark.asyncio
    async def test_execute_unregistered_command(self):
        """Test executing unregistered command."""
        bus = CommandBus()

        command = Mock()
        command.__class__.__name__ = 'UnknownCommand'

        with pytest.raises(ValueError, match="No handler registered"):
            await bus.execute(command)

    @pytest.mark.asyncio
    async def test_command_bus_error_handling(self):
        """Test command bus error handling."""
        bus = CommandBus()

        # Mock handler that raises exception
        mock_handler = Mock()
        mock_handler.handle = AsyncMock(side_effect=Exception("Handler error"))

        bus.register_handler('FailingCommand', mock_handler)

        command = Mock()
        command.__class__.__name__ = 'FailingCommand'

        with pytest.raises(Exception, match="Handler error"):
            await bus.execute(command)


class TestQueryBus:
    """Test cases for QueryBus."""

    def test_query_bus_creation(self):
        """Test creating query bus."""
        bus = QueryBus()
        assert bus is not None
        assert len(bus._handlers) == 0

    @pytest.mark.asyncio
    async def test_register_and_execute_query(self):
        """Test registering and executing queries."""
        bus = QueryBus()

        # Mock query handler
        mock_handler = Mock()
        mock_handler.handle = AsyncMock(return_value=[{'id': 'doc-1'}, {'id': 'doc-2'}])

        # Register handler
        bus.register_handler('GetDocumentsQuery', mock_handler)

        # Execute query
        query = Mock()
        query.__class__.__name__ = 'GetDocumentsQuery'

        result = await bus.execute(query)

        # Assert
        assert len(result) == 2
        assert result[0]['id'] == 'doc-1'
        mock_handler.handle.assert_called_once_with(query)

    @pytest.mark.asyncio
    async def test_execute_unregistered_query(self):
        """Test executing unregistered query."""
        bus = QueryBus()

        query = Mock()
        query.__class__.__name__ = 'UnknownQuery'

        with pytest.raises(ValueError, match="No handler registered"):
            await bus.execute(query)


class TestCommandHandlers:
    """Test cases for Command Handlers."""

    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories for testing."""
        return {
            'document_repository': Mock(),
            'analysis_repository': Mock(),
            'finding_repository': Mock()
        }

    @pytest.fixture
    def mock_services(self):
        """Mock domain services for testing."""
        return {
            'document_service': Mock(),
            'analysis_service': Mock(),
            'finding_service': Mock()
        }

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus for testing."""
        return Mock()

    def test_create_document_command_handler_creation(self, mock_repositories, mock_services, mock_event_bus):
        """Test creating create document command handler."""
        handler = CreateDocumentCommandHandler(
            document_repository=mock_repositories['document_repository'],
            document_service=mock_services['document_service'],
            event_bus=mock_event_bus
        )

        assert handler.document_repository == mock_repositories['document_repository']
        assert handler.document_service == mock_services['document_service']
        assert handler.event_bus == mock_event_bus

    @pytest.mark.asyncio
    async def test_create_document_command_handler_execution(self, mock_repositories, mock_services, mock_event_bus):
        """Test create document command handler execution."""
        # Setup mocks
        mock_document = Mock()
        mock_document.id = 'doc-123'

        mock_services['document_service'].create_document = AsyncMock(return_value=mock_document)
        mock_repositories['document_repository'].save = AsyncMock()
        mock_event_bus.publish = AsyncMock()

        handler = CreateDocumentCommandHandler(
            document_repository=mock_repositories['document_repository'],
            document_service=mock_services['document_service'],
            event_bus=mock_event_bus
        )

        command = CreateDocumentCommand(
            title='Test Document',
            content='Test content',
            repository_id='repo-123',
            author='test-author'
        )

        # Execute
        result = await handler.handle(command)

        # Assert
        assert result['document_id'] == 'doc-123'
        assert result['status'] == 'created'
        mock_services['document_service'].create_document.assert_called_once()
        mock_repositories['document_repository'].save.assert_called_once()
        mock_event_bus.publish.assert_called()

    def test_perform_analysis_command_handler_creation(self, mock_repositories, mock_services, mock_event_bus):
        """Test creating perform analysis command handler."""
        handler = PerformAnalysisCommandHandler(
            analysis_service=mock_services['analysis_service'],
            document_repository=mock_repositories['document_repository'],
            analysis_repository=mock_repositories['analysis_repository'],
            finding_repository=mock_repositories['finding_repository'],
            event_bus=mock_event_bus
        )

        assert handler.analysis_service == mock_services['analysis_service']
        assert handler.event_bus == mock_event_bus

    @pytest.mark.asyncio
    async def test_perform_analysis_command_handler_execution(self, mock_repositories, mock_services, mock_event_bus):
        """Test perform analysis command handler execution."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.id = 'doc-123'

        mock_analysis = Mock()
        mock_analysis.id = 'analysis-123'
        mock_analysis.status = AnalysisStatus.COMPLETED

        mock_repositories['document_repository'].get_by_id = AsyncMock(return_value=mock_doc)
        mock_repositories['analysis_repository'].save = AsyncMock()

        mock_services['analysis_service'].start_analysis = AsyncMock(return_value=mock_analysis)
        mock_services['analysis_service'].complete_analysis = AsyncMock(return_value=mock_analysis)

        mock_event_bus.publish = AsyncMock()

        handler = PerformAnalysisCommandHandler(
            analysis_service=mock_services['analysis_service'],
            document_repository=mock_repositories['document_repository'],
            analysis_repository=mock_repositories['analysis_repository'],
            finding_repository=mock_repositories['finding_repository'],
            event_bus=mock_event_bus
        )

        command = PerformAnalysisCommand(
            document_id='doc-123',
            analysis_type='semantic_similarity'
        )

        # Execute
        result = await handler.handle(command)

        # Assert
        assert result['analysis_id'] == 'analysis-123'
        assert result['status'] == 'completed'
        mock_services['analysis_service'].start_analysis.assert_called_once()
        mock_event_bus.publish.assert_called()


class TestQueryHandlers:
    """Test cases for Query Handlers."""

    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories for testing."""
        return {
            'document_repository': Mock(),
            'analysis_repository': Mock(),
            'finding_repository': Mock()
        }

    def test_get_document_query_handler_creation(self, mock_repositories):
        """Test creating get document query handler."""
        handler = GetDocumentQueryHandler(
            document_repository=mock_repositories['document_repository']
        )

        assert handler.document_repository == mock_repositories['document_repository']

    @pytest.mark.asyncio
    async def test_get_document_query_handler_execution(self, mock_repositories):
        """Test get document query handler execution."""
        # Setup mocks
        mock_document = Mock()
        mock_document.id = 'doc-123'
        mock_document.title = 'Test Document'

        mock_repositories['document_repository'].get_by_id = AsyncMock(return_value=mock_document)

        handler = GetDocumentQueryHandler(
            document_repository=mock_repositories['document_repository']
        )

        query = GetDocumentQuery(document_id='doc-123')

        # Execute
        result = await handler.handle(query)

        # Assert
        assert result['document']['id'] == 'doc-123'
        assert result['document']['title'] == 'Test Document'
        mock_repositories['document_repository'].get_by_id.assert_called_once_with('doc-123')

    def test_get_documents_query_handler_creation(self, mock_repositories):
        """Test creating get documents query handler."""
        handler = GetDocumentsQueryHandler(
            document_repository=mock_repositories['document_repository']
        )

        assert handler.document_repository == mock_repositories['document_repository']

    @pytest.mark.asyncio
    async def test_get_documents_query_handler_execution(self, mock_repositories):
        """Test get documents query handler execution."""
        # Setup mocks
        mock_documents = [
            Mock(id='doc-1', title='Doc 1'),
            Mock(id='doc-2', title='Doc 2'),
            Mock(id='doc-3', title='Doc 3')
        ]

        mock_repositories['document_repository'].get_all = AsyncMock(return_value=mock_documents)

        handler = GetDocumentsQueryHandler(
            document_repository=mock_repositories['document_repository']
        )

        query = GetDocumentsQuery()

        # Execute
        result = await handler.handle(query)

        # Assert
        assert len(result['documents']) == 3
        assert result['total_count'] == 3
        mock_repositories['document_repository'].get_all.assert_called_once()

    def test_get_analysis_query_handler_creation(self, mock_repositories):
        """Test creating get analysis query handler."""
        handler = GetAnalysisQueryHandler(
            analysis_repository=mock_repositories['analysis_repository']
        )

        assert handler.analysis_repository == mock_repositories['analysis_repository']

    @pytest.mark.asyncio
    async def test_get_analysis_query_handler_execution(self, mock_repositories):
        """Test get analysis query handler execution."""
        # Setup mocks
        mock_analysis = Mock()
        mock_analysis.id = 'analysis-123'
        mock_analysis.status = AnalysisStatus.COMPLETED

        mock_repositories['analysis_repository'].get_by_id = AsyncMock(return_value=mock_analysis)

        handler = GetAnalysisQueryHandler(
            analysis_repository=mock_repositories['analysis_repository']
        )

        query = GetAnalysisQuery(analysis_id='analysis-123')

        # Execute
        result = await handler.handle(query)

        # Assert
        assert result['analysis']['id'] == 'analysis-123'
        assert result['analysis']['status'] == AnalysisStatus.COMPLETED
        mock_repositories['analysis_repository'].get_by_id.assert_called_once_with('analysis-123')

    def test_get_findings_query_handler_creation(self, mock_repositories):
        """Test creating get findings query handler."""
        handler = GetFindingsQueryHandler(
            finding_repository=mock_repositories['finding_repository']
        )

        assert handler.finding_repository == mock_repositories['finding_repository']

    @pytest.mark.asyncio
    async def test_get_findings_query_handler_execution(self, mock_repositories):
        """Test get findings query handler execution."""
        # Setup mocks
        mock_findings = [
            Mock(id='finding-1', severity=FindingSeverity.HIGH),
            Mock(id='finding-2', severity=FindingSeverity.MEDIUM),
            Mock(id='finding-3', severity=FindingSeverity.LOW)
        ]

        mock_repositories['finding_repository'].get_by_analysis_id = AsyncMock(return_value=mock_findings)

        handler = GetFindingsQueryHandler(
            finding_repository=mock_repositories['finding_repository']
        )

        query = GetFindingsQuery(analysis_id='analysis-123')

        # Execute
        result = await handler.handle(query)

        # Assert
        assert len(result['findings']) == 3
        assert result['total_count'] == 3
        mock_repositories['finding_repository'].get_by_analysis_id.assert_called_once_with('analysis-123')


class TestCQRSCommands:
    """Test cases for CQRS Commands."""

    def test_create_document_command_creation(self):
        """Test creating create document command."""
        command = CreateDocumentCommand(
            title='Test Document',
            content='Test content',
            repository_id='repo-123',
            author='test-author',
            metadata={'tags': ['test']}
        )

        assert command.title == 'Test Document'
        assert command.content == 'Test content'
        assert command.repository_id == 'repo-123'
        assert command.author == 'test-author'
        assert command.metadata == {'tags': ['test']}

    def test_update_document_command_creation(self):
        """Test creating update document command."""
        command = UpdateDocumentCommand(
            document_id='doc-123',
            title='Updated Title',
            content='Updated content',
            metadata={'updated': True}
        )

        assert command.document_id == 'doc-123'
        assert command.title == 'Updated Title'
        assert command.content == 'Updated content'

    def test_delete_document_command_creation(self):
        """Test creating delete document command."""
        command = DeleteDocumentCommand(
            document_id='doc-123',
            reason='No longer needed'
        )

        assert command.document_id == 'doc-123'
        assert command.reason == 'No longer needed'

    def test_perform_analysis_command_creation(self):
        """Test creating perform analysis command."""
        command = PerformAnalysisCommand(
            document_id='doc-123',
            analysis_type='semantic_similarity',
            configuration={'threshold': 0.8},
            priority='high',
            timeout_seconds=300
        )

        assert command.document_id == 'doc-123'
        assert command.analysis_type == 'semantic_similarity'
        assert command.configuration == {'threshold': 0.8}
        assert command.priority == 'high'
        assert command.timeout_seconds == 300

    def test_cancel_analysis_command_creation(self):
        """Test creating cancel analysis command."""
        command = CancelAnalysisCommand(
            analysis_id='analysis-123',
            reason='User requested cancellation'
        )

        assert command.analysis_id == 'analysis-123'
        assert command.reason == 'User requested cancellation'


class TestCQRSQueries:
    """Test cases for CQRS Queries."""

    def test_get_document_query_creation(self):
        """Test creating get document query."""
        query = GetDocumentQuery(
            document_id='doc-123',
            include_metadata=True
        )

        assert query.document_id == 'doc-123'
        assert query.include_metadata is True

    def test_get_documents_query_creation(self):
        """Test creating get documents query."""
        query = GetDocumentsQuery(
            repository_id='repo-123',
            status='active',
            limit=50,
            offset=0,
            sort_by='created_at',
            sort_order='desc'
        )

        assert query.repository_id == 'repo-123'
        assert query.status == 'active'
        assert query.limit == 50
        assert query.offset == 0

    def test_get_analysis_query_creation(self):
        """Test creating get analysis query."""
        query = GetAnalysisQuery(
            analysis_id='analysis-123',
            include_details=True
        )

        assert query.analysis_id == 'analysis-123'
        assert query.include_details is True

    def test_get_findings_query_creation(self):
        """Test creating get findings query."""
        query = GetFindingsQuery(
            analysis_id='analysis-123',
            severity='high',
            category='security',
            limit=100,
            offset=0
        )

        assert query.analysis_id == 'analysis-123'
        assert query.severity == 'high'
        assert query.category == 'security'
        assert query.limit == 100

    def test_get_document_history_query_creation(self):
        """Test creating get document history query."""
        query = GetDocumentHistoryQuery(
            document_id='doc-123',
            since=datetime.now(timezone.utc),
            limit=20
        )

        assert query.document_id == 'doc-123'
        assert query.limit == 20


class TestCQRSIntegration:
    """Test integration between CQRS components."""

    @pytest.mark.asyncio
    async def test_complete_cqrs_workflow(self):
        """Test complete CQRS workflow."""
        # Setup command and query buses
        command_bus = CommandBus()
        query_bus = QueryBus()

        # Setup repositories and services
        mock_doc_repo = Mock()
        mock_analysis_repo = Mock()
        mock_doc_service = Mock()

        # Setup handlers
        create_handler = CreateDocumentCommandHandler(
            document_repository=mock_doc_repo,
            document_service=mock_doc_service,
            event_bus=Mock()
        )
        get_handler = GetDocumentQueryHandler(document_repository=mock_doc_repo)

        # Register handlers
        command_bus.register_handler('CreateDocumentCommand', create_handler)
        query_bus.register_handler('GetDocumentQuery', get_handler)

        # Setup mocks
        mock_document = Mock()
        mock_document.id = 'doc-123'
        mock_document.title = 'Created Document'

        mock_doc_service.create_document = AsyncMock(return_value=mock_document)
        mock_doc_repo.save = AsyncMock()
        mock_doc_repo.get_by_id = AsyncMock(return_value=mock_document)

        # Execute command
        create_command = CreateDocumentCommand(
            title='Test Document',
            content='Test content',
            repository_id='repo-123'
        )

        command_result = await command_bus.execute(create_command)
        assert command_result['document_id'] == 'doc-123'

        # Execute query
        get_query = GetDocumentQuery(document_id='doc-123')
        query_result = await query_bus.execute(get_query)
        assert query_result['document']['id'] == 'doc-123'

    @pytest.mark.asyncio
    async def test_cqrs_error_handling(self):
        """Test CQRS error handling."""
        command_bus = CommandBus()

        # Mock handler that raises exception
        mock_handler = Mock()
        mock_handler.handle = AsyncMock(side_effect=Exception("Command failed"))

        command_bus.register_handler('FailingCommand', mock_handler)

        command = Mock()
        command.__class__.__name__ = 'FailingCommand'

        with pytest.raises(Exception, match="Command failed"):
            await command_bus.execute(command)

    @pytest.mark.asyncio
    async def test_cqrs_handler_registration(self):
        """Test CQRS handler registration and lookup."""
        command_bus = CommandBus()

        # Register multiple handlers
        handler1 = Mock()
        handler2 = Mock()

        command_bus.register_handler('Command1', handler1)
        command_bus.register_handler('Command2', handler2)

        # Verify registrations
        assert 'Command1' in command_bus._handlers
        assert 'Command2' in command_bus._handlers
        assert command_bus._handlers['Command1'] == handler1
        assert command_bus._handlers['Command2'] == handler2


class TestCQRSPerformance:
    """Test performance aspects of CQRS implementation."""

    @pytest.mark.asyncio
    async def test_command_bus_performance(self):
        """Test command bus performance with multiple commands."""
        command_bus = CommandBus()

        # Mock handler
        mock_handler = Mock()
        mock_handler.handle = AsyncMock(return_value={'result': 'ok'})

        command_bus.register_handler('TestCommand', mock_handler)

        # Execute multiple commands
        commands = []
        for i in range(10):
            command = Mock()
            command.__class__.__name__ = 'TestCommand'
            commands.append(command)

        # Execute all commands concurrently
        import asyncio
        results = await asyncio.gather(*[command_bus.execute(cmd) for cmd in commands])

        # Assert all executed successfully
        assert len(results) == 10
        assert all(r['result'] == 'ok' for r in results)

        # Verify handler was called correct number of times
        assert mock_handler.handle.call_count == 10
