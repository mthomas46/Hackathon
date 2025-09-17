"""Relationships domain tests.

Comprehensive tests for document relationships, graph analysis, and connectivity features.
"""
import pytest
from unittest.mock import patch, Mock
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.unit
@pytest.mark.domain
class TestRelationshipsRepository(BaseTestCase):
    """Test RelationshipsRepository functionality."""

    @pytest.fixture
    def repository(self):
        """Create relationships repository instance."""
        from services.doc_store.domain.relationships.repository import RelationshipsRepository
        return RelationshipsRepository()

    def test_get_relationships_for_document_outgoing(self, repository):
        """Test getting outgoing relationships for a document."""
        mock_relationships = [
            {
                'id': 'rel1',
                'source_document_id': 'doc1',
                'target_document_id': 'doc2',
                'relationship_type': 'references',
                'strength': 0.8,
                'metadata': '{"line": 42}',
                'created_at': '2024-01-01T00:00:00',
                'updated_at': None
            }
        ]

        with patch('services.doc_store.domain.relationships.repository.execute_query', return_value=mock_relationships):
            relationships = repository.get_relationships_for_document('doc1', direction='outgoing')

            assert len(relationships) == 1
            assert relationships[0].id == 'rel1'
            assert relationships[0].source_document_id == 'doc1'
            assert relationships[0].target_document_id == 'doc2'
            assert relationships[0].relationship_type == 'references'

    def test_get_relationships_for_document_both_directions(self, repository, mock_execute_query):
        """Test getting relationships in both directions."""
        mock_relationships = [
            {
                'id': 'rel1',
                'source_document_id': 'doc1',
                'target_document_id': 'doc2',
                'relationship_type': 'references',
                'strength': 0.8,
                'metadata': '{}',
                'created_at': '2024-01-01T00:00:00',
                'updated_at': None
            },
            {
                'id': 'rel2',
                'source_document_id': 'doc3',
                'target_document_id': 'doc1',
                'relationship_type': 'extends',
                'strength': 0.9,
                'metadata': '{}',
                'created_at': '2024-01-01T01:00:00',
                'updated_at': None
            }
        ]
        with patch('services.doc_store.domain.relationships.repository.execute_query', return_value=mock_relationships):
            relationships = repository.get_relationships_for_document('doc1', direction='both')

            assert len(relationships) == 2
            rel_types = {r.relationship_type for r in relationships}
            assert rel_types == {'references', 'extends'}

    def test_get_relationship_types_distribution(self, repository, mock_execute_query):
        """Test getting relationship types distribution."""
        mock_types = [
            {'relationship_type': 'references', 'count': 10},
            {'relationship_type': 'extends', 'count': 5},
            {'relationship_type': 'implements', 'count': 3}
        ]
        with patch('services.doc_store.domain.relationships.repository.execute_query', return_value=mock_types):
            distribution = repository.get_relationship_types()

            assert distribution['references'] == 10
            assert distribution['extends'] == 5
            assert distribution['implements'] == 3

    def test_find_paths_simple(self, repository):
        """Test finding simple paths between documents."""
        # Mock the get_relationships_for_document method
        with patch.object(repository, 'get_relationships_for_document') as mock_get_rels:
            # doc1 -> doc2 -> doc3
            mock_get_rels.side_effect = [
                [Mock(source_document_id='doc1', target_document_id='doc2', relationship_type='references')],
                [Mock(source_document_id='doc2', target_document_id='doc3', relationship_type='references')],
                []  # No further relationships
            ]

            paths = repository.find_paths('doc1', 'doc3', max_depth=3)

            assert len(paths) == 1
            assert paths[0] == ['doc1', 'doc2', 'doc3']

    def test_find_paths_no_path(self, repository):
        """Test finding paths when no path exists."""
        with patch.object(repository, 'get_relationships_for_document', return_value=[]):
            paths = repository.find_paths('doc1', 'doc2', max_depth=3)

            assert len(paths) == 0

    def test_get_graph_statistics_comprehensive(self, repository):
        """Test comprehensive graph statistics calculation."""
        with patch.object(repository, 'get_relationship_types', return_value={'references': 10, 'extends': 5}), \
             patch('services.doc_store.domain.relationships.repository.execute_query') as mock_execute:
            mock_execute.side_effect = [
                {'count': 25},      # total relationships
                {'count': 10},      # unique documents
                {'count': 15}       # total connections for degree calculation
            ]

            stats = repository.get_graph_statistics()

            assert stats['total_relationships'] == 25
            assert stats['unique_documents'] == 10
            assert stats['relationship_types']['references'] == 10
            assert stats['relationship_types']['extends'] == 5
            assert stats['avg_degree'] == 1.5  # 15 total connections / 10 documents
            assert stats['density'] == 25 / (10 * 9 / 2)  # actual / possible connections


