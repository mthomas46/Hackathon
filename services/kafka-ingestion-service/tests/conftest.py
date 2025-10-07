"""Shared test fixtures for kafka-ingestion-service."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from domain.entities.document_event import DocumentEvent
from domain.entities.ingestion_job import IngestionJob
from domain.value_objects.event_type import EventType
from domain.value_objects.event_status import EventStatus
from domain.value_objects.job_status import JobStatus
from domain.value_objects.source_metadata import SourceMetadata


@pytest.fixture
def sample_source_metadata() -> SourceMetadata:
    """Create sample source metadata."""
    return SourceMetadata.for_docs_directory(
        path="/docs/architecture.md",
        author="test-user"
    )


@pytest.fixture
def sample_document_event(sample_source_metadata) -> DocumentEvent:
    """Create sample document event."""
    return DocumentEvent(
        document_id="test-doc-1",
        title="Test Document",
        content="# Test Content\n\nThis is a test document.",
        event_type=EventType.DOCUMENT_CREATED,
        source_metadata=sample_source_metadata,
        tags=["test", "architecture"],
        categories=["documentation"],
    )


@pytest.fixture
def sample_ingestion_job() -> IngestionJob:
    """Create sample ingestion job."""
    return IngestionJob(
        name="Test Ingestion Job",
        description="Test job for ingesting documents",
        source_type="docs_directory",
        source_config={"path": "/docs", "pattern": "**/*.md"},
        created_by="test-user",
    )


@pytest.fixture
def event_created_data() -> dict:
    """Sample event data for DOCUMENT_CREATED."""
    return {
        "event_id": str(uuid4()),
        "document_id": "doc-123",
        "event_type": "document_created",
        "status": "pending",
        "source_metadata": {
            "source_type": "docs_directory",
            "source_id": "/docs/test.md",
            "source_name": "Test Docs",
        },
        "title": "Test Document",
        "content": "# Test Content",
        "content_type": "text/markdown",
        "source_url": None,
        "tags": ["test"],
        "categories": [],
        "metadata": {},
        "retry_count": 0,
        "max_retries": 3,
        "error_message": None,
        "event_timestamp": datetime.now(timezone.utc).isoformat(),
        "ingested_at": None,
        "processed_at": None,
        "correlation_id": None,
        "parent_event_id": None,
    }


@pytest.fixture
async def mock_event_repository(mocker):
    """Create mock event repository."""
    repo = mocker.AsyncMock()
    repo.save = mocker.AsyncMock()
    repo.get_by_id = mocker.AsyncMock()
    repo.update = mocker.AsyncMock()
    repo.delete = mocker.AsyncMock()
    return repo


@pytest.fixture
async def mock_job_repository(mocker):
    """Create mock job repository."""
    repo = mocker.AsyncMock()
    repo.save = mocker.AsyncMock()
    repo.get_by_id = mocker.AsyncMock()
    repo.update = mocker.AsyncMock()
    repo.delete = mocker.AsyncMock()
    return repo


@pytest.fixture
def mock_kafka_producer(mocker):
    """Create mock Kafka producer."""
    producer = mocker.AsyncMock()
    producer.start = mocker.AsyncMock()
    producer.stop = mocker.AsyncMock()
    producer.publish_event = mocker.AsyncMock()
    return producer


@pytest.fixture
def mock_kafka_consumer(mocker):
    """Create mock Kafka consumer."""
    consumer = mocker.AsyncMock()
    consumer.start = mocker.AsyncMock()
    consumer.stop = mocker.AsyncMock()
    consumer.subscribe = mocker.AsyncMock()
    consumer.poll = mocker.AsyncMock(return_value={})
    consumer.commit = mocker.AsyncMock()
    return consumer

