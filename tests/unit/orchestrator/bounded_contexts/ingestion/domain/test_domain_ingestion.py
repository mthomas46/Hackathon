#!/usr/bin/env python3
"""
Domain Layer Tests for Ingestion

Tests the core domain logic for document ingestion including source management, processing, and metadata extraction.
"""

import pytest
import asyncio
from datetime import datetime

from services.orchestrator.domain.ingestion.value_objects import (
    IngestionSourceType, IngestionStatus, IngestionRequest,
    IngestionResult, DocumentMetadata
)
from services.orchestrator.domain.ingestion.services import (
    IngestionOrchestratorService, DocumentProcessorService
)


class TestIngestionSourceType:
    """Test IngestionSourceType enum."""

    def test_ingestion_source_type_values(self):
        """Test ingestion source type enum values."""
        assert IngestionSourceType.GITHUB.value == "github"
        assert IngestionSourceType.JIRA.value == "jira"
        assert IngestionSourceType.FILESYSTEM.value == "filesystem"

    def test_requires_authentication_property(self):
        """Test requires_authentication property."""
        assert IngestionSourceType.GITHUB.requires_authentication is True
        assert IngestionSourceType.WEB.requires_authentication is False

    def test_supports_incremental_sync_property(self):
        """Test supports_incremental_sync property."""
        assert IngestionSourceType.GITHUB.supports_incremental_sync is True
        assert IngestionSourceType.WEB.supports_incremental_sync is False

    def test_is_version_controlled_property(self):
        """Test is_version_controlled property."""
        assert IngestionSourceType.GITHUB.is_version_controlled is True
        assert IngestionSourceType.JIRA.is_version_controlled is False

    def test_typical_content_types(self):
        """Test typical_content_types property."""
        github_types = IngestionSourceType.GITHUB.typical_content_types
        assert 'code' in github_types
        assert 'issues' in github_types

        jira_types = IngestionSourceType.JIRA.typical_content_types
        assert 'issues' in jira_types


class TestIngestionStatus:
    """Test IngestionStatus enum."""

    def test_ingestion_status_values(self):
        """Test ingestion status enum values."""
        assert IngestionStatus.PENDING.value == "pending"
        assert IngestionStatus.COMPLETED.value == "completed"
        assert IngestionStatus.FAILED.value == "failed"

    def test_is_active_property(self):
        """Test is_active property."""
        assert IngestionStatus.PROCESSING.is_active is True
        assert IngestionStatus.COMPLETED.is_active is False

    def test_is_final_property(self):
        """Test is_final property."""
        assert IngestionStatus.COMPLETED.is_final is True
        assert IngestionStatus.PROCESSING.is_final is False

    def test_is_successful_property(self):
        """Test is_successful property."""
        assert IngestionStatus.COMPLETED.is_successful is True
        assert IngestionStatus.PARTIAL_SUCCESS.is_successful is True
        assert IngestionStatus.FAILED.is_successful is False

    def test_can_retry_property(self):
        """Test can_retry property."""
        assert IngestionStatus.FAILED.can_retry is True
        assert IngestionStatus.CANCELLED.can_retry is False

    def test_progress_percentage_property(self):
        """Test progress_percentage property."""
        assert IngestionStatus.PENDING.progress_percentage == 0
        assert IngestionStatus.COMPLETED.progress_percentage == 100
        assert IngestionStatus.PROCESSING.progress_percentage == 70


