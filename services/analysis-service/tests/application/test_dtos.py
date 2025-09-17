"""Tests for Application DTOs (Data Transfer Objects)."""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ...application.dto.request_dtos import (
    CreateDocumentRequest, UpdateDocumentRequest, DeleteDocumentRequest,
    PerformAnalysisRequest, CancelAnalysisRequest, GetDocumentRequest,
    GetDocumentsRequest, GetAnalysisRequest, GetFindingsRequest
)
from ...application.dto.response_dtos import (
    DocumentResponse, AnalysisResponse, FindingResponse,
    DocumentsListResponse, FindingsListResponse, AnalysisResultResponse,
    ErrorResponse, SuccessResponse, PaginatedResponse
)

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence


class TestRequestDTOs:
    """Test cases for Request DTOs."""

    def test_create_document_request_creation(self):
        """Test creating create document request."""
        request = CreateDocumentRequest(
            title='Test Document',
            content='Test content',
            repository_id='repo-123',
            author='test-author',
            metadata={'tags': ['test', 'documentation']},
            version='1.0.0'
        )

        assert request.title == 'Test Document'
        assert request.content == 'Test content'
        assert request.repository_id == 'repo-123'
        assert request.author == 'test-author'
        assert request.metadata == {'tags': ['test', 'documentation']}
        assert request.version == '1.0.0'

    def test_create_document_request_validation(self):
        """Test create document request validation."""
        # Valid request
        request = CreateDocumentRequest(
            title='Valid Title',
            content='Valid content',
            repository_id='repo-123'
        )

        assert request.is_valid()

        # Invalid request - empty title
        request = CreateDocumentRequest(
            title='',
            content='Valid content',
            repository_id='repo-123'
        )

        assert not request.is_valid()

        # Invalid request - empty content
        request = CreateDocumentRequest(
            title='Valid Title',
            content='',
            repository_id='repo-123'
        )

        assert not request.is_valid()

    def test_update_document_request_creation(self):
        """Test creating update document request."""
        request = UpdateDocumentRequest(
            document_id='doc-123',
            title='Updated Title',
            content='Updated content',
            metadata={'updated': True}
        )

        assert request.document_id == 'doc-123'
        assert request.title == 'Updated Title'
        assert request.content == 'Updated content'
        assert request.metadata == {'updated': True}

    def test_delete_document_request_creation(self):
        """Test creating delete document request."""
        request = DeleteDocumentRequest(
            document_id='doc-123',
            reason='No longer needed',
            force=False
        )

        assert request.document_id == 'doc-123'
        assert request.reason == 'No longer needed'
        assert request.force is False

    def test_perform_analysis_request_creation(self):
        """Test creating perform analysis request."""
        request = PerformAnalysisRequest(
            document_id='doc-123',
            analysis_type='semantic_similarity',
            configuration={'threshold': 0.8, 'model': 'bert'},
            priority='high',
            timeout_seconds=300,
            webhook_url='https://example.com/webhook'
        )

        assert request.document_id == 'doc-123'
        assert request.analysis_type == 'semantic_similarity'
        assert request.configuration == {'threshold': 0.8, 'model': 'bert'}
        assert request.priority == 'high'
        assert request.timeout_seconds == 300
        assert request.webhook_url == 'https://example.com/webhook'

    def test_cancel_analysis_request_creation(self):
        """Test creating cancel analysis request."""
        request = CancelAnalysisRequest(
            analysis_id='analysis-123',
            reason='User requested cancellation',
            force=True
        )

        assert request.analysis_id == 'analysis-123'
        assert request.reason == 'User requested cancellation'
        assert request.force is True

    def test_get_document_request_creation(self):
        """Test creating get document request."""
        request = GetDocumentRequest(
            document_id='doc-123',
            include_metadata=True,
            include_history=False
        )

        assert request.document_id == 'doc-123'
        assert request.include_metadata is True
        assert request.include_history is False

    def test_get_documents_request_creation(self):
        """Test creating get documents request."""
        request = GetDocumentsRequest(
            repository_id='repo-123',
            status='active',
            author='john.doe',
            tags=['documentation', 'api'],
            limit=50,
            offset=0,
            sort_by='created_at',
            sort_order='desc'
        )

        assert request.repository_id == 'repo-123'
        assert request.status == 'active'
        assert request.author == 'john.doe'
        assert request.tags == ['documentation', 'api']
        assert request.limit == 50
        assert request.offset == 0
        assert request.sort_by == 'created_at'
        assert request.sort_order == 'desc'

    def test_get_analysis_request_creation(self):
        """Test creating get analysis request."""
        request = GetAnalysisRequest(
            analysis_id='analysis-123',
            include_details=True,
            include_findings=True
        )

        assert request.analysis_id == 'analysis-123'
        assert request.include_details is True
        assert request.include_findings is True

    def test_get_findings_request_creation(self):
        """Test creating get findings request."""
        request = GetFindingsRequest(
            analysis_id='analysis-123',
            document_id='doc-123',
            severity='high',
            category='security',
            status='open',
            limit=100,
            offset=0
        )

        assert request.analysis_id == 'analysis-123'
        assert request.document_id == 'doc-123'
        assert request.severity == 'high'
        assert request.category == 'security'
        assert request.status == 'open'
        assert request.limit == 100
        assert request.offset == 0


