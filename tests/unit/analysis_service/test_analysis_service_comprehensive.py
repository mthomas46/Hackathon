"""Comprehensive Analysis Service Tests.

Tests for document analysis, quality assessment, consistency checking,
and AI-powered analysis workflows in the LLM Documentation Ecosystem.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List
import json

# Adjust path for local imports
import sys
from pathlib import Path

# Add the Analysis Service directory to Python path
analysis_service_path = Path(__file__).parent.parent.parent.parent / "services" / "analysis-service"
sys.path.insert(0, str(analysis_service_path))

from modules.core.document_analyzer import DocumentAnalyzer
from modules.core.quality_analyzer import QualityAnalyzer
from modules.core.consistency_analyzer import ConsistencyAnalyzer
from modules.core.ai_analyzer import AIAnalyzer
from modules.models import AnalysisRequest, DocumentAnalysis, QualityReport

# Test markers for parallel execution and categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.analysis_service
]


@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway for testing."""
    with patch('modules.core.document_analyzer.LLMGateway') as mock_gateway_class:
        mock_gateway = MagicMock()
        mock_gateway_class.return_value = mock_gateway

        # Mock analysis responses
        mock_gateway.analyze_document = AsyncMock(return_value={
            "success": True,
            "analysis": {
                "content_quality": 0.85,
                "structure_score": 0.9,
                "clarity_score": 0.8,
                "completeness_score": 0.75,
                "issues": ["Minor formatting issue"],
                "recommendations": ["Improve section organization"]
            }
        })

        mock_gateway.compare_documents = AsyncMock(return_value={
            "success": True,
            "similarity": 0.78,
            "differences": ["Different terminology used"],
            "consistency_score": 0.82
        })

        yield mock_gateway


@pytest.fixture
def mock_doc_store():
    """Mock Doc Store for testing."""
    with patch('modules.core.document_analyzer.DocStoreClient') as mock_store_class:
        mock_store = MagicMock()
        mock_store_class.return_value = mock_store

        mock_store.get_document = AsyncMock(return_value={
            "success": True,
            "data": {
                "document": {
                    "id": "test-doc-123",
                    "title": "Test API Documentation",
                    "content": "# API Documentation\n\nThis is test content for analysis.",
                    "metadata": {"type": "api_doc", "version": "1.0"}
                }
            }
        })

        mock_store.store_analysis = AsyncMock(return_value={
            "success": True,
            "analysis_id": "analysis-456"
        })

        yield mock_store


@pytest.fixture
def document_analyzer(mock_llm_gateway, mock_doc_store):
    """Create DocumentAnalyzer instance for testing."""
    return DocumentAnalyzer()


@pytest.fixture
def quality_analyzer(mock_llm_gateway):
    """Create QualityAnalyzer instance for testing."""
    return QualityAnalyzer()


@pytest.fixture
def consistency_analyzer(mock_llm_gateway, mock_doc_store):
    """Create ConsistencyAnalyzer instance for testing."""
    return ConsistencyAnalyzer()


@pytest.fixture
def ai_analyzer(mock_llm_gateway):
    """Create AIAnalyzer instance for testing."""
    return AIAnalyzer()


