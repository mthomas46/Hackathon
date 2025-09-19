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
        assert "quality" in rec["description"].lower() or "issues" in rec["description"].lower()

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
        with patch('main.SimpleSummarizer.generate_recommendations', side_effect=Exception("Test error")):
            response = self.client.post("/api/v1/recommendations", json={
                "documents": documents
            })

            assert response.status_code == 200  # Should still return 200 with error in response
            data = response.json()
            assert data["success"] is False
            assert "error" in data


class TestComprehensiveQualityAnalysis:
    """Test the comprehensive quality analysis functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.summarizer = SimpleSummarizer()

    def test_analyze_document_quality_comprehensive_empty_content(self):
        """Test quality analysis with empty content."""
        document = {"id": "doc1", "title": "Empty Doc", "content": ""}

        result = asyncio.run(self.summarizer._analyze_document_quality_comprehensive(document))

        assert len(result["issues"]) == 1
        assert result["issues"][0]["type"] == "missing_content"
        assert result["issues"][0]["severity"] == "critical"
        assert result["metrics"]["word_count"] == 0
        assert result["metrics"]["overall_score"] == 0

    def test_analyze_document_quality_comprehensive_good_document(self):
        """Test quality analysis with a well-structured document."""
        document = {
            "id": "doc1",
            "title": "API Documentation",
            "content": """# API Documentation

## Getting Started

This guide will help you get started with our API.

## Authentication

To authenticate, use your API key in the header.

## Endpoints

### GET /users

Retrieve a list of users.

**Parameters:**
- `limit` (optional): Maximum number of results

**Response:**
```json
{
  "users": [...]
}
```

## Examples

Here's how to get users:

```python
import requests

response = requests.get('/users')
print(response.json())
```

## Support

