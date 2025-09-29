"""Unit tests for source-agent application use cases."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from services.source-agent.application.use_cases.fetch_document_use_case import (
    FetchDocumentUseCase,
    FetchDocumentRequest,
    FetchDocumentResponse
)


class TestFetchDocumentUseCase:
    """Test cases for FetchDocumentUseCase."""

    @pytest.fixture
    def fetch_document_use_case(self):
        """Create FetchDocumentUseCase instance for testing."""
        # Mock dependencies
        mock_fetch_handler = Mock()
        mock_intelligent_ingestion_service = Mock()

        use_case = FetchDocumentUseCase(
            fetch_handler=mock_fetch_handler,
            intelligent_ingestion_service=mock_intelligent_ingestion_service
        )

        return use_case

    @pytest.fixture
    def sample_request(self):
        """Create a sample fetch document request."""
        return FetchDocumentRequest(
            source_type="github",
            source_id="myorg/myrepo",
            scope={"branch": "main", "include_patterns": ["*.md"]},
            include_metadata=True,
            timeout_seconds=300
        )

    def test_use_case_initialization(self, fetch_document_use_case):
        """Test use case initialization."""
        assert fetch_document_use_case is not None
        assert hasattr(fetch_document_use_case, 'execute')

    @pytest.mark.asyncio
    async def test_successful_document_fetch(self, fetch_document_use_case, sample_request):
        """Test successful document fetching."""
        # Mock the fetch handler to return documents
        mock_documents = [
            {
                "id": "doc1",
                "title": "README",
                "content": "# My Project\nThis is a test project.",
                "metadata": {"author": "test@example.com"},
                "tags": ["documentation"]
            }
        ]

        fetch_document_use_case._fetch_handler.fetch_documents = AsyncMock(return_value=mock_documents)
        fetch_document_use_case._intelligent_ingestion_service.process_documents = AsyncMock(return_value=mock_documents)

        response = await fetch_document_use_case.execute(sample_request)

        assert response.success is True
        assert len(response.documents) == 1
        assert response.documents[0].title == "README"
        assert response.ingestion_result.documents_processed == 1
        assert response.message.startswith("Successfully fetched")

    @pytest.mark.asyncio
    async def test_document_fetch_with_processing_failure(self, fetch_document_use_case, sample_request):
        """Test document fetching with intelligent processing failure."""
        mock_documents = [{"id": "doc1", "title": "Test", "content": "Content"}]

        fetch_document_use_case._fetch_handler.fetch_documents = AsyncMock(return_value=mock_documents)
        fetch_document_use_case._intelligent_ingestion_service.process_documents = AsyncMock(
            side_effect=Exception("Processing failed")
        )

        response = await fetch_document_use_case.execute(sample_request)

        # Should still succeed but with warning
        assert response.success is True
        assert len(response.documents) == 1
        assert "Processing failed" in response.ingestion_result.warnings[0]

    @pytest.mark.asyncio
    async def test_document_fetch_handler_failure(self, fetch_document_use_case, sample_request):
        """Test document fetching when fetch handler fails."""
        fetch_document_use_case._fetch_handler.fetch_documents = AsyncMock(
            side_effect=Exception("Network timeout")
        )

        response = await fetch_document_use_case.execute(sample_request)

        assert response.success is False
        assert len(response.documents) == 0
        assert response.message == "Failed to fetch documents: Network timeout"
        assert response.ingestion_result.status == "failed"

    @pytest.mark.asyncio
    async def test_document_entity_creation_failure(self, fetch_document_use_case, sample_request):
        """Test document fetching with invalid document data."""
        # Mock documents with invalid data
        mock_documents = [
            {
                "id": "invalid_doc",
                "title": "",  # Invalid: empty title
                "content": "Some content"
            }
        ]

        fetch_document_use_case._fetch_handler.fetch_documents = AsyncMock(return_value=mock_documents)
        fetch_document_use_case._intelligent_ingestion_service.process_documents = AsyncMock(return_value=[])

        response = await fetch_document_use_case.execute(sample_request)

        # Should succeed but with failure recorded
        assert response.success is True
        assert len(response.documents) == 0  # No valid documents created
        assert response.ingestion_result.documents_failed == 1

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure_documents(self, fetch_document_use_case, sample_request):
        """Test document fetching with mix of valid and invalid documents."""
        mock_documents = [
            {
                "id": "valid_doc",
                "title": "Valid Document",
                "content": "Valid content"
            },
            {
                "id": "invalid_doc",
                "title": "",  # Invalid
                "content": "Some content"
            },
            {
                "id": "another_valid",
                "title": "Another Valid",
                "content": "More content"
            }
        ]

        fetch_document_use_case._fetch_handler.fetch_documents = AsyncMock(return_value=mock_documents)
        # Only return valid documents after processing
        valid_docs = [mock_documents[0], mock_documents[2]]
        fetch_document_use_case._intelligent_ingestion_service.process_documents = AsyncMock(return_value=valid_docs)

        response = await fetch_document_use_case.execute(sample_request)

        assert response.success is True
        assert len(response.documents) == 2
        assert response.ingestion_result.documents_processed == 3
        assert response.ingestion_result.documents_succeeded == 2
        assert response.ingestion_result.documents_failed == 1

    def test_request_validation(self, sample_request):
        """Test request validation."""
        # Valid request
        assert sample_request.source_type == "github"
        assert sample_request.include_metadata is True

        # Test request with minimal data
        minimal_request = FetchDocumentRequest(
            source_type="github",
            source_id="test/repo"
        )

        assert minimal_request.scope is None
        assert minimal_request.include_metadata is True  # Default value

    @pytest.mark.asyncio
    async def test_performance_monitoring(self, fetch_document_use_case, sample_request):
        """Test performance monitoring in use case execution."""
        mock_documents = [{"id": "doc1", "title": "Test", "content": "Content"}]

        fetch_document_use_case._fetch_handler.fetch_documents = AsyncMock(return_value=mock_documents)
        fetch_document_use_case._intelligent_ingestion_service.process_documents = AsyncMock(return_value=mock_documents)

        response = await fetch_document_use_case.execute(sample_request)

        # Check that timing information is captured
        assert response.processing_time_seconds >= 0
        assert response.ingestion_result.processing_time_seconds >= 0
        assert response.ingestion_result.duration_seconds is not None

    @pytest.mark.asyncio
    async def test_empty_document_list(self, fetch_document_use_case, sample_request):
        """Test handling of empty document lists."""
        fetch_document_use_case._fetch_handler.fetch_documents = AsyncMock(return_value=[])
        fetch_document_use_case._intelligent_ingestion_service.process_documents = AsyncMock(return_value=[])

        response = await fetch_document_use_case.execute(sample_request)

        assert response.success is True
        assert len(response.documents) == 0
        assert response.ingestion_result.documents_processed == 0
        assert "0 documents" in response.message

    def test_response_structure(self):
        """Test response structure and data types."""
        response = FetchDocumentResponse(
            success=True,
            documents=[],
            ingestion_result=Mock(),
            message="Test message",
            processing_time_seconds=1.5
        )

        assert response.success is True
        assert isinstance(response.documents, list)
        assert response.processing_time_seconds == 1.5
        assert response.message == "Test message"

    @pytest.mark.asyncio
    async def test_error_propagation(self, fetch_document_use_case, sample_request):
        """Test that errors are properly propagated and handled."""
        # Test various error scenarios
        error_scenarios = [
            ("Connection timeout", "Network error"),
            ("Authentication failed", "Auth error"),
            ("Rate limit exceeded", "Rate limit error"),
            ("Invalid source", "Validation error")
        ]

        for error_msg, error_type in error_scenarios:
            fetch_document_use_case._fetch_handler.fetch_documents = AsyncMock(
                side_effect=Exception(error_msg)
            )

            response = await fetch_document_use_case.execute(sample_request)

            assert response.success is False
            assert error_msg in response.message
            assert response.ingestion_result.status == "failed"

    @pytest.mark.asyncio
    async def test_metadata_handling(self, fetch_document_use_case, sample_request):
        """Test metadata inclusion and processing."""
        # Request with metadata inclusion
        request_with_metadata = FetchDocumentRequest(
            source_type="github",
            source_id="test/repo",
            include_metadata=True
        )

        mock_documents = [{
            "id": "doc1",
            "title": "Test Doc",
            "content": "Content",
            "metadata": {"author": "test@example.com", "created": "2023-01-01"}
        }]

        fetch_document_use_case._fetch_handler.fetch_documents = AsyncMock(return_value=mock_documents)
        fetch_document_use_case._intelligent_ingestion_service.process_documents = AsyncMock(return_value=mock_documents)

        response = await fetch_document_use_case.execute(request_with_metadata)

        assert response.success is True
        assert len(response.documents) == 1
        # Metadata should be preserved in the document entity