class TestDocumentAnalyzer:
    """Comprehensive tests for document analysis functionality."""

    def test_analyze_document_comprehensive(self, document_analyzer, mock_llm_gateway, mock_doc_store):
        """Test comprehensive document analysis."""
        doc_id = "test-doc-123"

        result = document_analyzer.analyze_document_comprehensive(doc_id)

        assert isinstance(result, dict)
        assert "success" in result
        assert "analysis" in result

        analysis = result["analysis"]
        assert "content_analysis" in analysis
        assert "structure_analysis" in analysis
        assert "quality_metrics" in analysis
        assert "recommendations" in analysis

        # Verify LLM was called
        mock_llm_gateway.analyze_document.assert_called_once()

        # Verify analysis was stored
        mock_doc_store.store_analysis.assert_called_once()

    def test_analyze_document_structure(self, document_analyzer):
        """Test analysis of document structure."""
        structured_content = """
# Main Title

## Introduction
This is the introduction section.

## API Reference

### Authentication
Authentication details here.

### Endpoints
- GET /users
- POST /users

## Conclusion
Summary of the API.
"""

        structure_analysis = document_analyzer.analyze_document_structure(structured_content)

        assert isinstance(structure_analysis, dict)
        assert "headings" in structure_analysis
        assert "sections" in structure_analysis
        assert "hierarchy" in structure_analysis
        assert "structure_score" in structure_analysis

        headings = structure_analysis["headings"]
        assert len(headings) >= 4  # Main title + 3 H2 sections

    def test_extract_document_metadata(self, document_analyzer):
        """Test extraction of document metadata."""
        content = """
---
title: User Authentication API
version: 1.0.0
author: API Team
description: Authentication service for user management
tags: [authentication, security, api]
---

# User Authentication API

This API provides secure authentication functionality.
"""

        metadata = document_analyzer.extract_document_metadata(content)

        assert isinstance(metadata, dict)
        assert metadata["title"] == "User Authentication API"
        assert metadata["version"] == "1.0.0"
        assert metadata["author"] == "API Team"
        assert "authentication" in metadata["tags"]

    def test_identify_document_type(self, document_analyzer):
        """Test automatic document type identification."""
        test_cases = [
            ("# REST API Documentation\n## Endpoints", "api_documentation"),
            ("# User Guide\n## Getting Started", "user_guide"),
            ("# System Architecture\n## Components", "architecture_doc"),
            ("# Code Review\n## Findings", "code_review"),
            ("# Requirements\n## Functional Requirements", "requirements")
        ]

        for content, expected_type in test_cases:
            doc_type = document_analyzer.identify_document_type(content)
            assert isinstance(doc_type, dict)
            assert "document_type" in doc_type
            assert "confidence" in doc_type

    def test_analyze_document_readability(self, document_analyzer):
        """Test analysis of document readability."""
        readable_content = """
# Clear Documentation

## Introduction
This document explains the authentication system in simple terms.

## How It Works
The system uses JWT tokens for secure authentication. Users log in with their credentials and receive a token that can be used for subsequent requests.

## Benefits
- Secure authentication
- Easy to implement
- Scalable solution
"""

        readability = document_analyzer.analyze_document_readability(readable_content)

        assert isinstance(readability, dict)
        assert "readability_score" in readability
        assert "reading_level" in readability
        assert "complexity_metrics" in readability

        # Well-structured content should have good readability
        assert readability["readability_score"] > 0.7

    def test_extract_key_concepts(self, document_analyzer, mock_llm_gateway):
        """Test extraction of key concepts from documents."""
        technical_content = """
The authentication service implements OAuth 2.0 protocol with JWT tokens.
Users authenticate via REST API endpoints using secure HTTPS connections.
The system supports multi-factor authentication and role-based access control.
"""

        concepts = document_analyzer.extract_key_concepts(technical_content)

        assert isinstance(concepts, list)
        assert len(concepts) > 0

        # Should extract technical concepts
        concept_names = [c.get("name", "").lower() for c in concepts]
        assert any("authentication" in name for name in concept_names)
        assert any("oauth" in name for name in concept_names)
        assert any("jwt" in name for name in concept_names)

    def test_analyze_document_freshness(self, document_analyzer):
        """Test analysis of document freshness and timeliness."""
        content_with_dates = """
Last updated: January 15, 2024

## Recent Changes
- Added OAuth2 support (Jan 10, 2024)
- Improved security (Dec 20, 2023)
- Bug fixes (Nov 15, 2023)

## Future Plans
- Multi-factor authentication (Q2 2024)
"""

        freshness = document_analyzer.analyze_document_freshness(content_with_dates)

        assert isinstance(freshness, dict)
        assert "freshness_score" in freshness
        assert "last_updated" in freshness
        assert "staleness_indicators" in freshness
        assert "update_recommendations" in freshness

    def test_generate_document_summary(self, document_analyzer, mock_llm_gateway):
        """Test generation of document summaries."""
        long_content = """
# Comprehensive API Documentation

## Overview
This API provides comprehensive user management functionality including authentication, authorization, and profile management.

## Authentication
The API supports multiple authentication methods:
- JWT Bearer tokens
- API keys
- OAuth2 flows
- SAML integration

## User Management
### Creating Users
POST /users endpoint for user creation.

### User Profiles
GET /users/{id} for retrieving user profiles.

### Updating Users
PUT /users/{id} for updating user information.

## Security Features
- Rate limiting
- Input validation
- SQL injection prevention
- XSS protection

## Error Handling
Standard HTTP status codes with detailed error messages.
"""

        summary = document_analyzer.generate_document_summary(long_content)

        assert isinstance(summary, dict)
        assert "summary" in summary
        assert "key_points" in summary
        assert "word_count" in summary
        assert "compression_ratio" in summary

        # Summary should be significantly shorter than original
        original_words = len(long_content.split())
        summary_words = len(summary["summary"].split())
        assert summary_words < original_words * 0.5  # At least 50% compression

    def test_analyze_cross_references(self, document_analyzer):
        """Test analysis of cross-references between documents."""
        documents = [
            {
                "id": "api-doc",
                "content": "See the user guide (user-guide.md) for detailed instructions."
            },
            {
                "id": "user-guide",
                "content": "Refer to the API documentation (api-doc.md) for technical details."
            },
            {
                "id": "troubleshooting",
                "content": "Check the API docs for error codes."
            }
        ]

        cross_refs = document_analyzer.analyze_cross_references(documents)

        assert isinstance(cross_refs, dict)
        assert "reference_map" in cross_refs
        assert "broken_links" in cross_refs
        assert "reference_health" in cross_refs

    def test_batch_document_analysis(self, document_analyzer, mock_llm_gateway, mock_doc_store):
        """Test batch processing of multiple documents."""
        doc_ids = ["doc-1", "doc-2", "doc-3"]

        batch_result = document_analyzer.batch_analyze_documents(doc_ids)

        assert isinstance(batch_result, dict)
        assert "success" in batch_result
        assert "results" in batch_result

        results = batch_result["results"]
        assert isinstance(results, list)
        assert len(results) == len(doc_ids)

        for result in results:
            assert isinstance(result, dict)
            assert "document_id" in result
            assert "analysis" in result

    def test_incremental_document_analysis(self, document_analyzer, mock_doc_store):
        """Test incremental analysis of document changes."""
        doc_id = "test-doc-123"
        previous_analysis = {
            "content_hash": "old-hash",
            "last_analyzed": "2024-01-10T10:00:00Z",
            "analysis_summary": {"quality_score": 0.8}
        }

        incremental = document_analyzer.incremental_analyze_document(doc_id, previous_analysis)

        assert isinstance(incremental, dict)
        assert "needs_reanalysis" in incremental
        assert "changes_detected" in incremental

    def test_document_analysis_with_context(self, document_analyzer):
        """Test document analysis with contextual information."""
        content = "This API uses JWT for authentication."
        context = {
            "project": "auth-service",
            "audience": "developers",
            "domain": "security",
            "previous_versions": ["v1.0", "v1.1"]
        }

        contextual_analysis = document_analyzer.analyze_document_with_context(content, context)

        assert isinstance(contextual_analysis, dict)
        assert "context_aware_analysis" in contextual_analysis
        assert "contextual_insights" in contextual_analysis
        assert "adapted_recommendations" in contextual_analysis


