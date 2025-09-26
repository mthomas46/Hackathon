"""Bulk operations domain tests.

Comprehensive tests for bulk document operations, processing, and management.
"""
import pytest
from unittest.mock import patch, AsyncMock, Mock
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.unit
@pytest.mark.domain
class TestBulkOperationsRepository(BaseTestCase):
    """Test BulkOperationsRepository functionality."""

    @pytest.fixture
    def repository(self):
        """Create bulk operations repository instance."""
        from services.doc_store.domain.bulk.repository import BulkOperationsRepository
        return BulkOperationsRepository()

    def test_get_operation_by_id(self, repository, mock_execute_query):
        """Test getting bulk operation by ID."""
        mock_operation = {
            'operation_id': 'bulk123',
            'operation_type': 'create_documents',
            'status': 'processing',
            'total_items': 10,
            'processed_items': 5,
            'successful_items': 4,
            'failed_items': 1,
            'errors': '["error1"]',
            'results': '[{"id": "doc1"}]',
            'metadata': '{"source": "test"}',
            'created_at': '2024-01-01T00:00:00',
            'completed_at': None
        }
        mock_execute_query.return_value = mock_operation

        operation = repository.get_by_id('bulk123')

        assert operation.operation_id == 'bulk123'
        assert operation.operation_type == 'create_documents'
        assert operation.total_items == 10
        assert operation.processed_items == 5

    def test_update_operation_progress(self, repository):
        """Test updating operation progress."""
        with patch('services.doc_store.domain.bulk.repository.execute_query') as mock_execute:
            repository.update_operation_progress('bulk123', processed=5, successful=4, failed=1)

            # Verify the update query was called
            assert mock_execute.called
            call_args = mock_execute.call_args
            query = call_args[0][0]
            params = call_args[0][1]

        assert 'UPDATE' in query.upper()
        assert 'bulk_operations' in query
        assert params[0] == 5   # processed_items
        assert params[1] == 4   # successful_items
        assert params[2] == 1   # failed_items
        assert params[3] == 'bulk123'  # operation_id

    def test_add_operation_result(self, repository):
        """Test adding operation result."""
        result = {'id': 'doc1', 'status': 'success'}

        with patch('services.doc_store.domain.bulk.repository.execute_query') as mock_execute:
            repository.add_operation_result('bulk123', result)

            assert mock_execute.called