class TestResponseDTOs:
    """Test cases for Response DTOs."""

    def test_document_response_creation(self):
        """Test creating document response."""
        response = DocumentResponse(
            id='doc-123',
            title='Test Document',
            content='Test content',
            repository_id='repo-123',
            author='test-author',
            version='1.0.0',
            status='active',
            metadata={'tags': ['test']},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            word_count=100,
            file_size=1024
        )

        assert response.id == 'doc-123'
        assert response.title == 'Test Document'
        assert response.status == 'active'
        assert response.word_count == 100

    def test_document_response_from_entity(self):
        """Test creating document response from entity."""
        # Create mock document entity
        mock_document = Mock()
        mock_document.id = 'doc-123'
        mock_document.title = 'Test Document'
        mock_document.content = 'Test content'
        mock_document.repository_id = 'repo-123'
        mock_document.author = 'test-author'
        mock_document.version = '1.0.0'
        mock_document.status = DocumentStatus.ACTIVE
        mock_document.metadata = {'tags': ['test']}
        mock_document.created_at = datetime.now(timezone.utc)
        mock_document.updated_at = datetime.now(timezone.utc)

        # Create response from entity
        response = DocumentResponse.from_entity(mock_document)

        assert response.id == 'doc-123'
        assert response.title == 'Test Document'
        assert response.status == 'active'

    def test_analysis_response_creation(self):
        """Test creating analysis response."""
        response = AnalysisResponse(
            id='analysis-123',
            document_id='doc-123',
            analysis_type='semantic_similarity',
            status='completed',
            confidence=0.85,
            results={'similarity_score': 0.85},
            metadata={'model': 'bert'},
            created_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            execution_time_seconds=2.5
        )

        assert response.id == 'analysis-123'
        assert response.analysis_type == 'semantic_similarity'
        assert response.status == 'completed'
        assert response.confidence == 0.85
        assert response.execution_time_seconds == 2.5

    def test_finding_response_creation(self):
        """Test creating finding response."""
        response = FindingResponse(
            id='finding-123',
            analysis_id='analysis-123',
            document_id='doc-123',
            title='Test Finding',
            description='Test description',
            severity='medium',
            confidence=0.75,
            category='code_quality',
            location={'file': 'test.py', 'line': 42},
            recommendation='Consider refactoring',
            metadata={'rule_id': 'TEST-001'},
            created_at=datetime.now(timezone.utc),
            resolved_at=None
        )

        assert response.id == 'finding-123'
        assert response.title == 'Test Finding'
        assert response.severity == 'medium'
        assert response.confidence == 0.75

    def test_findings_list_response_creation(self):
        """Test creating findings list response."""
        findings = [
            FindingResponse(
                id='finding-1',
                analysis_id='analysis-123',
                document_id='doc-123',
                title='Finding 1',
                description='Description 1',
                severity='high',
                confidence=0.9,
                category='security'
            ),
            FindingResponse(
                id='finding-2',
                analysis_id='analysis-123',
                document_id='doc-123',
                title='Finding 2',
                description='Description 2',
                severity='medium',
                confidence=0.7,
                category='code_quality'
            )
        ]

        response = FindingsListResponse(
            findings=findings,
            total_count=2,
            limit=10,
            offset=0
        )

        assert len(response.findings) == 2
        assert response.total_count == 2
        assert response.limit == 10
        assert response.offset == 0

    def test_analysis_result_response_creation(self):
        """Test creating analysis result response."""
        document = DocumentResponse(
            id='doc-123',
            title='Test Document',
            content='Test content',
            repository_id='repo-123'
        )

        findings = [
            FindingResponse(
                id='finding-1',
                analysis_id='analysis-123',
                document_id='doc-123',
                title='Test Finding',
                description='Test description',
                severity='medium',
                confidence=0.75,
                category='code_quality'
            )
        ]

        response = AnalysisResultResponse(
            analysis_id='analysis-123',
            document=document,
            findings=findings,
            status='completed',
            execution_time_seconds=2.5,
            error_message=None
        )

        assert response.analysis_id == 'analysis-123'
        assert response.document.id == 'doc-123'
        assert len(response.findings) == 1
        assert response.status == 'completed'
        assert response.execution_time_seconds == 2.5
        assert response.error_message is None

    def test_error_response_creation(self):
        """Test creating error response."""
        response = ErrorResponse(
            error_code='VALIDATION_ERROR',
            message='Validation failed',
            details={'field': 'title', 'reason': 'required'},
            request_id='req-123',
            timestamp=datetime.now(timezone.utc)
        )

        assert response.error_code == 'VALIDATION_ERROR'
        assert response.message == 'Validation failed'
        assert response.details == {'field': 'title', 'reason': 'required'}
        assert response.request_id == 'req-123'
        assert response.timestamp is not None

    def test_success_response_creation(self):
        """Test creating success response."""
        response = SuccessResponse(
            message='Operation completed successfully',
            data={'document_id': 'doc-123'},
            request_id='req-123',
            timestamp=datetime.now(timezone.utc)
        )

        assert response.message == 'Operation completed successfully'
        assert response.data == {'document_id': 'doc-123'}
        assert response.request_id == 'req-123'
        assert response.timestamp is not None

    def test_paginated_response_creation(self):
        """Test creating paginated response."""
        items = [{'id': 'item-1'}, {'id': 'item-2'}, {'id': 'item-3'}]

        response = PaginatedResponse(
            items=items,
            total_count=100,
            limit=10,
            offset=0,
            has_more=True
        )

        assert len(response.items) == 3
        assert response.total_count == 100
        assert response.limit == 10
        assert response.offset == 0
        assert response.has_more is True