class TestIngestionRequest:
    """Test IngestionRequest value object."""

    def test_create_ingestion_request(self):
        """Test creating an ingestion request."""
        request = IngestionRequest(
            source_url="https://github.com/user/repo",
            source_type=IngestionSourceType.GITHUB,
            correlation_id="corr-123",
            parameters={"depth": 2},
            priority=8,
            requested_by="user@example.com",
            tags=["important", "urgent"]
        )

        assert request.source_url == "https://github.com/user/repo"
        assert request.source_type == IngestionSourceType.GITHUB
        assert request.correlation_id == "corr-123"
        assert request.parameters == {"depth": 2}
        assert request.priority == 8
        assert request.requested_by == "user@example.com"
        assert request.tags == ["important", "urgent"]

    def test_validation(self):
        """Test request validation."""
        # Valid request
        request = IngestionRequest(
            source_url="https://example.com",
            source_type=IngestionSourceType.WEB
        )
        assert request.source_url == "https://example.com"

        # Invalid: empty source URL
        with pytest.raises(ValueError, match="Source URL cannot be empty"):
            IngestionRequest(source_url="", source_type=IngestionSourceType.WEB)

        # Invalid: long source URL
        long_url = "https://example.com/" + "x" * 2000
        with pytest.raises(ValueError, match="Source URL too long"):
            IngestionRequest(source_url=long_url, source_type=IngestionSourceType.WEB)

    def test_capability_properties(self):
        """Test capability-related properties."""
        github_request = IngestionRequest(
            source_url="https://github.com/user/repo",
            source_type=IngestionSourceType.GITHUB
        )

        assert github_request.requires_authentication is True
        assert github_request.supports_incremental_sync is True

        web_request = IngestionRequest(
            source_url="https://example.com",
            source_type=IngestionSourceType.WEB
        )

        assert web_request.requires_authentication is False
        assert web_request.supports_incremental_sync is False

    def test_to_dict(self):
        """Test converting to dictionary."""
        request = IngestionRequest(
            source_url="https://example.com",
            source_type=IngestionSourceType.WEB,
            correlation_id="corr-123"
        )

        data = request.to_dict()
        assert data["source_url"] == "https://example.com"
        assert data["source_type"] == "web"
        assert data["correlation_id"] == "corr-123"
        assert data["requires_authentication"] is False


class TestIngestionResult:
    """Test IngestionResult value object."""

    @pytest.fixture
    def sample_result_data(self):
        """Sample result data for testing."""
        return {
            'request_id': 'req-123',
            'status': IngestionStatus.COMPLETED,
            'total_items': 20,  # Increased to allow more updates
            'successful_items': 8,
            'failed_items': 1,
            'skipped_items': 1,
            'errors': [{'type': 'network', 'message': 'Connection timeout'}],
            'metadata': {'source': 'github'}
        }

    def test_create_ingestion_result(self, sample_result_data):
        """Test creating an ingestion result."""
        result = IngestionResult(**sample_result_data)

        assert result.request_id == 'req-123'
        assert result.status == IngestionStatus.COMPLETED
        assert result.total_items == 20
        assert result.successful_items == 8
        assert result.failed_items == 1
        assert result.skipped_items == 1
        assert result.processed_items == 10
        assert result.success_rate == 0.4  # 8/20 = 0.4
        assert result.is_successful is True

    def test_validation(self, sample_result_data):
        """Test result validation."""
        # Valid result
        result = IngestionResult(**sample_result_data)
        assert result.request_id == 'req-123'

        # Invalid: empty request ID
        invalid_data = sample_result_data.copy()
        invalid_data['request_id'] = ''
        with pytest.raises(ValueError, match="Request ID cannot be empty"):
            IngestionResult(**invalid_data)

        # Invalid: empty request ID
        invalid_data = sample_result_data.copy()
        invalid_data['request_id'] = ''
        with pytest.raises(ValueError, match="Request ID cannot be empty"):
            IngestionResult(**invalid_data)

    def test_update_counts(self, sample_result_data):
        """Test updating item counts."""
        result = IngestionResult(**sample_result_data)

        # Initially: 8 successful, 1 failed, 1 skipped, total_items = 20
        assert result.successful_items == 8
        assert result.processed_items == 10

        # Add 2 successful items (should succeed, total processed = 12, within total)
        result.update_counts(successful=2)
        assert result.successful_items == 10  # 8 + 2 = 10
        assert result.processed_items == 12  # 10 + 1 + 1 = 12

        # Add failed items
        result.update_counts(failed=1)
        assert result.failed_items == 2

    def test_mark_completed(self, sample_result_data):
        """Test marking result as completed."""
        result = IngestionResult(**sample_result_data)
        result.mark_started()

        assert result.started_at is not None

        result.mark_completed(IngestionStatus.COMPLETED)

        assert result.completed_at is not None
        assert result.status == IngestionStatus.COMPLETED
        assert result.duration_seconds is not None

    def test_to_dict(self, sample_result_data):
        """Test converting to dictionary."""
        result = IngestionResult(**sample_result_data)

        data = result.to_dict()
        assert data['request_id'] == 'req-123'
        assert data['status'] == 'completed'
        assert data['total_items'] == 20
        assert data['successful_items'] == 8
        assert data['success_rate'] == 0.4
        assert data['is_successful'] is True