class TestQualityAnalyzer:
    """Comprehensive tests for quality analysis functionality."""

    def test_comprehensive_quality_assessment(self, quality_analyzer, mock_llm_gateway):
        """Test comprehensive quality assessment."""
        document_content = """
# API Documentation

## Overview
This is an API for user management.

## Endpoints
- GET /users - Get users
- POST /users - Create user

## Examples
No examples provided.
"""

        quality_report = quality_analyzer.assess_document_quality(document_content)

        assert isinstance(quality_report, dict)
        assert "overall_quality_score" in quality_report
        assert "quality_dimensions" in quality_report
        assert "issues" in quality_report
        assert "recommendations" in quality_report

        dimensions = quality_report["quality_dimensions"]
        assert "completeness" in dimensions
        assert "accuracy" in dimensions
        assert "clarity" in dimensions

    def test_quality_dimension_analysis(self, quality_analyzer):
        """Test analysis of individual quality dimensions."""
        dimensions_to_test = [
            ("completeness", "API documentation with all endpoints documented"),
            ("accuracy", "Technical documentation with correct information"),
            ("clarity", "Clear and understandable documentation"),
            ("consistency", "Consistent formatting and terminology"),
            ("usability", "Easy to navigate and use documentation")
        ]

        for dimension, content in dimensions_to_test:
            dimension_score = quality_analyzer.analyze_quality_dimension(content, dimension)

            assert isinstance(dimension_score, dict)
            assert "score" in dimension_score
            assert "assessment" in dimension_score
            assert 0.0 <= dimension_score["score"] <= 1.0

    def test_identify_quality_issues(self, quality_analyzer):
        """Test identification of quality issues."""
        problematic_doc = """
API Docs

endpoints:
get /users
post /users

no examples or details
"""

        issues = quality_analyzer.identify_quality_issues(problematic_doc)

        assert isinstance(issues, list)
        assert len(issues) > 0

        # Should identify common quality issues
        issue_types = [issue.get("type") for issue in issues]
        assert any(issue_type in ["completeness", "structure", "formatting"]
                  for issue_type in issue_types)

    def test_generate_quality_recommendations(self, quality_analyzer):
        """Test generation of quality improvement recommendations."""
        quality_data = {
            "overall_score": 0.6,
            "dimensions": {
                "completeness": 0.5,
                "clarity": 0.7,
                "structure": 0.8
            },
            "issues": [
                {"type": "completeness", "severity": "high", "description": "Missing examples"}
            ]
        }

        recommendations = quality_analyzer.generate_quality_recommendations(quality_data)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should include actionable recommendations
        recommendation_texts = [rec.get("text", "") for rec in recommendations]
        assert any("example" in text.lower() or "complete" in text.lower()
                  for text in recommendation_texts)

    def test_quality_benchmarking(self, quality_analyzer):
        """Test quality benchmarking against standards."""
        quality_scores = {
            "completeness": 0.85,
            "accuracy": 0.9,
            "clarity": 0.8,
            "consistency": 0.75,
            "usability": 0.7
        }

        benchmark = quality_analyzer.benchmark_quality(quality_scores)

        assert isinstance(benchmark, dict)
        assert "benchmark_score" in benchmark
        assert "grade" in benchmark
        assert "industry_standards" in benchmark
        assert "improvement_areas" in benchmark

    def test_quality_trend_analysis(self, quality_analyzer):
        """Test analysis of quality trends over time."""
        historical_quality = [
            {"date": "2024-01-01", "score": 0.7},
            {"date": "2024-01-08", "score": 0.75},
            {"date": "2024-01-15", "score": 0.8},
            {"date": "2024-01-22", "score": 0.82}
        ]

        trends = quality_analyzer.analyze_quality_trends(historical_quality)

        assert isinstance(trends, dict)
        assert "trend_direction" in trends
        assert "improvement_rate" in trends
        assert "stability_score" in trends

        # Should show positive trend
        assert trends["trend_direction"] == "improving"

    def test_content_type_specific_quality(self, quality_analyzer):
        """Test quality assessment specific to content types."""
        content_types = [
            ("api_documentation", "# API Docs\n## Endpoints\nGET /users"),
            ("user_guide", "# User Guide\n## Getting Started\nFollow these steps..."),
            ("technical_spec", "# Technical Specification\n## Requirements\nReq-1: ..."),
            ("code_documentation", "# Function: authenticate_user\nValidates user credentials")
        ]

        for content_type, content in content_types:
            type_quality = quality_analyzer.assess_content_type_quality(content, content_type)

            assert isinstance(type_quality, dict)
            assert "type_specific_score" in type_quality
            assert "type_criteria" in type_quality
            assert "type_recommendations" in type_quality

    def test_quality_feedback_loop(self, quality_analyzer):
        """Test quality improvement through feedback loops."""
        initial_quality = {"overall_score": 0.7}
        user_feedback = {
            "ratings": [4, 5, 3, 4],
            "comments": ["good examples", "needs more details", "clear structure"],
            "usage_patterns": ["frequently_referenced", "high_completion_rate"]
        }

        improved_quality = quality_analyzer.apply_quality_feedback(initial_quality, user_feedback)

        assert isinstance(improved_quality, dict)
        assert "adjusted_score" in improved_quality
        assert "feedback_impact" in improved_quality
        assert "applied_improvements" in improved_quality

    def test_quality_assurance_automation(self, quality_analyzer):
        """Test automated quality assurance processes."""
        quality_checks = [
            {"name": "completeness_check", "automated": True, "threshold": 0.8},
            {"name": "consistency_check", "automated": True, "threshold": 0.7},
            {"name": "manual_review", "automated": False, "criteria": "expert_review"}
        ]

        automation = quality_analyzer.automate_quality_assurance(quality_checks)

        assert isinstance(automation, dict)
        assert "automated_checks" in automation
        assert "manual_checks" in automation
        assert "automation_coverage" in automation
        assert "quality_gate_status" in automation


