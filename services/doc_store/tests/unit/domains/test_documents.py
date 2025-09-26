"""Document domain tests.

Comprehensive tests for document management, CRUD operations, and document-related functionality.
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.unit
@pytest.mark.domain
class TestDocumentRepository(BaseTestCase):
    """Test DocumentRepository functionality."""

    @pytest.fixture
    def repository(self):
        """Create document repository instance."""
        from services.doc_store.domain.documents.repository import DocumentRepository
        return DocumentRepository()

    def test_calculate_content_hash(self, repository):
        """Test content hash calculation."""
        content = "Test document content"
        hash_value = repository.calculate_content_hash(content)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 hex length

        # Same content should produce same hash
        hash_value2 = repository.calculate_content_hash(content)
        assert hash_value == hash_value2

    def test_get_by_id_not_found(self, repository, mock_execute_query):
        """Test getting non-existent document."""
        mock_execute_query.return_value = None

        result = repository.get_by_id("non-existent")
        assert result is None

    @patch('services.doc_store.domain.documents.repository.execute_query')
    def test_get_by_content_hash(self, mock_query, repository):
        """Test getting document by content hash."""
        mock_doc = {
            'id': 'doc123',
            'content': 'test content',
            'content_hash': 'hash123',
            'metadata': '{"type": "test"}',
            'correlation_id': 'corr123',
            'created_at': '2024-01-01T00:00:00',
            'updated_at': None
        }
        mock_query.return_value = mock_doc

        result = repository.get_by_content_hash('hash123')

        assert result is not None
        assert result.id == 'doc123'
        assert result.content == 'test content'
        assert result.content_hash == 'hash123'

    @patch('services.doc_store.domain.documents.repository.execute_query')
    def test_list_documents(self, mock_query, repository):
        """Test listing documents."""
        mock_docs = [
            {'id': 'doc1', 'content': 'content1', 'content_hash': 'hash1', 'metadata': '{}', 'correlation_id': None, 'created_at': '2024-01-01T00:00:00'},
            {'id': 'doc2', 'content': 'content2', 'content_hash': 'hash2', 'metadata': '{}', 'correlation_id': None, 'created_at': '2024-01-01T01:00:00'}
        ]
        mock_query.return_value = mock_docs

        result = repository.get_all(limit=2, offset=0)

        assert len(result) == 2
        # Repository returns Document entities, not dicts
        assert hasattr(result[0], 'id')
        assert hasattr(result[1], 'id')


@pytest.mark.unit
@pytest.mark.domain
class TestDocumentService(BaseTestCase):
    """Test DocumentService functionality."""

    @pytest.fixture
    def service(self):
        """Create document service instance."""
        from services.doc_store.domain.documents.service import DocumentService
        return DocumentService()

    @pytest.fixture
    def mock_repository(self, service):
        """Mock the repository for isolated testing."""
        with patch.object(service, 'repository') as mock_repo:
            yield mock_repo

    def test_create_document_success(self, service, mock_repository, sample_document):
        """Test successful document creation."""
        # Setup mock
        mock_doc = Mock()
        mock_doc.id = sample_document['id']
        mock_doc.content_hash = 'hash123'
        mock_doc.metadata = sample_document['metadata']
        mock_repository.get_by_content_hash.return_value = None
        mock_repository.calculate_content_hash.return_value = 'hash123'
        mock_repository.save.return_value = None

        with patch.object(service, '_create_entity_from_data', return_value=mock_doc):
            result = service.create_document(
                content=sample_document['content'],
                metadata=sample_document['metadata']
            )

            assert result.id == sample_document['id']
            mock_repository.save.assert_called_once()

    def test_create_document_duplicate_content(self, service, mock_repository, sample_document):
        """Test creating document with duplicate content returns existing."""
        # Setup mock to return existing document
        existing_doc = Mock()
        existing_doc.id = 'existing-doc-id'
        mock_repository.get_by_content_hash.return_value = existing_doc

        result = service.create_document(content=sample_document['content'], metadata=sample_document['metadata'])

        assert result == existing_doc
        mock_repository.save.assert_not_called()

    def test_create_document_empty_content(self, service):
        """Test creating document with empty content raises error."""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            service.create_document(content="")

    def test_create_document_invalid_metadata(self, service):
        """Test creating document with invalid metadata raises error."""
        with pytest.raises(ValueError, match="Metadata must be a dictionary"):
            service.create_document(content="test", metadata="invalid")

    def test_get_document_not_found(self, service, mock_repository):
        """Test getting non-existent document."""
        mock_repository.get_by_id.return_value = None

        result = service.get_entity("non-existent")
        assert result is None

    def test_update_metadata_success(self, service, mock_repository, sample_document_entity):
        """Test successful metadata update."""
        mock_repository.get_by_id.return_value = sample_document_entity

        service.update_metadata(sample_document_entity.id, {"new_field": "value"})

        mock_repository.update.assert_called_once()

    def test_update_metadata_not_found(self, service, mock_repository):
        """Test updating metadata for non-existent document."""
        mock_repository.get_by_id.return_value = None

        from services.shared.error_handling import ServiceException
        with pytest.raises(ServiceException, match="Entity .* not found"):
            service.update_metadata("non-existent", {"field": "value"})

    def test_search_documents_empty_query(self, service):
        """Test searching with empty query raises error."""
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            service.search_documents("")

    @patch('services.doc_store.domain.documents.repository.search_documents')
    def test_search_documents_success(self, mock_search, service):
        """Test successful document search."""
        mock_results = [
            {'id': 'doc1', 'content': 'content with test', 'score': 0.9},
            {'id': 'doc2', 'content': 'another test document', 'score': 0.8}
        ]
        mock_search.return_value = mock_results

        result = service.search_documents("test", limit=10)

        assert result['total'] == 2
        assert result['query'] == 'test'
        assert len(result['items']) == 2

    def test_list_documents_success(self, service, mock_repository):
        """Test successful document listing."""
        mock_doc1 = Mock()
        mock_doc1.to_dict.return_value = {'id': 'doc1', 'content': 'content1'}
        mock_doc2 = Mock()
        mock_doc2.to_dict.return_value = {'id': 'doc2', 'content': 'content2'}
        mock_repository.get_all.return_value = [mock_doc1, mock_doc2]

        result = service.list_entities(limit=10, offset=0)

        assert result['total'] == 2
        assert result['has_more'] is False
        assert result['limit'] == 10
        assert result['offset'] == 0


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.domain
class TestDocumentHandlers(BaseTestCase):
    """Test DocumentHandlers functionality."""

    @pytest.fixture
    def handlers(self):
        """Create document handlers instance."""
        from services.doc_store.domain.documents.handlers import DocumentHandlers
        return DocumentHandlers()

    @pytest.fixture
    def mock_service(self, handlers):
        """Mock the service for isolated testing."""
        with patch.object(handlers, 'service') as mock_svc:
            yield mock_svc

    async def test_handle_create_document_success(self, handlers, sample_document):
        """Test successful document creation via handler."""
        from services.doc_store.core.models import DocumentRequest

        mock_doc = Mock()
        mock_doc.id = sample_document['id']
        mock_doc.content = sample_document['content']
        mock_doc.content_hash = 'hash123'
        mock_doc.metadata = sample_document['metadata']
        mock_doc.correlation_id = sample_document.get('correlation_id')
        mock_doc.created_at.isoformat.return_value = sample_document['created_at']
        mock_doc.to_dict.return_value = sample_document

        with patch.object(handlers.service, 'create_document', return_value=mock_doc):
            request = DocumentRequest(**sample_document)
            result = await handlers.handle_create_document(request)

            self.assert_success_response(result)
            assert result['data']['id'] == sample_document['id']

    async def test_handle_get_document_success(self, handlers, sample_document_entity):
        """Test successful document retrieval via handler."""
        with patch.object(handlers.service, 'get_document', return_value=sample_document_entity):
            result = await handlers.handle_get_document(sample_document_entity.id)

            self.assert_success_response(result)
            assert result['data']['id'] == sample_document_entity.id

    async def test_handle_get_document_not_found(self, handlers):
        """Test retrieving non-existent document via handler."""
        with patch.object(handlers.service, 'get_document', return_value=None):
            result = await handlers.handle_get_document("non-existent")

            assert result['success'] is False
            assert "not found" in result['message'].lower()

    async def test_handle_list_documents_success(self, handlers):
        """Test successful document listing via handler."""
        mock_result = {
            'items': [{'id': 'doc1'}, {'id': 'doc2'}],
            'total': 2,
            'has_more': False,
            'limit': 10,
            'offset': 0
        }

        with patch.object(handlers.service, 'list_documents', return_value=mock_result):
            result = await handlers.handle_list_documents(limit=10, offset=0)

            self.assert_success_response(result)
            assert result['data']['total'] == 2
            assert len(result['data']['items']) == 2

    async def test_handle_search_documents_success(self, handlers):
        """Test successful document search via handler."""
        from services.doc_store.core.models import SearchRequest

        mock_result = {
            'items': [{'id': 'doc1', 'content': 'test content'}],
            'total': 1,
            'query': 'test',
            'limit': 10
        }

        with patch.object(handlers.service, 'search_documents', return_value=mock_result):
            request = SearchRequest(query="test", limit=10)
            result = await handlers.handle_search_documents(request)

            self.assert_success_response(result)
            assert result['data']['total'] == 1

    async def test_handle_search_documents_empty_query(self, handlers, mock_service):
        """Test search with empty query raises error."""
        from services.doc_store.core.models import SearchRequest

        mock_service.search_documents.side_effect = ValueError("Search query cannot be empty")

        request = SearchRequest(query="", limit=10)
        result = await handlers.handle_search_documents(request)

        assert result['success'] is False
        assert "empty" in result['message'].lower()
