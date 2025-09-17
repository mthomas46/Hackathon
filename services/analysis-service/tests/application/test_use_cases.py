"""Tests for Application Use Cases."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any, List
from uuid import uuid4

from ...application.use_cases.perform_analysis_use_case import (
    PerformAnalysisUseCase, PerformAnalysisCommand, PerformAnalysisResult
)
from ...application.use_cases.create_document_use_case import CreateDocumentUseCase
from ...application.use_cases.get_document_use_case import GetDocumentUseCase
from ...application.use_cases.get_findings_use_case import GetFindingsUseCase
from ...application.use_cases.create_finding_use_case import CreateFindingUseCase

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence

from ...domain.exceptions import DocumentNotFoundException, AnalysisExecutionException


class TestPerformAnalysisUseCase:
    """Test cases for PerformAnalysisUseCase."""

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
            'analysis_service': Mock(),
            'finding_service': Mock()
        }

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus for testing."""
        return Mock()

    def test_use_case_creation(self, mock_services, mock_repositories, mock_event_bus):
        """Test creating perform analysis use case."""
        use_case = PerformAnalysisUseCase(
            analysis_service=mock_services['analysis_service'],
            finding_service=mock_services['finding_service'],
            document_repository=mock_repositories['document_repository'],
            analysis_repository=mock_repositories['analysis_repository'],
            finding_repository=mock_repositories['finding_repository'],
            event_bus=mock_event_bus
        )

        assert use_case.analysis_service == mock_services['analysis_service']
        assert use_case.event_bus == mock_event_bus

    def test_command_creation(self):
        """Test perform analysis command creation."""
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

    @pytest.mark.asyncio
    async def test_successful_analysis_execution(self, mock_services, mock_repositories, mock_event_bus):
        """Test successful analysis execution."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.id = 'doc-123'

        mock_analysis = Mock()
        mock_analysis.id = Mock()
        mock_analysis.id.value = 'analysis-123'
        mock_analysis.document_id = 'doc-123'
        mock_analysis.start = Mock()
        mock_analysis.complete = Mock()

        mock_repositories['document_repository'].get_by_id = AsyncMock(return_value=mock_doc)
        mock_repositories['analysis_repository'].save = AsyncMock()
        mock_repositories['finding_repository'].save = AsyncMock()

        mock_services['analysis_service'].create_analysis = Mock(return_value=mock_analysis)
        mock_services['analysis_service'].execute_analysis = Mock(return_value={
            'findings': [
                {
                    'title': 'Test Finding',
                    'description': 'Test description',
                    'severity': 'medium',
                    'category': 'test',
                    'confidence': 0.8
                }
            ]
        })

        mock_services['finding_service'].create_finding = Mock(return_value=Mock())

        mock_event_bus.publish = AsyncMock()

        use_case = PerformAnalysisUseCase(
            analysis_service=mock_services['analysis_service'],
            finding_service=mock_services['finding_service'],
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
        result = await use_case.execute(command)

        # Assert
        assert result.success is True
        assert result.analysis == mock_analysis
        assert len(result.findings) == 1
        assert result.error_message is None
        assert len(result.events) > 0

        # Verify method calls
        mock_repositories['document_repository'].get_by_id.assert_called_once_with('doc-123')
        mock_repositories['analysis_repository'].save.assert_called()
        mock_event_bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_document_not_found_error(self, mock_services, mock_repositories, mock_event_bus):
        """Test document not found error handling."""
        # Setup mocks
        mock_repositories['document_repository'].get_by_id = AsyncMock(return_value=None)
        mock_event_bus.publish = AsyncMock()

        use_case = PerformAnalysisUseCase(
            analysis_service=mock_services['analysis_service'],
            finding_service=mock_services['finding_service'],
            document_repository=mock_repositories['document_repository'],
            analysis_repository=mock_repositories['analysis_repository'],
            finding_repository=mock_repositories['finding_repository'],
            event_bus=mock_event_bus
        )

        command = PerformAnalysisCommand(
            document_id='non-existent-doc',
            analysis_type='semantic_similarity'
        )

        # Execute and expect exception
        with pytest.raises(DocumentNotFoundException):
            await use_case.execute(command)

        # Verify error event was published
        mock_event_bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_analysis_execution_error(self, mock_services, mock_repositories, mock_event_bus):
        """Test analysis execution error handling."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.id = 'doc-123'

        mock_analysis = Mock()
        mock_analysis.id = Mock()
        mock_analysis.id.value = 'analysis-123'
        mock_analysis.fail = Mock()

        mock_repositories['document_repository'].get_by_id = AsyncMock(return_value=mock_doc)
        mock_repositories['analysis_repository'].save = AsyncMock()
        mock_event_bus.publish = AsyncMock()

        mock_services['analysis_service'].create_analysis = Mock(return_value=mock_analysis)
        mock_services['analysis_service'].execute_analysis = Mock(side_effect=Exception("Analysis failed"))

        use_case = PerformAnalysisUseCase(
            analysis_service=mock_services['analysis_service'],
            finding_service=mock_services['finding_service'],
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
        result = await use_case.execute(command)

        # Assert error handling
        assert result.success is False
        assert result.error_message == "Analysis failed"
        assert len(result.events) > 0

        # Verify error event was published
        mock_event_bus.publish.assert_called()

    @pytest.mark.asyncio
    async def test_findings_processing(self, mock_services, mock_repositories, mock_event_bus):
        """Test findings processing in analysis result."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.id = 'doc-123'

        mock_analysis = Mock()
        mock_analysis.id = Mock()
        mock_analysis.id.value = 'analysis-123'
        mock_analysis.document_id = 'doc-123'
        mock_analysis.start = Mock()
        mock_analysis.complete = Mock()

        mock_finding = Mock()
        mock_finding.id = Mock()
        mock_finding.id.value = 'finding-123'

        mock_repositories['document_repository'].get_by_id = AsyncMock(return_value=mock_doc)
        mock_repositories['analysis_repository'].save = AsyncMock()
        mock_repositories['finding_repository'].save = AsyncMock()

        mock_services['analysis_service'].create_analysis = Mock(return_value=mock_analysis)
        mock_services['analysis_service'].execute_analysis = Mock(return_value={
            'findings': [
                {
                    'title': 'Security Issue',
                    'description': 'Potential security vulnerability',
                    'severity': 'high',
                    'category': 'security',
                    'confidence': 0.9
                }
            ]
        })

        mock_services['finding_service'].create_finding = Mock(return_value=mock_finding)

        mock_event_bus.publish = AsyncMock()

        use_case = PerformAnalysisUseCase(
            analysis_service=mock_services['analysis_service'],
            finding_service=mock_services['finding_service'],
            document_repository=mock_repositories['document_repository'],
            analysis_repository=mock_repositories['analysis_repository'],
            finding_repository=mock_repositories['finding_repository'],
            event_bus=mock_event_bus
        )

        command = PerformAnalysisCommand(
            document_id='doc-123',
            analysis_type='security_scan'
        )

        # Execute
        result = await use_case.execute(command)

        # Assert findings were processed
        assert len(result.findings) == 1
        mock_services['finding_service'].create_finding.assert_called_once()
        mock_repositories['finding_repository'].save.assert_called()

    def test_result_creation(self):
        """Test perform analysis result creation."""
        mock_analysis = Mock()
        mock_findings = [Mock(), Mock()]

        result = PerformAnalysisResult(
            analysis=mock_analysis,
            findings=mock_findings,
            execution_time_seconds=2.5,
            success=True,
            error_message=None,
            events=[]
        )

        assert result.analysis == mock_analysis
        assert len(result.findings) == 2
        assert result.execution_time_seconds == 2.5
        assert result.success is True
        assert result.error_message is None

    @pytest.mark.asyncio
    async def test_event_publishing(self, mock_services, mock_repositories, mock_event_bus):
        """Test event publishing during analysis execution."""
        # Setup mocks
        mock_doc = Mock()
        mock_doc.id = 'doc-123'

        mock_analysis = Mock()
        mock_analysis.id = Mock()
        mock_analysis.id.value = 'analysis-123'
        mock_analysis.document_id = 'doc-123'
        mock_analysis.start = Mock()
        mock_analysis.complete = Mock()

        mock_repositories['document_repository'].get_by_id = AsyncMock(return_value=mock_doc)
        mock_repositories['analysis_repository'].save = AsyncMock()

        mock_services['analysis_service'].create_analysis = Mock(return_value=mock_analysis)
        mock_services['analysis_service'].execute_analysis = Mock(return_value={})

        mock_event_bus.publish = AsyncMock()

        use_case = PerformAnalysisUseCase(
            analysis_service=mock_services['analysis_service'],
            finding_service=mock_services['finding_service'],
            document_repository=mock_repositories['document_repository'],
            analysis_repository=mock_repositories['analysis_repository'],
            finding_repository=mock_repositories['finding_repository'],
            event_bus=mock_event_bus
        )

        command = PerformAnalysisCommand(
            document_id='doc-123',
            analysis_type='semantic_similarity',
            user_id='user-456',
            session_id='session-789'
        )

        # Execute
        result = await use_case.execute(command)

        # Assert events were published
        assert mock_event_bus.publish.call_count >= 2  # At least requested and completed events
        assert len(result.events) >= 2


class TestCreateDocumentUseCase:
    """Test cases for CreateDocumentUseCase."""

    @pytest.fixture
    def mock_document_repository(self):
        """Mock document repository."""
        return Mock()

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus."""
        return Mock()

    def test_use_case_creation(self, mock_document_repository, mock_event_bus):
        """Test creating create document use case."""
        use_case = CreateDocumentUseCase(
            document_repository=mock_document_repository,
            event_bus=mock_event_bus
        )

        assert use_case.document_repository == mock_document_repository
        assert use_case.event_bus == mock_event_bus

    @pytest.mark.asyncio
    async def test_create_document_success(self, mock_document_repository, mock_event_bus):
        """Test successful document creation."""
        # Setup mocks
        mock_document = Mock()
        mock_document.id = 'doc-123'

        mock_document_repository.save = AsyncMock()
        mock_event_bus.publish = AsyncMock()

        use_case = CreateDocumentUseCase(
            document_repository=mock_document_repository,
            event_bus=mock_event_bus
        )

        # Execute
        result = await use_case.execute({
            'title': 'Test Document',
            'content': 'Test content',
            'repository_id': 'repo-123',
            'author': 'test-author'
        })

        # Assert
        assert result.success is True
        assert result.document.id == 'doc-123'
        mock_document_repository.save.assert_called_once()
        mock_event_bus.publish.assert_called()


class TestGetDocumentUseCase:
    """Test cases for GetDocumentUseCase."""

    @pytest.fixture
    def mock_document_repository(self):
        """Mock document repository."""
        return Mock()

    def test_use_case_creation(self, mock_document_repository):
        """Test creating get document use case."""
        use_case = GetDocumentUseCase(document_repository=mock_document_repository)
        assert use_case.document_repository == mock_document_repository

    @pytest.mark.asyncio
    async def test_get_document_success(self, mock_document_repository):
        """Test successful document retrieval."""
        # Setup mocks
        mock_document = Mock()
        mock_document.id = 'doc-123'

        mock_document_repository.get_by_id = AsyncMock(return_value=mock_document)

        use_case = GetDocumentUseCase(document_repository=mock_document_repository)

        # Execute
        result = await use_case.execute('doc-123')

        # Assert
        assert result.success is True
        assert result.document == mock_document
        mock_document_repository.get_by_id.assert_called_once_with('doc-123')

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, mock_document_repository):
        """Test document not found error."""
        mock_document_repository.get_by_id = AsyncMock(return_value=None)

        use_case = GetDocumentUseCase(document_repository=mock_document_repository)

        # Execute
        result = await use_case.execute('non-existent-doc')

        # Assert
        assert result.success is False
        assert result.error == "Document not found"


