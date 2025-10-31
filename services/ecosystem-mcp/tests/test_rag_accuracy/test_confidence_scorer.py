"""
Unit tests for confidence scorer.

Tests:
- Individual scoring factors
- Overall confidence calculation
- Confidence levels
- Recommendations
"""

import pytest
from unittest.mock import Mock, AsyncMock
from src.services.rag.confidence_scorer import ConfidenceScorer


@pytest.fixture
def confidence_scorer():
    """Create confidence scorer instance."""
    scorer = ConfidenceScorer()
    scorer.ollama_router = Mock()  # Mock to avoid real LLM calls
    return scorer


@pytest.fixture
def mock_documents_high_quality():
    """High quality documents with good scores."""
    return [
        {
            "id": "doc1",
            "file_path": "test.py",
            "content_snippet": "Document about ingestion processing",
            "semantic_score": 0.95,
            "quality_score": 90.0,
            "metadata": {"category": "documentation"}
        },
        {
            "id": "doc2",
            "file_path": "guide.md",
            "content_snippet": "Ingestion guide and processing steps",
            "semantic_score": 0.92,
            "quality_score": 85.0,
            "metadata": {"category": "documentation"}
        },
        {
            "id": "doc3",
            "file_path": "impl.py",
            "content_snippet": "Implementation of ingestion processor",
            "semantic_score": 0.88,
            "quality_score": 80.0,
            "metadata": {"category": "code"}
        },
    ]


@pytest.fixture
def mock_documents_low_quality():
    """Low quality documents with poor scores."""
    return [
        {
            "id": "doc1",
            "file_path": "test.py",
            "semantic_score": 0.45,
            "quality_score": 30.0,
        },
    ]


class TestRetrievalConfidence:
    """Test retrieval quality scoring."""
    
    def test_high_retrieval_quality(self, confidence_scorer, mock_documents_high_quality):
        """Test high retrieval quality scores well."""
        score = confidence_scorer._calculate_retrieval_confidence(mock_documents_high_quality)
        
        assert score >= 15.0  # Should be high
        assert score <= 20.0
    
    def test_low_retrieval_quality(self, confidence_scorer, mock_documents_low_quality):
        """Test low retrieval quality scores poorly."""
        score = confidence_scorer._calculate_retrieval_confidence(mock_documents_low_quality)
        
        assert score < 12.0  # Should be low
    
    def test_no_documents(self, confidence_scorer):
        """Test zero score with no documents."""
        score = confidence_scorer._calculate_retrieval_confidence([])
        
        assert score == 0.0


class TestSourceQuality:
    """Test source quality scoring."""
    
    def test_high_source_quality(self, confidence_scorer, mock_documents_high_quality):
        """Test high source quality scores well."""
        score = confidence_scorer._calculate_source_quality(mock_documents_high_quality)
        
        assert score >= 15.0  # Should be high
        assert score <= 20.0
    
    def test_low_source_quality(self, confidence_scorer, mock_documents_low_quality):
        """Test low source quality scores poorly."""
        score = confidence_scorer._calculate_source_quality(mock_documents_low_quality)
        
        assert score < 10.0  # Should be low
    
    def test_no_quality_scores(self, confidence_scorer):
        """Test neutral score when no quality scores available."""
        docs = [{"id": "doc1", "file_path": "test.py"}]
        score = confidence_scorer._calculate_source_quality(docs)
        
        assert score == 10.0  # Neutral


class TestAlignmentScoring:
    """Test answer-source alignment scoring."""
    
    def test_alignment_heuristic_high(self, confidence_scorer, mock_documents_high_quality):
        """Test high alignment with heuristic method."""
        answer = "Ingestion processing involves documents and implementation steps"
        
        score = confidence_scorer._calculate_alignment_heuristic(answer, mock_documents_high_quality)
        
        assert score > 5.0  # Should have some alignment
    
    def test_alignment_heuristic_low(self, confidence_scorer):
        """Test low alignment with heuristic method."""
        answer = "This answer talks about completely different topics like weather"
        docs = [{"content_snippet": "Document about ingestion"}]
        
        score = confidence_scorer._calculate_alignment_heuristic(answer, docs)
        
        assert score < 15.0  # Low alignment
    
    @pytest.mark.asyncio
    async def test_alignment_llm(self, confidence_scorer, mock_documents_high_quality):
        """Test LLM-based alignment."""
        confidence_scorer.ollama_router.generate = AsyncMock(return_value="8")
        
        answer = "Ingestion processes documents"
        score = await confidence_scorer._calculate_alignment_llm(answer, mock_documents_high_quality)
        
        assert score > 0.0
        assert score <= 20.0
    
    @pytest.mark.asyncio
    async def test_alignment_llm_fallback(self, confidence_scorer, mock_documents_high_quality):
        """Test LLM alignment falls back to heuristic on error."""
        confidence_scorer.ollama_router.generate = AsyncMock(side_effect=Exception("LLM error"))
        
        answer = "Ingestion processes documents"
        score = await confidence_scorer._calculate_alignment_llm(answer, mock_documents_high_quality)
        
        # Should still return a score (from heuristic fallback)
        assert score >= 0.0
        assert score <= 20.0


