"""
Unit tests for Summarizer-Hub recommendation endpoints.
Following TDD principles with comprehensive test coverage.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
from datetime import datetime, timedelta

# Import the FastAPI app and test client
from fastapi.testclient import TestClient
from main import app, SimpleSummarizer


class TestRecommendationEndpoints:
    """Test the recommendation API endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)
        self.summarizer = SimpleSummarizer()

    def test_recommendations_endpoint_structure(self):
        """Test that recommendations endpoint accepts proper request structure."""
        # Test with empty documents list
        response = self.client.post("/api/v1/recommendations", json={
            "documents": []
        })
        assert response.status_code == 422  # Validation error for empty documents

    def test_recommendations_endpoint_with_valid_data(self):
        """Test recommendations endpoint with valid document data."""
        documents = [
            {
                "id": "doc1",
                "title": "API Guide",
                "content": "This is an API guide with comprehensive information about using the API.",
                "type": "api_docs"
            },
            {
                "id": "doc2",
                "title": "API Reference",
                "content": "This is an API reference with comprehensive information about using the API.",
                "type": "api_docs"
            },
            {
                "id": "doc3",
                "title": "Old Documentation",
                "content": "This is old documentation that may be outdated.",
                "dateCreated": "2020-01-01T00:00:00Z",
                "type": "tutorial"
            }
        ]

        # Mock the LLM calls to avoid external dependencies
        with patch('main.SimpleSummarizer.generate_recommendations') as mock_generate:
            mock_generate.return_value = {
                "recommendations": [
                    {
                        "id": "rec1",
                        "type": "consolidation",
                        "description": "Consolidate 2 api_docs documents into a comprehensive guide",
                        "affected_documents": ["doc1", "doc2"],
                        "confidence_score": 0.8,
                        "priority": "high",
                        "rationale": "Multiple api_docs documents with high similarity",
                        "expected_impact": "Reduce maintenance overhead by 40%",
                        "effort_level": "medium",
                        "tags": ["consolidation", "api_docs"],
                        "metadata": {
                            "document_type": "api_docs",
                            "document_count": 2,
                            "average_similarity": 0.85
                        }
                    },
                    {
                        "id": "rec2",
                        "type": "outdated",
                        "description": "Document 'Old Documentation' is outdated",
                        "affected_documents": ["doc3"],
                        "confidence_score": 0.9,
                        "priority": "high",
                        "rationale": "Document is over 2 years old",
                        "expected_impact": "Ensure users have current information",
                        "effort_level": "medium",
                        "tags": ["outdated", "maintenance"],
                        "age_days": 1461,
                        "metadata": {"last_updated": "2020-01-01T00:00:00Z"}
                    }
                ],
                "total_documents": 3,
                "recommendations_count": 2,
                "processing_time": 0.5,
                "recommendation_types": ["consolidation", "duplicate", "outdated", "quality"],
                "confidence_threshold": 0.4
            }

            response = self.client.post("/api/v1/recommendations", json={
                "documents": documents,
                "recommendation_types": ["consolidation", "outdated"],
                "confidence_threshold": 0.4
            })

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True
            assert data["total_documents"] == 3
            assert data["recommendations_count"] == 2
            assert len(data["recommendations"]) == 2

            # Check first recommendation
            rec1 = data["recommendations"][0]
            assert rec1["type"] == "consolidation"
            assert rec1["confidence_score"] == 0.8
            assert rec1["priority"] == "high"
            assert len(rec1["affected_documents"]) == 2

            # Check second recommendation
            rec2 = data["recommendations"][1]
            assert rec2["type"] == "outdated"
            assert rec2["confidence_score"] == 0.9
            assert rec2["age_days"] == 1461

    def test_recommendations_endpoint_with_invalid_data(self):
        """Test recommendations endpoint with invalid data."""
        # Test with missing content field
        response = self.client.post("/api/v1/recommendations", json={
            "documents": [{"id": "doc1", "title": "Test"}]  # Missing content
        })
        assert response.status_code == 422

        # Test with missing id field
        response = self.client.post("/api/v1/recommendations", json={
            "documents": [{"title": "Test", "content": "Test content"}]  # Missing id
        })
        assert response.status_code == 422

    def test_recommendations_endpoint_filters_by_type(self):
        """Test that recommendations can be filtered by type."""
        documents = [
            {"id": "doc1", "title": "API Guide", "content": "API content", "type": "api_docs"},
            {"id": "doc2", "title": "API Reference", "content": "API content", "type": "api_docs"}
        ]

        with patch('main.SimpleSummarizer.generate_recommendations') as mock_generate:
            mock_generate.return_value = {
                "recommendations": [
                    {
                        "id": "rec1",
                        "type": "consolidation",
                        "description": "Consolidation recommendation",
                        "affected_documents": ["doc1", "doc2"],
                        "confidence_score": 0.8,
                        "priority": "high",
                        "rationale": "Multiple similar documents",
                        "expected_impact": "Reduce overhead",
                        "effort_level": "medium",
                        "tags": ["consolidation"],
                        "metadata": {}
                    }
                ],
                "total_documents": 2,
                "recommendations_count": 1,
                "processing_time": 0.3,
                "recommendation_types": ["consolidation"],
                "confidence_threshold": 0.4
            }

            # Test with specific recommendation types
            response = self.client.post("/api/v1/recommendations", json={
                "documents": documents,
                "recommendation_types": ["consolidation"]
            })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["recommendations"]) == 1
            assert data["recommendations"][0]["type"] == "consolidation"

    def test_recommendations_endpoint_respects_confidence_threshold(self):
        """Test that confidence threshold filtering works."""
        documents = [
            {"id": "doc1", "title": "High Quality", "content": "Excellent content", "type": "guide"},
            {"id": "doc2", "title": "Low Quality", "content": "Poor", "type": "guide"}
        ]

        with patch('main.SimpleSummarizer.generate_recommendations') as mock_generate:
            mock_generate.return_value = {
                "recommendations": [
                    {
                        "id": "rec1",
                        "type": "quality",
                        "description": "Quality improvement needed",
                        "affected_documents": ["doc2"],
                        "confidence_score": 0.9,
                        "priority": "high",
                        "rationale": "Low quality content detected",
                        "expected_impact": "Improve user experience",
                        "effort_level": "low",
                        "tags": ["quality"],
                        "metadata": {"issues": ["content too short"]}
                    }
                ],
                "total_documents": 2,
                "recommendations_count": 1,
                "processing_time": 0.2,
                "recommendation_types": ["quality"],
                "confidence_threshold": 0.8
            }

            # Test with high confidence threshold
            response = self.client.post("/api/v1/recommendations", json={
                "documents": documents,
                "confidence_threshold": 0.8
            })

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            # Should only return recommendations above threshold
            for rec in data["recommendations"]:
                assert rec["confidence_score"] >= 0.8


