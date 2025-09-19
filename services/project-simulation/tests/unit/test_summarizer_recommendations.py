"""
Unit Tests for Summarizer-Hub Recommendation Engine (TDD RED Phase)
Following TDD principles: RED -> GREEN -> REFACTOR

These tests are written FIRST (RED phase) and will initially FAIL.
They define the expected behavior before implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Import the modules we'll be testing (these may not exist yet - that's why tests will fail)
from simulation.domain.recommendations.recommendation_engine import RecommendationEngine
from simulation.domain.recommendations.recommendation import Recommendation, RecommendationType
from simulation.application.recommendations.document_recommendation_service import DocumentRecommendationService
from simulation.infrastructure.recommendations.summarizer_hub_client import SummarizerHubClient


class TestRecommendationEngine:
    """Test the core recommendation engine functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.engine = RecommendationEngine()

    @pytest.mark.asyncio
    async def test_generate_document_consolidation_recommendations(self):
        """Test generation of document consolidation recommendations."""
        # Arrange
        documents = [
            {"id": "doc1", "title": "API Guide", "content": "API documentation", "type": "api_docs"},
            {"id": "doc2", "title": "API Reference", "content": "API reference guide", "type": "api_docs"},
            {"id": "doc3", "title": "API Examples", "content": "API usage examples", "type": "api_docs"}
        ]

        # Act
        recommendations = await self.engine.generate_consolidation_recommendations(documents)

        # Assert
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.type == RecommendationType.CONSOLIDATION
            assert "consolidat" in rec.description.lower()  # Check for "consolidat" to match both "consolidate" and "consolidating"
            assert rec.confidence_score > 0
            assert rec.priority in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_generate_duplicate_detection_recommendations(self):
        """Test generation of duplicate document detection recommendations."""
        # Arrange
        documents = [
            {"id": "doc1", "title": "User Guide", "content": "How to use the system"},
            {"id": "doc2", "title": "User Manual", "content": "How to use the system"},
            {"id": "doc3", "title": "Getting Started", "content": "How to use the system"}
        ]

        # Act
        recommendations = await self.engine.generate_duplicate_recommendations(documents)

        # Assert
        assert isinstance(recommendations, list)

        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.type == RecommendationType.DUPLICATE
            assert "duplicate" in rec.description.lower()
            assert rec.affected_documents is not None
            assert len(rec.affected_documents) >= 2

    @pytest.mark.asyncio
    async def test_generate_outdated_document_recommendations(self):
        """Test generation of outdated document recommendations."""
        # Arrange
        current_time = datetime.now()
        old_time = current_time - timedelta(days=365*2)  # 2 years old

        documents = [
            {
                "id": "doc1",
                "title": "Old API Guide",
                "content": "Outdated API information",
                "dateCreated": old_time.isoformat(),
                "dateUpdated": old_time.isoformat()
            },
            {
                "id": "doc2",
                "title": "Current API Guide",
                "content": "Current API information",
                "dateCreated": current_time.isoformat(),
                "dateUpdated": current_time.isoformat()
            }
        ]

        # Act
        recommendations = await self.engine.generate_outdated_recommendations(documents)

        # Assert
        assert isinstance(recommendations, list)

        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.type == RecommendationType.OUTDATED
            assert "outdated" in rec.description.lower() or "obsolete" in rec.description.lower()
            assert rec.age_days > 365  # Should be more than a year old

    @pytest.mark.asyncio
    async def test_generate_quality_improvement_recommendations(self):
        """Test generation of document quality improvement recommendations."""
        # Arrange
        documents = [
            {
                "id": "doc1",
                "title": "Poor Documentation",
                "content": "This is very short and unclear.",
                "word_count": 10
            },
            {
                "id": "doc2",
                "title": "Good Documentation",
                "content": "This is a comprehensive and clear explanation of the topic with detailed examples and thorough coverage.",
                "word_count": 500
            }
        ]

        # Act
        recommendations = await self.engine.generate_quality_recommendations(documents)

        # Assert
        assert isinstance(recommendations, list)

        for rec in recommendations:
            assert isinstance(rec, Recommendation)
            assert rec.type == RecommendationType.QUALITY
            assert any(word in rec.description.lower() for word in ["clarity", "completeness", "quality", "improve"])

    @pytest.mark.asyncio
    async def test_generate_comprehensive_recommendations(self):
        """Test generation of comprehensive recommendations across all types."""
        # Arrange
        documents = [
            {"id": "doc1", "title": "API Guide", "content": "API info", "type": "api_docs"},
            {"id": "doc2", "title": "API Reference", "content": "API info", "type": "api_docs"},
            {"id": "doc3", "title": "Old Guide", "content": "Old content", "dateCreated": "2020-01-01"}
        ]

        # Act
        recommendations = await self.engine.generate_comprehensive_recommendations(documents)

        # Assert
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should include multiple types of recommendations
        recommendation_types = set(rec.type for rec in recommendations)
        assert len(recommendation_types) > 1

        # All recommendations should have required fields
        for rec in recommendations:
            assert rec.id is not None
            assert rec.description is not None
            assert rec.priority is not None
            assert rec.confidence_score >= 0
            assert rec.confidence_score <= 1

    @pytest.mark.asyncio
    async def test_recommendation_prioritization(self):
        """Test that recommendations are properly prioritized."""
        # Arrange
        documents = [
            {"id": "doc1", "title": "Critical API", "content": "Critical API documentation"},
            {"id": "doc2", "title": "Minor Guide", "content": "Minor guide content"}
        ]

        # Act
        recommendations = await self.engine.generate_comprehensive_recommendations(documents)

        # Assert
        # Sort by priority (high first)
        high_priority = [r for r in recommendations if r.priority == "high"]
        medium_priority = [r for r in recommendations if r.priority == "medium"]
        low_priority = [r for r in recommendations if r.priority == "low"]

        # High priority should come first in sorted list
        sorted_recs = sorted(recommendations, key=lambda r: ["high", "medium", "low"].index(r.priority))
        assert sorted_recs == recommendations or len(high_priority) == 0