class TestConsistencyAnalyzer:
    """Comprehensive tests for consistency analysis functionality."""

    def test_analyze_document_consistency(self, consistency_analyzer, mock_llm_gateway, mock_doc_store):
        """Test comprehensive document consistency analysis."""
        doc_id = "test-doc-123"

        consistency_report = consistency_analyzer.analyze_document_consistency(doc_id)

        assert isinstance(consistency_report, dict)
        assert "overall_consistency_score" in consistency_report
        assert "consistency_dimensions" in consistency_report
        assert "issues" in consistency_report
        assert "recommendations" in consistency_report

        dimensions = consistency_report["consistency_dimensions"]
        assert "terminology" in dimensions
        assert "formatting" in dimensions
        assert "structure" in dimensions

    def test_terminology_consistency_check(self, consistency_analyzer):
        """Test consistency checking of terminology."""
        documents = [
            {"content": "Use authentication token for API access"},
            {"content": "Use auth token for API access"},
            {"content": "Use API key for authentication"}
        ]

        terminology_check = consistency_analyzer.check_terminology_consistency(documents)

        assert isinstance(terminology_check, dict)
        assert "terminology_variants" in terminology_check
        assert "recommended_terms" in terminology_check
        assert "inconsistency_score" in terminology_check

        # Should identify "authentication token" vs "auth token" vs "API key"
        variants = terminology_check["terminology_variants"]
        assert len(variants) > 0

    def test_formatting_consistency_analysis(self, consistency_analyzer):
        """Test analysis of formatting consistency."""
        inconsistent_docs = [
            {"content": "# Title\n## Section 1\n### Subsection"},
            {"content": "# Title\n## Section 1\n### Subsection"},  # Consistent
            {"content": "# Title\n## Section 1\n#### Subsection"}  # Inconsistent heading level
        ]

        formatting_analysis = consistency_analyzer.analyze_formatting_consistency(inconsistent_docs)

        assert isinstance(formatting_analysis, dict)
        assert "formatting_patterns" in formatting_analysis
        assert "inconsistencies" in formatting_analysis
        assert "consistency_score" in formatting_analysis

        inconsistencies = formatting_analysis["inconsistencies"]
        assert len(inconsistencies) > 0

    def test_structural_consistency_check(self, consistency_analyzer):
        """Test checking of structural consistency."""
        structures = [
            ["Introduction", "API Reference", "Examples", "Conclusion"],
            ["Overview", "API Docs", "Examples", "Summary"],  # Similar structure
            ["Getting Started", "Configuration", "Usage"]  # Different structure
        ]

        structural_consistency = consistency_analyzer.check_structural_consistency(structures)

        assert isinstance(structural_consistency, dict)
        assert "common_structure" in structural_consistency
        assert "structural_variations" in structural_consistency
        assert "consistency_score" in structural_consistency

    def test_cross_document_consistency(self, consistency_analyzer, mock_llm_gateway):
        """Test consistency analysis across multiple documents."""
        documents = [
            {"id": "api-v1", "content": "API v1 documentation"},
            {"id": "api-v2", "content": "API v2 documentation"},
            {"id": "user-guide", "content": "User guide referencing API"}
        ]

        cross_consistency = consistency_analyzer.analyze_cross_document_consistency(documents)

        assert isinstance(cross_consistency, dict)
        assert "document_relationships" in cross_consistency
        assert "consistency_matrix" in cross_consistency
        assert "cross_references" in cross_consistency

    def test_consistency_rule_engine(self, consistency_analyzer):
        """Test application of consistency rules."""
        custom_rules = [
            {"type": "terminology", "pattern": r"auth.*token", "standard": "authentication token"},
            {"type": "formatting", "pattern": r"^##\s", "standard": "Use H2 for main sections"},
            {"type": "structure", "pattern": r"## API Reference", "standard": "Include API Reference section"}
        ]

        content = """
## Authentication
Use auth token for access.

## User Guide
Some content.

## API Reference
API endpoints listed here.
"""

        rule_results = consistency_analyzer.apply_consistency_rules(content, custom_rules)

        assert isinstance(rule_results, list)
        assert len(rule_results) > 0

        # Should identify rule violations and compliances
        rule_types = [result.get("rule_type") for result in rule_results]
        assert "terminology" in rule_types
        assert "formatting" in rule_types

    def test_consistency_baseline_establishment(self, consistency_analyzer):
        """Test establishment of consistency baselines."""
        baseline_documents = [
            {"content": "Standard API documentation format"},
            {"content": "Another standard document"},
            {"content": "Third baseline document"}
        ]

        baseline = consistency_analyzer.establish_consistency_baseline(baseline_documents)

        assert isinstance(baseline, dict)
        assert "terminology_standards" in baseline
        assert "formatting_standards" in baseline
        assert "structural_patterns" in baseline
        assert "baseline_score" in baseline

    def test_consistency_deviation_detection(self, consistency_analyzer):
        """Test detection of deviations from consistency baselines."""
        baseline = {
            "terminology_standards": ["authentication token", "API endpoint"],
            "formatting_standards": [r"^#\s", r"^##\s"],
            "structural_patterns": ["Introduction", "API Reference", "Examples"]
        }

        test_content = "Use auth token for API access. ## Section"  # Deviations present

        deviations = consistency_analyzer.detect_consistency_deviations(test_content, baseline)

        assert isinstance(deviations, list)
        assert len(deviations) > 0

        # Should detect terminology and formatting deviations
        deviation_types = [d.get("type") for d in deviations]
        assert any("terminology" in str(deviation_types).lower() for d_type in deviation_types)

    def test_consistency_report_generation(self, consistency_analyzer):
        """Test generation of comprehensive consistency reports."""
        consistency_data = {
            "overall_score": 0.75,
            "dimensions": {
                "terminology": 0.8,
                "formatting": 0.7,
                "structure": 0.9
            },
            "issues": [
                {"type": "terminology", "severity": "medium", "description": "Inconsistent auth terminology"}
            ],
            "recommendations": ["Standardize authentication terminology"]
        }

        report = consistency_analyzer.generate_consistency_report(consistency_data)

        assert isinstance(report, dict)
        assert "executive_summary" in report
        assert "detailed_findings" in report
        assert "action_plan" in report
        assert "generated_at" in report

    def test_batch_consistency_analysis(self, consistency_analyzer, mock_llm_gateway):
        """Test batch processing for consistency analysis."""
        document_batch = [
            {"id": "doc-1", "content": "Content 1"},
            {"id": "doc-2", "content": "Content 2"},
            {"id": "doc-3", "content": "Content 3"}
        ]

        batch_results = consistency_analyzer.batch_consistency_analysis(document_batch)

        assert isinstance(batch_results, list)
        assert len(batch_results) == len(document_batch)

        for result in batch_results:
            assert isinstance(result, dict)
            assert "document_id" in result
            assert "consistency_score" in result

    def test_consistency_trend_analysis(self, consistency_analyzer):
        """Test analysis of consistency trends over time."""
        historical_consistency = [
            {"date": "2024-01-01", "score": 0.7},
            {"date": "2024-01-08", "score": 0.75},
            {"date": "2024-01-15", "score": 0.8},
            {"date": "2024-01-22", "score": 0.82}
        ]

        trends = consistency_analyzer.analyze_consistency_trends(historical_consistency)

        assert isinstance(trends, dict)
        assert "trend_direction" in trends
        assert "improvement_rate" in trends
        assert "volatility_score" in trends

        # Should show positive trend
        assert trends["trend_direction"] == "improving"