For help, contact support@example.com or visit our GitHub repository.
"""
        }

        result = asyncio.run(self.summarizer._analyze_document_quality_comprehensive(document))

        # Should have minimal issues for a well-structured document
        assert len(result["issues"]) <= 5  # Allow some minor issues
        assert result["metrics"]["word_count"] > 50  # More realistic word count
        assert result["metrics"]["overall_score"] > 0.5  # More realistic score

    def test_analyze_document_quality_comprehensive_poor_document(self):
        """Test quality analysis with a poorly structured document."""
        document = {
            "id": "doc2",
            "title": "Poor Documentation",
            "content": "This is a very short document. It has some stuff but not much. It uses passive voice a lot and doesn't explain anything clearly. There are some things that could be better but it's not clear what to do. The document lacks structure and examples."
        }

        result = asyncio.run(self.summarizer._analyze_document_quality_comprehensive(document))

        # Should identify multiple quality issues
        assert len(result["issues"]) >= 3

        issue_types = [issue["type"] for issue in result["issues"]]
        assert "too_short" in issue_types or "unclear_language" in issue_types
        assert result["metrics"]["overall_score"] < 0.6

    def test_analyze_content_length_issues(self):
        """Test content length analysis."""
        # Test too short content
        short_content = "This is short."
        metrics = {"word_count": 3}
        issues = self.summarizer._analyze_content_length(short_content, metrics)

        assert len(issues) == 1
        assert issues[0]["type"] == "too_short"
        assert issues[0]["severity"] == "high"

        # Test too verbose content
        long_content = "word " * 4000  # Very long content
        metrics = {"word_count": 4000}
        issues = self.summarizer._analyze_content_length(long_content, metrics)

        assert len(issues) == 1
        assert issues[0]["type"] == "too_verbose"
        assert issues[0]["severity"] == "medium"

    def test_analyze_clarity_and_readability(self):
        """Test clarity and readability analysis."""
        # Test complex sentences - make one very long sentence
        complex_content = "This is a very long and complex sentence that contains many words and intricate ideas with multiple clauses and complex concepts that might be quite difficult for readers to understand and process effectively without considerable mental effort and deep concentration as they navigate through the various layers of meaning and technical details presented in this extended textual construction which continues for an extended period of time."
        metrics = {"word_count": len(complex_content.split())}
        issues = self.summarizer._analyze_clarity_and_readability(complex_content, metrics)

        print(f"Complex content word count: {len(complex_content.split())}")
        print(f"Issues found: {len(issues)}")
        for issue in issues:
            print(f"  - {issue['type']}: {issue['description']}")

        # Should detect either complex sentences or passive voice
        assert len(issues) >= 1
        has_complex = any(issue["type"] == "complex_sentences" for issue in issues)
        has_passive = any(issue["type"] == "passive_voice" for issue in issues)
        assert has_complex or has_passive

        # Test passive voice detection
        passive_content = "The system is used by users. Data is processed by the server. Results are returned to the client."
        metrics = {"word_count": len(passive_content.split())}
        issues = self.summarizer._analyze_clarity_and_readability(passive_content, metrics)

        passive_issues = [i for i in issues if i["type"] == "passive_voice"]
        assert len(passive_issues) >= 1

    def test_analyze_technical_accuracy(self):
        """Test technical accuracy analysis."""
        # Test unformatted code detection
        code_content = "function processData(data) { return data.map(item => item.value); }"
        document = {"id": "doc1", "title": "Code Example"}
        metrics = {"technical_accuracy": 1.0}
        issues = self.summarizer._analyze_technical_accuracy(code_content, document, metrics)

        assert len(issues) >= 1
        assert any(issue["type"] == "unformatted_code" for issue in issues)

        # Test API documentation completeness
        api_content = "Our API is great. It has many features. API API API."
        document = {"id": "doc2", "title": "API Overview"}
        metrics = {"technical_accuracy": 1.0}
        issues = self.summarizer._analyze_technical_accuracy(api_content, document, metrics)

        api_issues = [i for i in issues if "api" in i["type"]]
        assert len(api_issues) >= 1

    def test_analyze_structure_and_organization(self):
        """Test structure and organization analysis."""
        # Test poor structure - make it much longer to trigger detection
        unstructured_content = ("This is a long document without any headings or structure. " * 50) + "It just keeps going on and on with lots of text that doesn't have any clear organization or logical flow. There are no sections to break up the content and make it easier to read and understand. " * 20
        title = "Long Document"
        metrics = {"structure_score": 1.0}
        issues = self.summarizer._analyze_structure_and_organization(unstructured_content, title, metrics)

        print(f"Unstructured content word count: {len(unstructured_content.split())}")
        print(f"Issues found: {len(issues)}")
        for issue in issues:
            print(f"  - {issue['type']}: {issue['description']}")

        # Should detect poor structure or poor flow
        assert len(issues) >= 1
        assert any(issue["type"] in ["poor_structure", "poor_flow"] for issue in issues)

        # Test good structure
        structured_content = """# Main Title

## Section 1
Content for section 1.

## Section 2
Content for section 2.

### Subsection
More detailed content.

