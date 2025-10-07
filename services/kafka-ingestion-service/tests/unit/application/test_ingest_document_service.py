"""Unit tests for IngestDocumentService."""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from application.services.ingest_document_service import IngestDocumentService
from domain.entities.document_event import DocumentEvent
from domain.value_objects.event_type import EventType
from domain.value_objects.event_status import EventStatus


class TestIngestDocumentService:
    """Test IngestDocumentService."""
    
    @pytest.fixture
    def mock_event_repo(self):
        """Create mock event repository."""
        repo = Mock()
        repo.add = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.update = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_kafka_producer(self):
        """Create mock Kafka producer."""
        producer = Mock()
        producer.send_event = AsyncMock()
        return producer
    
    @pytest.fixture
    def service(self, mock_event_repo, mock_kafka_producer):
        """Create service instance."""
        return IngestDocumentService(
            event_repo=mock_event_repo,
            kafka_producer=mock_kafka_producer,
        )
    
    @pytest.mark.asyncio
    async def test_ingest_document_creates_event(self, service, mock_event_repo):
        """Test that ingesting document creates event."""
        result = await service.ingest_document(
            document_id="doc-123",
            content="Test content",
            event_type=EventType.DOCUMENT_CREATED,
            source_metadata={"repo": "test/repo"},
        )
        
        assert result.document_id == "doc-123"
        assert result.event_type == EventType.DOCUMENT_CREATED
        assert result.status == EventStatus.PENDING
        mock_event_repo.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ingest_document_sends_to_kafka(self, service, mock_kafka_producer):
        """Test that ingesting document sends to Kafka."""
        await service.ingest_document(
            document_id="doc-123",
            content="Test content",
            event_type=EventType.DOCUMENT_CREATED,
        )
        
        mock_kafka_producer.send_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_event_by_id(self, service, mock_event_repo):
        """Test getting event by ID."""
        mock_event = DocumentEvent(
            document_id="doc-123",
            content="Test",
            event_type=EventType.DOCUMENT_CREATED,
        )
        mock_event_repo.get_by_id.return_value = mock_event
        
        result = await service.get_event("evt-123")
        
        assert result == mock_event
        mock_event_repo.get_by_id.assert_called_once_with("evt-123")
    
    @pytest.mark.asyncio
    async def test_process_event_updates_status(self, service, mock_event_repo):
        """Test processing event updates status."""
        event = DocumentEvent(
            document_id="doc-123",
            content="Test",
            event_type=EventType.DOCUMENT_CREATED,
        )
        mock_event_repo.get_by_id.return_value = event
        
        await service.process_event("evt-123")
        
        assert event.status == EventStatus.PROCESSING
        mock_event_repo.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_complete_event_marks_completed(self, service, mock_event_repo):
        """Test completing event marks it as completed."""
        event = DocumentEvent(
            document_id="doc-123",
            content="Test",
            event_type=EventType.DOCUMENT_CREATED,
        )
        event.start_processing()
        mock_event_repo.get_by_id.return_value = event
        
        await service.complete_event("evt-123")
        
        assert event.status == EventStatus.COMPLETED
        assert event.completed_at is not None
        mock_event_repo.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_fail_event_marks_failed(self, service, mock_event_repo):
        """Test failing event marks it as failed."""
        event = DocumentEvent(
            document_id="doc-123",
            content="Test",
            event_type=EventType.DOCUMENT_CREATED,
        )
        mock_event_repo.get_by_id.return_value = event
        
        await service.fail_event("evt-123", "Test error")
        
        assert event.status == EventStatus.FAILED
        assert event.error_message == "Test error"
        mock_event_repo.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_retry_event_increments_count(self, service, mock_event_repo):
        """Test retrying event increments retry count."""
        event = DocumentEvent(
            document_id="doc-123",
            content="Test",
            event_type=EventType.DOCUMENT_CREATED,
        )
        event.fail("Initial error")
        mock_event_repo.get_by_id.return_value = event
        
        await service.retry_event("evt-123")
        
        assert event.status == EventStatus.RETRYING
        assert event.retry_count == 1
        mock_event_repo.update.assert_called()
    
    @pytest.mark.asyncio
    async def test_ingest_document_with_custom_metadata(self, service, mock_event_repo):
        """Test ingesting document with custom metadata."""
        metadata = {
            "repo": "test/repo",
            "branch": "main",
            "commit": "abc123",
        }
        
        result = await service.ingest_document(
            document_id="doc-123",
            content="Test content",
            event_type=EventType.DOCUMENT_CREATED,
            source_metadata=metadata,
        )
        
        assert result.source_metadata == metadata
        mock_event_repo.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_ingest_documents(self, service, mock_event_repo):
        """Test batch ingesting multiple documents."""
        documents = [
            {"document_id": "doc-1", "content": "Content 1"},
            {"document_id": "doc-2", "content": "Content 2"},
            {"document_id": "doc-3", "content": "Content 3"},
        ]
        
        results = await service.batch_ingest(
            documents=documents,
            event_type=EventType.BATCH_IMPORT,
        )
        
        assert len(results) == 3
        assert mock_event_repo.add.call_count == 3

