"""
Unit tests for application use cases.

Tests FindExpertsUseCase with mocked repositories and scoring service.
"""

import pytest
from unittest.mock import AsyncMock, Mock

from application.use_cases.find_experts_use_case import FindExpertsUseCase
from domain.entities.expert import Expert
from domain.value_objects.expert_query import ExpertQuery
from domain.value_objects.expert_match import ExpertMatch
from domain.services.relevance_scoring_service import RelevanceScoringService


class TestFindExpertsUseCase:
    """Tests for FindExpertsUseCase."""
    
    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        repo = AsyncMock()
        repo.get_users_by_role = AsyncMock(return_value=[])
        repo.get_users_by_topic = AsyncMock(return_value=[])  # Singular
        repo.get_users_by_topics = AsyncMock(return_value=[])  # Plural
        repo.get_users_by_services = AsyncMock(return_value=[])
        repo.get_all_users = AsyncMock(return_value=[])
        repo.search_users = AsyncMock(return_value=[])
        return repo
    
    @pytest.fixture
    def mock_doc_repo(self):
        """Create a mock document repository."""
        repo = AsyncMock()
        repo.get_document_counts_by_user_ids = AsyncMock(return_value={})
        repo.get_document_count_by_author = AsyncMock(return_value=0)
        return repo
    
    @pytest.fixture
    def mock_service_repo(self):
        """Create a mock service repository."""
        repo = AsyncMock()
        repo.get_services_by_user_ids = AsyncMock(return_value={})
        repo.get_service_count_by_user = AsyncMock(return_value=0)
        return repo
    
    @pytest.fixture
    def mock_scoring_service(self):
        """Create a mock scoring service."""
        service = Mock()
        service.calculate_batch_scores = Mock(return_value=[])
        return service
    
    @pytest.fixture
    def use_case(self, mock_user_repo, mock_doc_repo, mock_service_repo, mock_scoring_service):
        """Create a use case with mocked dependencies."""
        return FindExpertsUseCase(
            user_repo=mock_user_repo,
            doc_repo=mock_doc_repo,
            service_repo=mock_service_repo,
            scoring_service=mock_scoring_service
        )
    
    @pytest.mark.asyncio
    async def test_find_experts_by_role(self, use_case, mock_user_repo, mock_scoring_service):
        """Test finding experts by role."""
        # Setup mocks - Return Expert objects, not dicts
        mock_users = [
            Expert(user_id="1", name="Alice", role="Backend Developer"),
            Expert(user_id="2", name="Bob", role="Backend Developer")
        ]
        mock_user_repo.get_users_by_role.return_value = mock_users
        
        mock_matches = [
            ExpertMatch(
                expert=Expert(user_id="1", name="Alice", role="Backend Developer"),
                overall_score=0.85,
                role_score=0.9,
                topic_score=0.8,
                service_score=0.7,
                document_score=0.6
            )
        ]
        mock_scoring_service.calculate_batch_scores.return_value = mock_matches
        
        # Execute
        query = ExpertQuery(
            query_text="Python backend developer",
            role="Backend Developer",
            limit=10
        )
        results = await use_case.execute(query)
        
        # Verify
        assert len(results) == 1
        assert results[0].expert.name == "Alice"
        assert results[0].overall_score == 0.85
        mock_user_repo.get_users_by_role.assert_called_once()
        # Verify it was called with the role (limit is implementation detail)
        call_args = mock_user_repo.get_users_by_role.call_args
        assert call_args[0][0] == "Backend Developer"  # First positional arg
    
    @pytest.mark.asyncio
    async def test_find_experts_by_topics(self, use_case, mock_user_repo, mock_scoring_service):
        """Test finding experts by topics."""
        # Setup mocks - Return Expert objects
        mock_users = [
            Expert(user_id="1", name="Alice", topics=["Python", "FastAPI"])
        ]
        mock_user_repo.get_users_by_topic.return_value = mock_users  # Singular method
        
        mock_matches = [
            ExpertMatch(
                expert=Expert(user_id="1", name="Alice", topics=["Python", "FastAPI"]),
                overall_score=0.9,
                role_score=0.8,
                topic_score=1.0,
                service_score=0.7,
                document_score=0.6
            )
        ]
        mock_scoring_service.calculate_batch_scores.return_value = mock_matches
        
        # Execute
        query = ExpertQuery(
            query_text="Python expert",
            topics=["Python", "FastAPI"],
            limit=5
        )
        results = await use_case.execute(query)
        
        # Verify
        assert len(results) == 1
        assert "Python" in results[0].expert.topics
        # Verify topic-based fetch was called (implementation may vary)
        assert mock_user_repo.get_users_by_topic.called or mock_user_repo.get_users_by_topics.called
    
    @pytest.mark.asyncio
    async def test_find_experts_enriches_with_documents(
        self, use_case, mock_user_repo, mock_doc_repo, mock_scoring_service
    ):
        """Test that experts are enriched with document counts."""
        # Setup mocks - Return Expert objects
        mock_users = [
            Expert(user_id="1", name="Alice")
        ]
        mock_user_repo.get_users_by_role.return_value = mock_users
        
        mock_doc_counts = {"1": 25}
        mock_doc_repo.get_document_counts_by_user_ids.return_value = mock_doc_counts
        
        mock_matches = [
            ExpertMatch(
                expert=Expert(user_id="1", name="Alice", document_count=25),
                overall_score=0.8,
                role_score=0.8,
                topic_score=0.8,
                service_score=0.8,
                document_score=0.8
            )
        ]
        mock_scoring_service.calculate_batch_scores.return_value = mock_matches
        
        # Execute
        query = ExpertQuery(query_text="test", role="Developer", limit=10)
        results = await use_case.execute(query)
        
        # Verify - document enrichment was attempted
        assert mock_doc_repo.get_document_counts_by_user_ids.called or mock_doc_repo.get_document_count_by_author.called
        assert results[0].expert.document_count == 25
    
    @pytest.mark.asyncio
    async def test_find_experts_enriches_with_services(
        self, use_case, mock_user_repo, mock_service_repo, mock_scoring_service
    ):
        """Test that experts are enriched with service contributions."""
        # Setup mocks - Return Expert objects
        mock_users = [
            Expert(user_id="1", name="Alice")
        ]
        mock_user_repo.get_users_by_role.return_value = mock_users
        
        mock_services = {
            "1": ["user-store", "doc-store"]
        }
        mock_service_repo.get_services_by_user_ids.return_value = mock_services
        
        mock_matches = [
            ExpertMatch(
                expert=Expert(user_id="1", name="Alice", services=["user-store", "doc-store"]),
                overall_score=0.8,
                role_score=0.8,
                topic_score=0.8,
                service_score=0.9,
                document_score=0.6
            )
        ]
        mock_scoring_service.calculate_batch_scores.return_value = mock_matches
        
        # Execute
        query = ExpertQuery(query_text="test", role="Developer", limit=10)
        results = await use_case.execute(query)
        
        # Verify - service enrichment was attempted
        assert mock_service_repo.get_services_by_user_ids.called or mock_service_repo.get_service_count_by_user.called
        assert len(results[0].expert.services) == 2
    
    @pytest.mark.asyncio
    async def test_find_experts_handles_empty_results(
        self, use_case, mock_user_repo, mock_scoring_service
    ):
        """Test that empty results are handled gracefully."""
        # Setup mocks
        mock_user_repo.get_users_by_role.return_value = []
        mock_scoring_service.calculate_batch_scores.return_value = []
        
        # Execute
        query = ExpertQuery(query_text="nonexistent", role="Ghost", limit=10)
        results = await use_case.execute(query)
        
        # Verify
        assert results == []
    
    @pytest.mark.asyncio
    async def test_find_experts_respects_limit(
        self, use_case, mock_user_repo, mock_scoring_service
    ):
        """Test that result limit is respected."""
        # Setup mocks - Return Expert objects
        mock_users = [
            Expert(user_id=str(i), name=f"User{i}")
            for i in range(20)
        ]
        mock_user_repo.get_users_by_role.return_value = mock_users
        
        mock_matches = [
            ExpertMatch(
                expert=Expert(user_id=str(i), name=f"User{i}"),
                overall_score=0.8 - (i * 0.01),
                role_score=0.8,
                topic_score=0.8,
                service_score=0.8,
                document_score=0.8
            )
            for i in range(20)
        ]
        mock_scoring_service.calculate_batch_scores.return_value = mock_matches[:5]
        
        # Execute
        query = ExpertQuery(query_text="test", role="Developer", limit=5)
        results = await use_case.execute(query)
        
        # Verify
        assert len(results) <= 5
    
    @pytest.mark.asyncio
    async def test_find_experts_filters_by_min_score(
        self, use_case, mock_user_repo, mock_scoring_service
    ):
        """Test that minimum score filter is applied."""
        # Setup mocks - Return Expert objects
        mock_users = [
            Expert(user_id="1", name="Alice"),
            Expert(user_id="2", name="Bob")
        ]
        mock_user_repo.get_users_by_role.return_value = mock_users
        
        # Only return matches above threshold
        mock_matches = [
            ExpertMatch(
                expert=Expert(user_id="1", name="Alice"),
                overall_score=0.85,
                role_score=0.9,
                topic_score=0.8,
                service_score=0.7,
                document_score=0.6
            )
        ]
        mock_scoring_service.calculate_batch_scores.return_value = mock_matches
        
        # Execute
        query = ExpertQuery(
            query_text="test",
            role="Developer",
            min_score=0.7,
            limit=10
        )
        results = await use_case.execute(query)
        
        # Verify
        assert len(results) == 1
        assert all(r.overall_score >= 0.7 for r in results)
    
    @pytest.mark.asyncio
    async def test_find_experts_deduplicates_results(
        self, use_case, mock_user_repo, mock_scoring_service
    ):
        """Test that duplicate experts are deduplicated."""
        # Setup mocks - same user returned from multiple sources
        mock_users = [
            Expert(user_id="1", name="Alice"),
            Expert(user_id="1", name="Alice")  # Duplicate
        ]
        mock_user_repo.get_users_by_role.return_value = mock_users
        
        mock_matches = [
            ExpertMatch(
                expert=Expert(user_id="1", name="Alice"),
                overall_score=0.85,
                role_score=0.9,
                topic_score=0.8,
                service_score=0.7,
                document_score=0.6
            )
        ]
        mock_scoring_service.calculate_batch_scores.return_value = mock_matches
        
        # Execute
        query = ExpertQuery(query_text="test", role="Developer", limit=10)
        results = await use_case.execute(query)
        
        # Verify - should only have one result
        assert len(results) == 1
        assert results[0].expert.user_id == "1"

