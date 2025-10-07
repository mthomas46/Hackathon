"""Unit tests for ingestion domain events."""

import pytest
from datetime import datetime, timezone
from domain.events.ingestion_events import (
    DocumentIngested,
    IngestionFailed,
    JobStarted,
    JobCompleted,
    JobFailed,
)


class TestDocumentIngested:
    """Test DocumentIngested event."""
    
    def test_create_document_ingested_event(self):
        """Test creating DocumentIngested event."""
        event = DocumentIngested(
            event_id="evt-123",
            document_id="doc-456",
            source_type="github",
        )
        
        assert event.event_id == "evt-123"
        assert event.document_id == "doc-456"
        assert event.source_type == "github"
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
    
    def test_document_ingested_with_metadata(self):
        """Test DocumentIngested with metadata."""
        metadata = {"repo": "test/repo", "branch": "main"}
        event = DocumentIngested(
            event_id="evt-123",
            document_id="doc-456",
            source_type="github",
            metadata=metadata,
        )
        
        assert event.metadata == metadata
        assert event.metadata["repo"] == "test/repo"
    
    def test_document_ingested_to_dict(self):
        """Test converting to dictionary."""
        event = DocumentIngested(
            event_id="evt-123",
            document_id="doc-456",
            source_type="github",
        )
        
        data = event.to_dict()
        
        assert data["event_id"] == "evt-123"
        assert data["document_id"] == "doc-456"
        assert data["source_type"] == "github"
        assert "timestamp" in data


class TestIngestionFailed:
    """Test IngestionFailed event."""
    
    def test_create_ingestion_failed_event(self):
        """Test creating IngestionFailed event."""
        event = IngestionFailed(
            event_id="evt-123",
            document_id="doc-456",
            error_message="Connection timeout",
        )
        
        assert event.event_id == "evt-123"
        assert event.document_id == "doc-456"
        assert event.error_message == "Connection timeout"
        assert event.timestamp is not None
    
    def test_ingestion_failed_with_retry_count(self):
        """Test IngestionFailed with retry count."""
        event = IngestionFailed(
            event_id="evt-123",
            document_id="doc-456",
            error_message="Connection timeout",
            retry_count=3,
        )
        
        assert event.retry_count == 3
    
    def test_ingestion_failed_to_dict(self):
        """Test converting to dictionary."""
        event = IngestionFailed(
            event_id="evt-123",
            document_id="doc-456",
            error_message="Connection timeout",
        )
        
        data = event.to_dict()
        
        assert data["event_id"] == "evt-123"
        assert data["error_message"] == "Connection timeout"


class TestJobStarted:
    """Test JobStarted event."""
    
    def test_create_job_started_event(self):
        """Test creating JobStarted event."""
        event = JobStarted(
            job_id="job-123",
            source_type="github",
        )
        
        assert event.job_id == "job-123"
        assert event.source_type == "github"
        assert event.timestamp is not None
    
    def test_job_started_with_config(self):
        """Test JobStarted with configuration."""
        config = {"repo": "test/repo", "branch": "main"}
        event = JobStarted(
            job_id="job-123",
            source_type="github",
            source_config=config,
        )
        
        assert event.source_config == config
    
    def test_job_started_to_dict(self):
        """Test converting to dictionary."""
        event = JobStarted(
            job_id="job-123",
            source_type="github",
        )
        
        data = event.to_dict()
        
        assert data["job_id"] == "job-123"
        assert data["source_type"] == "github"


class TestJobCompleted:
    """Test JobCompleted event."""
    
    def test_create_job_completed_event(self):
        """Test creating JobCompleted event."""
        event = JobCompleted(
            job_id="job-123",
            total_events=100,
            processed_events=95,
            failed_events=5,
        )
        
        assert event.job_id == "job-123"
        assert event.total_events == 100
        assert event.processed_events == 95
        assert event.failed_events == 5
        assert event.timestamp is not None
    
    def test_job_completed_with_duration(self):
        """Test JobCompleted with duration."""
        event = JobCompleted(
            job_id="job-123",
            total_events=100,
            processed_events=100,
            failed_events=0,
            duration_seconds=45.5,
        )
        
        assert event.duration_seconds == 45.5
    
    def test_job_completed_to_dict(self):
        """Test converting to dictionary."""
        event = JobCompleted(
            job_id="job-123",
            total_events=100,
            processed_events=95,
            failed_events=5,
        )
        
        data = event.to_dict()
        
        assert data["job_id"] == "job-123"
        assert data["total_events"] == 100
        assert data["processed_events"] == 95


class TestJobFailed:
    """Test JobFailed event."""
    
    def test_create_job_failed_event(self):
        """Test creating JobFailed event."""
        event = JobFailed(
            job_id="job-123",
            error_message="Connection failed",
        )
        
        assert event.job_id == "job-123"
        assert event.error_message == "Connection failed"
        assert event.timestamp is not None
    
    def test_job_failed_with_partial_completion(self):
        """Test JobFailed with partial completion."""
        event = JobFailed(
            job_id="job-123",
            error_message="Connection failed",
            processed_events=50,
            total_events=100,
        )
        
        assert event.processed_events == 50
        assert event.total_events == 100
    
    def test_job_failed_to_dict(self):
        """Test converting to dictionary."""
        event = JobFailed(
            job_id="job-123",
            error_message="Connection failed",
        )
        
        data = event.to_dict()
        
        assert data["job_id"] == "job-123"
        assert data["error_message"] == "Connection failed"