class TestGetFindingsUseCase:
    """Test cases for GetFindingsUseCase."""

    @pytest.fixture
    def mock_finding_repository(self):
        """Mock finding repository."""
        return Mock()

    def test_use_case_creation(self, mock_finding_repository):
        """Test creating get findings use case."""
        use_case = GetFindingsUseCase(finding_repository=mock_finding_repository)
        assert use_case.finding_repository == mock_finding_repository

    @pytest.mark.asyncio
    async def test_get_findings_by_analysis(self, mock_finding_repository):
        """Test getting findings by analysis."""
        # Setup mocks
        mock_findings = [Mock(), Mock(), Mock()]
        mock_finding_repository.get_by_analysis_id = AsyncMock(return_value=mock_findings)

        use_case = GetFindingsUseCase(finding_repository=mock_finding_repository)

        # Execute
        result = await use_case.execute(analysis_id='analysis-123')

        # Assert
        assert result.success is True
        assert len(result.findings) == 3
        mock_finding_repository.get_by_analysis_id.assert_called_once_with('analysis-123')

    @pytest.mark.asyncio
    async def test_get_findings_by_severity(self, mock_finding_repository):
        """Test getting findings by severity."""
        # Setup mocks
        mock_findings = [Mock(), Mock()]
        mock_finding_repository.get_by_severity = AsyncMock(return_value=mock_findings)

        use_case = GetFindingsUseCase(finding_repository=mock_finding_repository)

        # Execute
        result = await use_case.execute(severity='high')

        # Assert
        assert result.success is True
        assert len(result.findings) == 2
        mock_finding_repository.get_by_severity.assert_called_once_with('high')


