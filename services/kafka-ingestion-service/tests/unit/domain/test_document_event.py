"""Unit tests for DocumentEvent entity."""

import pytest
from datetime import datetime, timezone

from domain.entities.document_event import DocumentEvent
from domain.value_objects.event_type import EventType
from domain.value_objects.event_status import EventStatus
from domain.value_objects.source_metadata import SourceMetadata


@pytest.mark.unit
class TestDocumentEvent:
    """Test suite for DocumentEvent entity."""
    
    def test_create_document_event(self, sample_document_event):
        """
        Test that DocumentEvent can be created with valid data.
        
        Given: Valid event data
        When: Creating DocumentEvent
        Then: Event is created successfully
        """
        # Assert
        assert sample_document_event.document_id == "test-doc-1"
        assert sample_document_event.title == "Test Document"
        assert sample_document_event.event_type == EventType.DOCUMENT_CREATED
        assert sample_document_event.status == EventStatus.PENDING
    
    def test_event_requires_document_id(self, sample_source_metadata):
        """
        Test that DocumentEvent requires document_id.
        
        Given: Event data without document_id
        When: Creating DocumentEvent
        Then: ValueError is raised
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Document ID is required"):
            DocumentEvent(
                document_id="",  # Empty document_id
                title="Test",
                content="Content",
                event_type=EventType.DOCUMENT_CREATED,
                source_metadata=sample_source_metadata,
            )
    
    def test_event_requires_title(self, sample_source_metadata):
        """
        Test that DocumentEvent requires title.
        
        Given: Event data without title
        When: Creating DocumentEvent
        Then: ValueError is raised
        """
        # Act & Assert
        with pytest.raises(ValueError, match="Document title is required"):
            DocumentEvent(
                document_id="doc-1",
                title="",  # Empty title
                content="Content",
                event_type=EventType.DOCUMENT_CREATED,
                source_metadata=sample_source_metadata,
            )
    
    def test_mark_as_ingested(self, sample_document_event):
        """
        Test that event can be marked as ingested.
        
        Given: Pending event
        When: Marking as ingested
        Then: Status is updated and timestamp set
        """
        # Act
        sample_document_event.mark_as_ingested()
        
        # Assert
        assert sample_document_event.status == EventStatus.INGESTED
        assert sample_document_event.ingested_at is not None
    
    def test_mark_as_processing(self, sample_document_event):
        """
        Test that ingested event can be marked as processing.
        
        Given: Ingested event
        When: Marking as processing
        Then: Status transitions successfully
        """
        # Arrange
        sample_document_event.mark_as_ingested()
        
        # Act
        sample_document_event.mark_as_processing()
        
        # Assert
        assert sample_document_event.status == EventStatus.PROCESSING
    
    def test_mark_as_processed(self, sample_document_event):
        """
        Test that processing event can be marked as processed.
        
        Given: Processing event
        When: Marking as processed
        Then: Status transitions and timestamp set
        """
        # Arrange
        sample_document_event.mark_as_ingested()
        sample_document_event.mark_as_processing()
        
        # Act
        sample_document_event.mark_as_processed()
        
        # Assert
        assert sample_document_event.status == EventStatus.PROCESSED
        assert sample_document_event.processed_at is not None
    
    def test_mark_as_failed(self, sample_document_event):
        """
        Test that event can be marked as failed.
        
        Given: Processing event
        When: Marking as failed with error message
        Then: Status updated and error message stored
        """
        # Arrange
        sample_document_event.mark_as_ingested()
        sample_document_event.mark_as_processing()
        error_msg = "Processing failed due to timeout"
        
        # Act
        sample_document_event.mark_as_failed(error_msg)
        
        # Assert
        assert sample_document_event.status == EventStatus.FAILED
        assert sample_document_event.error_message == error_msg
        assert sample_document_event.processed_at is not None
    
    def test_increment_retry(self, sample_document_event):
        """
        Test that retry count can be incremented.
        
        Given: Failed event
        When: Incrementing retry count
        Then: Count increases and returns True if can retry
        """
        # Arrange
        sample_document_event.mark_as_failed("Error")
        initial_retry_count = sample_document_event.retry_count
        
        # Act
        can_retry = sample_document_event.increment_retry()
        
        # Assert
        assert sample_document_event.retry_count == initial_retry_count + 1
        assert can_retry is True
    
    def test_increment_retry_exceeds_max(self, sample_document_event):
        """
        Test that increment_retry returns False when max retries exceeded.
        
        Given: Event with max retries reached
        When: Incrementing retry count
        Then: Returns False
        """
        # Arrange
        sample_document_event.retry_count = 3
        sample_document_event.max_retries = 3
        
        # Act
        can_retry = sample_document_event.increment_retry()
        
        # Assert
        assert can_retry is False
    
    def test_can_retry(self, sample_document_event):
        """
        Test that can_retry correctly identifies retryable events.
        
        Given: Failed event with retries remaining
        When: Checking can_retry
        Then: Returns True
        """
        # Arrange
        sample_document_event.mark_as_failed("Error")
        sample_document_event.retry_count = 1
        
        # Act
        can_retry = sample_document_event.can_retry()
        
        # Assert
        assert can_retry is True
    
    def test_is_terminal(self, sample_document_event):
        """
        Test that is_terminal identifies terminal states.
        
        Given: Processed event
        When: Checking is_terminal
        Then: Returns True
        """
        # Arrange
        sample_document_event.mark_as_ingested()
        sample_document_event.mark_as_processing()
        sample_document_event.mark_as_processed()
        
        # Act
        is_terminal = sample_document_event.is_terminal()
        
        # Assert
        assert is_terminal is True
    
    def test_to_dict(self, sample_document_event):
        """
        Test that event can be serialized to dict.
        
        Given: DocumentEvent
        When: Converting to dict
        Then: All fields are present
        """
        # Act
        event_dict = sample_document_event.to_dict()
        
        # Assert
        assert event_dict["document_id"] == "test-doc-1"
        assert event_dict["title"] == "Test Document"
        assert event_dict["event_type"] == "document_created"
        assert event_dict["status"] == "pending"
        assert "source_metadata" in event_dict
    
    def test_from_dict(self, event_created_data):
        """
        Test that event can be deserialized from dict.
        
        Given: Event dict data
        When: Creating DocumentEvent from dict
        Then: Event is created with correct data
        """
        # Act
        event = DocumentEvent.from_dict(event_created_data)
        
        # Assert
        assert event.document_id == event_created_data["document_id"]
        assert event.title == event_created_data["title"]
        assert event.event_type == EventType.DOCUMENT_CREATED
        assert event.status == EventStatus.PENDING
    
    def test_get_processing_duration(self, sample_document_event):
        """
        Test that processing duration is calculated correctly.
        
        Given: Processed event
        When: Getting processing duration
        Then: Returns duration in seconds
        """
        # Arrange
        sample_document_event.mark_as_ingested()
        sample_document_event.mark_as_processing()
        sample_document_event.mark_as_processed()
        
        # Act
        duration = sample_document_event.get_processing_duration()
        
        # Assert
        assert duration is not None
        assert duration >= 0.0

