"""Unit tests for base classes and utilities.

Tests for BaseEntity, BaseRepository, BaseService, BaseHandler, and utility functions.
"""
import pytest
from unittest.mock import patch, Mock
from datetime import datetime
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.unit
class TestBaseEntity(BaseTestCase):
    """Test BaseEntity functionality."""

    def test_document_entity_inheritance(self):
        """Test Document entity inherits from BaseEntity."""
        from services.doc_store.core.entities import Document

        doc = Document(
            id="test-doc",
            content="Test content",
            content_hash="hash123",
            metadata={"type": "test"}
        )

        # Should have BaseEntity methods
        assert hasattr(doc, 'update_timestamp')
        assert hasattr(doc, 'to_dict')

        # Should have document-specific attributes
        assert doc.content == "Test content"
        assert doc.content_hash == "hash123"

    def test_to_dict_method(self):
        """Test to_dict method works correctly."""
        from services.doc_store.core.entities import Document

        doc = Document(
            id="test-doc",
            content="Test content",
            content_hash="hash123",
            metadata={"type": "test"},
            correlation_id="corr123"
        )

        result = doc.to_dict()

        assert result['id'] == "test-doc"
        assert result['content'] == "Test content"
        assert result['metadata']['type'] == "test"
        assert result['correlation_id'] == "corr123"
        assert 'created_at' in result


@pytest.mark.unit
class TestBaseRepository(BaseTestCase):
    """Test BaseRepository functionality."""

    @pytest.fixture
    def repository(self):
        """Create a test repository instance."""
        from services.doc_store.core.repository import BaseRepository

        class TestRepository(BaseRepository):
            def __init__(self):
                super().__init__("test_table")

            def _row_to_entity(self, row):
                # Mock conversion
                entity = Mock()
                entity.id = row.get('id')
                entity.name = row.get('name')
                return entity

            def _entity_to_row(self, entity):
                return {'id': entity.id, 'name': entity.name}

        return TestRepository()

    def test_repository_initialization(self, repository):
        """Test repository initializes correctly."""
        assert repository.table_name == "test_table"

    def test_get_by_id_success(self, repository, mock_execute_query):
        """Test getting entity by ID."""
        mock_row = {'id': 'test-id', 'name': 'test-name'}
        mock_execute_query.return_value = mock_row

        result = repository.get_by_id('test-id')

        assert result.id == 'test-id'
        assert result.name == 'test-name'
        mock_execute_query.assert_called_once()

    def test_get_by_id_not_found(self, repository, mock_execute_query):
        """Test getting non-existent entity."""
        mock_execute_query.return_value = None

        result = repository.get_by_id('non-existent')

        assert result is None

    def test_get_all_with_pagination(self, repository, mock_execute_query):
        """Test getting all entities with pagination."""
        mock_rows = [
            {'id': '1', 'name': 'item1'},
            {'id': '2', 'name': 'item2'}
        ]
        mock_execute_query.return_value = mock_rows

        result = repository.get_all(limit=10, offset=0)

        assert len(result) == 2
        assert result[0].id == '1'
        assert result[1].name == 'item2'

    def test_save_entity(self, repository, mock_execute_query):
        """Test saving an entity."""
        entity = Mock()
        entity.id = 'test-id'
        entity.name = 'test-name'

        repository.save(entity)

        mock_execute_query.assert_called_once()
        # Verify the INSERT query structure
        call_args = mock_execute_query.call_args
        query = call_args[0][0]
        assert 'INSERT OR REPLACE INTO' in query.upper()
        assert 'test_table' in query

    def test_update_entity(self, repository, mock_execute_query):
        """Test updating an entity."""
        entity = Mock()
        entity.id = 'test-id'
        entity.name = 'updated-name'
        entity.update_timestamp = Mock()

        repository.update(entity)

        # Should call update_timestamp and execute UPDATE query
        entity.update_timestamp.assert_called_once()
        mock_execute_query.assert_called_once()

        call_args = mock_execute_query.call_args
        query = call_args[0][0]
        assert 'UPDATE' in query.upper()
        assert 'test_table' in query

    def test_delete_by_id(self, repository, mock_execute_query):
        """Test deleting entity by ID."""
        repository.delete_by_id('test-id')

        mock_execute_query.assert_called_once()
        call_args = mock_execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert 'DELETE FROM' in query.upper()
        assert 'test_table' in query
        assert params[0] == 'test-id'

    def test_exists_entity(self, repository, mock_execute_query):
        """Test checking if entity exists."""
        mock_execute_query.return_value = {'id': 'test-id'}  # Any row means exists

        exists = repository.exists('test-id')

        assert exists is True

        mock_execute_query.return_value = None  # No row means doesn't exist
        exists = repository.exists('non-existent')

        assert exists is False

    def test_count_entities(self, repository, mock_execute_query):
        """Test counting entities."""
        mock_execute_query.return_value = {'count': 42}

        count = repository.count()

        assert count == 42
        mock_execute_query.assert_called_once()