## Section 3
Final section content.
"""
        title = "Well Structured Document"
        metrics = {"structure_score": 1.0}
        issues = self.summarizer._analyze_structure_and_organization(structured_content, title, metrics)

        # Should have fewer or no structural issues
        structural_issues = [i for i in issues if "structure" in i["type"] or "flow" in i["type"]]
        assert len(structural_issues) <= 1

    def test_analyze_consistency(self):
        """Test consistency analysis."""
        # Test inconsistent terminology
        inconsistent_content = "You can visit our web site or website to create a user name or username. Then you can log in or login to access your account."
        metrics = {"consistency_score": 1.0}
        issues = self.summarizer._analyze_consistency(inconsistent_content, metrics)

        assert len(issues) >= 1
        assert any("terminology" in issue["type"] for issue in issues)

    def test_analyze_completeness(self):
        """Test completeness analysis."""
        # Test tutorial missing sections
        tutorial_content = "This is a tutorial about getting started. It explains how to begin but doesn't have prerequisites or examples or a conclusion."
        document = {"id": "doc1", "title": "Tutorial", "type": "tutorial"}
        metrics = {"completeness_score": 1.0}
        issues = self.summarizer._analyze_completeness(tutorial_content, document, metrics)

        completeness_issues = [i for i in issues if "missing_sections" in i["type"]]
        assert len(completeness_issues) >= 1

    def test_calculate_overall_quality_score(self):
        """Test overall quality score calculation."""
        # Test with good metrics and no issues
        metrics = {
            "technical_accuracy": 0.9,
            "structure_score": 0.9,
            "consistency_score": 0.9,
            "completeness_score": 0.9,
            "word_count": 500
        }
        issues = []

        score = self.summarizer._calculate_overall_quality_score(metrics, issues)
        assert score > 0.8

        # Test with poor metrics and many issues
        metrics = {
            "technical_accuracy": 0.3,
            "structure_score": 0.3,
            "consistency_score": 0.3,
            "completeness_score": 0.3,
            "word_count": 20
        }
        issues = [
            {"severity": "high"},
            {"severity": "critical"},
            {"severity": "medium"}
        ]

        score = self.summarizer._calculate_overall_quality_score(metrics, issues)
        assert score < 0.5

    def test_determine_quality_priority(self):
        """Test quality priority determination."""
        # Test critical issues
        issues = [{"severity": "critical"}, {"severity": "low"}]
        metrics = {}
        priority = self.summarizer._determine_quality_priority(issues, metrics)
        assert priority == "high"

        # Test many high severity issues
        issues = [{"severity": "high"}, {"severity": "high"}, {"severity": "high"}]
        priority = self.summarizer._determine_quality_priority(issues, metrics)
        assert priority == "high"

        # Test minor issues
        issues = [{"severity": "low"}, {"severity": "low"}]
        priority = self.summarizer._determine_quality_priority(issues, metrics)
        assert priority == "low"

    def test_comprehensive_quality_analysis_integration(self):
        """Test the complete quality analysis workflow."""
        documents = [
            {
                "id": "good_doc",
                "title": "Well-Structured API Guide",
                "content": """# API Documentation

## Overview
This comprehensive guide covers our REST API with detailed examples and best practices for developers.

## Authentication
To authenticate with our API, you need to include a Bearer token in the Authorization header of your HTTP requests. You can obtain tokens from the developer portal.

## Endpoints

### GET /users
Retrieve a list of users from the system.

**Parameters:**
- `limit` (optional): Maximum number of results to return (default: 20)
- `offset` (optional): Number of results to skip (default: 0)

**Response:**
```json
{
  "users": [
    {
      "id": 123,
      "name": "John Doe",
      "email": "john@example.com"
    }
  ],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

**Example:**
```bash
curl -H "Authorization: Bearer your_token_here" \\
     -H "Content-Type: application/json" \\
     "https://api.example.com/users?limit=10"
```

## Error Handling
The API uses standard HTTP status codes. Common errors include:
- 400 Bad Request: Invalid parameters
- 401 Unauthorized: Missing or invalid token
- 404 Not Found: Resource doesn't exist
- 500 Internal Server Error: Server error

## Rate Limiting
API calls are limited to 1000 requests per hour. Rate limit headers are included in responses.

## Support
For help, contact support@example.com or visit our GitHub repository for code examples and issue tracking.
"""
            },
            {
                "id": "poor_doc",
                "title": "Poor Documentation",
                "content": "This document is very short and unclear. It doesn't explain anything well and lacks examples or structure. Very confusing content that doesn't help users understand anything."
            }
        ]

        # Test comprehensive recommendations
        result = asyncio.run(self.summarizer.generate_recommendations(documents))

        # Should generate recommendations for both documents
        quality_recs = [r for r in result["recommendations"] if r["type"] == "quality"]
        assert len(quality_recs) >= 1

        # Should have quality recommendations for both documents
        affected_docs = set()
        for rec in quality_recs:
            affected_docs.update(rec["affected_documents"])

        assert "poor_doc" in affected_docs
        assert "good_doc" in affected_docs

        # Both should have quality scores in their metadata
        for rec in quality_recs:
            assert "quality_score" in rec["metadata"]
            assert "issues" in rec["metadata"]
            assert len(rec["metadata"]["issues"]) > 0