@pytest.mark.unit
@pytest.mark.domain
class TestBulkOperationsService(BaseTestCase):
    """Test BulkOperationsService functionality."""

    @pytest.fixture
    def service(self):
        """Create bulk operations service instance."""
        from services.doc_store.domain.bulk.service import BulkOperationsService
        return BulkOperationsService()

    @pytest.fixture
    def mock_repository(self, service):
        """Mock the repository for isolated testing."""
        with patch.object(service, 'repository') as mock_repo:
            yield mock_repo

    def test_create_bulk_operation_success(self, service, mock_repository):
        """Test successful bulk operation creation."""
        mock_operation = Mock()
        mock_operation.operation_id = 'bulk123'
        mock_repository.create_entity.return_value = mock_operation

        with patch('asyncio.create_task'):
            result = service.create_bulk_operation('create_documents', [{'content': 'test'}])

            assert result.operation_id is not None
            assert isinstance(result.operation_id, str)
            assert len(result.operation_id) > 0
            mock_repository.save.assert_called_once()

    def test_create_bulk_operation_validation(self, service):
        """Test bulk operation creation validation."""
        # Empty documents
        with pytest.raises(ValueError, match="Total items must be positive"):
            service.create_bulk_operation('create_documents', [])

        # Invalid operation type
        with pytest.raises(ValueError, match="Invalid operation type"):
            service.create_bulk_operation('invalid_type', [{'content': 'test'}])

    @pytest.mark.asyncio
    async def test_process_bulk_operation_create_documents(self, service, mock_repository):
        """Test processing bulk document creation."""
        mock_operation = Mock()
        mock_operation.operation_id = 'bulk123'
        mock_operation.operation_type = 'create_documents'
        mock_operation.status = 'pending'
        mock_operation.total_items = 2

        mock_repository.get_by_id.return_value = mock_operation

        # Mock document creation - patch at the method level
        mock_doc_service = Mock()
        mock_doc_service.create_document.side_effect = [
            Mock(id='doc1', content='test1'),
            Mock(id='doc2', content='test2')
        ]

        # Create proper BulkDocumentItem objects
        from services.doc_store.core.entities import BulkDocumentItem
        items = [
            BulkDocumentItem(content='test1'),
            BulkDocumentItem(content='test2')
        ]

        # Patch the DocumentService import inside the method
        with patch('services.doc_store.domain.documents.service.DocumentService', return_value=mock_doc_service):
            await service._process_document_creation('bulk123', items)

            # Verify operation completion
            mock_repository.complete_operation.assert_called_once()
            call_args = mock_repository.complete_operation.call_args[0]
            assert call_args[0] == 'bulk123'  # operation_id
            results = call_args[1][0]  # results list
            assert results['successful'] == 2
            assert results['failed'] == 0
            assert results['total_processed'] == 2

    def test_get_operation_status(self, service, mock_repository):
        """Test getting operation status."""
        mock_operation = Mock()
        mock_operation.to_dict.return_value = {
            'operation_id': 'bulk123',
            'status': 'completed',
            'progress': {'percentage': 100.0}
        }
        mock_repository.get_by_id.return_value = mock_operation

        result = service.get_operation_status('bulk123')

        assert result['operation_id'] == 'bulk123'
        assert result['status'] == 'completed'

    def test_list_operations_with_filtering(self, service, mock_repository):
        """Test listing operations with filtering."""
        mock_operations = [Mock(to_dict=lambda: {'operation_id': 'bulk123'})]
        mock_repository.get_operations_by_status.return_value = mock_operations

        result = service.list_operations(status='completed', limit=20)

        assert result['total'] == 1
        assert len(result['operations']) == 1
        mock_repository.get_operations_by_status.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.domain
class TestBulkOperationsHandlers(BaseTestCase):
    """Test BulkOperationsHandlers functionality."""

    @pytest.fixture
    def handlers(self):
        """Create bulk operations handlers instance."""
        from services.doc_store.domain.bulk.handlers import BulkOperationsHandlers
        return BulkOperationsHandlers()

    @pytest.fixture
    def mock_service(self, handlers):
        """Mock the service for isolated testing."""
        with patch.object(handlers, 'service') as mock_svc:
            yield mock_svc

    async def test_handle_create_bulk_operation_success(self, handlers, mock_service):
        """Test successful bulk operation creation via handler."""
        mock_operation = Mock()
        mock_operation.to_dict.return_value = {
            'operation_id': 'bulk123',
            'operation_type': 'create_documents',
            'status': 'pending'
        }
        mock_service.create_bulk_operation.return_value = mock_operation

        result = await handlers.handle_bulk_create_documents([{'content': 'test'}])

        self.assert_success_response(result)
        assert result['data']['operation_id'] == 'bulk123'

    async def test_handle_get_operation_status_success(self, handlers, mock_service):
        """Test successful operation status retrieval."""
        mock_status = {'operation_id': 'bulk123', 'status': 'processing', 'progress': {'percentage': 50.0}}
        mock_service.get_operation_status.return_value = mock_status

        result = await handlers.handle_get_bulk_operation_status('bulk123')

        self.assert_success_response(result)
        assert result['data']['status'] == 'processing'

    async def test_handle_list_operations_success(self, handlers, mock_service):
        """Test successful operations listing."""
        mock_result = {
            'operations': [{'operation_id': 'bulk123'}],
            'total': 1,
            'limit': 50
        }
        mock_service.list_operations.return_value = mock_result

        result = await handlers.handle_list_bulk_operations(limit=50)

        self.assert_success_response(result)
        assert result['data']['total'] == 1