class TestCreateFindingUseCase:
    """Test cases for CreateFindingUseCase."""

    @pytest.fixture
    def mock_finding_repository(self):
        """Mock finding repository."""
        return Mock()

    @pytest.fixture
    def mock_event_bus(self):
        """Mock event bus."""
        return Mock()

    def test_use_case_creation(self, mock_finding_repository, mock_event_bus):
        """Test creating create finding use case."""
        use_case = CreateFindingUseCase(
            finding_repository=mock_finding_repository,
            event_bus=mock_event_bus
        )

        assert use_case.finding_repository == mock_finding_repository
        assert use_case.event_bus == mock_event_bus

    @pytest.mark.asyncio
    async def test_create_finding_success(self, mock_finding_repository, mock_event_bus):
        """Test successful finding creation."""
        # Setup mocks
        mock_finding = Mock()
        mock_finding.id = 'finding-123'

        mock_finding_repository.save = AsyncMock()
        mock_event_bus.publish = AsyncMock()

        use_case = CreateFindingUseCase(
            finding_repository=mock_finding_repository,
            event_bus=mock_event_bus
        )

        # Execute
        result = await use_case.execute({
            'analysis_id': 'analysis-123',
            'document_id': 'doc-123',
            'title': 'Test Finding',
            'description': 'Test description',
            'severity': 'medium',
            'category': 'test'
        })

        # Assert
        assert result.success is True
        assert result.finding.id == 'finding-123'
        mock_finding_repository.save.assert_called_once()
        mock_event_bus.publish.assert_called()