class TestDTOValidation:
    """Test validation functionality in DTOs."""

    def test_request_dto_validation(self):
        """Test request DTO validation."""
        # Test valid request
        request = CreateDocumentRequest(
            title='Valid Title',
            content='Valid content with sufficient length',
            repository_id='repo-123'
        )

        assert request.validate() == []

        # Test invalid request
        request = CreateDocumentRequest(
            title='',  # Empty title
            content='',  # Empty content
            repository_id=''  # Empty repository ID
        )

        errors = request.validate()
        assert len(errors) > 0
        assert any('title' in error.lower() for error in errors)
        assert any('content' in error.lower() for error in errors)

    def test_response_dto_serialization(self):
        """Test response DTO serialization."""
        response = DocumentResponse(
            id='doc-123',
            title='Test Document',
            content='Test content',
            repository_id='repo-123',
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Test JSON serialization
        json_data = response.to_json()
        assert isinstance(json_data, str)

        # Test dict serialization
        dict_data = response.to_dict()
        assert isinstance(dict_data, dict)
        assert dict_data['id'] == 'doc-123'
        assert dict_data['title'] == 'Test Document'

    def test_response_dto_headers(self):
        """Test response DTO HTTP headers."""
        response = SuccessResponse(
            message='Success',
            request_id='req-123'
        )

        headers = response.get_headers()
        assert isinstance(headers, dict)
        assert 'X-Request-ID' in headers
        assert headers['X-Request-ID'] == 'req-123'


class TestDTOConversion:
    """Test DTO conversion functionality."""

    def test_entity_to_dto_conversion(self):
        """Test converting domain entities to DTOs."""
        # Create mock entities
        mock_document = Mock()
        mock_document.id = 'doc-123'
        mock_document.title = 'Test Document'
        mock_document.status = DocumentStatus.ACTIVE

        mock_analysis = Mock()
        mock_analysis.id = 'analysis-123'
        mock_analysis.analysis_type = AnalysisType.SEMANTIC_SIMILARITY
        mock_analysis.status = AnalysisStatus.COMPLETED

        mock_finding = Mock()
        mock_finding.id = 'finding-123'
        mock_finding.severity = FindingSeverity.HIGH
        mock_finding.confidence = Confidence(0.9)

        # Convert to DTOs
        doc_response = DocumentResponse.from_entity(mock_document)
        analysis_response = AnalysisResponse.from_entity(mock_analysis)
        finding_response = FindingResponse.from_entity(mock_finding)

        # Assert conversions
        assert doc_response.id == 'doc-123'
        assert analysis_response.id == 'analysis-123'
        assert finding_response.id == 'finding-123'

    def test_dto_to_entity_conversion(self):
        """Test converting DTOs to domain entities."""
        # This would typically be done in command handlers
        # For testing, we verify the DTO structure is correct

        request = CreateDocumentRequest(
            title='Test Document',
            content='Test content',
            repository_id='repo-123'
        )

        # Verify DTO has all required fields for entity creation
        assert hasattr(request, 'title')
        assert hasattr(request, 'content')
        assert hasattr(request, 'repository_id')

    def test_bulk_dto_conversion(self):
        """Test bulk DTO conversion."""
        # Create multiple entities
        entities = []
        for i in range(5):
            mock_entity = Mock()
            mock_entity.id = f'entity-{i}'
            mock_entity.title = f'Title {i}'
            entities.append(mock_entity)

        # Convert to DTOs
        dtos = [DocumentResponse.from_entity(entity) for entity in entities]

        # Assert bulk conversion
        assert len(dtos) == 5
        for i, dto in enumerate(dtos):
            assert dto.id == f'entity-{i}'
            assert dto.title == f'Title {i}'


class TestDTOErrorHandling:
    """Test error handling in DTOs."""

    def test_dto_creation_with_invalid_data(self):
        """Test DTO creation with invalid data."""
        # Test with missing required fields
        with pytest.raises(ValueError):
            CreateDocumentRequest(
                title=None,  # Invalid
                content='Valid content',
                repository_id='repo-123'
            )

    def test_dto_validation_error_messages(self):
        """Test validation error messages in DTOs."""
        request = CreateDocumentRequest(
            title='',  # Invalid
            content='Valid content',
            repository_id='repo-123'
        )

        errors = request.validate()
        assert len(errors) > 0

        # Error messages should be descriptive
        for error in errors:
            assert isinstance(error, str)
            assert len(error) > 0

    def test_response_dto_error_formatting(self):
        """Test error response formatting."""
        error_response = ErrorResponse(
            error_code='VALIDATION_ERROR',
            message='Invalid input data',
            details={
                'title': 'Title is required',
                'content': 'Content must be at least 10 characters'
            }
        )

        # Test error formatting
        formatted = error_response.format_error()
        assert 'VALIDATION_ERROR' in formatted
        assert 'Invalid input data' in formatted

        # Test details inclusion
        assert 'title' in str(error_response.details)
        assert 'content' in str(error_response.details)


class TestDTOPagination:
    """Test pagination functionality in DTOs."""

    def test_paginated_response_navigation(self):
        """Test pagination navigation."""
        response = PaginatedResponse(
            items=[{'id': 'item-1'}, {'id': 'item-2'}],
            total_count=100,
            limit=10,
            offset=0
        )

        # Test pagination metadata
        assert response.has_more is True
        assert response.total_pages == 10  # 100 total / 10 limit
        assert response.current_page == 1  # offset 0 / limit 10 + 1

        # Test page navigation
        next_offset = response.get_next_offset()
        assert next_offset == 10

        prev_offset = response.get_previous_offset()
        assert prev_offset == 0  # Already at first page

    def test_pagination_edge_cases(self):
        """Test pagination edge cases."""
        # Empty result set
        response = PaginatedResponse(
            items=[],
            total_count=0,
            limit=10,
            offset=0
        )

        assert response.has_more is False
        assert response.total_pages == 0

        # Last page
        response = PaginatedResponse(
            items=[{'id': 'item-1'}],
            total_count=25,
            limit=10,
            offset=20
        )

        assert response.has_more is False  # 25 total, 20 offset + 1 item = 21
        assert response.current_page == 3  # offset 20 / limit 10 + 1

    def test_pagination_validation(self):
        """Test pagination parameter validation."""
        # Valid pagination
        response = PaginatedResponse(
            items=[],
            total_count=100,
            limit=50,
            offset=0
        )

        assert response.is_valid_pagination() is True

        # Invalid pagination - negative limit
        response = PaginatedResponse(
            items=[],
            total_count=100,
            limit=-1,
            offset=0
        )

        assert response.is_valid_pagination() is False

        # Invalid pagination - negative offset
        response = PaginatedResponse(
            items=[],
            total_count=100,
            limit=50,
            offset=-10
        )

        assert response.is_valid_pagination() is False