class TestConsensusScoring:
    """Test consensus scoring."""
    
    def test_consensus_multiple_docs(self, confidence_scorer, mock_documents_high_quality):
        """Test high consensus with multiple diverse documents."""
        score = confidence_scorer._calculate_consensus(mock_documents_high_quality)
        
        assert score >= 10.0  # Should have good consensus
    
    def test_consensus_single_doc(self, confidence_scorer):
        """Test low consensus with single document."""
        docs = [{"id": "doc1", "file_path": "test.py"}]
        score = confidence_scorer._calculate_consensus(docs)
        
        assert score < 10.0  # Low consensus
    
    def test_consensus_same_file(self, confidence_scorer):
        """Test low diversity when all docs from same file."""
        docs = [
            {"id": "doc1", "file_path": "test.py"},
            {"id": "doc2", "file_path": "test.py"},
            {"id": "doc3", "file_path": "test.py"},
        ]
        score = confidence_scorer._calculate_consensus(docs)
        
        # Should be lower than diverse files
        assert score < 15.0


class TestCompletenessScoring:
    """Test completeness scoring."""
    
    def test_completeness_detailed_answer(self, confidence_scorer):
        """Test high completeness with detailed answer."""
        query = "How does ingestion work?"
        answer = "Ingestion is a process that works by reading files, processing documents, and storing them in the database. It involves multiple steps including normalization and embedding generation."
        
        score = confidence_scorer._calculate_completeness(query, answer)
        
        assert score >= 12.0  # Should be complete
    
    def test_completeness_short_answer(self, confidence_scorer):
        """Test low completeness with short answer."""
        query = "How does ingestion work?"
        answer = "It processes files."
        
        score = confidence_scorer._calculate_completeness(query, answer)
        
        assert score < 10.0  # Incomplete
    
    def test_completeness_covers_query_terms(self, confidence_scorer):
        """Test completeness with query term coverage."""
        query = "What is document processing and ingestion?"
        answer = "Document processing and ingestion involve handling files systematically."
        
        score = confidence_scorer._calculate_completeness(query, answer)
        
        # Should score well for covering key terms
        assert score > 8.0


class TestOverallConfidence:
    """Test overall confidence calculation."""
    
    @pytest.mark.asyncio
    async def test_score_high_confidence(self, confidence_scorer, mock_documents_high_quality):
        """Test overall high confidence scenario."""
        query = "How does ingestion work?"
        answer = "Ingestion is a comprehensive process that handles document processing, including reading files, normalizing content, generating embeddings, and storing everything in the database."
        
        result = await confidence_scorer.score(
            query=query,
            retrieved_documents=mock_documents_high_quality,
            answer=answer,
            use_llm_for_alignment=False  # Use heuristic for speed
        )
        
        assert result["confidence"] >= 60.0  # Should be moderate to high
        assert result["confidence"] <= 100.0
        assert result["confidence_level"] in ["Very High", "High", "Medium"]
        assert "breakdown" in result
        assert len(result["breakdown"]) == 5
    
    @pytest.mark.asyncio
    async def test_score_low_confidence(self, confidence_scorer, mock_documents_low_quality):
        """Test overall low confidence scenario."""
        query = "How does ingestion work?"
        answer = "It works."
        
        result = await confidence_scorer.score(
            query=query,
            retrieved_documents=mock_documents_low_quality,
            answer=answer,
            use_llm_for_alignment=False
        )
        
        assert result["confidence"] < 60.0  # Should be low
        assert result["confidence_level"] in ["Low", "Very Low", "Medium"]
    
    @pytest.mark.asyncio
    async def test_score_no_documents(self, confidence_scorer):
        """Test scoring with no documents."""
        result = await confidence_scorer.score(
            query="test",
            retrieved_documents=[],
            answer="no answer",
            use_llm_for_alignment=False
        )
        
        assert result["confidence"] == 0.0
        assert result["confidence_level"] == "Very Low"


class TestConfidenceLevels:
    """Test confidence level mapping."""
    
    def test_very_high_level(self, confidence_scorer):
        """Test very high confidence level."""
        level = confidence_scorer._get_confidence_level(95.0)
        assert level == "Very High"
    
    def test_high_level(self, confidence_scorer):
        """Test high confidence level."""
        level = confidence_scorer._get_confidence_level(80.0)
        assert level == "High"
    
    def test_medium_level(self, confidence_scorer):
        """Test medium confidence level."""
        level = confidence_scorer._get_confidence_level(65.0)
        assert level == "Medium"
    
    def test_low_level(self, confidence_scorer):
        """Test low confidence level."""
        level = confidence_scorer._get_confidence_level(45.0)
        assert level == "Low"
    
    def test_very_low_level(self, confidence_scorer):
        """Test very low confidence level."""
        level = confidence_scorer._get_confidence_level(20.0)
        assert level == "Very Low"


class TestRecommendations:
    """Test recommendation generation."""
    
    def test_recommendation_high_confidence(self, confidence_scorer):
        """Test recommendation for high confidence."""
        rec = confidence_scorer._get_recommendation(
            total=85.0,
            retrieval=18.0,
            quality=17.0,
            alignment=18.0,
            consensus=17.0,
            completeness=15.0
        )
        
        assert "high confidence" in rec.lower() or "trustworthy" in rec.lower()
    
    def test_recommendation_low_confidence(self, confidence_scorer):
        """Test recommendation for low confidence."""
        rec = confidence_scorer._get_recommendation(
            total=35.0,
            retrieval=5.0,
            quality=8.0,
            alignment=7.0,
            consensus=8.0,
            completeness=7.0
        )
        
        assert "low confidence" in rec.lower() or "verify" in rec.lower()
    
    def test_recommendation_identifies_weakness(self, confidence_scorer):
        """Test recommendation identifies weakest factor."""
        rec = confidence_scorer._get_recommendation(
            total=50.0,
            retrieval=2.0,  # Weakest
            quality=15.0,
            alignment=13.0,
            consensus=12.0,
            completeness=8.0
        )
        
        # Should mention retrieval as the weak point
        assert "retrieval" in rec.lower() or "relevant" in rec.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