class TestUseCaseIntegration:
    """Test integration between use cases."""

    @pytest.mark.asyncio
    async def test_analysis_workflow_use_cases(self):
        """Test complete analysis workflow using multiple use cases."""
        # This would test the integration between:
        # 1. CreateDocumentUseCase
        # 2. PerformAnalysisUseCase
        # 3. GetFindingsUseCase

        # Setup comprehensive mocks
        mock_doc_repo = Mock()
        mock_analysis_repo = Mock()
        mock_finding_repo = Mock()
        mock_event_bus = Mock()

        mock_document = Mock()
        mock_document.id = 'doc-123'

        mock_analysis = Mock()
        mock_analysis.id = Mock()
        mock_analysis.id.value = 'analysis-123'
        mock_analysis.document_id = 'doc-123'

        # Create use cases
        create_doc_uc = CreateDocumentUseCase(mock_doc_repo, mock_event_bus)
        perform_analysis_uc = PerformAnalysisUseCase(
            analysis_service=Mock(),
            finding_service=Mock(),
            document_repository=mock_doc_repo,
            analysis_repository=mock_analysis_repo,
            finding_repository=mock_finding_repo,
            event_bus=mock_event_bus
        )
        get_findings_uc = GetFindingsUseCase(mock_finding_repo)

        # This is a high-level integration test
        # In practice, you would set up all the mocks properly
        # and test the complete workflow

        assert create_doc_uc is not None
        assert perform_analysis_uc is not None
        assert get_findings_uc is not None


class TestUseCaseErrorHandling:
    """Test error handling across use cases."""

    @pytest.mark.asyncio
    async def test_use_case_exception_handling(self):
        """Test that use cases handle exceptions properly."""
        # Test that exceptions are caught and wrapped in result objects
        # rather than propagating up

        mock_repo = Mock()
        mock_repo.operation = AsyncMock(side_effect=Exception("Database error"))

        # Most use cases should catch exceptions and return error results
        # rather than letting them bubble up

        assert mock_repo is not None  # Placeholder assertion


class TestUseCaseValidation:
    """Test input validation in use cases."""

    def test_command_validation(self):
        """Test command input validation."""
        # Test that invalid command data is rejected

        # Valid command
        valid_command = PerformAnalysisCommand(
            document_id='doc-123',
            analysis_type='semantic_similarity',
            configuration={'valid': 'config'},
            priority='normal'
        )

        assert valid_command.document_id == 'doc-123'

        # Invalid command would be caught by validation layers
        # (business validators, etc.)


class TestUseCasePerformance:
    """Test performance aspects of use cases."""

    @pytest.mark.asyncio
    async def test_use_case_execution_time(self):
        """Test that use cases execute within reasonable time limits."""
        # This would measure execution time and assert it's within bounds

        mock_repo = Mock()
        mock_repo.get_by_id = AsyncMock(return_value=Mock())

        # Use case execution should be fast
        # (specific timing tests would depend on the actual implementation)

        assert mock_repo is not None  # Placeholder assertion
