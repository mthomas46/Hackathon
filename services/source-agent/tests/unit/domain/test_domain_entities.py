"""Unit tests for source-agent domain entities."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock

from services.source_agent.domain.entities import Document, Source, IngestionResult


class TestDocument:
    """Test cases for Document entity."""

    def test_document_creation(self):
        """Test basic Document creation."""
        doc = Document(
            source_type="github",
            source_id="repo/docs",
            title="Test Document",
            content="This is test content",
            metadata={"author": "test@example.com"},
            tags=["test", "documentation"]
        )

        assert doc.source_type == "github"
        assert doc.source_id == "repo/docs"
        assert doc.title == "Test Document"
        assert doc.content == "This is test content"
        assert doc.metadata["author"] == "test@example.com"
        assert "test" in doc.tags
        assert doc.status == "active"
        assert isinstance(doc.created_at, datetime)

    def test_document_validation(self):
        """Test document validation rules."""
        # Valid document
        valid_doc = Document(
            source_type="github",
            source_id="repo/docs",
            title="Valid Document",
            content="Valid content"
        )
        assert valid_doc.source_type == "github"

        # Invalid source type
        with pytest.raises(ValueError):
            Document(
                source_type="invalid_source",
                source_id="repo/docs",
                title="Invalid Document",
                content="Content"
            )

        # Empty title
        with pytest.raises(ValueError):
            Document(
                source_type="github",
                source_id="repo/docs",
                title="",
                content="Content"
            )

    def test_document_content_operations(self):
        """Test document content operations."""
        doc = Document(
            source_type="github",
            source_id="repo/docs",
            title="Test Document",
            content="Original content",
            tags=["original"]
        )

        # Update content
        doc.update_content("Updated content", {"version": "2.0"})
        assert doc.content == "Updated content"
        assert doc.metadata["version"] == "2.0"
        assert doc.updated_at > doc.created_at

        # Add tags
        doc.add_tag("updated")
        assert "updated" in doc.tags

        # Remove tags
        doc.remove_tag("original")
        assert "original" not in doc.tags

    def test_document_status_transitions(self):
        """Test document status transitions."""
        doc = Document(
            source_type="github",
            source_id="repo/docs",
            title="Test Document",
            content="Content"
        )

        assert doc.status == "active"

        doc.mark_as_archived()
        assert doc.status == "archived"

        doc.mark_as_deleted()
        assert doc.status == "deleted"

    def test_document_properties(self):
        """Test document computed properties."""
        recent_doc = Document(
            source_type="github",
            source_id="repo/docs",
            title="Recent Document",
            content="Content",
            fetched_at=datetime.now(timezone.utc) - timedelta(minutes=30)
        )

        old_doc = Document(
            source_type="github",
            source_id="repo/docs",
            title="Old Document",
            content="Content",
            fetched_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )

        assert recent_doc.is_recent is True
        assert old_doc.is_recent is False
        assert recent_doc.content_length == len(recent_doc.content)
        assert recent_doc.has_metadata is False  # No metadata provided


class TestSource:
    """Test cases for Source entity."""

    def test_source_creation(self):
        """Test basic Source creation."""
        source = Source(
            name="GitHub Main",
            type="github",
            base_url="https://api.github.com",
            credentials={"token": "secret"},
            configuration={"timeout": 30}
        )

        assert source.name == "GitHub Main"
        assert source.type == "github"
        assert source.base_url == "https://api.github.com"
        assert source.is_active is True
        assert source.sync_status == "never_synced"

    def test_source_validation(self):
        """Test source validation rules."""
        # Valid source
        valid_source = Source(
            name="Valid Source",
            type="github",
            base_url="https://api.github.com"
        )
        assert valid_source.name == "Valid Source"

        # Invalid type
        with pytest.raises(ValueError):
            Source(
                name="Invalid Source",
                type="invalid_type",
                base_url="https://example.com"
            )

        # Invalid URL
        with pytest.raises(ValueError):
            Source(
                name="Invalid URL",
                type="filesystem",
                base_url="not-a-url"
            )

    def test_source_connection_string(self):
        """Test source connection string generation."""
        github_source = Source(
            name="GitHub",
            type="github",
            base_url="https://api.github.com"
        )
        assert github_source.get_connection_string() == "https://api.github.com"

        filesystem_source = Source(
            name="Local Files",
            type="filesystem",
            base_url="/data/docs"
        )
        assert filesystem_source.get_connection_string() == "file:///data/docs"

    def test_source_sync_operations(self):
        """Test source synchronization operations."""
        source = Source(
            name="Test Source",
            type="github",
            base_url="https://api.github.com"
        )

        # Initial state
        assert source.sync_status == "never_synced"
        assert source.last_sync_at is None

        # Update sync status
        source.update_sync_status("synced")
        assert source.sync_status == "synced"
        assert source.last_sync_at is not None

        # Update with error
        source.update_sync_status("failed", "Connection timeout")
        assert source.sync_status == "failed"
        assert source.error_message == "Connection timeout"

    def test_source_activation(self):
        """Test source activation/deactivation."""
        source = Source(
            name="Test Source",
            type="github",
            base_url="https://api.github.com"
        )

        assert source.is_active is True

        source.deactivate()
        assert source.is_active is False

        source.activate()
        assert source.is_active is True

    def test_source_sync_due_check(self):
        """Test sync due checking."""
        recent_sync = Source(
            name="Recent Sync",
            type="github",
            base_url="https://api.github.com",
            last_sync_at=datetime.now(timezone.utc) - timedelta(minutes=10)
        )

        old_sync = Source(
            name="Old Sync",
            type="github",
            base_url="https://api.github.com",
            last_sync_at=datetime.now(timezone.utc) - timedelta(hours=2)
        )

        assert recent_sync.is_due_for_sync is False  # Less than 15 minutes
        assert old_sync.is_due_for_sync is True     # More than 15 minutes


class TestIngestionResult:
    """Test cases for IngestionResult entity."""

    def test_ingestion_result_creation(self):
        """Test basic IngestionResult creation."""
        result = IngestionResult(
            source_id="repo/docs",
            source_type="github",
            operation_type="fetch"
        )

        assert result.source_id == "repo/docs"
        assert result.source_type == "github"
        assert result.operation_type == "fetch"
        assert result.status == "running"
        assert result.documents_processed == 0
        assert result.documents_succeeded == 0
        assert result.documents_failed == 0

    def test_ingestion_result_validation(self):
        """Test ingestion result validation."""
        # Valid result
        valid_result = IngestionResult(
            source_id="valid",
            source_type="github",
            operation_type="fetch"
        )
        assert valid_result.operation_type == "fetch"

        # Invalid operation type
        with pytest.raises(ValueError):
            IngestionResult(
                source_id="invalid",
                source_type="github",
                operation_type="invalid_op"
            )

    def test_ingestion_result_operations(self):
        """Test ingestion result operations tracking."""
        result = IngestionResult(
            source_id="test",
            source_type="github",
            operation_type="fetch"
        )

        # Record successes
        result.record_success("doc1", 1024)
        result.record_success("doc2", 2048)

        assert result.documents_processed == 2
        assert result.documents_succeeded == 2
        assert result.documents_failed == 0
        assert result.bytes_processed == 3072

        # Record failure
        result.record_failure("doc3", "Parse error", 512)

        assert result.documents_processed == 3
        assert result.documents_succeeded == 2
        assert result.documents_failed == 1
        assert result.has_failures is True

    def test_ingestion_result_completion(self):
        """Test ingestion result completion."""
        result = IngestionResult(
            source_id="test",
            source_type="github",
            operation_type="fetch",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=5)
        )

        # Complete successfully
        result.complete_successfully()

        assert result.status == "completed"
        assert result.completed_at is not None
        assert result.is_complete is True
        assert result.is_successful is True

        # Test with failures
        result.record_failure("doc1", "Error")
        result.complete_successfully()
        assert result.status == "partial_success"

    def test_ingestion_result_metrics(self):
        """Test ingestion result metrics calculation."""
        result = IngestionResult(
            source_id="test",
            source_type="github",
            operation_type="fetch"
        )

        # Add some results
        result.record_success("doc1")
        result.record_success("doc2")
        result.record_failure("doc3")

        assert result.success_rate == 66.67  # 2/3 * 100
        assert result.has_failures is True

        # Test duration
        result.started_at = datetime.now(timezone.utc) - timedelta(seconds=30)
        result.completed_at = datetime.now(timezone.utc)
        assert result.duration_seconds == 30.0

    def test_ingestion_result_summary(self):
        """Test ingestion result summary generation."""
        result = IngestionResult(
            source_id="test-repo",
            source_type="github",
            operation_type="fetch"
        )

        result.record_success("doc1", 1000)
        result.record_success("doc2", 2000)
        result.complete_successfully()

        summary = result.get_summary()

        assert summary["operation_type"] == "fetch"
        assert summary["documents_processed"] == 2
        assert summary["documents_succeeded"] == 2
        assert summary["bytes_processed"] == 3000
        assert summary["success"] is True