@pytest.mark.unit
@pytest.mark.domain
class TestRelationshipsService(BaseTestCase):
    """Test RelationshipsService functionality."""

    @pytest.fixture
    def service(self):
        """Create relationships service instance."""
        from services.doc_store.domain.relationships.service import RelationshipsService
        return RelationshipsService()

    @pytest.fixture
    def mock_repository(self, service):
        """Mock the repository for isolated testing."""
        with patch.object(service, 'repository') as mock_repo:
            yield mock_repo

    def test_create_relationship_success(self, service, mock_repository):
        """Test successful relationship creation."""
        result = service.create_relationship('doc1', 'doc2', 'references', strength=0.8)

        # Service creates entity with auto-generated UUID
        assert result is not None
        assert hasattr(result, 'id')
        assert result.source_document_id == 'doc1'
        assert result.target_document_id == 'doc2'
        assert result.relationship_type == 'references'
        assert result.strength == 0.8
        mock_repository.save.assert_called_once()

    def test_create_relationship_validation_errors(self, service):
        """Test relationship creation validation."""
        # Same source and target
        with pytest.raises(ValueError, match="Cannot create relationship to self"):
            service.create_relationship('doc1', 'doc1', 'references')

        # Invalid strength
        with pytest.raises(ValueError, match="Relationship strength must be between 0 and 1"):
            service.create_relationship('doc1', 'doc2', 'references', strength=1.5)

        # Missing relationship type
        with pytest.raises(ValueError, match="Relationship type is required"):
            service.create_relationship('doc1', 'doc2', '')

    def test_get_relationships_for_document(self, service, mock_repository):
        """Test getting relationships for a document."""
        mock_relationships = [
            Mock(source_document_id='doc1', target_document_id='doc2', relationship_type='references',
                 to_dict=lambda: {'source_id': 'doc1', 'target_id': 'doc2', 'relationship_type': 'references'})
        ]
        mock_repository.get_relationships_for_document.return_value = mock_relationships

        result = service.get_relationships_for_document('doc1', direction='outgoing', limit=10)

        assert result['document_id'] == 'doc1'
        assert len(result['relationships']) == 1
        assert result['direction'] == 'outgoing'
        assert result['limit'] == 10

    def test_find_paths_validation(self, service):
        """Test path finding validation."""
        with pytest.raises(ValueError, match="Max depth must be between 1 and 5"):
            service.find_paths('doc1', 'doc2', max_depth=10)


    def test_extract_relationships_from_content(self, service):
        """Test relationship extraction from document content."""
        content = '''
        This document references api-guide-doc and extends base-module-doc.
        It also uses @utility-functions and implements interface-spec.
        Check out https://github.com/example/repo for more info.
        '''

        relationships = service.extract_relationships_from_content('doc1', content)

        # Should extract various types of relationships
        assert len(relationships) > 0

        # Check that relationships have proper structure
        for rel in relationships:
            assert rel.source_document_id == 'doc1'
            assert rel.relationship_type in ['references', 'links_to']
            assert 0 <= rel.strength <= 1

    def test_build_graph_single_document(self, service, mock_repository):
        """Test building graph for single document."""
        mock_relationships = [
            Mock(source_document_id='doc1', target_document_id='doc2', relationship_type='references',
                 strength=0.8, metadata={})
        ]
        mock_repository.get_relationships_for_document.return_value = mock_relationships

        graph = service.build_graph(document_ids=['doc1'])

        assert graph['node_count'] == 2  # doc1 and doc2
        assert graph['edge_count'] == 1
        assert len(graph['nodes']) == 2
        assert len(graph['edges']) == 1



@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.domain
class TestRelationshipsHandlers(BaseTestCase):
    """Test RelationshipsHandlers functionality."""

    @pytest.fixture
    def handlers(self):
        """Create relationships handlers instance."""
        from services.doc_store.domain.relationships.handlers import RelationshipsHandlers
        return RelationshipsHandlers()

    @pytest.fixture
    def mock_service(self, handlers):
        """Mock the service for isolated testing."""
        with patch.object(handlers, 'service') as mock_svc:
            yield mock_svc

    async def test_handle_add_relationship_success(self, handlers, mock_service):
        """Test successful relationship creation via handler."""
        mock_relationship = Mock()
        mock_relationship.to_dict.return_value = {
            'id': 'rel123',
            'source_document_id': 'doc1',
            'target_document_id': 'doc2',
            'relationship_type': 'references',
            'strength': 0.8
        }
        mock_service.create_relationship.return_value = mock_relationship

        result = await handlers.handle_add_relationship('doc1', 'doc2', 'references', strength=0.8)

        self.assert_success_response(result)
        assert result['data']['id'] == 'rel123'

    async def test_handle_get_relationships_success(self, handlers, mock_service):
        """Test successful relationships retrieval via handler."""
        mock_result = {
            'document_id': 'doc1',
            'relationships': [{'source_id': 'doc1', 'target_id': 'doc2'}],
            'total': 1,
            'direction': 'outgoing'
        }
        mock_service.get_relationships_for_document.return_value = mock_result

        result = await handlers.handle_get_relationships('doc1', direction='outgoing')

        self.assert_success_response(result)
        assert result['data']['document_id'] == 'doc1'
        assert result['data']['total'] == 1

    async def test_handle_find_paths_success(self, handlers, mock_service):
        """Test successful path finding via handler."""
        mock_result = {
            'start_document': 'doc1',
            'end_document': 'doc3',
            'paths': [['doc1', 'doc2', 'doc3']],
            'total_paths': 1
        }
        mock_service.find_paths.return_value = mock_result

        result = await handlers.handle_find_paths('doc1', 'doc3', max_depth=3)

        self.assert_success_response(result)
        assert result['data']['total_paths'] == 1
        assert len(result['data']['paths']) == 1

    async def test_handle_graph_statistics_success(self, handlers, mock_service):
        """Test successful graph statistics retrieval."""
        mock_stats = {
            'total_relationships': 25,
            'unique_documents': 10,
            'avg_degree': 1.5,
            'density': 0.3
        }
        mock_service.get_graph_statistics.return_value = mock_stats

        result = await handlers.handle_graph_statistics()

        self.assert_success_response(result)
        assert result['data']['total_relationships'] == 25
        assert result['data']['unique_documents'] == 10

    async def test_handle_add_relationship_validation_error(self, handlers, mock_service):
        """Test relationship creation with validation error."""
        mock_service.create_relationship.side_effect = ValueError("Cannot create relationship to self")

        result = await handlers.handle_add_relationship('doc1', 'doc1', 'references')

        assert result['success'] is False
        assert "self" in result['message']