class TestSummarizerHubClient:
    """Test the Summarizer-Hub client integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = SummarizerHubClient()

    @pytest.mark.asyncio
    async def test_analyze_document_with_summarizer_hub(self):
        """Test document analysis using summarizer-hub service."""
        # Arrange
        document = {
            "id": "doc1",
            "content": "This is a test document about API usage.",
            "title": "API Documentation"
        }

        # Act
        analysis_result = await self.client.analyze_document(document)

        # Assert
        assert isinstance(analysis_result, dict)
        assert "summary" in analysis_result
        assert "key_points" in analysis_result
        assert "sentiment" in analysis_result or "quality_score" in analysis_result

    @pytest.mark.asyncio
    async def test_generate_recommendations_from_analysis(self):
        """Test recommendation generation from analysis results."""
        # Arrange
        analysis_results = [
            {
                "document_id": "doc1",
                "summary": "API documentation",
                "quality_score": 0.3,
                "issues": ["unclear", "incomplete"]
            }
        ]

        # Act
        recommendations = await self.client.generate_recommendations(analysis_results)

        # Assert
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        for rec in recommendations:
            assert "type" in rec
            assert "description" in rec
            assert "priority" in rec

    @pytest.mark.asyncio
    async def test_batch_document_analysis(self):
        """Test batch processing of multiple documents."""
        # Arrange
        documents = [
            {"id": "doc1", "content": "Document 1 content", "title": "Doc 1"},
            {"id": "doc2", "content": "Document 2 content", "title": "Doc 2"},
            {"id": "doc3", "content": "Document 3 content", "title": "Doc 3"}
        ]

        # Act
        batch_results = await self.client.analyze_documents_batch(documents)

        # Assert
        assert isinstance(batch_results, list)
        assert len(batch_results) == len(documents)

        for result in batch_results:
            assert "document_id" in result
            assert "analysis" in result

    @pytest.mark.asyncio
    async def test_service_fallback_handling(self):
        """Test fallback handling when summarizer-hub is unavailable."""
        # This test should verify that the client gracefully handles service unavailability
        # and provides meaningful fallback recommendations

        # Act - This should work even if the service is down
        fallback_result = await self.client.get_fallback_analysis()

        # Assert
        assert isinstance(fallback_result, dict)
        assert "fallback_mode" in fallback_result
        assert fallback_result["fallback_mode"] is True


class TestDocumentRecommendationService:
    """Test the document recommendation service."""

    def setup_method(self):
        """Setup test fixtures."""
        self.service = DocumentRecommendationService()

    @pytest.mark.asyncio
    async def test_analyze_document_quality(self):
        """Test document quality analysis."""
        # Arrange
        document = {
            "id": "doc1",
            "content": "This is a well-written, comprehensive document with clear examples.",
            "title": "Quality Documentation"
        }

        # Act
        quality_score = await self.service.analyze_document_quality(document)

        # Assert
        assert isinstance(quality_score, float)
        assert 0.0 <= quality_score <= 1.0

    @pytest.mark.asyncio
    async def test_detect_similar_documents(self):
        """Test detection of similar documents."""
        # Arrange
        documents = [
            {"id": "doc1", "content": "API authentication guide", "title": "Auth Guide"},
            {"id": "doc2", "content": "API authentication tutorial", "title": "Auth Tutorial"},
            {"id": "doc3", "content": "Database connection guide", "title": "DB Guide"}
        ]

        # Act
        similar_pairs = await self.service.detect_similar_documents(documents)

        # Assert
        assert isinstance(similar_pairs, list)

        for pair in similar_pairs:
            assert "document1_id" in pair
            assert "document2_id" in pair
            assert "similarity_score" in pair
            assert pair["similarity_score"] > 0.5  # Should be reasonably similar

    @pytest.mark.asyncio
    async def test_identify_content_gaps(self):
        """Test identification of content gaps."""
        # Arrange
        documents = [
            {"id": "doc1", "content": "Basic API usage", "type": "api_docs"},
            {"id": "doc2", "content": "Advanced database queries", "type": "database"}
        ]

        # Act
        content_gaps = await self.service.identify_content_gaps(documents)

        # Assert
        assert isinstance(content_gaps, list)

        for gap in content_gaps:
            assert "topic" in gap
            assert "importance" in gap
            assert "missing_content_type" in gap

    @pytest.mark.asyncio
    async def test_generate_actionable_recommendations(self):
        """Test generation of actionable recommendations."""
        # Arrange
        analysis_results = {
            "quality_scores": {"doc1": 0.3, "doc2": 0.8},
            "similar_documents": [{"doc1": "doc2", "similarity": 0.85}],
            "content_gaps": ["error_handling", "security"]
        }

        # Act
        recommendations = await self.service.generate_actionable_recommendations(analysis_results)

        # Assert
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        for rec in recommendations:
            assert "action" in rec
            assert "rationale" in rec
            assert "expected_impact" in rec
            assert "effort_level" in rec


class TestRecommendationTypes:
    """Test different types of recommendations."""

    def test_recommendation_type_enum_values(self):
        """Test that all expected recommendation types are defined."""
        expected_types = [
            "CONSOLIDATION",
            "DUPLICATE",
            "OUTDATED",
            "QUALITY",
            "CONTENT_GAP",
            "STRUCTURAL_IMPROVEMENT",
            "PRIORITY_REORDERING"
        ]

        for expected_type in expected_types:
            assert hasattr(RecommendationType, expected_type)

    def test_recommendation_creation(self):
        """Test creation of recommendation objects."""
        rec = Recommendation(
            type=RecommendationType.QUALITY,
            description="Improve documentation clarity",
            affected_documents=["doc1", "doc2"],
            confidence_score=0.85,
            priority="high"
        )

        assert rec.type == RecommendationType.QUALITY
        assert rec.description == "Improve documentation clarity"
        assert rec.affected_documents == ["doc1", "doc2"]
        assert rec.confidence_score == 0.85
        assert rec.priority == "high"
        assert rec.id is not None  # Should be auto-generated

    def test_recommendation_priority_sorting(self):
        """Test that recommendations can be sorted by priority."""
        recommendations = [
            Recommendation(type=RecommendationType.QUALITY, description="Low priority", priority="low"),
            Recommendation(type=RecommendationType.CONSOLIDATION, description="High priority", priority="high"),
            Recommendation(type=RecommendationType.DUPLICATE, description="Medium priority", priority="medium")
        ]

        # Sort by priority
        sorted_recs = sorted(recommendations, key=lambda r: ["high", "medium", "low"].index(r.priority))

        assert sorted_recs[0].priority == "high"
        assert sorted_recs[1].priority == "medium"
        assert sorted_recs[2].priority == "low"
