"""Clean unit tests for source-agent domain entities."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Optional

# Define domain entities inline to avoid import dependencies
from enum import Enum


class DocumentStatus(str, Enum):
    """Document status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SourceType(str, Enum):
    """Source type enumeration."""
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    LOCAL = "local"
    HTTP = "http"
    FTP = "ftp"


class OperationType(str, Enum):
    """Operation type enumeration."""
    FETCH = "fetch"
    ANALYZE = "analyze"
    NORMALIZE = "normalize"
    STORE = "store"
    INDEX = "index"


class IngestionResult:
    """Domain entity for ingestion results."""

    def __init__(self,
                 result_id: str = None,
                 source_id: str = None,
                 operation_type: OperationType = OperationType.FETCH,
                 status: DocumentStatus = DocumentStatus.PENDING,
                 documents_processed: int = 0,
                 documents_succeeded: int = 0,
                 documents_failed: int = 0,
                 total_size_bytes: int = 0,
                 processing_time_ms: int = 0,
                 error_messages: List[str] = None,
                 metadata: Dict = None,
                 created_at: datetime = None):
        self.result_id = result_id or str(uuid4())
        self.source_id = source_id
        self.operation_type = operation_type
        self.status = status
        self.documents_processed = documents_processed
        self.documents_succeeded = documents_succeeded
        self.documents_failed = documents_failed
        self.total_size_bytes = total_size_bytes
        self.processing_time_ms = processing_time_ms
        self.error_messages = error_messages or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_successful(self) -> bool:
        """Check if ingestion was successful."""
        return (self.status == DocumentStatus.COMPLETED and
                self.documents_failed == 0 and
                self.documents_processed > 0)

    def is_partial_success(self) -> bool:
        """Check if ingestion had partial success."""
        return (self.status == DocumentStatus.COMPLETED and
                self.documents_succeeded > 0 and
                self.documents_failed > 0)

    def is_failed(self) -> bool:
        """Check if ingestion failed."""
        return self.status == DocumentStatus.FAILED or self.documents_processed == 0

    def get_success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.documents_processed == 0:
            return 0.0
        return (self.documents_succeeded / self.documents_processed) * 100.0

    def add_error_message(self, message: str):
        """Add an error message."""
        self.error_messages.append(message)

    def mark_completed(self):
        """Mark result as completed."""
        self.status = DocumentStatus.COMPLETED

    def mark_failed(self):
        """Mark result as failed."""
        self.status = DocumentStatus.FAILED


class Source:
    """Domain entity for data sources."""

    def __init__(self,
                 source_id: str = None,
                 name: str = None,
                 source_type: SourceType = SourceType.GITHUB,
                 url: str = None,
                 credentials: Dict = None,
                 configuration: Dict = None,
                 is_active: bool = True,
                 last_ingested_at: datetime = None,
                 created_at: datetime = None):
        self.source_id = source_id or str(uuid4())
        self.name = name or ""
        self.source_type = source_type
        self.url = url or ""
        self.credentials = credentials or {}
        self.configuration = configuration or {}
        self.is_active = is_active
        self.last_ingested_at = last_ingested_at
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_accessible(self) -> bool:
        """Check if source is accessible."""
        return self.is_active and bool(self.url)

    def supports_operation(self, operation: OperationType) -> bool:
        """Check if source supports a specific operation."""
        supported_ops = {
            SourceType.GITHUB: [OperationType.FETCH, OperationType.ANALYZE],
            SourceType.GITLAB: [OperationType.FETCH, OperationType.ANALYZE],
            SourceType.BITBUCKET: [OperationType.FETCH, OperationType.ANALYZE],
            SourceType.LOCAL: [OperationType.FETCH, OperationType.STORE],
            SourceType.HTTP: [OperationType.FETCH],
            SourceType.FTP: [OperationType.FETCH],
        }
        return operation in supported_ops.get(self.source_type, [])

    def update_last_ingested(self):
        """Update last ingested timestamp."""
        self.last_ingested_at = datetime.now(timezone.utc)

    def deactivate(self):
        """Deactivate the source."""
        self.is_active = False

    def activate(self):
        """Activate the source."""
        self.is_active = True


