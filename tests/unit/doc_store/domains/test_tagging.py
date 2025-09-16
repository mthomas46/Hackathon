"""Tagging domain tests.

Comprehensive tests for semantic tagging, taxonomy management, and automated tagging.
"""
import pytest
from unittest.mock import patch, Mock
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.unit
@pytest.mark.domain
class TestTaggingRepository(BaseTestCase):
    """Test TaggingRepository functionality."""

    @pytest.fixture
    def repository(self):
        """Create tagging repository instance."""
        from services.doc_store.domain.tagging.repository import TaggingRepository
        return TaggingRepository()

    def test_get_document_tags(self, repository, mock_execute_query):
        """Test getting tags for a document."""
        mock_tags = [
            {
                'id': 'tag1',
                'document_id': 'doc1',
                'tag': 'python',
                'confidence': 0.9,
                'created_at': '2024-01-01T00:00:00'
            }
        ]
        with patch('services.doc_store.domain.tagging.repository.execute_query', return_value=mock_tags):
            tags = repository.get_tags_for_document('doc1')

            assert len(tags) == 1
            assert tags[0].tag == 'python'
            assert tags[0].confidence == 0.9


@pytest.mark.unit
@pytest.mark.domain
class TestTaggingService(BaseTestCase):
    """Test TaggingService functionality."""

    @pytest.fixture
    def service(self):
        """Create tagging service instance."""
        from services.doc_store.domain.tagging.service import TaggingService
        return TaggingService()

    @pytest.fixture
    def mock_repository(self, service):
        """Mock the repository for isolated testing."""
        with patch.object(service, 'repository') as mock_repo:
            yield mock_repo

    def test_tag_document_success(self, service, mock_repository):
        """Test successful document tagging."""
        mock_tag = Mock()
        mock_tag.tag = 'python'
        mock_tag.confidence = 0.9
        mock_repository.create_entity.return_value = mock_tag

        result = service.tag_document('doc1', 'This is python code content', metadata={'tags': ['python']})

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0].tag == 'python'
        assert result[0].confidence == 0.9

    def test_extract_entities_from_content(self, service):
        """Test entity extraction from content."""
        content = """
        This document discusses Python programming and machine learning.
        It also covers API development and database design.
        """

        # Test the internal _analyze_content method
        entities = service._analyze_content(content, {})

        assert len(entities) > 0
        # Should extract technical terms
        entity_values = {e.entity_value for e in entities}
        assert any('python' in e.lower() for e in entity_values)

    def test_categorize_entity(self, service):
        """Test entity categorization."""
        entity = Mock(entity_type='programming_language', entity_value='Python')

        category = service._categorize_entity(entity)

        assert category == 'language'


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.domain
class TestTaggingHandlers(BaseTestCase):
    """Test TaggingHandlers functionality."""

    @pytest.fixture
    def handlers(self):
        """Create tagging handlers instance."""
        from services.doc_store.domain.tagging.handlers import TaggingHandlers
        return TaggingHandlers()

    @pytest.fixture
    def mock_service(self, handlers):
        """Mock the service for isolated testing."""
        with patch.object(handlers, 'service') as mock_svc:
            yield mock_svc

    async def test_handle_tag_document_success(self, handlers):
        """Test successful document tagging via handler."""
        expected_response = {
            'success': True,
            'message': 'Operation completed successfully',
            'data': {'tags': [{'tag': 'python', 'confidence': 0.9}], 'count': 1},
            'request_id': None
        }

        with patch.object(handlers, '_handle_request', return_value=expected_response):
            result = await handlers.handle_tag_document('doc1')

            self.assert_success_response(result)
            assert result['data']['count'] == 1

    async def test_handle_get_document_tags_success(self, handlers):
        """Test successful document tags retrieval."""
        expected_response = {
            'success': True,
            'message': 'Operation completed successfully',
            'data': [{'tag': 'python'}, {'tag': 'api'}],
            'request_id': None
        }

        with patch.object(handlers, '_handle_request', return_value=expected_response):
            result = await handlers.handle_get_document_tags('doc1')

            self.assert_success_response(result)
            assert len(result['data']) == 2
