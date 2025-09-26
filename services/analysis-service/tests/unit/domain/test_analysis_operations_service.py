"""Tests for Analysis Operations Domain Service"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from services.analysis_service.domain.services.analysis_operations_service import AnalysisOperationsService
from services.analysis_service.domain.entities.document import Document


class TestAnalysisOperationsService:
    """Test cases for AnalysisOperationsService."""

    @pytest.fixture
    def service(self):
        """Create analysis operations service instance."""
        return AnalysisOperationsService()

    @pytest.fixture
    def mock_document(self):
        """Create mock document for testing."""
        doc = Mock(spec=Document)
        doc.id = "test-doc-123"
        doc.title = "Test Document"
        doc.content = "This is test content for analysis."
        doc.type = "markdown"
        return doc

    @pytest.mark.asyncio
    async def test_perform_document_analysis_basic(self, service, mock_document):
        """Test basic document analysis."""
        analysis_types = ["semantic", "sentiment"]

        result = await service.perform_document_analysis(mock_document, analysis_types)

        assert result["document_id"] == "test-doc-123"
        assert "analysis_results" in result
        assert "semantic" in result["analysis_results"]
        assert "sentiment" in result["analysis_results"]
        assert result["analysis_types_performed"] == analysis_types
        assert "analysis_timestamp" in result

    @pytest.mark.asyncio
    async def test_perform_document_analysis_empty_types(self, service, mock_document):
        """Test document analysis with no analysis types."""
        result = await service.perform_document_analysis(mock_document, [])

        assert result["document_id"] == "test-doc-123"
        assert result["analysis_results"] == {}
        assert result["analysis_types_performed"] == []

    @pytest.mark.asyncio
    async def test_perform_document_analysis_single_type(self, service, mock_document):
        """Test document analysis with single analysis type."""
        analysis_types = ["tone"]

        result = await service.perform_document_analysis(mock_document, analysis_types)

        assert result["document_id"] == "test-doc-123"
        assert "tone" in result["analysis_results"]
        assert result["analysis_types_performed"] == analysis_types

    @pytest.mark.asyncio
    async def test_perform_batch_analysis(self, service, mock_document):
        """Test batch analysis of multiple documents."""
        documents = [mock_document, mock_document]  # Same doc twice for simplicity
        analysis_types = ["semantic"]

        result = await service.perform_batch_analysis(documents, analysis_types, batch_size=2)

        assert result["total_documents"] == 2
        assert result["processed_documents"] == 2
        assert result["failed_documents"] == 0
        assert len(result["results"]) == 2
        assert "batch_processing_completed" in result

    @pytest.mark.asyncio
    async def test_perform_batch_analysis_partial_failure(self, service, mock_document):
        """Test batch analysis with partial failures."""
        # Create a document that will fail
        failing_doc = Mock(spec=Document)
        failing_doc.id = "failing-doc"
        failing_doc.title = "Failing Document"
        # Don't set content to trigger an error in analysis

        documents = [mock_document, failing_doc]
        analysis_types = ["semantic"]

        # Mock the perform_document_analysis to fail for the second doc
        original_method = service.perform_document_analysis
        call_count = 0

        async def mock_perform_analysis(doc, types):
            nonlocal call_count
            call_count += 1
            if call_count == 2:  # Second call fails
                raise Exception("Analysis failed")
            return await original_method(doc, types)

        service.perform_document_analysis = mock_perform_analysis

        result = await service.perform_batch_analysis(documents, analysis_types)

        assert result["total_documents"] == 2
        assert result["processed_documents"] == 1  # Only first doc succeeds
        assert result["failed_documents"] == 1
        assert len(result["results"]) == 2

        # Check that one result is successful and one has error
        successful_results = [r for r in result["results"] if "error" not in r]
        failed_results = [r for r in result["results"] if "error" in r]

        assert len(successful_results) == 1
        assert len(failed_results) == 1
        assert failed_results[0]["error"] == "Analysis failed"

    def test_validate_analysis_request_valid(self, service):
        """Test validation of valid analysis request."""
        request_data = {
            "documents": [{"id": "doc1", "content": "test"}],
            "analysis_types": ["semantic", "sentiment"]
        }

        result = service.validate_analysis_request(request_data)

        assert result["is_valid"] == True
        assert result["errors"] == []
        assert len(result["warnings"]) == 0
        assert "validation_timestamp" in result

    def test_validate_analysis_request_missing_documents(self, service):
        """Test validation with missing documents."""
        request_data = {
            "analysis_types": ["semantic"]
        }

        result = service.validate_analysis_request(request_data)

        assert result["is_valid"] == False
        assert "documents" in str(result["errors"][0])

    def test_validate_analysis_request_missing_types(self, service):
        """Test validation with missing analysis types."""
        request_data = {
            "documents": [{"id": "doc1", "content": "test"}]
        }

        result = service.validate_analysis_request(request_data)

        assert result["is_valid"] == False
        assert "analysis_types" in str(result["errors"][0])

    def test_validate_analysis_request_invalid_type(self, service):
        """Test validation with invalid analysis type."""
        request_data = {
            "documents": [{"id": "doc1", "content": "test"}],
            "analysis_types": ["semantic", "invalid_type"]
        }

        result = service.validate_analysis_request(request_data)

        assert result["is_valid"] == True  # Still valid, just warnings
        assert len(result["warnings"]) == 1
        assert "invalid_type" in str(result["warnings"][0])

    def test_validate_analysis_request_empty_content(self, service):
        """Test validation with document having no content."""
        request_data = {
            "documents": [{"id": "doc1"}],  # No content field
            "analysis_types": ["semantic"]
        }

        result = service.validate_analysis_request(request_data)

        assert result["is_valid"] == True  # Still valid, just warnings
        assert len(result["warnings"]) == 1
        assert "content" in str(result["warnings"][0])

    def test_validate_analysis_request_invalid_document_format(self, service):
        """Test validation with invalid document format."""
        request_data = {
            "documents": ["not a dict"],  # Should be dict
            "analysis_types": ["semantic"]
        }

        result = service.validate_analysis_request(request_data)

        assert result["is_valid"] == False
        assert len(result["errors"]) == 1
        assert "dictionary" in str(result["errors"][0])