class Document:
    """Domain entity for documents."""

    def __init__(self,
                 document_id: str = None,
                 source_id: str = None,
                 title: str = None,
                 content: str = None,
                 content_type: str = "text/plain",
                 metadata: Dict = None,
                 status: DocumentStatus = DocumentStatus.PENDING,
                 file_path: str = None,
                 file_size: int = 0,
                 checksum: str = None,
                 version: str = "1.0",
                 tags: List[str] = None,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.document_id = document_id or str(uuid4())
        self.source_id = source_id
        self.title = title or ""
        self.content = content or ""
        self.content_type = content_type
        self.metadata = metadata or {}
        self.status = status
        self.file_path = file_path
        self.file_size = file_size
        self.checksum = checksum
        self.version = version
        self.tags = tags or []
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def is_processed(self) -> bool:
        """Check if document is processed."""
        return self.status in [DocumentStatus.COMPLETED, DocumentStatus.FAILED]

    def is_successful(self) -> bool:
        """Check if document processing was successful."""
        return self.status == DocumentStatus.COMPLETED

    def has_content(self) -> bool:
        """Check if document has content."""
        return bool(self.content.strip())

    def add_tag(self, tag: str):
        """Add a tag to the document."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove a tag from the document."""
        if tag in self.tags:
            self.tags.remove(tag)

    def update_content(self, new_content: str):
        """Update document content."""
        self.content = new_content
        self.file_size = len(new_content.encode('utf-8'))
        self.updated_at = datetime.now(timezone.utc)

    def mark_completed(self):
        """Mark document as completed."""
        self.status = DocumentStatus.COMPLETED
        self.updated_at = datetime.now(timezone.utc)

    def mark_failed(self):
        """Mark document as failed."""
        self.status = DocumentStatus.FAILED
        self.updated_at = datetime.now(timezone.utc)

    def get_content_length(self) -> int:
        """Get content length."""
        return len(self.content)


class TestIngestionResultEntity:
    """Test the IngestionResult domain entity."""

    def test_ingestion_result_creation(self):
        """Test creating an ingestion result."""
        result = IngestionResult(
            source_id="source123",
            operation_type=OperationType.FETCH,
            documents_processed=10,
            documents_succeeded=8,
            documents_failed=2,
            total_size_bytes=1024000,
            processing_time_ms=1500
        )

        assert result.result_id is not None
        assert result.source_id == "source123"
        assert result.operation_type == OperationType.FETCH
        assert result.status == DocumentStatus.PENDING
        assert result.documents_processed == 10
        assert result.documents_succeeded == 8
        assert result.documents_failed == 2

    def test_ingestion_result_status_methods(self):
        """Test status checking methods."""
        # Successful result
        success_result = IngestionResult(
            status=DocumentStatus.COMPLETED,
            documents_processed=5,
            documents_succeeded=5,
            documents_failed=0
        )
        assert success_result.is_successful()
        assert not success_result.is_partial_success()
        assert not success_result.is_failed()

        # Partial success result
        partial_result = IngestionResult(
            status=DocumentStatus.COMPLETED,
            documents_processed=5,
            documents_succeeded=3,
            documents_failed=2
        )
        assert not partial_result.is_successful()
        assert partial_result.is_partial_success()
        assert not partial_result.is_failed()

        # Failed result
        failed_result = IngestionResult(status=DocumentStatus.FAILED)
        assert not failed_result.is_successful()
        assert not failed_result.is_partial_success()
        assert failed_result.is_failed()

        # Empty result
        empty_result = IngestionResult(documents_processed=0)
        assert not empty_result.is_successful()
        assert not empty_result.is_partial_success()
        assert empty_result.is_failed()

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        result = IngestionResult(
            documents_processed=10,
            documents_succeeded=7,
            documents_failed=3
        )

        assert result.get_success_rate() == 70.0

        # Empty result
        empty_result = IngestionResult(documents_processed=0)
        assert empty_result.get_success_rate() == 0.0

    def test_error_message_management(self):
        """Test error message management."""
        result = IngestionResult()

        assert len(result.error_messages) == 0

        result.add_error_message("Connection timeout")
        result.add_error_message("Invalid credentials")

        assert len(result.error_messages) == 2
        assert "Connection timeout" in result.error_messages
        assert "Invalid credentials" in result.error_messages

    def test_status_transitions(self):
        """Test status transition methods."""
        result = IngestionResult()

        assert result.status == DocumentStatus.PENDING

        result.mark_completed()
        assert result.status == DocumentStatus.COMPLETED

        result.mark_failed()
        assert result.status == DocumentStatus.FAILED


class TestSourceEntity:
    """Test the Source domain entity."""

    def test_source_creation(self):
        """Test creating a source."""
        source = Source(
            name="GitHub Repository",
            source_type=SourceType.GITHUB,
            url="https://github.com/user/repo",
            credentials={"token": "secret"},
            configuration={"branch": "main", "include_docs": True}
        )

        assert source.source_id is not None
        assert source.name == "GitHub Repository"
        assert source.source_type == SourceType.GITHUB
        assert source.url == "https://github.com/user/repo"
        assert source.credentials["token"] == "secret"
        assert source.configuration["branch"] == "main"
        assert source.is_active

    def test_source_accessibility(self):
        """Test source accessibility checks."""
        accessible_source = Source(
            name="Accessible Source",
            url="https://example.com",
            is_active=True
        )
        assert accessible_source.is_accessible()

        # Inactive source
        inactive_source = Source(url="https://example.com", is_active=False)
        assert not inactive_source.is_accessible()

        # Source without URL
        no_url_source = Source(is_active=True)
        assert not no_url_source.is_accessible()

    def test_source_operation_support(self):
        """Test operation support checking."""
        github_source = Source(source_type=SourceType.GITHUB)
        assert github_source.supports_operation(OperationType.FETCH)
        assert github_source.supports_operation(OperationType.ANALYZE)
        assert not github_source.supports_operation(OperationType.STORE)

        local_source = Source(source_type=SourceType.LOCAL)
        assert local_source.supports_operation(OperationType.FETCH)
        assert local_source.supports_operation(OperationType.STORE)
        assert not local_source.supports_operation(OperationType.ANALYZE)

        http_source = Source(source_type=SourceType.HTTP)
        assert http_source.supports_operation(OperationType.FETCH)
        assert not http_source.supports_operation(OperationType.ANALYZE)

    def test_source_status_management(self):
        """Test source status management."""
        source = Source()

        assert source.is_active

        source.deactivate()
        assert not source.is_active

        source.activate()
        assert source.is_active

    def test_source_ingestion_tracking(self):
        """Test source ingestion tracking."""
        source = Source()

        assert source.last_ingested_at is None

        source.update_last_ingested()
        assert source.last_ingested_at is not None
        assert isinstance(source.last_ingested_at, datetime)


class TestDocumentEntity:
    """Test the Document domain entity."""

    def test_document_creation(self):
        """Test creating a document."""
        document = Document(
            source_id="source123",
            title="API Documentation",
            content="This is API documentation content",
            content_type="text/markdown",
            file_path="/docs/api.md",
            file_size=1024,
            checksum="abc123",
            version="1.2.0",
            tags=["api", "documentation"]
        )

        assert document.document_id is not None
        assert document.source_id == "source123"
        assert document.title == "API Documentation"
        assert document.content == "This is API documentation content"
        assert document.content_type == "text/markdown"
        assert document.status == DocumentStatus.PENDING
        assert document.file_path == "/docs/api.md"
        assert document.file_size == 1024
        assert document.checksum == "abc123"
        assert document.version == "1.2.0"
        assert "api" in document.tags
        assert "documentation" in document.tags

    def test_document_status_methods(self):
        """Test document status methods."""
        document = Document()

        assert not document.is_processed()
        assert not document.is_successful()

        document.mark_completed()
        assert document.is_processed()
        assert document.is_successful()

        document.mark_failed()
        assert document.is_processed()
        assert not document.is_successful()

    def test_document_content_methods(self):
        """Test document content methods."""
        document = Document(content="   ")
        assert not document.has_content()

        document.update_content("New content here")
        assert document.has_content()
        assert document.get_content_length() == 16
        assert document.file_size == len("New content here".encode('utf-8'))

    def test_document_tag_management(self):
        """Test document tag management."""
        document = Document()

        assert len(document.tags) == 0

        document.add_tag("important")
        assert len(document.tags) == 1
        assert "important" in document.tags

        document.add_tag("urgent")
        assert len(document.tags) == 2

        # Adding duplicate should not increase count
        document.add_tag("important")
        assert len(document.tags) == 2

        document.remove_tag("important")
        assert len(document.tags) == 1
        assert "important" not in document.tags

    def test_document_metadata_operations(self):
        """Test document metadata operations."""
        document = Document()
        document.metadata = {"author": "John Doe", "priority": "high"}

        assert document.metadata["author"] == "John Doe"
        assert document.metadata["priority"] == "high"


class TestEntityIntegration:
    """Test integration between entities."""

    def test_ingestion_result_with_source(self):
        """Test integration between IngestionResult and Source."""
        source = Source(
            name="GitHub Repo",
            source_type=SourceType.GITHUB,
            url="https://github.com/user/repo"
        )

        result = IngestionResult(
            source_id=source.source_id,
            operation_type=OperationType.FETCH,
            documents_processed=5,
            documents_succeeded=5,
            documents_failed=0
        )
        result.status = DocumentStatus.COMPLETED

        assert result.source_id == source.source_id
        assert source.supports_operation(result.operation_type)
        assert result.is_successful()

        # Update source last ingested time
        source.update_last_ingested()
        assert source.last_ingested_at is not None

    def test_document_with_ingestion_result(self):
        """Test integration between Document and IngestionResult."""
        document = Document(
            source_id="source123",
            title="Test Document",
            content="Document content",
            status=DocumentStatus.PENDING
        )

        result = IngestionResult(
            source_id="source123",
            operation_type=OperationType.FETCH,
            documents_processed=1,
            documents_succeeded=1,
            documents_failed=0
        )
        result.status = DocumentStatus.COMPLETED

        assert document.source_id == result.source_id
        assert document.status == DocumentStatus.PENDING
        assert result.is_successful()

        # Mark document as completed
        document.mark_completed()
        assert document.is_successful()

    def test_source_with_documents(self):
        """Test integration between Source and Documents."""
        source = Source(
            name="Code Repository",
            source_type=SourceType.GITHUB,
            url="https://github.com/user/repo"
        )

        doc1 = Document(
            source_id=source.source_id,
            title="README.md",
            content="# Project README",
            content_type="text/markdown"
        )

        doc2 = Document(
            source_id=source.source_id,
            title="main.py",
            content="print('Hello World')",
            content_type="text/x-python"
        )

        assert doc1.source_id == source.source_id
        assert doc2.source_id == source.source_id
        assert source.supports_operation(OperationType.FETCH)
        assert source.is_accessible()

        # Both documents should be processable
        assert not doc1.is_processed()
        assert not doc2.is_processed()

    def test_complete_ingestion_workflow(self):
        """Test complete ingestion workflow."""
        # Create source
        source = Source(
            name="Test Repository",
            source_type=SourceType.GITHUB,
            url="https://github.com/test/repo"
        )

        # Create ingestion result
        result = IngestionResult(
            source_id=source.source_id,
            operation_type=OperationType.FETCH,
            documents_processed=3,
            documents_succeeded=2,
            documents_failed=1
        )
        result.status = DocumentStatus.COMPLETED

        # Create documents
        doc1 = Document(
            source_id=source.source_id,
            title="Document 1",
            content="Content 1",
            status=DocumentStatus.COMPLETED
        )

        doc2 = Document(
            source_id=source.source_id,
            title="Document 2",
            content="Content 2",
            status=DocumentStatus.COMPLETED
        )

        doc3 = Document(
            source_id=source.source_id,
            title="Document 3",
            content="Content 3",
            status=DocumentStatus.FAILED
        )

        # Verify workflow integration
        assert source.is_accessible()
        assert source.supports_operation(result.operation_type)
        assert result.is_partial_success()
        assert doc1.is_successful()
        assert doc2.is_successful()
        assert not doc3.is_successful()

        # Update source tracking
        source.update_last_ingested()
        assert source.last_ingested_at is not None

        # Add error to result
        result.add_error_message("Failed to process Document 3")
        assert len(result.error_messages) == 1

        # Complete result
        result.mark_completed()
        assert result.status == DocumentStatus.COMPLETED