@pytest.mark.unit
class TestBaseService(BaseTestCase):
    """Test BaseService functionality."""

    @pytest.fixture
    def service(self):
        """Create a test service instance."""
        from services.doc_store.core.service import BaseService
        from services.doc_store.core.entities import BaseEntity

        class TestEntity(BaseEntity):
            def __init__(self, id, name):
                self.id = id
                self.name = name
                self.created_at = None
                self.updated_at = None

            def to_dict(self):
                return {"id": self.id, "name": self.name}

        class TestRepository:
            def save(self, entity):
                pass

            def get_by_id(self, id):
                return TestEntity(id, "test")

            def update(self, entity):
                pass

            def delete_by_id(self, id):
                pass

        class TestService(BaseService):
            def __init__(self):
                super().__init__(TestRepository())

            def _create_entity_from_data(self, entity_id, data):
                return TestEntity(entity_id, data.get("name"))

            def _validate_entity(self, entity):
                return True

        return TestService()

    @pytest.fixture
    def mock_repository(self, service):
        """Mock the repository for testing."""
        with patch.object(service, 'repository') as mock_repo:
            yield mock_repo

    def test_create_entity_success(self, service, mock_repository):
        """Test creating an entity."""
        result = service.create_entity({'name': 'test'}, entity_id='test-id')

        assert result.id == 'test-id'
        assert result.name == 'test'
        mock_repository.save.assert_called_once()

    def test_get_entity_success(self, service, mock_repository):
        """Test getting an entity."""
        mock_entity = Mock()
        mock_entity.id = 'test-id'
        mock_entity.name = 'test'
        mock_repository.get_by_id.return_value = mock_entity

        result = service.get_entity('test-id')

        assert result.id == 'test-id'
        mock_repository.get_by_id.assert_called_once_with('test-id')

    def test_get_entity_not_found(self, service, mock_repository):
        """Test getting non-existent entity."""
        mock_repository.get_by_id.return_value = None

        result = service.get_entity('non-existent')

        assert result is None

    def test_update_entity_success(self, service, mock_repository):
        """Test updating an entity."""
        mock_entity = Mock()
        mock_entity.id = 'test-id'
        mock_entity.name = 'test'
        mock_entity.update_timestamp = Mock()
        mock_repository.get_by_id.return_value = mock_entity

        result = service.update_entity('test-id', {'name': 'updated'})

        assert result == mock_entity
        mock_repository.update.assert_called_once_with(mock_entity)

    def test_update_entity_not_found(self, service, mock_repository):
        """Test updating non-existent entity."""
        mock_repository.get_by_id.return_value = None

        from services.shared.error_handling import ServiceException
        with pytest.raises(ServiceException, match="Entity .* not found"):
            service.update_entity('non-existent', {'name': 'updated'})

    def test_delete_entity_success(self, service, mock_repository):
        """Test deleting an entity."""
        mock_entity = Mock()
        mock_entity.id = 'test-id'
        mock_entity.name = 'test'
        mock_repository.get_by_id.return_value = mock_entity
        mock_repository.exists.return_value = True

        result = service.delete_entity('test-id')

        assert result is None  # delete_entity returns None
        mock_repository.delete_by_id.assert_called_once_with('test-id')

    def test_list_entities_success(self, service, mock_repository):
        """Test listing entities."""
        mock_entities = [Mock(id='1', name='entity1', to_dict=lambda: {'id': '1', 'name': 'entity1'}),
                        Mock(id='2', name='entity2', to_dict=lambda: {'id': '2', 'name': 'entity2'})]
        mock_repository.get_all.return_value = mock_entities

        result = service.list_entities(limit=10, offset=0)

        assert len(result['items']) == 2
        assert result['total'] == 2
        assert result['limit'] == 10
        assert result['offset'] == 0


