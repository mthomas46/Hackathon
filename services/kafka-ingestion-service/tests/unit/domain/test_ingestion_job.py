"""Unit tests for IngestionJob entity."""

import pytest
from datetime import datetime, timezone
from domain.entities.ingestion_job import IngestionJob
from domain.value_objects.job_status import JobStatus


class TestIngestionJob:
    """Test IngestionJob entity."""
    
    def test_create_ingestion_job(self):
        """Test creating an ingestion job."""
        job = IngestionJob(
            source_type="github",
            source_config={"repo": "test/repo"},
            target_collection="docs",
        )
        
        assert job.job_id is not None
        assert job.source_type == "github"
        assert job.status == JobStatus.PENDING
        assert job.progress == 0
        assert job.total_events == 0
        assert job.processed_events == 0
        assert job.failed_events == 0
    
    def test_start_job(self):
        """Test starting a job."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        job.start()
        
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None
        assert job.progress == 0
    
    def test_complete_job(self):
        """Test completing a job."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        job.start()
        job.complete()
        
        assert job.status == JobStatus.COMPLETED
        assert job.completed_at is not None
        assert job.progress == 100
        assert job.duration_seconds is not None
        assert job.duration_seconds >= 0
    
    def test_fail_job(self):
        """Test failing a job."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        job.start()
        job.fail("Connection error")
        
        assert job.status == JobStatus.FAILED
        assert job.completed_at is not None
        assert "Connection error" in job.errors
        assert job.duration_seconds is not None
    
    def test_update_progress(self):
        """Test updating job progress."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        job.update_progress(50)
        assert job.progress == 50
        
        job.update_progress(100)
        assert job.progress == 100
    
    def test_invalid_progress_raises_error(self):
        """Test that invalid progress raises ValueError."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            job.update_progress(150)
        
        with pytest.raises(ValueError, match="Progress must be between 0 and 100"):
            job.update_progress(-10)
    
    def test_increment_total(self):
        """Test incrementing total events."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        job.increment_total()
        assert job.total_events == 1
        
        job.increment_total()
        assert job.total_events == 2
    
    def test_increment_processed(self):
        """Test incrementing processed events."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        job.increment_processed()
        assert job.processed_events == 1
        
        job.increment_processed()
        assert job.processed_events == 2
    
    def test_increment_failed(self):
        """Test incrementing failed events."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        job.increment_failed()
        assert job.failed_events == 1
        
        job.increment_failed()
        assert job.failed_events == 2
    
    def test_add_error(self):
        """Test adding errors."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        job.add_error("Error 1")
        assert "Error 1" in job.errors
        assert len(job.errors) == 1
        
        job.add_error("Error 2")
        assert len(job.errors) == 2
    
    def test_add_warning(self):
        """Test adding warnings."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        job.add_warning("Warning 1")
        assert "Warning 1" in job.warnings
        assert len(job.warnings) == 1
    
    def test_is_running(self):
        """Test is_running check."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        assert not job.is_running()
        
        job.start()
        assert job.is_running()
        
        job.complete()
        assert not job.is_running()
    
    def test_is_completed(self):
        """Test is_completed check."""
        job = IngestionJob(
            source_type="github",
            source_config={},
            target_collection="docs",
        )
        
        assert not job.is_completed()
        
        job.start()
        assert not job.is_completed()
        
        job.complete()
        assert job.is_completed()
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        job = IngestionJob(
            source_type="github",
            source_config={"repo": "test/repo"},
            target_collection="docs",
        )
        
        data = job.to_dict()
        
        assert data["job_id"] == job.job_id
        assert data["source_type"] == "github"
        assert data["status"] == JobStatus.PENDING.value
        assert data["progress"] == 0
        assert "created_at" in data
    
    def test_job_requires_source_type(self):
        """Test that job requires source_type."""
        with pytest.raises(ValueError, match="source_type is required"):
            IngestionJob(
                source_type="",
                source_config={},
                target_collection="docs",
            )
    
    def test_job_requires_target_collection(self):
        """Test that job requires target_collection."""
        with pytest.raises(ValueError, match="target_collection is required"):
            IngestionJob(
                source_type="github",
                source_config={},
                target_collection="",
            )

