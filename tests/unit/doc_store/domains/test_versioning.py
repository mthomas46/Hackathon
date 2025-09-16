"""Versioning domain tests.

Comprehensive tests for document versioning, history tracking, and rollback functionality.
"""
import pytest
from unittest.mock import patch, Mock
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.unit
@pytest.mark.domain
class TestVersioningRepository(BaseTestCase):
    """Test VersioningRepository functionality."""

    @pytest.fixture
    def repository(self):
        """Create versioning repository instance."""
        from services.doc_store.domain.versioning.repository import VersioningRepository
        return VersioningRepository()

    def test_get_version_history(self, repository, mock_execute_query):
        """Test getting version history for a document."""
        mock_versions = [
            {
                'id': 'v1',
                'document_id': 'doc1',
                'version_number': 1,
                'content': 'Version 1 content',
                'content_hash': 'hash1',
                'change_summary': 'Initial version',
                'created_at': '2024-01-01T00:00:00'
            },
            {
                'id': 'v2',
                'document_id': 'doc1',
                'version_number': 2,
                'content': 'Version 2 content',
                'content_hash': 'hash2',
                'change_summary': 'Updated content',
                'created_at': '2024-01-02T00:00:00'
            }
        ]
        with patch('services.doc_store.domain.versioning.repository.execute_query', return_value=mock_versions):
            history = repository.get_versions_for_document('doc1')

            assert len(history) == 2
            assert history[0].version_number == 1
            assert history[1].version_number == 2

    def test_create_version(self, repository, mock_execute_query):
        """Test creating a new version."""
        repository.create_version('doc1', 'Updated content', 'hash123', 'Fixed bug')

        assert mock_execute_query.called
        # Verify the insert query structure
        call_args = mock_execute_query.call_args
        query = call_args[0][0]
        params = call_args[0][1]

        assert 'INSERT OR REPLACE INTO' in query.upper()
        assert 'document_versions' in query
        assert params[0] == 'doc1:v1'  # id (document_id:v{version})
        assert params[1] == 'doc1'  # document_id
        assert params[2] == 1      # version_number (first version)
        assert params[3] == 'Updated content'


@pytest.mark.unit
@pytest.mark.domain
class TestVersioningService(BaseTestCase):
    """Test VersioningService functionality."""

    @pytest.fixture
    def service(self):
        """Create versioning service instance."""
        from services.doc_store.domain.versioning.service import VersioningService
        return VersioningService()

    @pytest.fixture
    def mock_repository(self, service):
        """Mock the repository for isolated testing."""
        with patch.object(service, 'repository') as mock_repo:
            yield mock_repo

    def test_create_version_success(self, service):
        """Test successful version creation."""
        with patch.object(service.repository, 'get_latest_version_number', return_value=0), \
             patch.object(service.repository, 'save') as mock_save:
            mock_version = Mock()
            mock_version.version_number = 1
            mock_version.document_id = 'doc1'
            mock_save.return_value = mock_version

            result = service.create_version('doc1', 'content', 'hash123', 'Initial version')

            assert result.version_number == 1
            assert result.document_id == 'doc1'

    def test_get_version_history(self, service):
        """Test getting version history."""
        mock_version1 = Mock()
        mock_version1.version_number = 1
        mock_version1.to_dict.return_value = {'version_number': 1, 'content': 'content1'}
        mock_version2 = Mock()
        mock_version2.version_number = 2
        mock_version2.to_dict.return_value = {'version_number': 2, 'content': 'content2'}

        with patch.object(service.repository, 'get_versions_for_document', return_value=[mock_version1, mock_version2]):
            result = service.get_document_versions('doc1')

            assert 'versions' in result
            assert len(result['versions']) == 2
            assert result['versions'][0]['version_number'] == 1
            assert result['versions'][1]['version_number'] == 2

    def test_compare_versions(self, service, mock_repository):
        """Test version comparison."""
        mock_comparison = {
            'document_id': 'doc1',
            'comparison': {'version_a': 1, 'version_b': 2},
            'content_diff': {'content_changed': True}
        }
        mock_repository.compare_versions.return_value = mock_comparison

        comparison = service.compare_versions('doc1', 1, 2)

        assert 'comparison' in comparison
        assert comparison['comparison']['version_a'] == 1
        assert comparison['comparison']['version_b'] == 2
        assert 'content_diff' in comparison

    def test_rollback_to_version(self, service):
        """Test rolling back to a specific version."""
        mock_target_version = Mock(content='Rollback content', metadata={}, content_hash='hash123')
        mock_new_version = Mock(version_number=3)

        with patch.object(service.repository, 'get_version_by_number', return_value=mock_target_version), \
             patch.object(service.repository, 'get_latest_version_number', return_value=2), \
             patch.object(service.repository, 'save', return_value=mock_new_version):
            result = service.rollback_to_version('doc1', 2)

            assert result.version_number == 3  # New version created for rollback


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.domain
class TestVersioningHandlers(BaseTestCase):
    """Test VersioningHandlers functionality."""

    @pytest.fixture
    def handlers(self):
        """Create versioning handlers instance."""
        from services.doc_store.domain.versioning.handlers import VersioningHandlers
        return VersioningHandlers()

    @pytest.fixture
    def mock_service(self, handlers):
        """Mock the service for isolated testing."""
        with patch.object(handlers, 'service') as mock_svc:
            yield mock_svc

    async def test_handle_get_document_versions_success(self, handlers, mock_service):
        """Test successful document versions retrieval via handler."""
        mock_result = {
            'versions': [{'version_number': 1, 'content_hash': 'hash123'}],
            'total': 1,
            'document_id': 'doc1'
        }
        mock_service.get_document_versions.return_value = mock_result

        result = await handlers.handle_get_document_versions('doc1', limit=10)

        self.assert_success_response(result)
        assert result['data']['total'] == 1
        assert len(result['data']['versions']) == 1

    async def test_handle_cleanup_versions_success(self, handlers, mock_service):
        """Test successful version cleanup."""
        mock_result = {
            'versions_deleted': 5,
            'versions_kept': 10,
            'document_id': 'doc1'
        }
        mock_service.cleanup_versions.return_value = mock_result

        result = await handlers.handle_cleanup_versions('doc1', keep_versions=10)

        self.assert_success_response(result)
        assert result['data']['versions_deleted'] == 5

    async def test_handle_compare_versions_success(self, handlers, mock_service):
        """Test successful version comparison."""
        mock_comparison = {
            'differences': ['Content changed'],
            'from_version': 1,
            'to_version': 2
        }
        mock_service.compare_versions.return_value = mock_comparison

        result = await handlers.handle_compare_versions('doc1', 1, 2)

        self.assert_success_response(result)
        assert 'differences' in result['data']

    async def test_handle_rollback_version_success(self, handlers, mock_service):
        """Test successful version rollback."""
        mock_version = Mock()
        mock_version.to_dict.return_value = {'version_number': 3, 'content': 'rolled back content'}
        mock_version.version_number = 3
        mock_service.rollback_to_version.return_value = mock_version

        result = await handlers.handle_rollback_version('doc1', 2)

        self.assert_success_response(result)
        assert result['data']['version_number'] == 3