class TestSimpleSummarizerRecommendations:
    """Test the SimpleSummarizer recommendation logic."""

    def setup_method(self):
        """Setup test fixtures."""
        self.summarizer = SimpleSummarizer()

    def test_generate_recommendations_empty_documents(self):
        """Test that empty document list returns empty recommendations."""
        result = asyncio.run(self.summarizer.generate_recommendations([]))
        assert result["recommendations"] == []
        assert result["total_documents"] == 0
        assert result["recommendations_count"] == 0

    def test_generate_recommendations_single_document(self):
        """Test recommendations with single document."""
        documents = [
            {
                "id": "doc1",
                "title": "Single Document",
                "content": "This is a single document.",
                "type": "guide"
            }
        ]

        result = asyncio.run(self.summarizer.generate_recommendations(documents))
        # Single document should not generate consolidation recommendations
        consolidation_recs = [r for r in result["recommendations"] if r["type"] == "consolidation"]
        assert len(consolidation_recs) == 0

    def test_generate_recommendations_consolidation_logic(self):
        """Test consolidation recommendation generation."""
        documents = [
            {"id": "doc1", "title": "API Guide", "content": "API documentation content", "type": "api_docs"},
            {"id": "doc2", "title": "API Reference", "content": "API documentation content", "type": "api_docs"},
            {"id": "doc3", "title": "API Examples", "content": "API documentation content", "type": "api_docs"}
        ]

        result = asyncio.run(self.summarizer.generate_recommendations(documents))

        # Should generate consolidation recommendation for 3 similar documents
        consolidation_recs = [r for r in result["recommendations"] if r["type"] == "consolidation"]
        assert len(consolidation_recs) >= 1

        rec = consolidation_recs[0]
        assert rec["confidence_score"] > 0
        assert len(rec["affected_documents"]) == 3
        assert "api_docs" in rec["tags"]

    def test_generate_recommendations_duplicate_detection(self):
        """Test duplicate recommendation generation."""
        documents = [
            {"id": "doc1", "title": "User Guide", "content": "How to use the system effectively with detailed instructions and examples", "type": "guide"},
            {"id": "doc2", "title": "User Manual", "content": "How to use the system effectively with detailed instructions and examples", "type": "guide"},
            {"id": "doc3", "title": "Quick Start", "content": "This is a completely different document about getting started quickly", "type": "guide"}
        ]

        result = asyncio.run(self.summarizer.generate_recommendations(documents))

        # Should detect duplicates between doc1 and doc2
        duplicate_recs = [r for r in result["recommendations"] if r["type"] == "duplicate"]
        assert len(duplicate_recs) >= 1

        rec = duplicate_recs[0]
        assert rec["confidence_score"] > 0.5  # High confidence for clear duplicates
        assert len(rec["affected_documents"]) == 2

    def test_generate_recommendations_outdated_detection(self):
        """Test outdated document recommendation generation."""
        old_date = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%S")  # Over a year old
        recent_date = datetime.now().isoformat()

        documents = [
            {
                "id": "doc1",
                "title": "Old Guide",
                "content": "Outdated information",
                "dateCreated": old_date,
                "dateUpdated": old_date,
                "type": "guide"
            },
            {
                "id": "doc2",
                "title": "Recent Guide",
                "content": "Current information",
                "dateCreated": recent_date,
                "dateUpdated": recent_date,
                "type": "guide"
            }
        ]

        result = asyncio.run(self.summarizer.generate_recommendations(documents))

        # Should generate outdated recommendation for doc1
        outdated_recs = [r for r in result["recommendations"] if r["type"] == "outdated"]
        assert len(outdated_recs) >= 1

        rec = outdated_recs[0]
        assert rec["affected_documents"] == ["doc1"]
        assert rec["age_days"] > 365
        assert rec["confidence_score"] > 0

    def test_generate_recommendations_quality_analysis(self):
        """Test quality improvement recommendation generation."""
        documents = [
            {
                "id": "doc1",
                "title": "Poor Documentation",
                "content": "This is very short.",  # Short content
                "type": "guide"
            },
            {
                "id": "doc2",
                "title": "Good Documentation",
                "content": "This is a comprehensive guide with examples and detailed information about the topic.",
                "type": "guide"
            }
        ]

        result = asyncio.run(self.summarizer.generate_recommendations(documents))

        # Should generate quality recommendation for doc1
        quality_recs = [r for r in result["recommendations"] if r["type"] == "quality"]
        assert len(quality_recs) >= 1

        rec = quality_recs[0]
        assert rec["affected_documents"] == ["doc1"]
        assert "short" in rec["description"].lower() or "improve" in rec["description"].lower()

    def test_generate_recommendations_comprehensive_types(self):
        """Test that comprehensive recommendations include all types."""
        documents = [
            {"id": "doc1", "title": "API Guide", "content": "API content", "type": "api_docs"},
            {"id": "doc2", "title": "API Reference", "content": "API content", "type": "api_docs"},
            {"id": "doc3", "title": "Old Doc", "content": "Old content", "dateCreated": "2020-01-01", "type": "guide"},
            {"id": "doc4", "title": "Short Doc", "content": "Short", "type": "guide"}
        ]

        result = asyncio.run(self.summarizer.generate_recommendations(documents))

        # Should include multiple types of recommendations
        rec_types = set(rec["type"] for rec in result["recommendations"])
        expected_types = {"consolidation", "outdated", "quality"}

        # At minimum, should have some recommendations
        assert len(result["recommendations"]) > 0
        # Should have at least some of the expected types
        assert len(rec_types & expected_types) > 0

    def test_generate_recommendations_confidence_threshold(self):
        """Test that confidence threshold filtering works."""
        documents = [
            {"id": "doc1", "title": "API Guide", "content": "API content", "type": "api_docs"},
            {"id": "doc2", "title": "API Reference", "content": "API content", "type": "api_docs"}
        ]

        # Test with very high confidence threshold
        result = asyncio.run(self.summarizer.generate_recommendations(
            documents,
            confidence_threshold=0.9
        ))

        # Should filter out low-confidence recommendations
        for rec in result["recommendations"]:
            assert rec["confidence_score"] >= 0.9

    def test_generate_recommendations_specific_types(self):
        """Test that specific recommendation types can be requested."""
        documents = [
            {"id": "doc1", "title": "API Guide", "content": "API content", "type": "api_docs"},
            {"id": "doc2", "title": "API Reference", "content": "API content", "type": "api_docs"},
            {"id": "doc3", "title": "Old Doc", "content": "Old content", "dateCreated": "2020-01-01", "type": "guide"}
        ]

        # Test requesting only consolidation recommendations
        result = asyncio.run(self.summarizer.generate_recommendations(
            documents,
            recommendation_types=["consolidation"]
        ))

        # Should only include consolidation recommendations
        rec_types = set(rec["type"] for rec in result["recommendations"])
        assert rec_types == {"consolidation"} or len(result["recommendations"]) == 0


