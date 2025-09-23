"""Lifecycle domain tests.

Comprehensive tests for document lifecycle management, policies, and transitions.
"""
import pytest
from unittest.mock import patch, Mock
from tests.unit.doc_store.conftest import BaseTestCase


@pytest.mark.unit
@pytest.mark.domain
class TestLifecycleRepository(BaseTestCase):
    """Test LifecycleRepository functionality."""

    @pytest.fixture
    def repository(self):
        """Create lifecycle repository instance."""
        from services.doc_store.domain.lifecycle.repository import LifecycleRepository
        return LifecycleRepository()

    def test_get_policies_for_document(self, repository):
        """Test getting policies applicable to a document."""
        mock_policies = [
            {
                'id': 'policy1',
                'name': 'Retention Policy',
                'description': 'Keep docs for 1 year',
                'conditions': '{"content_types": ["api"]}',
                'actions': '{"retention_days": 365}',
                'priority': 5,
                'enabled': True,
                'created_at': '2024-01-01T00:00:00'
            }
        ]

        with patch('services.doc_store.domain.lifecycle.repository.execute_query', return_value=mock_policies):
            policies = repository.get_policies_for_document({'metadata': {'type': 'api'}})

            assert len(policies) == 1
            assert policies[0].name == 'Retention Policy'

    def test_update_document_lifecycle(self, repository):
        """Test updating document lifecycle."""
        with patch('services.doc_store.domain.lifecycle.repository.execute_query') as mock_execute:
            repository.update_document_lifecycle('doc1', 'archived', retention_days=365)

            assert mock_execute.called
            # Verify the query structure
            call_args = mock_execute.call_args
            query = call_args[0][0]
            assert 'document_lifecycle' in query
            assert 'INSERT OR REPLACE' in query.upper()


@pytest.mark.unit
@pytest.mark.domain
class TestLifecycleService(BaseTestCase):
    """Test LifecycleService functionality."""

    @pytest.fixture
    def service(self):
        """Create lifecycle service instance."""
        from services.doc_store.domain.lifecycle.service import LifecycleService
        return LifecycleService()

    @pytest.fixture
    def mock_repository(self, service):
        """Mock the repository for isolated testing."""
        with patch.object(service, 'repository') as mock_repo:
            yield mock_repo

    def test_apply_lifecycle_policies_no_policies(self, service, mock_repository):
        """Test applying policies when none match."""
        mock_repository.get_policies_for_document.return_value = []

        result = service.apply_lifecycle_policies({'id': 'doc1', 'metadata': {}})

        assert result['document_id'] == 'doc1'
        assert len(result['applied_policies']) == 0

    def test_evaluate_policy_matches(self, service, mock_repository):
        """Test policy evaluation logic."""
        from services.doc_store.core.entities import LifecyclePolicy

        policy = LifecyclePolicy(
            id='test-policy',
            name='Test Policy',
            description='Test policy',
            conditions={'content_types': ['api'], 'max_age_days': 365},
            actions={'retention_days': 730}
        )

        document = {
            'id': 'doc1',
            'metadata': {'type': 'api'},
            'created_at': '2024-01-01T00:00:00Z'  # Less than 365 days old
        }

        mock_repository.get_policies_for_document.return_value = [policy]

        policies = service.evaluate_document_policies(document)

        assert len(policies) == 1
        assert policies[0].id == policy.id

    def test_process_lifecycle_transitions(self, service, mock_repository):
        """Test processing lifecycle transitions."""
        mock_archival_docs = [{'id': 'doc1'}]
        mock_deletion_docs = []

        mock_repository.get_documents_for_lifecycle_transition.side_effect = [mock_archival_docs, mock_deletion_docs]

        result = service.process_lifecycle_transitions()

        assert result['archived'] == 1
        assert result['deleted'] == 0
        assert len(result['errors']) == 0


@pytest.mark.asyncio
@pytest.mark.unit
@pytest.mark.domain
class TestLifecycleHandlers(BaseTestCase):
    """Test LifecycleHandlers functionality."""

    @pytest.fixture
    def handlers(self):
        """Create lifecycle handlers instance."""
        from services.doc_store.domain.lifecycle.handlers import LifecycleHandlers
        return LifecycleHandlers()

    @pytest.fixture
    def mock_service(self, handlers):
        """Mock the service for isolated testing."""
        with patch.object(handlers, 'service') as mock_svc:
            yield mock_svc

    async def test_handle_apply_lifecycle_policies_success(self, handlers, mock_service):
        """Test successful policy application."""
        mock_result = {
            'document_id': 'doc1',
            'applied_policies': [{'policy_id': 'policy1'}],
            'transitions': []
        }
        mock_service.apply_lifecycle_policies.return_value = mock_result

        document = {'id': 'doc1', 'metadata': {'type': 'api'}}
        result = await handlers.handle_apply_lifecycle_policies(document)

        self.assert_success_response(result)
        assert result['data']['document_id'] == 'doc1'

    async def test_handle_process_lifecycle_transitions_success(self, handlers, mock_service):
        """Test successful lifecycle transition processing."""
        mock_result = {
            'archived': 3,
            'deleted': 2,
            'errors': []
        }
        mock_service.process_lifecycle_transitions.return_value = mock_result

        result = await handlers.handle_process_lifecycle_transitions()

        self.assert_success_response(result)
        assert result['data']['archived'] == 3
        assert result['data']['deleted'] == 2
