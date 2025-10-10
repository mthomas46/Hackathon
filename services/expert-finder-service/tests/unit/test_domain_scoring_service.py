"""
Unit tests for RelevanceScoringService.

Tests the refactored scoring algorithm (complexity reduced from 18 → 3).
CRITICAL: Validates mandatory KISS fix from Phase 2.8.
"""

import pytest
from domain.entities.expert import Expert
from domain.value_objects.expert_query import ExpertQuery
from domain.services.relevance_scoring_service import RelevanceScoringService


class TestRelevanceScoringService:
    """Tests for relevance scoring service."""
    
    @pytest.fixture
    def scoring_service(self):
        """Create scoring service with default weights."""
        return RelevanceScoringService(
            role_weight=0.30,
            topic_weight=0.40,
            service_weight=0.20,
            document_weight=0.10
        )
    
    @pytest.fixture
    def sample_expert(self):
        """Create a sample expert for testing."""
        return Expert(
            user_id="user123",
            name="Alice Smith",
            role="Backend Developer",
            seniority="senior",
            topics=["Python", "FastAPI", "Docker"],
            tags=["backend", "python"],
            services=["user-store", "doc-store"],
            document_count=25
        )
    
    @pytest.fixture
    def sample_query(self):
        """Create a sample query for testing."""
        return ExpertQuery(
            query_text="Python backend developer",
            role="Backend Developer",
            topics=["Python", "FastAPI"],
            limit=10
        )
    
    def test_scoring_service_initialization(self):
        """Test scoring service can be initialized with weights."""
        service = RelevanceScoringService(
            role_weight=0.30,
            topic_weight=0.40,
            service_weight=0.20,
            document_weight=0.10
        )
        
        assert service.role_weight == 0.30
        assert service.topic_weight == 0.40
        assert service.service_weight == 0.20
        assert service.document_weight == 0.10
    
    def test_invalid_weights(self):
        """Test that invalid weights raise error."""
        with pytest.raises(ValueError, match="Weights must sum"):
            RelevanceScoringService(
                role_weight=0.50,
                topic_weight=0.50,
                service_weight=0.50,
                document_weight=0.50
            )
    
    def test_calculate_score(self, scoring_service, sample_expert, sample_query):
        """Test calculating overall score."""
        match = scoring_service.calculate_score(sample_expert, sample_query)
        
        # Should return an ExpertMatch
        assert match.expert == sample_expert
        assert 0.0 <= match.overall_score <= 1.0
        assert 0.0 <= match.role_score <= 1.0
        assert 0.0 <= match.topic_score <= 1.0
        assert 0.0 <= match.service_score <= 1.0
        assert 0.0 <= match.document_score <= 1.0
        
        # Should have high score for this perfect match
        assert match.overall_score > 0.7
    
    def test_role_score_matching(self, scoring_service):
        """Test role scoring."""
        expert = Expert(user_id="1", name="Alice", role="Backend Developer", seniority="senior")
        query = ExpertQuery(query_text="test", role="Backend Developer")
        
        match = scoring_service.calculate_score(expert, query)
        
        # Senior backend developer matching backend = 1.0
        assert match.role_score == 1.0
    
    def test_role_score_senior_multiplier(self, scoring_service):
        """Test seniority multipliers."""
        query = ExpertQuery(query_text="test", role="Backend Developer")
        
        senior = Expert(user_id="1", name="Alice", role="Backend Developer", seniority="senior")
        mid = Expert(user_id="2", name="Bob", role="Backend Developer", seniority="mid")
        junior = Expert(user_id="3", name="Carol", role="Backend Developer", seniority="junior")
        
        senior_match = scoring_service.calculate_score(senior, query)
        mid_match = scoring_service.calculate_score(mid, query)
        junior_match = scoring_service.calculate_score(junior, query)
        
        assert senior_match.role_score == 1.0  # senior multiplier
        assert mid_match.role_score == 0.7     # mid multiplier
        assert junior_match.role_score == 0.5  # junior multiplier
    
    def test_topic_score_exact_match(self, scoring_service):
        """Test topic scoring with exact matches."""
        expert = Expert(
            user_id="1",
            name="Alice",
            topics=["Python", "FastAPI"]
        )
        query = ExpertQuery(
            query_text="test",
            topics=["Python", "FastAPI"]
        )
        
        match = scoring_service.calculate_score(expert, query)
        
        # Both topics match = 100%
        assert match.topic_score == 1.0
    
    def test_topic_score_partial_match(self, scoring_service):
        """Test topic scoring with partial matches."""
        expert = Expert(
            user_id="1",
            name="Alice",
            topics=["Python", "FastAPI", "Docker"]
        )
        query = ExpertQuery(
            query_text="test",
            topics=["Python"]
        )
        
        match = scoring_service.calculate_score(expert, query)
        
        # 1 out of 1 query topics matches = 100%
        assert match.topic_score == 1.0
    
    def test_document_score_thresholds(self, scoring_service):
        """Test document scoring thresholds."""
        query = ExpertQuery(query_text="test")
        
        expert_0_docs = Expert(user_id="1", name="Alice", document_count=0)
        expert_3_docs = Expert(user_id="2", name="Bob", document_count=3)
        expert_15_docs = Expert(user_id="3", name="Carol", document_count=15)
        expert_50_docs = Expert(user_id="4", name="Dave", document_count=50)
        
        match_0 = scoring_service.calculate_score(expert_0_docs, query)
        match_3 = scoring_service.calculate_score(expert_3_docs, query)
        match_15 = scoring_service.calculate_score(expert_15_docs, query)
        match_50 = scoring_service.calculate_score(expert_50_docs, query)
        
        assert match_0.document_score == 0.0
        assert match_3.document_score == 0.2
        assert match_15.document_score == 0.6
        assert match_50.document_score == 1.0
    
    def test_batch_scoring(self, scoring_service, sample_query):
        """Test scoring multiple experts at once."""
        experts = [
            Expert(user_id="1", name="Alice", role="Backend Developer", topics=["Python"]),
            Expert(user_id="2", name="Bob", role="Frontend Developer", topics=["React"]),
            Expert(user_id="3", name="Carol", role="Backend Developer", topics=["Python", "FastAPI"]),
        ]
        
        matches = scoring_service.calculate_batch_scores(experts, sample_query)
        
        # Should return sorted matches
        assert len(matches) <= len(experts)
        
        # Should be sorted by score (descending)
        for i in range(len(matches) - 1):
            assert matches[i].overall_score >= matches[i + 1].overall_score
    
    def test_min_score_filter(self, scoring_service):
        """Test minimum score filtering."""
        experts = [
            Expert(user_id="1", name="Alice", role="Backend Developer", topics=["Python"]),
            Expert(user_id="2", name="Bob", role="Frontend Developer", topics=["React"]),
        ]
        query = ExpertQuery(
            query_text="Python backend",
            role="Backend Developer",
            min_score=0.5  # High threshold
        )
        
        matches = scoring_service.calculate_batch_scores(experts, query)
        
        # All matches should be above min_score
        for match in matches:
            assert match.overall_score >= 0.5

