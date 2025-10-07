"""Unit tests for value objects."""

import pytest
from domain.value_objects.event_status import EventStatus
from domain.value_objects.event_type import EventType
from domain.value_objects.job_status import JobStatus
from domain.value_objects.source_metadata import SourceMetadata


class TestEventStatus:
    """Test EventStatus enum."""
    
    def test_event_status_values(self):
        """Test EventStatus enum values."""
        assert EventStatus.PENDING.value == "pending"
        assert EventStatus.PROCESSING.value == "processing"
        assert EventStatus.COMPLETED.value == "completed"
        assert EventStatus.FAILED.value == "failed"
        assert EventStatus.SKIPPED.value == "skipped"
        assert EventStatus.CANCELLED.value == "cancelled"
        assert EventStatus.RETRYING.value == "retrying"
    
    def test_event_status_from_string(self):
        """Test creating EventStatus from string."""
        status = EventStatus("pending")
        assert status == EventStatus.PENDING
    
    def test_event_status_comparison(self):
        """Test EventStatus comparison."""
        assert EventStatus.PENDING == EventStatus.PENDING
        assert EventStatus.PENDING != EventStatus.COMPLETED


class TestEventType:
    """Test EventType enum."""
    
    def test_event_type_values(self):
        """Test EventType enum values."""
        assert EventType.DOCUMENT_CREATED.value == "document_created"
        assert EventType.DOCUMENT_UPDATED.value == "document_updated"
        assert EventType.DOCUMENT_DELETED.value == "document_deleted"
        assert EventType.BATCH_IMPORT.value == "batch_import"
        assert EventType.SYNC_REQUEST.value == "sync_request"
    
    def test_event_type_from_string(self):
        """Test creating EventType from string."""
        event_type = EventType("document_created")
        assert event_type == EventType.DOCUMENT_CREATED


class TestJobStatus:
    """Test JobStatus enum."""
    
    def test_job_status_values(self):
        """Test JobStatus enum values."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.CANCELLED.value == "cancelled"
    
    def test_job_status_from_string(self):
        """Test creating JobStatus from string."""
        status = JobStatus("running")
        assert status == JobStatus.RUNNING


class TestSourceMetadata:
    """Test SourceMetadata value object."""
    
    def test_create_source_metadata(self):
        """Test creating SourceMetadata."""
        metadata = SourceMetadata(
            source_id="github-123",
            source_type="github",
            repository="test/repo",
            branch="main",
        )
        
        assert metadata.source_id == "github-123"
        assert metadata.source_type == "github"
        assert metadata.repository == "test/repo"
        assert metadata.branch == "main"
        assert metadata.commit_sha is None
    
    def test_source_metadata_with_commit(self):
        """Test SourceMetadata with commit SHA."""
        metadata = SourceMetadata(
            source_id="github-123",
            source_type="github",
            repository="test/repo",
            branch="main",
            commit_sha="abc123",
        )
        
        assert metadata.commit_sha == "abc123"
    
    def test_source_metadata_with_url(self):
        """Test SourceMetadata with URL."""
        metadata = SourceMetadata(
            source_id="github-123",
            source_type="github",
            repository="test/repo",
            url="https://github.com/test/repo",
        )
        
        assert metadata.url == "https://github.com/test/repo"
    
    def test_source_metadata_immutable(self):
        """Test that SourceMetadata is immutable."""
        metadata = SourceMetadata(
            source_id="github-123",
            source_type="github",
            repository="test/repo",
        )
        
        # Attempt to modify should raise error (frozen dataclass)
        with pytest.raises(Exception):  # FrozenInstanceError
            metadata.source_id = "new-id"
    
    def test_source_metadata_requires_fields(self):
        """Test that SourceMetadata requires certain fields."""
        # This should work - minimum required fields
        metadata = SourceMetadata(
            source_id="test",
            source_type="github",
            repository="test/repo",
        )
        assert metadata.source_id == "test"
        
        # Missing required fields would raise TypeError at creation
        with pytest.raises(TypeError):
            SourceMetadata(source_id="test")
    
    def test_source_metadata_equality(self):
        """Test SourceMetadata equality."""
        metadata1 = SourceMetadata(
            source_id="github-123",
            source_type="github",
            repository="test/repo",
        )
        
        metadata2 = SourceMetadata(
            source_id="github-123",
            source_type="github",
            repository="test/repo",
        )
        
        metadata3 = SourceMetadata(
            source_id="github-456",
            source_type="github",
            repository="test/repo",
        )
        
        assert metadata1 == metadata2
        assert metadata1 != metadata3
    
    def test_source_metadata_with_path(self):
        """Test SourceMetadata with file path."""
        metadata = SourceMetadata(
            source_id="github-123",
            source_type="github",
            repository="test/repo",
            path="/docs/README.md",
        )
        
        assert metadata.path == "/docs/README.md"
    
    def test_source_metadata_with_author(self):
        """Test SourceMetadata with author info."""
        metadata = SourceMetadata(
            source_id="github-123",
            source_type="github",
            repository="test/repo",
            author="john@example.com",
        )
        
        assert metadata.author == "john@example.com"