class TestAIAnalyzer:
    """Comprehensive tests for AI analysis functionality."""

    def test_ai_powered_document_insights(self, ai_analyzer, mock_llm_gateway):
        """Test AI-powered document insights generation."""
        content = """
The authentication service handles user login and session management.
It supports JWT tokens, OAuth2 flows, and multi-factor authentication.
The API includes endpoints for user registration, password reset, and profile management.
"""

        insights = ai_analyzer.generate_document_insights(content)

        assert isinstance(insights, dict)
        assert "key_insights" in insights
        assert "sentiment_analysis" in insights
        assert "topic_modeling" in insights
        assert "entity_recognition" in insights

        key_insights = insights["key_insights"]
        assert isinstance(key_insights, list)
        assert len(key_insights) > 0

    def test_intelligent_content_categorization(self, ai_analyzer, mock_llm_gateway):
        """Test intelligent content categorization."""
        content = """
# Machine Learning API

## Overview
This API provides machine learning model inference capabilities.

## Endpoints
- POST /predict - Run model predictions
- GET /models - List available models
- POST /train - Train new models

## Features
- Support for multiple ML frameworks
- Batch processing capabilities
- Real-time inference
"""

        categorization = ai_analyzer.categorize_content_intelligently(content)

        assert isinstance(categorization, dict)
        assert "primary_category" in categorization
        assert "secondary_categories" in categorization
        assert "confidence_scores" in categorization
        assert "category_hierarchy" in categorization

        # Should categorize as technical/API documentation
        primary_category = categorization["primary_category"]
        assert "technical" in primary_category.lower() or "api" in primary_category.lower()

    def test_ai_powered_quality_assessment(self, ai_analyzer, mock_llm_gateway):
        """Test AI-powered quality assessment."""
        document = """
API Documentation

## Getting Started
Install the package using pip.

## Usage
Call the API with your key.

No examples or detailed instructions provided.
"""

        ai_quality = ai_analyzer.assess_quality_with_ai(document)

        assert isinstance(ai_quality, dict)
        assert "ai_quality_score" in ai_quality
        assert "quality_insights" in ai_quality
        assert "improvement_suggestions" in ai_quality
        assert "quality_benchmarks" in ai_quality

        # Should identify quality issues
        insights = ai_quality["quality_insights"]
        assert len(insights) > 0

    def test_context_aware_analysis(self, ai_analyzer, mock_llm_gateway):
        """Test context-aware AI analysis."""
        content = "The service uses JWT for authentication."
        context = {
            "domain": "security",
            "audience": "developers",
            "project_type": "web_api",
            "compliance_requirements": ["owasp", "gdpr"]
        }

        contextual_analysis = ai_analyzer.analyze_with_context(content, context)

        assert isinstance(contextual_analysis, dict)
        assert "contextual_insights" in contextual_analysis
        assert "domain_specific_analysis" in contextual_analysis
        assert "compliance_analysis" in contextual_analysis
        assert "audience_adapted_content" in contextual_analysis

    def test_ai_generated_recommendations(self, ai_analyzer, mock_llm_gateway):
        """Test AI-generated recommendations for improvements."""
        analysis_results = {
            "quality_score": 0.7,
            "issues": [
                {"type": "completeness", "description": "Missing API examples"},
                {"type": "clarity", "description": "Unclear authentication flow"}
            ],
            "content_type": "api_documentation"
        }

        recommendations = ai_analyzer.generate_ai_recommendations(analysis_results)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should include specific, actionable recommendations
        recommendation_texts = [rec.get("text", "") for rec in recommendations]
        assert any("example" in text.lower() or "clarify" in text.lower()
                  for text in recommendation_texts)

    def test_sentiment_and_tone_analysis(self, ai_analyzer, mock_llm_gateway):
        """Test sentiment and tone analysis."""
        content_samples = [
            "This API is excellent and well-documented!",  # Positive
            "The documentation is confusing and incomplete.",  # Negative
            "Please review the API documentation.",  # Neutral
            "The authentication system works as expected."  # Neutral
        ]

        for content in content_samples:
            sentiment = ai_analyzer.analyze_sentiment_and_tone(content)

            assert isinstance(sentiment, dict)
            assert "sentiment" in sentiment
            assert "tone" in sentiment
            assert "confidence" in sentiment
            assert "emotional_indicators" in sentiment

    def test_topic_modeling_and_clustering(self, ai_analyzer, mock_llm_gateway):
        """Test topic modeling and document clustering."""
        documents = [
            "API authentication using JWT tokens",
            "User management and profile endpoints",
            "Database schema for user storage",
            "Security best practices for APIs",
            "Error handling and status codes"
        ]

        topic_modeling = ai_analyzer.perform_topic_modeling(documents)

        assert isinstance(topic_modeling, dict)
        assert "topics" in topic_modeling
        assert "document_clusters" in topic_modeling
        assert "topic_coherence" in topic_modeling
        assert "cluster_quality" in topic_modeling

        topics = topic_modeling["topics"]
        assert len(topics) > 0

    def test_ai_powered_content_enrichment(self, ai_analyzer, mock_llm_gateway):
        """Test AI-powered content enrichment."""
        basic_content = "The API supports user authentication."

        enriched = ai_analyzer.enrich_content_with_ai(basic_content)

        assert isinstance(enriched, dict)
        assert "enriched_content" in enriched
        assert "added_information" in enriched
        assert "enrichment_metadata" in enriched
        assert "quality_improvement" in enriched

        # Enriched content should be longer and more comprehensive
        original_length = len(basic_content)
        enriched_length = len(enriched["enriched_content"])
        assert enriched_length > original_length

    def test_ai_bias_and_fairness_analysis(self, ai_analyzer, mock_llm_gateway):
        """Test AI bias and fairness analysis."""
        content = """
Our user management system supports various user types.
Administrators have full access to all features.
Regular users can access basic functionality.
Guest users have limited read-only access.
"""

        bias_analysis = ai_analyzer.analyze_bias_and_fairness(content)

        assert isinstance(bias_analysis, dict)
        assert "bias_indicators" in bias_analysis
        assert "fairness_assessment" in bias_analysis
        assert "inclusivity_score" in bias_analysis
        assert "bias_mitigation_suggestions" in bias_analysis

    def test_ai_powered_content_summarization(self, ai_analyzer, mock_llm_gateway):
        """Test AI-powered content summarization."""
        long_content = """
The comprehensive user authentication system provides multiple layers of security.
It implements OAuth 2.0 authorization framework with support for authorization code,
implicit, and client credentials flows. The system includes JWT token generation and
validation, refresh token handling, and configurable token expiration policies.
Multi-factor authentication is supported through SMS, email, and authenticator apps.
The API provides endpoints for user registration, login, logout, password reset,
and profile management. Rate limiting is implemented to prevent abuse, and
comprehensive logging captures all authentication events for security auditing.
"""

        ai_summary = ai_analyzer.generate_ai_powered_summary(long_content)

        assert isinstance(ai_summary, dict)
        assert "ai_summary" in ai_summary
        assert "key_points" in ai_summary
        assert "compression_ratio" in ai_summary
        assert "summary_quality" in ai_summary

        # AI summary should capture essential information
        ai_summary_text = ai_summary["ai_summary"]
        assert len(ai_summary_text) < len(long_content) * 0.5  # Significant compression

        # Should include key concepts
        key_points = ai_summary["key_points"]
        assert len(key_points) > 0
        assert any("oauth" in point.lower() for point in key_points)

    def test_adaptive_ai_analysis(self, ai_analyzer, mock_llm_gateway):
        """Test adaptive AI analysis based on content characteristics."""
        content_types = [
            ("code_heavy", "def authenticate(user, pass): return check_creds(user, pass)"),
            ("narrative", "The authentication process involves several steps..."),
            ("structured", "- Step 1: Validate input\n- Step 2: Check credentials\n- Step 3: Generate token"),
            ("technical_spec", "API shall support JWT tokens per RFC 7519")
        ]

        for content_type, content in content_types:
            adaptive_analysis = ai_analyzer.perform_adaptive_analysis(content, content_type)

            assert isinstance(adaptive_analysis, dict)
            assert "analysis_strategy" in adaptive_analysis
            assert "adapted_approach" in adaptive_analysis
            assert "content_type_insights" in adaptive_analysis

    def test_ai_confidence_scoring(self, ai_analyzer):
        """Test AI confidence scoring for analysis results."""
        analysis_results = {
            "sentiment": "positive",
            "topics": ["authentication", "security"],
            "entities": ["JWT", "OAuth"],
            "quality_score": 0.85
        }

        confidence_scores = ai_analyzer.calculate_ai_confidence(analysis_results)

        assert isinstance(confidence_scores, dict)
        assert "overall_confidence" in confidence_scores
        assert "component_confidence" in confidence_scores
        assert "confidence_factors" in confidence_scores
        assert "uncertainty_indicators" in confidence_scores

        # Overall confidence should be a reasonable score
        assert 0.0 <= confidence_scores["overall_confidence"] <= 1.0

    def test_ai_analysis_explainability(self, ai_analyzer):
        """Test explainability of AI analysis results."""
        analysis_result = {
            "quality_score": 0.75,
            "issues": ["Missing examples"],
            "sentiment": "neutral"
        }

        explanation = ai_analyzer.explain_ai_analysis(analysis_result)

        assert isinstance(explanation, dict)
        assert "explanation_text" in explanation
        assert "reasoning_steps" in explanation
        assert "evidence" in explanation
        assert "confidence_explanation" in explanation

        # Should provide human-readable explanation
        explanation_text = explanation["explanation_text"]
        assert len(explanation_text) > 0
        assert "because" in explanation_text.lower() or "due to" in explanation_text.lower()