@pytest.mark.asyncio
@pytest.mark.unit
class TestBaseHandler(BaseTestCase):
    """Test BaseHandler functionality."""

    @pytest.fixture
    def handler(self):
        """Create a test handler instance."""
        from services.doc_store.core.handler import BaseHandler
        from services.doc_store.core.entities import BaseEntity
        from services.doc_store.core.service import BaseService

        class TestEntity(BaseEntity):
            def __init__(self, id, name):
                self.id = id
                self.name = name
                self.created_at = None
                self.updated_at = None

            def to_dict(self):
                return {"id": self.id, "name": self.name}

        class TestRepository:
            def save(self, entity):
                pass

            def get_by_id(self, id):
                return TestEntity(id, "test")

            def update(self, entity):
                pass

            def delete_by_id(self, id):
                pass

        class TestService(BaseService):
            def __init__(self):
                super().__init__(TestRepository())

            def _create_entity_from_data(self, entity_id, data):
                return TestEntity(entity_id, data.get("name"))

            def _validate_entity(self, entity):
                return True

        class TestHandler(BaseHandler):
            def __init__(self):
                self.service = TestService()

        return TestHandler()

    @pytest.fixture
    def mock_service(self, handler):
        """Mock the service for testing."""
        with patch.object(handler, 'service') as mock_svc:
            yield mock_svc

    async def test_handle_create_success(self, handler):
        """Test successful entity creation via handler."""
        expected_response = {
            'success': True,
            'message': 'Operation completed successfully',
            'data': {'id': 'test-id', 'name': 'test'},
            'request_id': None
        }

        with patch.object(handler, '_handle_request', return_value=expected_response):
            result = await handler.handle_create({'name': 'test'})

            self.assert_success_response(result)
            assert result['data']['id'] == 'test-id'

    async def test_handle_get_success(self, handler):
        """Test successful entity retrieval via handler."""
        expected_response = {
            'success': True,
            'message': 'Operation completed successfully',
            'data': {'id': 'test-id', 'name': 'test'},
            'request_id': None
        }

        with patch.object(handler, '_handle_request', return_value=expected_response):
            result = await handler.handle_get('test-id')

            self.assert_success_response(result)
            assert result['data']['id'] == 'test-id'

    async def test_handle_get_not_found(self, handler):
        """Test retrieving non-existent entity via handler."""
        with patch.object(handler, '_handle_request', return_value=None):
            result = await handler.handle_get('non-existent')

            assert result['success'] is False
            assert "not found" in result['message'].lower()

    async def test_handle_update_success(self, handler):
        """Test successful entity update via handler."""
        expected_response = {
            'success': True,
            'message': 'Operation completed successfully',
            'data': {'id': 'test-id', 'name': 'updated'},
            'request_id': None
        }

        with patch.object(handler, '_handle_request', return_value=expected_response):
            result = await handler.handle_update('test-id', {'name': 'updated'})

            self.assert_success_response(result)
            assert result['data']['name'] == 'updated'

    async def test_handle_delete_success(self, handler, mock_service):
        """Test successful entity deletion via handler."""
        mock_service.delete_entity.return_value = True

        result = await handler.handle_delete('test-id')

        self.assert_success_response(result)

    async def test_handle_list_success(self, handler, mock_service):
        """Test successful entity listing via handler."""
        mock_result = {
            'items': [{'id': '1'}, {'id': '2'}],
            'total': 2,
            'limit': 10,
            'offset': 0
        }
        mock_service.list_entities.return_value = mock_result

        result = await handler.handle_list(limit=10, offset=0)

        self.assert_success_response(result)
        assert result['data']['total'] == 2
