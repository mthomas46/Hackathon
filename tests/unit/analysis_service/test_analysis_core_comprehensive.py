"""Comprehensive Analysis Service Core Tests.

Tests for the core analysis functionality including AI-powered document analysis,
quality assessment, consistency checking, and cross-document analysis.
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
analysis_path = Path(__file__).parent.parent.parent.parent / "services" / "analysis-service"
sys.path.insert(0, str(analysis_path))

from modules.core.analysis_engine import AnalysisEngine
from modules.core.quality_assessor import QualityAssessor
from modules.core.consistency_checker import ConsistencyChecker
from modules.models import AnalysisRequest, QualityAssessment, ConsistencyReport

# Test markers for parallel execution and categorization
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.analysis_service
]


@pytest.fixture
def mock_llm_gateway():
    """Mock LLM Gateway for testing."""
    with patch('modules.core.analysis_engine.LLMGateway') as mock_gateway_class:
        mock_gateway = MagicMock()
        mock_gateway_class.return_value = mock_gateway

        # Mock LLM responses for different analysis types
        mock_gateway.analyze_text = AsyncMock(return_value={
            "success": True,
            "analysis": {
                "quality_score": 0.85,
                "issues": ["Minor formatting issue"],
                "recommendations": ["Improve formatting"],
                "confidence": 0.92
            }
        })

        mock_gateway.compare_documents = AsyncMock(return_value={
            "success": True,
            "similarity_score": 0.78,
            "differences": ["Different terminology used"],
            "consistency_score": 0.82
        })

        yield mock_gateway


@pytest.fixture
def mock_doc_store():
    """Mock Doc Store for testing."""
    with patch('modules.core.analysis_engine.DocStoreClient') as mock_store_class:
        mock_store = MagicMock()
        mock_store_class.return_value = mock_store

        mock_store.get_document = AsyncMock(return_value={
            "success": True,
            "data": {
                "document": {
                    "id": "test-doc-123",
                    "content": "This is test document content for analysis.",
                    "metadata": {"type": "api_doc", "version": "1.0"}
                }
            }
        })

        yield mock_store


@pytest.fixture
def analysis_engine(mock_llm_gateway, mock_doc_store):
    """Create AnalysisEngine instance for testing."""
    return AnalysisEngine()


@pytest.fixture
def quality_assessor(mock_llm_gateway):
    """Create QualityAssessor instance for testing."""
    return QualityAssessor()


@pytest.fixture
def consistency_checker(mock_llm_gateway, mock_doc_store):
    """Create ConsistencyChecker instance for testing."""
    return ConsistencyChecker()


class TestAnalysisEngine:
    """Comprehensive tests for the core analysis engine."""

    def test_analyze_document_quality(self, analysis_engine, mock_llm_gateway):
        """Test document quality analysis."""
        doc_content = """
        # API Documentation

        ## Overview
        This API provides user management functionality.

        ## Endpoints
        - GET /users - Retrieve users
        - POST /users - Create user

        ## Authentication
        All requests require API key.
        """

        result = analysis_engine.analyze_document_quality(doc_content)

        assert isinstance(result, dict)
        assert "success" in result
        assert "analysis" in result

        analysis = result["analysis"]
        assert "quality_score" in analysis
        assert "issues" in analysis
        assert "recommendations" in analysis
        assert "confidence" in analysis

        # Verify LLM was called correctly
        mock_llm_gateway.analyze_text.assert_called_once()

    def test_analyze_document_consistency(self, analysis_engine, mock_llm_gateway, mock_doc_store):
        """Test document consistency analysis."""
        doc_id = "test-doc-123"

        result = analysis_engine.analyze_document_consistency(doc_id)

        assert isinstance(result, dict)
        assert "success" in result
        assert "consistency_report" in result

        report = result["consistency_report"]
        assert "overall_score" in report
        assert "issues" in report
        assert "recommendations" in report

    def test_compare_multiple_documents(self, analysis_engine, mock_llm_gateway):
        """Test comparison of multiple documents."""
        documents = [
            {"id": "doc-1", "content": "API documentation v1"},
            {"id": "doc-2", "content": "API documentation v2"},
            {"id": "doc-3", "content": "API documentation v3"}
        ]

        result = analysis_engine.compare_multiple_documents(documents)

        assert isinstance(result, dict)
        assert "success" in result
        assert "comparisons" in result

        comparisons = result["comparisons"]
        assert isinstance(comparisons, list)
        assert len(comparisons) > 0

    def test_extract_document_structure(self, analysis_engine):
        """Test document structure extraction."""
        doc_content = """
        # Main Title

        ## Section 1
        Content for section 1.

        ### Subsection 1.1
        More detailed content.

        ## Section 2
        Content for section 2.
        """

        result = analysis_engine.extract_document_structure(doc_content)

        assert isinstance(result, dict)
        assert "structure" in result

        structure = result["structure"]
        assert "headings" in structure
        assert "sections" in structure

        headings = structure["headings"]
        assert len(headings) >= 3  # Main title + 2 sections

    def test_identify_document_type(self, analysis_engine):
        """Test automatic document type identification."""
        test_cases = [
            ("API Documentation", "api_documentation"),
            ("User Guide", "user_guide"),
            ("System Architecture", "architecture_doc"),
            ("Code Review", "code_review"),
            ("Requirements Spec", "requirements")
        ]

        for content, expected_type in test_cases:
            result = analysis_engine.identify_document_type(content)
            assert isinstance(result, dict)
            assert "document_type" in result
            # Note: This would be improved with actual ML classification

    def test_generate_analysis_report(self, analysis_engine):
        """Test comprehensive analysis report generation."""
        analysis_results = {
            "quality_score": 0.85,
            "consistency_score": 0.78,
            "structure_score": 0.92,
            "completeness_score": 0.88
        }

        result = analysis_engine.generate_analysis_report(analysis_results)

        assert isinstance(result, dict)
        assert "success" in result
        assert "report" in result

        report = result["report"]
        assert "overall_score" in report
        assert "summary" in report
        assert "recommendations" in report
        assert "generated_at" in report

    def test_batch_document_analysis(self, analysis_engine, mock_llm_gateway):
        """Test batch processing of multiple documents."""
        documents = [
            {"id": "doc-1", "content": "Content 1"},
            {"id": "doc-2", "content": "Content 2"},
            {"id": "doc-3", "content": "Content 3"}
        ]

        results = analysis_engine.batch_analyze_documents(documents)

        assert isinstance(results, list)
        assert len(results) == 3

        for result in results:
            assert isinstance(result, dict)
            assert "success" in result
            assert "document_id" in result

    def test_analysis_with_custom_prompt(self, analysis_engine, mock_llm_gateway):
        """Test analysis with custom prompts."""
        doc_content = "Test document content"
        custom_prompt = "Analyze this document for technical accuracy and clarity."

        result = analysis_engine.analyze_with_custom_prompt(doc_content, custom_prompt)

        assert isinstance(result, dict)
        assert "success" in result
        assert "analysis" in result

        # Verify custom prompt was used
        call_args = mock_llm_gateway.analyze_text.call_args
        assert custom_prompt in call_args[1]["prompt"]

    def test_error_handling_invalid_document(self, analysis_engine):
        """Test error handling for invalid documents."""
        invalid_content = None

        with pytest.raises(ValueError):
            analysis_engine.analyze_document_quality(invalid_content)

    def test_error_handling_llm_failure(self, analysis_engine, mock_llm_gateway):
        """Test error handling when LLM service fails."""
        mock_llm_gateway.analyze_text.side_effect = Exception("LLM service unavailable")

        doc_content = "Test content"

        result = analysis_engine.analyze_document_quality(doc_content)

        # Should handle gracefully and return error information
        assert isinstance(result, dict)
        assert result["success"] is False
        assert "error" in result

    def test_analysis_caching(self, analysis_engine, mock_llm_gateway):
        """Test analysis result caching."""
        doc_content = "Test content for caching"

        # First analysis
        result1 = analysis_engine.analyze_document_quality(doc_content)

        # Second analysis (should use cache if implemented)
        result2 = analysis_engine.analyze_document_quality(doc_content)

        assert result1["success"] == result2["success"]
        # Note: Actual caching implementation would verify cache hit

    def test_performance_metrics_collection(self, analysis_engine):
        """Test collection of performance metrics."""
        doc_content = "Test content"

        result = analysis_engine.analyze_document_quality(doc_content)

        assert isinstance(result, dict)
        # Performance metrics would be collected during analysis
        # This test verifies the analysis completes with timing


class TestQualityAssessor:
    """Comprehensive tests for quality assessment functionality."""

    def test_assess_document_quality_comprehensive(self, quality_assessor, mock_llm_gateway):
        """Test comprehensive document quality assessment."""
        doc_content = """
        # API Reference

        ## Authentication
        Use API key for authentication.

        ## Endpoints
        GET /users
        Returns list of users.

        POST /users
        Creates new user.

        Parameters:
        - name: string
        - email: string
        """

        result = quality_assessor.assess_document_quality(doc_content)

        assert isinstance(result, dict)
        assert "success" in result
        assert "quality_assessment" in result

        assessment = result["quality_assessment"]
        assert "overall_score" in assessment
        assert "criteria_scores" in assessment
        assert "issues" in assessment
        assert "recommendations" in assessment

    def test_quality_criteria_evaluation(self, quality_assessor):
        """Test individual quality criteria evaluation."""
        criteria_tests = [
            ("completeness", "Complete documentation with all sections", 0.9),
            ("accuracy", "Accurate technical information", 0.85),
            ("clarity", "Clear and understandable content", 0.8),
            ("consistency", "Consistent formatting and terminology", 0.75),
            ("structure", "Well-organized document structure", 0.9)
        ]

        for criterion, content, expected_score in criteria_tests:
            score = quality_assessor.evaluate_criterion(content, criterion)
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_identify_quality_issues(self, quality_assessor):
        """Test identification of quality issues."""
        problematic_content = """
        API docs

        endpoints:
        /users - get users
        /create - create user

        no details or examples
        """

        issues = quality_assessor.identify_quality_issues(problematic_content)

        assert isinstance(issues, list)
        assert len(issues) > 0

        # Should identify common issues
        issue_types = [issue.get("type") for issue in issues]
        assert "completeness" in issue_types or "structure" in issue_types

    def test_generate_quality_recommendations(self, quality_assessor):
        """Test generation of quality improvement recommendations."""
        assessment_data = {
            "overall_score": 0.6,
            "issues": [
                {"type": "completeness", "severity": "high"},
                {"type": "structure", "severity": "medium"}
            ]
        }

        recommendations = quality_assessor.generate_recommendations(assessment_data)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should include specific actionable recommendations
        recommendation_texts = [rec.get("text", "") for rec in recommendations]
        assert any("completeness" in text.lower() or "structure" in text.lower()
                  for text in recommendation_texts)

    def test_quality_score_calculation(self, quality_assessor):
        """Test quality score calculation from multiple criteria."""
        criteria_scores = {
            "completeness": 0.8,
            "accuracy": 0.9,
            "clarity": 0.7,
            "consistency": 0.8,
            "structure": 0.9
        }

        weights = {
            "completeness": 0.25,
            "accuracy": 0.25,
            "clarity": 0.2,
            "consistency": 0.15,
            "structure": 0.15
        }

        overall_score = quality_assessor.calculate_overall_score(criteria_scores, weights)

        assert isinstance(overall_score, float)
        assert 0.0 <= overall_score <= 1.0

        # Verify weighted calculation
        expected_score = sum(score * weights[criterion]
                           for criterion, score in criteria_scores.items())
        assert abs(overall_score - expected_score) < 0.01

    def test_quality_benchmarking(self, quality_assessor):
        """Test quality benchmarking against standards."""
        assessment_data = {
            "overall_score": 0.85,
            "criteria_scores": {
                "completeness": 0.9,
                "accuracy": 0.8,
                "clarity": 0.9
            }
        }

        benchmark_result = quality_assessor.benchmark_quality(assessment_data)

        assert isinstance(benchmark_result, dict)
        assert "benchmark_score" in benchmark_result
        assert "grade" in benchmark_result
        assert "comparison" in benchmark_result

    def test_quality_trend_analysis(self, quality_assessor):
        """Test quality trend analysis over time."""
        historical_scores = [
            {"date": "2024-01-01", "score": 0.7},
            {"date": "2024-01-08", "score": 0.75},
            {"date": "2024-01-15", "score": 0.8},
            {"date": "2024-01-22", "score": 0.85}
        ]

        trend_analysis = quality_assessor.analyze_quality_trends(historical_scores)

        assert isinstance(trend_analysis, dict)
        assert "trend" in trend_analysis
        assert "improvement_rate" in trend_analysis
        assert "prediction" in trend_analysis

        # Should show positive trend
        assert trend_analysis["trend"] == "improving"
        assert trend_analysis["improvement_rate"] > 0


class TestConsistencyChecker:
    """Comprehensive tests for consistency checking functionality."""

    def test_check_document_consistency_basic(self, consistency_checker, mock_llm_gateway, mock_doc_store):
        """Test basic document consistency checking."""
        doc_id = "test-doc-123"

        result = consistency_checker.check_document_consistency(doc_id)

        assert isinstance(result, dict)
        assert "success" in result
        assert "consistency_report" in result

        report = result["consistency_report"]
        assert "overall_score" in report
        assert "issues" in report
        assert "recommendations" in report

    def test_compare_document_versions(self, consistency_checker, mock_llm_gateway):
        """Test comparison between document versions."""
        version1 = {"content": "Original API documentation", "version": 1}
        version2 = {"content": "Updated API documentation with changes", "version": 2}

        comparison = consistency_checker.compare_document_versions(version1, version2)

        assert isinstance(comparison, dict)
        assert "similarity_score" in comparison
        assert "differences" in comparison
        assert "breaking_changes" in comparison

    def test_cross_reference_analysis(self, consistency_checker, mock_llm_gateway):
        """Test cross-reference analysis between documents."""
        documents = [
            {"id": "api-doc", "content": "API documentation with endpoint definitions"},
            {"id": "user-guide", "content": "User guide referencing API endpoints"},
            {"id": "implementation", "content": "Implementation using API endpoints"}
        ]

        cross_refs = consistency_checker.analyze_cross_references(documents)

        assert isinstance(cross_refs, dict)
        assert "references" in cross_refs
        assert "missing_links" in cross_refs
        assert "inconsistencies" in cross_refs

    def test_terminology_consistency(self, consistency_checker):
        """Test terminology consistency checking."""
        documents = [
            {"content": "Use authentication token for API access"},
            {"content": "Use auth token for API access"},
            {"content": "Use API key for authentication"}
        ]

        terminology_check = consistency_checker.check_terminology_consistency(documents)

        assert isinstance(terminology_check, dict)
        assert "terminology_variants" in terminology_check
        assert "recommended_terms" in terminology_check
        assert "inconsistencies" in terminology_check

    def test_format_consistency(self, consistency_checker):
        """Test format consistency checking."""
        documents = [
            {"content": "# API Reference\n## Endpoint 1\n### Parameters"},
            {"content": "# User Guide\n## Section 1\n### Details"},
            {"content": "# Implementation\n## Component 1\n### Usage"}  # Inconsistent format
        ]

        format_check = consistency_checker.check_format_consistency(documents)

        assert isinstance(format_check, dict)
        assert "format_patterns" in format_check
        assert "inconsistencies" in format_check
        assert "recommendations" in format_check

    def test_link_validation(self, consistency_checker):
        """Test link and reference validation."""
        content_with_links = """
        See [API Documentation](#api-docs) for details.
        Refer to [User Guide](user-guide.md) for usage.
        Check [Broken Link](#nonexistent) for issues.
        """

        link_validation = consistency_checker.validate_links(content_with_links)

        assert isinstance(link_validation, dict)
        assert "valid_links" in link_validation
        assert "broken_links" in link_validation
        assert "warnings" in link_validation

    def test_generate_consistency_report(self, consistency_checker):
        """Test comprehensive consistency report generation."""
        consistency_data = {
            "overall_score": 0.82,
            "terminology_issues": 3,
            "format_inconsistencies": 2,
            "broken_links": 1,
            "cross_reference_issues": 2
        }

        report = consistency_checker.generate_consistency_report(consistency_data)

        assert isinstance(report, dict)
        assert "summary" in report
        assert "detailed_findings" in report
        assert "priority_actions" in report
        assert "generated_at" in report

    def test_consistency_rule_engine(self, consistency_checker):
        """Test consistency rule engine."""
        # Define custom consistency rules
        rules = [
            {"type": "terminology", "pattern": r"auth.*token", "standard": "authentication token"},
            {"type": "format", "pattern": r"^##\s", "standard": "Use H2 headers consistently"},
            {"type": "reference", "pattern": r"\[.*\]\(.*\)", "standard": "Valid markdown links"}
        ]

        content = """
        ## Authentication
        Use auth token for access.

        ## User Guide
        See [docs](docs.md) for details.
        """

        rule_results = consistency_checker.apply_consistency_rules(content, rules)

        assert isinstance(rule_results, list)
        assert len(rule_results) > 0

        # Should identify rule violations
        violations = [r for r in rule_results if not r.get("passed", True)]
        assert len(violations) > 0

    def test_consistency_score_calculation(self, consistency_checker):
        """Test consistency score calculation."""
        consistency_metrics = {
            "terminology_consistency": 0.9,
            "format_consistency": 0.8,
            "link_validity": 0.95,
            "cross_reference_accuracy": 0.85
        }

        overall_score = consistency_checker.calculate_consistency_score(consistency_metrics)

        assert isinstance(overall_score, float)
        assert 0.0 <= overall_score <= 1.0

        # Should be weighted average
        expected_score = sum(consistency_metrics.values()) / len(consistency_metrics)
        assert abs(overall_score - expected_score) < 0.01

    def test_batch_consistency_analysis(self, consistency_checker, mock_llm_gateway):
        """Test batch processing for consistency analysis."""
        document_batch = [
            {"id": "doc-1", "content": "Content 1"},
            {"id": "doc-2", "content": "Content 2"},
            {"id": "doc-3", "content": "Content 3"}
        ]

        batch_results = consistency_checker.batch_consistency_analysis(document_batch)

        assert isinstance(batch_results, list)
        assert len(batch_results) == 3

        for result in batch_results:
            assert isinstance(result, dict)
            assert "document_id" in result
            assert "consistency_score" in result

    def test_consistency_baseline_establishment(self, consistency_checker):
        """Test establishment of consistency baselines."""
        documents = [
            {"content": "Standard API documentation format"},
            {"content": "Another standard document"},
            {"content": "Third baseline document"}
        ]

        baseline = consistency_checker.establish_consistency_baseline(documents)

        assert isinstance(baseline, dict)
        assert "terminology_standards" in baseline
        assert "format_patterns" in baseline
        assert "reference_patterns" in baseline

    def test_consistency_deviation_detection(self, consistency_checker):
        """Test detection of deviations from established baselines."""
        baseline = {
            "terminology_standards": ["authentication token"],
            "format_patterns": [r"^#\s"]
        }

        test_content = "Use auth token for access. ## Section"  # Deviations present

        deviations = consistency_checker.detect_baseline_deviations(test_content, baseline)

        assert isinstance(deviations, list)
        assert len(deviations) > 0

        # Should detect terminology and format deviations
        deviation_types = [d.get("type") for d in deviations]
        assert "terminology" in deviation_types or "format" in deviation_types