class TestDocumentMetadata:
    """Test DocumentMetadata value object."""

    @pytest.fixture
    def sample_metadata_data(self):
        """Sample metadata data for testing."""
        return {
            'document_id': 'doc-123',
            'source_url': 'https://github.com/user/repo/README.md',
            'title': 'Project README',
            'content_type': 'text/markdown',
            'file_size': 2048,
            'checksum': 'abc123',
            'author': 'user@example.com',
            'tags': ['documentation', 'readme'],
            'custom_metadata': {'version': '1.0'}
        }

    def test_create_document_metadata(self, sample_metadata_data):
        """Test creating document metadata."""
        metadata = DocumentMetadata(**sample_metadata_data)

        assert metadata.document_id == 'doc-123'
        assert metadata.source_url == 'https://github.com/user/repo/README.md'
        assert metadata.title == 'Project README'
        assert metadata.content_type == 'text/markdown'
        assert metadata.file_size == 2048
        assert metadata.checksum == 'abc123'
        assert metadata.author == 'user@example.com'
        assert metadata.tags == ['documentation', 'readme']

    def test_validation(self, sample_metadata_data):
        """Test metadata validation."""
        # Valid metadata
        metadata = DocumentMetadata(**sample_metadata_data)
        assert metadata.document_id == 'doc-123'

        # Invalid: empty document ID
        invalid_data = sample_metadata_data.copy()
        invalid_data['document_id'] = ''
        with pytest.raises(ValueError, match="Document ID cannot be empty"):
            DocumentMetadata(**invalid_data)

        # Invalid: long document ID
        invalid_data = sample_metadata_data.copy()
        invalid_data['document_id'] = 'x' * 256
        with pytest.raises(ValueError, match="Document ID too long"):
            DocumentMetadata(**invalid_data)

    def test_calculated_properties(self, sample_metadata_data):
        """Test calculated properties."""
        metadata = DocumentMetadata(**sample_metadata_data)

        assert metadata.file_size_mb is not None
        assert metadata.file_size_mb < 1  # 2048 bytes is less than 1 MB
        assert metadata.has_tags is True
        assert metadata.has_custom_metadata is True

        # Test tag operations
        metadata.add_tag('new_tag')
        assert 'new_tag' in metadata.tags

        metadata.remove_tag('readme')
        assert 'readme' not in metadata.tags

    def test_custom_metadata_operations(self, sample_metadata_data):
        """Test custom metadata operations."""
        metadata = DocumentMetadata(**sample_metadata_data)

        # Set custom metadata
        metadata.set_custom_metadata('processing_time', 2.5)
        assert metadata.get_custom_metadata('processing_time') == 2.5

        # Get with default
        assert metadata.get_custom_metadata('missing_key', 'default') == 'default'

    def test_to_dict(self, sample_metadata_data):
        """Test converting to dictionary."""
        metadata = DocumentMetadata(**sample_metadata_data)

        data = metadata.to_dict()
        assert data['document_id'] == 'doc-123'
        assert data['title'] == 'Project README'
        assert data['content_type'] == 'text/markdown'
        assert data['file_size'] == 2048
        assert data['tags'] == ['documentation', 'readme']
        assert data['has_tags'] is True


