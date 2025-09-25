"""Comprehensive tests for DocumentService."""
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch

from services.doc_store.domain.entities import Document
from services.doc_store.domain.documents.service import DocumentService
from services.doc_store.domain.repository import DocumentRepository
from services.shared.infrastructure.utilities.error_handling import ValidationException


class TestDocumentService:
    """Comprehensive test cases for DocumentService."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        mock_repo = AsyncMock(spec=DocumentRepository)
        mock_repo.entity_class = Document
        return mock_repo

    @pytest.fixture
    def service(self, mock_repository):
        """Create a test service instance with mock repository."""
        return DocumentService(mock_repository)

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            id="test-doc-123",
            content="This is test content for service testing",
            content_hash="test_hash_123",
            correlation_id="test-correlation-456",
            metadata={"title": "Test Document", "author": "Test Author"}
        )

    @pytest.fixture
    def sample_document_data(self):
        """Create sample document data for creation tests."""
        return {
            "content": "This is test content for service testing",
            "correlation_id": "test-correlation-456",
            "metadata": {"title": "Test Document", "author": "Test Author"}
        }

    @pytest.mark.asyncio
    async def test_create_document_success(self, service, mock_repository, sample_document_data):
        """Test successfully creating a document."""
        # Mock repository methods
        mock_repository.find_by_content_hash.return_value = None
        mock_repository.save.return_value = Document(
            id="generated-id-123",
            content=sample_document_data["content"],
            content_hash="calculated_hash",
            correlation_id=sample_document_data["correlation_id"],
            metadata=sample_document_data["metadata"]
        )

        # Create document
        result = await service.create(sample_document_data)

        assert result is not None
        assert result.content == sample_document_data["content"]
        assert result.correlation_id == sample_document_data["correlation_id"]
        assert result.metadata == sample_document_data["metadata"]

        # Verify repository was called
        mock_repository.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_document_duplicate_content(self, service, mock_repository, sample_document_data):
        """Test creating document with duplicate content returns existing document."""
        existing_doc = Document(
            id="existing-doc-123",
            content=sample_document_data["content"],
            content_hash="existing_hash",
            correlation_id="existing-correlation"
        )

        mock_repository.find_by_content_hash.return_value = existing_doc

        # Create document
        result = await service.create(sample_document_data)

        # Should return existing document
        assert result == existing_doc

        # Repository save should not be called
        mock_repository.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_document_empty_content(self, service, sample_document_data):
        """Test creating document with empty content raises ValidationException."""
        invalid_data = sample_document_data.copy()
        invalid_data["content"] = ""

        with pytest.raises(ValidationException) as exc_info:
            await service.create(invalid_data)

        assert "content" in str(exc_info.value)
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_document_whitespace_content(self, service, sample_document_data):
        """Test creating document with whitespace-only content raises ValidationException."""
        invalid_data = sample_document_data.copy()
        invalid_data["content"] = "   \n\t   "

        with pytest.raises(ValidationException) as exc_info:
            await service.create(invalid_data)

        assert "content" in str(exc_info.value)
        assert "cannot be empty" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_document_content_too_large(self, service, sample_document_data):
        """Test creating document with content exceeding size limit."""
        # Create content larger than 10MB
        large_content = "A" * (11 * 1024 * 1024)  # 11MB
        invalid_data = sample_document_data.copy()
        invalid_data["content"] = large_content

        with pytest.raises(ValidationException) as exc_info:
            await service.create(invalid_data)

        assert "content" in str(exc_info.value)
        assert "10MB limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_document_invalid_metadata_type(self, service, sample_document_data):
        """Test creating document with invalid metadata type."""
        invalid_data = sample_document_data.copy()
        invalid_data["metadata"] = "invalid_metadata_string"

        with pytest.raises(ValidationException) as exc_info:
            await service.create(invalid_data)

        assert "metadata" in str(exc_info.value)
        assert "dictionary" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_document_metadata_too_many_keys(self, service, sample_document_data):
        """Test creating document with too many metadata keys."""
        # Create metadata with more than 50 keys
        large_metadata = {f"key_{i}": f"value_{i}" for i in range(51)}
        invalid_data = sample_document_data.copy()
        invalid_data["metadata"] = large_metadata

        with pytest.raises(ValidationException) as exc_info:
            await service.create(invalid_data)

        assert "metadata" in str(exc_info.value)
        assert "50 keys" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_document_invalid_metadata_key(self, service, sample_document_data):
        """Test creating document with invalid metadata key names."""
        invalid_data = sample_document_data.copy()
        invalid_data["metadata"] = {"": "empty_key_not_allowed"}

        with pytest.raises(ValidationException) as exc_info:
            await service.create(invalid_data)

        assert "metadata" in str(exc_info.value)
        assert "key name" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_document_by_id(self, service, mock_repository, sample_document):
        """Test getting document by ID."""
        mock_repository.find_by_id.return_value = sample_document

        result = await service.get_by_id(sample_document.id)

        assert result == sample_document
        mock_repository.find_by_id.assert_called_once_with(sample_document.id)

    @pytest.mark.asyncio
    async def test_get_document_by_id_not_found(self, service, mock_repository):
        """Test getting nonexistent document by ID."""
        mock_repository.find_by_id.return_value = None

        result = await service.get_by_id("nonexistent-id")

        assert result is None
        mock_repository.find_by_id.assert_called_once_with("nonexistent-id")

    @pytest.mark.asyncio
    async def test_update_document(self, service, mock_repository, sample_document):
        """Test updating a document."""
        updated_data = {
            "content": "Updated content",
            "metadata": {"title": "Updated Title"}
        }

        mock_repository.get_by_id.return_value = sample_document
        mock_repository.update.return_value = Document(
            id=sample_document.id,
            content="Updated content",
            content_hash=sample_document.content_hash,
            metadata={"title": "Updated Title"}
        )

        result = await service.update(sample_document.id, updated_data)

        assert result.content == "Updated content"
        assert result.metadata["title"] == "Updated Title"

        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_document_not_found(self, service, mock_repository):
        """Test updating nonexistent document."""
        mock_repository.get_by_id.return_value = None

        with pytest.raises(Exception):  # Should raise EntityNotFoundError from base service
            await service.update("nonexistent-id", {"content": "Updated"})

    @pytest.mark.asyncio
    async def test_update_document_invalid_content(self, service, mock_repository, sample_document):
        """Test updating document with invalid content."""
        mock_repository.get_by_id.return_value = sample_document

        with pytest.raises(ValidationException):
            await service.update(sample_document.id, {"content": ""})

    @pytest.mark.asyncio
    async def test_delete_document(self, service, mock_repository, sample_document):
        """Test deleting a document."""
        mock_repository.delete.return_value = True

        result = await service.delete(sample_document.id)

        assert result is True
        mock_repository.delete.assert_called_once_with(sample_document.id)

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, service, mock_repository):
        """Test deleting nonexistent document."""
        mock_repository.delete.return_value = False

        result = await service.delete("nonexistent-id")

        assert result is False

    @pytest.mark.asyncio
    async def test_list_documents(self, service, mock_repository, sample_document):
        """Test listing all documents."""
        mock_repository.get_all.return_value = [sample_document]

        result = await service.list()

        assert len(result) == 1
        assert result[0] == sample_document

        mock_repository.get_all.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, service, mock_repository):
        """Test listing documents when none exist."""
        mock_repository.get_all.return_value = []

        result = await service.list()

        assert result == []

    @pytest.mark.asyncio
    async def test_search_documents_by_correlation_id(self, service, mock_repository, sample_document):
        """Test searching documents by correlation ID."""
        mock_repository.find_by_correlation_id.return_value = [sample_document]

        result = await service.search_by_correlation_id("test-correlation-456")

        assert len(result) == 1
        assert result[0] == sample_document

        mock_repository.find_by_correlation_id.assert_called_once_with("test-correlation-456")

    @pytest.mark.asyncio
    async def test_search_documents_by_content_pattern(self, service, mock_repository, sample_document):
        """Test searching documents by content pattern."""
        mock_repository.find_by_content_pattern.return_value = [sample_document]

        result = await service.search_by_content_pattern("test content")

        assert len(result) == 1
        assert result[0] == sample_document

        mock_repository.find_by_content_pattern.assert_called_once_with("test content")


    def test_content_hash_calculation(self, service):
        """Test content hash calculation."""
        content = "Test content for hashing"
        expected_hash = "a1b2c3d4e5f6"  # Mock expected hash

        with patch('services.doc_store.domain.documents.service.hashlib') as mock_hashlib:
            mock_sha256 = Mock()
            mock_sha256.hexdigest.return_value = expected_hash
            mock_hashlib.sha256.return_value = mock_sha256

            result = service._calculate_content_hash(content)

            assert result == expected_hash
            mock_hashlib.sha256.assert_called_once_with(content.encode())

    def test_metadata_validation_valid(self, service):
        """Test metadata validation with valid metadata."""
        valid_metadata = {
            "title": "Test Document",
            "author": "Test Author",
            "tags": ["test", "document"],
            "version": 1
        }

        # Should not raise exception
        service._validate_metadata(valid_metadata)

    def test_metadata_validation_invalid_type(self, service):
        """Test metadata validation with invalid type."""
        with pytest.raises(ValidationException):
            service._validate_metadata("invalid_metadata_string")

    def test_metadata_validation_too_many_keys(self, service):
        """Test metadata validation with too many keys."""
        too_many_metadata = {f"key_{i}": f"value_{i}" for i in range(51)}

        with pytest.raises(ValidationException) as exc_info:
            service._validate_metadata(too_many_metadata)

        assert "50 keys" in str(exc_info.value)

    def test_metadata_validation_invalid_key_name(self, service):
        """Test metadata validation with invalid key names."""
        # Empty key name
        with pytest.raises(ValidationException):
            service._validate_metadata({"": "empty_key_not_allowed"})

        # Key name too long
        long_key = "a" * 101
        with pytest.raises(ValidationException):
            service._validate_metadata({long_key: "value"})

        # Non-string key
        with pytest.raises(ValidationException):
            service._validate_metadata({123: "numeric_key_not_allowed"})

    @pytest.mark.asyncio
    async def test_bulk_operations(self, service, mock_repository):
        """Test bulk operations."""
        docs_data = [
            {"content": "Bulk content 1", "metadata": {"index": 1}},
            {"content": "Bulk content 2", "metadata": {"index": 2}},
            {"content": "Bulk content 3", "metadata": {"index": 3}},
        ]

        # Mock bulk create
        mock_docs = [
            Document(id=f"bulk-doc-{i}", content=data["content"], content_hash=f"hash-{i}", **data)
            for i, data in enumerate(docs_data)
        ]
        mock_repository.bulk_create.return_value = mock_docs

        # Test bulk create
        result = await service.bulk_create(docs_data)
        assert len(result) == 3
        mock_repository.bulk_create.assert_called_once()

        # Test bulk delete
        mock_repository.bulk_delete.return_value = 3
        delete_result = await service.bulk_delete([doc.id for doc in mock_docs])
        assert delete_result == 3
        mock_repository.bulk_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_exists_check(self, service, mock_repository):
        """Test document existence checking."""
        mock_repository.exists_by_id.return_value = True

        result = await service.exists("test-doc-id")
        assert result is True

        mock_repository.exists_by_id.assert_called_once_with("test-doc-id")

    @pytest.mark.asyncio
    async def test_count_documents(self, service, mock_repository):
        """Test counting documents."""
        mock_repository.count.return_value = 42

        result = await service.count()
        assert result == 42

        mock_repository.count.assert_called_once()

    @pytest.mark.asyncio
    async def test_paginated_listing(self, service, mock_repository, sample_document):
        """Test paginated document listing."""
        mock_repository.get_paginated.return_value = [sample_document]

        result = await service.get_paginated(page=1, page_size=10)

        assert len(result) == 1
        assert result[0] == sample_document

        mock_repository.get_paginated.assert_called_once_with(page=1, page_size=10)

    @pytest.mark.asyncio
    async def test_find_by_criteria(self, service, mock_repository, sample_document):
        """Test finding documents by custom criteria."""
        mock_repository.find_by_criteria.return_value = [sample_document]

        criteria = {"status": "PUBLISHED", "type": "MARKDOWN"}
        result = await service.find_by_criteria(criteria)

        assert len(result) == 1
        assert result[0] == sample_document

        mock_repository.find_by_criteria.assert_called_once_with(criteria)

    @pytest.mark.asyncio
    async def test_service_initialization_with_repository(self):
        """Test service initialization with explicit repository."""
        mock_repo = AsyncMock()
        svc = DocumentService(mock_repo)

        assert svc.repository == mock_repo

    @pytest.mark.asyncio
    async def test_service_initialization_without_repository(self):
        """Test service initialization creates repository automatically."""
        with patch('services.doc_store.domain.documents.service.get_document_connection_string') as mock_conn:
            mock_conn.return_value = "sqlite:///test.db"

            svc = DocumentService()

            # Should create repository
            assert svc.repository is not None
            assert isinstance(svc.repository, DocumentRepository)

    def test_entity_validation(self, service, sample_document):
        """Test entity validation."""
        # Valid document should pass
        service._validate_entity(sample_document)

        # Invalid document should raise exception
        invalid_doc = Document(
            id="invalid",
            content="",  # Empty content
            content_hash="hash"
        )

        with pytest.raises(ValidationException):
            service._validate_entity(invalid_doc)

    @pytest.mark.asyncio
    async def test_duplicate_content_handling(self, service, mock_repository, sample_document_data):
        """Test that duplicate content returns existing document."""
        # Mock finding existing document
        mock_repository.find_by_content_hash.return_value = sample_document

        result = await service.create(sample_document_data)

        # Should return existing document, not create new one
        assert result == sample_document
        mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_transaction_rollback_on_validation_error(self, service, mock_repository, sample_document):
        """Test that transactions rollback on validation errors during bulk operations."""
        # This would test transaction behavior, but for now we'll test the validation
        invalid_docs = [
            {"content": "Valid content", "metadata": {}},
            {"content": "", "metadata": {}},  # Invalid
            {"content": "Another valid", "metadata": {}}
        ]

        mock_repository.bulk_create.side_effect = ValidationException("content", "cannot be empty")

        with pytest.raises(ValidationException):
            await service.bulk_create(invalid_docs)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, service, mock_repository):
        """Test service handles concurrent operations properly."""
        import asyncio

        # Mock concurrent repository calls
        async def mock_create(data):
            doc = Document(
                id=f"concurrent-{hash(str(data))}",
                content=data["content"],
                content_hash="hash"
            )
            return doc

        mock_repository.create.side_effect = mock_create
        mock_repository.find_by_content_hash.return_value = None

        # Create multiple documents concurrently
        docs_data = [
            {"content": f"Concurrent content {i}"}
            for i in range(10)
        ]

        tasks = [service.create(data) for data in docs_data]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for result in results:
            assert result.content.startswith("Concurrent content")