class TestRecommendationDataValidation:
    """Test data validation for recommendation endpoints."""

    def setup_method(self):
        """Setup test fixtures."""
        self.client = TestClient(app)

    def test_recommendations_endpoint_validation(self):
        """Test comprehensive input validation."""
        # Test invalid document structure
        response = self.client.post("/api/v1/recommendations", json={
            "documents": "not_a_list"
        })
        assert response.status_code == 422

        # Test document without required fields
        response = self.client.post("/api/v1/recommendations", json={
            "documents": [{"title": "Test"}]  # Missing id and content
        })
        assert response.status_code == 422

        # Test with invalid recommendation types
        response = self.client.post("/api/v1/recommendations", json={
            "documents": [
                {"id": "doc1", "title": "Test", "content": "Test content"}
            ],
            "recommendation_types": "not_a_list"
        })
        assert response.status_code == 422

        # Test with invalid confidence threshold
        response = self.client.post("/api/v1/recommendations", json={
            "documents": [
                {"id": "doc1", "title": "Test", "content": "Test content"}
            ],
            "confidence_threshold": "not_a_number"
        })
        assert response.status_code == 422

    def test_recommendations_endpoint_error_handling(self):
        """Test error handling in recommendation endpoints."""
        documents = [
            {"id": "doc1", "title": "Test", "content": "Test content"}
        ]

        # Mock an exception in the summarizer
        with patch.object(SimpleSummarizer, 'generate_recommendations', side_effect=Exception("Test error")):
            response = self.client.post("/api/v1/recommendations", json={
                "documents": documents
            })

            assert response.status_code == 200  # Should still return 200 with error in response
            data = response.json()
            assert data["success"] is False
            assert "error" in data