class TestIngestionOrchestratorService:
    """Test IngestionOrchestratorService domain service."""

    @pytest.fixture
    def orchestrator_service(self):
        """Create ingestion orchestrator service for testing."""
        return IngestionOrchestratorService()

    def test_create_ingestion_request(self, orchestrator_service):
        """Test creating an ingestion request."""
        request = orchestrator_service.create_ingestion_request(
            source_url="https://github.com/user/repo",
            source_type=IngestionSourceType.GITHUB,
            correlation_id="corr-123",
            parameters={"depth": 2},
            priority=8,
            tags=["important"]
        )

        assert request.source_url == "https://github.com/user/repo"
        assert request.source_type == IngestionSourceType.GITHUB
        assert request.correlation_id == "corr-123"
        assert request.parameters == {"depth": 2}
        assert request.priority == 8
        assert request.tags == ["important"]

    @pytest.mark.asyncio
    async def test_start_ingestion(self, orchestrator_service):
        """Test starting an ingestion process."""
        request = orchestrator_service.create_ingestion_request(
            source_url="https://github.com/user/repo",
            source_type=IngestionSourceType.GITHUB
        )

        result = await orchestrator_service.start_ingestion(request)

        assert result.request_id == request.request_id
        assert result.status == IngestionStatus.QUEUED
        assert result.ingestion_id is not None

        # Wait a bit for processing to complete
        await asyncio.sleep(0.8)

        # Check final status
        final_result = orchestrator_service.get_ingestion_status(result.ingestion_id)
        assert final_result is not None
        assert final_result.is_complete
        assert final_result.status in [IngestionStatus.COMPLETED, IngestionStatus.PARTIAL_SUCCESS]

    @pytest.mark.asyncio
    async def test_get_ingestion_status(self, orchestrator_service):
        """Test getting ingestion status."""
        # Initially no ingestions
        status = orchestrator_service.get_ingestion_status("nonexistent")
        assert status is None

        # After starting ingestion
        request = orchestrator_service.create_ingestion_request(
            source_url="https://example.com",
            source_type=IngestionSourceType.WEB
        )

        # Start ingestion
        result = await orchestrator_service.start_ingestion(request)

        # Should have the ingestion in active state
        status = orchestrator_service.get_ingestion_status(result.ingestion_id)
        assert status is not None
        assert status.status == IngestionStatus.QUEUED

    def test_cancel_ingestion(self, orchestrator_service):
        """Test cancelling an ingestion."""
        request = orchestrator_service.create_ingestion_request(
            source_url="https://example.com",
            source_type=IngestionSourceType.WEB
        )

        # Start ingestion
        import asyncio
        result = asyncio.run(orchestrator_service.start_ingestion(request))

        # Cancel immediately
        cancelled = orchestrator_service.cancel_ingestion(result.ingestion_id)
        assert cancelled is True

        # Check status
        final_result = orchestrator_service.get_ingestion_status(result.ingestion_id)
        assert final_result.status == IngestionStatus.CANCELLED

    def test_get_ingestion_stats(self, orchestrator_service):
        """Test getting ingestion statistics."""
        stats = orchestrator_service.get_ingestion_stats()

        # Should have basic structure even with no ingestions
        assert 'active_ingestions' in stats
        assert 'completed_ingestions' in stats
        assert 'total_ingestions' in stats
        assert stats['active_ingestions'] >= 0
        assert stats['completed_ingestions'] >= 0


class TestDocumentProcessorService:
    """Test DocumentProcessorService domain service."""

    @pytest.fixture
    def processor_service(self):
        """Create document processor service for testing."""
        return DocumentProcessorService()

    def test_extract_metadata_text(self, processor_service):
        """Test extracting metadata from text content."""
        content = b"# Project Title\n\nThis is a project description."
        metadata = processor_service.extract_metadata(
            document_id="doc-123",
            source_url="https://github.com/user/repo/README.md",
            raw_content=content,
            source_type=IngestionSourceType.GITHUB
        )

        assert metadata.document_id == "doc-123"
        assert metadata.source_url == "https://github.com/user/repo/README.md"
        assert metadata.content_type == "text/markdown"
        assert metadata.file_size == len(content)
        assert metadata.checksum is not None
        assert len(metadata.tags) > 0

    def test_extract_metadata_html(self, processor_service):
        """Test extracting metadata from HTML content."""
        content = b"<html><head><title>Test Document</title></head><body>Content</body></html>"
        metadata = processor_service.extract_metadata(
            document_id="doc-456",
            source_url="https://example.com/page.html",
            raw_content=content,
            source_type=IngestionSourceType.WEB
        )

        assert metadata.content_type == "text/html"
        assert metadata.title == "Test Document"

    def test_validate_document(self, processor_service):
        """Test document validation."""
        content = b"Sample content"
        metadata = processor_service.extract_metadata(
            document_id="doc-123",
            source_url="https://example.com/doc.txt",
            raw_content=content,
            source_type=IngestionSourceType.WEB
        )

        validation = processor_service.validate_document(metadata, content)

        assert validation['valid'] is True
        assert len(validation['issues']) == 0

    def test_enrich_metadata(self, processor_service):
        """Test metadata enrichment."""
        metadata = processor_service.extract_metadata(
            document_id="doc-123",
            source_url="https://example.com/doc.txt",
            raw_content=b"content",
            source_type=IngestionSourceType.WEB
        )

        enriched = processor_service.enrich_metadata(metadata, {
            'tags': ['enriched'],
            'processing_info': {'step': 'completed'}
        })

        assert 'enriched' in enriched.tags
        assert enriched.get_custom_metadata('processing') == {'step': 'completed'}

    def test_categorize_document(self, processor_service):
        """Test document categorization."""
        # GitHub document
        github_metadata = processor_service.extract_metadata(
            document_id="doc-123",
            source_url="https://github.com/user/repo/README.md",
            raw_content=b"# README",
            source_type=IngestionSourceType.GITHUB
        )

        category = processor_service.categorize_document(github_metadata)

        assert 'primary_category' in category
        assert 'all_categories' in category
        assert 'confidence' in category
        assert category['confidence'] > 0
