#!/usr/bin/env python3
"""
Domain Layer Tests for Reporting

Tests the core domain logic for reporting including report generation, summarization, and analysis.
"""

import pytest
from datetime import datetime

from services.orchestrator.domain.reporting.value_objects import (
    ReportFormat, ReportType, ConfidenceLevel, ApprovalRecommendation,
    SummarizationRequest, PRConfidenceReport
)
from services.orchestrator.domain.reporting.services import (
    ReportGeneratorService, SummarizationService
)


class TestReportFormat:
    """Test ReportFormat enum."""

    def test_report_format_values(self):
        """Test report format enum values."""
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.PDF.value == "pdf"
        assert ReportFormat.TEXT.value == "text"
        assert ReportFormat.XML.value == "xml"

    def test_content_type_property(self):
        """Test content type property."""
        assert ReportFormat.JSON.content_type == "application/json"
        assert ReportFormat.HTML.content_type == "text/html"
        assert ReportFormat.PDF.content_type == "application/pdf"

    def test_file_extension_property(self):
        """Test file extension property."""
        assert ReportFormat.JSON.file_extension == ".json"
        assert ReportFormat.HTML.file_extension == ".html"
        assert ReportFormat.PDF.file_extension == ".pdf"


class TestReportType:
    """Test ReportType enum."""

    def test_report_type_values(self):
        """Test report type enum values."""
        assert ReportType.SUMMARY.value == "summary"
        assert ReportType.DETAILED.value == "detailed"
        assert ReportType.PR_CONFIDENCE.value == "pr_confidence"

    def test_description_property(self):
        """Test description property."""
        assert "summary" in ReportType.SUMMARY.description.lower()
        assert "confidence" in ReportType.PR_CONFIDENCE.description.lower()

    def test_requires_ai_property(self):
        """Test requires_ai property."""
        assert ReportType.PR_CONFIDENCE.requires_ai is True
        assert ReportType.SUMMARY.requires_ai is False


class TestConfidenceLevel:
    """Test ConfidenceLevel enum."""

    def test_confidence_level_values(self):
        """Test confidence level enum values."""
        assert ConfidenceLevel.CRITICAL.value == "critical"
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.EXCELLENT.value == "excellent"

    def test_numeric_range_property(self):
        """Test numeric range property."""
        critical_range = ConfidenceLevel.CRITICAL.numeric_range
        assert critical_range == (0.0, 0.25)

        excellent_range = ConfidenceLevel.EXCELLENT.numeric_range
        assert excellent_range == (0.90, 1.0)

    def test_from_score_method(self):
        """Test from_score class method."""
        assert ConfidenceLevel.from_score(0.1) == ConfidenceLevel.CRITICAL
        assert ConfidenceLevel.from_score(0.5) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0.95) == ConfidenceLevel.EXCELLENT

    def test_invalid_score(self):
        """Test invalid score handling."""
        with pytest.raises(ValueError):
            ConfidenceLevel.from_score(1.5)

        with pytest.raises(ValueError):
            ConfidenceLevel.from_score(-0.1)


class TestApprovalRecommendation:
    """Test ApprovalRecommendation enum."""

    def test_approval_recommendation_values(self):
        """Test approval recommendation enum values."""
        assert ApprovalRecommendation.APPROVE.value == "approve"
        assert ApprovalRecommendation.REJECT.value == "reject"
        assert ApprovalRecommendation.ESCALATE.value == "escalate"

    def test_priority_property(self):
        """Test priority property."""
        assert ApprovalRecommendation.REJECT.priority == 5
        assert ApprovalRecommendation.APPROVE.priority == 1

    def test_requires_action_property(self):
        """Test requires_action property."""
        assert ApprovalRecommendation.REJECT.requires_action is True
        assert ApprovalRecommendation.APPROVE.requires_action is False


class TestSummarizationRequest:
    """Test SummarizationRequest value object."""

    def test_create_summarization_request(self):
        """Test creating a summarization request."""
        request = SummarizationRequest(
            content="This is a test content for summarization.",
            keywords=["test", "content"],
            max_length=100,
            style="formal"
        )

        assert request.content == "This is a test content for summarization."
        assert request.keywords == ["test", "content"]
        assert request.max_length == 100
        assert request.style == "formal"
        assert request.content_length == 41  # "This is a test content for summarization."

    def test_validation(self):
        """Test request validation."""
        # Valid request
        request = SummarizationRequest(content="This is valid content.")
        assert request.content_length >= 10

        # Invalid: empty content
        with pytest.raises(ValueError, match="Content cannot be empty"):
            SummarizationRequest(content="")

        # Invalid: content too short
        with pytest.raises(ValueError, match="at least 10 characters"):
            SummarizationRequest(content="short")

        # Invalid: invalid style
        with pytest.raises(ValueError, match="Style must be one of"):
            SummarizationRequest(content="This is valid content.", style="invalid")

    def test_to_dict(self):
        """Test converting to dictionary."""
        request = SummarizationRequest(
            content="Test content",
            keywords=["test"],
            style="technical"
        )

        data = request.to_dict()
        assert data["content"] == "Test content"
        assert data["keywords"] == ["test"]
        assert data["style"] == "technical"
        assert data["has_keywords"] is True


class TestPRConfidenceReport:
    """Test PRConfidenceReport value object."""

    @pytest.fixture
    def sample_report_data(self):
        """Sample report data for testing."""
        return {
            'workflow_id': 'wf-123',
            'pr_id': 'pr-456',
            'confidence_score': 0.85,
            'confidence_level': ConfidenceLevel.HIGH,
            'approval_recommendation': ApprovalRecommendation.APPROVE_WITH_CONDITIONS,
            'component_scores': {'code_quality': 0.9, 'tests': 0.8},
            'cross_reference_results': {'consistency': 0.75},
            'detected_gaps': [{'gap_type': 'test_coverage', 'severity': 'medium'}],
            'risk_assessment': 'low',
            'recommendations': ['Add more tests'],
            'critical_concerns': [],
            'strengths': ['Good code quality'],
            'improvement_areas': ['Test coverage'],
            'analysis_duration': 2.5,
            'jira_ticket': 'JIRA-123'
        }

    def test_create_pr_confidence_report(self, sample_report_data):
        """Test creating a PR confidence report."""
        report = PRConfidenceReport(**sample_report_data)

        assert report.workflow_id == 'wf-123'
        assert report.pr_id == 'pr-456'
        assert report.confidence_score == 0.85
        assert report.confidence_percentage == 85.0
        assert report.confidence_level == ConfidenceLevel.HIGH
        assert report.approval_recommendation == ApprovalRecommendation.APPROVE_WITH_CONDITIONS
        assert report.gap_count == 1
        assert report.has_critical_concerns is False

    def test_validation(self, sample_report_data):
        """Test report validation."""
        # Valid report
        report = PRConfidenceReport(**sample_report_data)
        assert report.workflow_id == 'wf-123'

        # Invalid: empty workflow_id
        invalid_data = sample_report_data.copy()
        invalid_data['workflow_id'] = ''
        with pytest.raises(ValueError, match="Workflow ID cannot be empty"):
            PRConfidenceReport(**invalid_data)

    def test_readiness_assessment(self, sample_report_data):
        """Test approval readiness assessment."""
        # Report ready for approval
        ready_data = sample_report_data.copy()
        ready_data['approval_recommendation'] = ApprovalRecommendation.APPROVE
        ready_data['detected_gaps'] = []
        ready_data['critical_concerns'] = []
        ready_report = PRConfidenceReport(**ready_data)

        assert ready_report.is_ready_for_approval is True

        # Report not ready
        not_ready_data = sample_report_data.copy()
        not_ready_data['critical_concerns'] = ['Security issue']
        not_ready_report = PRConfidenceReport(**not_ready_data)

        assert not_ready_report.is_ready_for_approval is False

    def test_to_dict(self, sample_report_data):
        """Test converting to dictionary."""
        report = PRConfidenceReport(**sample_report_data)

        data = report.to_dict()
        assert data['report_id'] is not None
        assert data['workflow_id'] == 'wf-123'
        assert data['pr_id'] == 'pr-456'
        assert data['confidence_score'] == 0.85
        assert data['confidence_percentage'] == 85.0
        assert data['gap_count'] == 1
        assert data['is_ready_for_approval'] is False


class TestReportGeneratorService:
    """Test ReportGeneratorService domain service."""

    @pytest.fixture
    def report_service(self):
        """Create report generator service for testing."""
        return ReportGeneratorService()

    def test_generate_pr_confidence_report(self, report_service):
        """Test generating a PR confidence report."""
        report = report_service.generate_pr_confidence_report(
            workflow_id='wf-123',
            pr_id='pr-456',
            confidence_score=0.75,
            component_scores={'code': 0.8, 'tests': 0.7},
            cross_reference_results={'consistency': 0.6},
            detected_gaps=[{'gap_type': 'coverage', 'severity': 'medium'}],
            recommendations=['Improve test coverage'],
            critical_concerns=[],
            strengths=['Good structure'],
            improvement_areas=['Documentation'],
            analysis_duration=3.2
        )

        assert isinstance(report, PRConfidenceReport)
        assert report.confidence_score == 0.75
        assert report.confidence_level == ConfidenceLevel.HIGH  # 0.75 falls in HIGH range (0.75-0.90)
        assert report.approval_recommendation == ApprovalRecommendation.APPROVE_WITH_CONDITIONS  # HIGH confidence level

    def test_risk_assessment_logic(self, report_service):
        """Test risk assessment logic."""
        # Test various risk scenarios
        test_cases = [
            # High risk: blocking gaps
            {
                'cross_ref': {'documentation_consistency_overall': 0.8},
                'gaps': [{'blocking_approval': True}],
                'expected': 'high'
            },
            # Medium risk: many gaps
            {
                'cross_ref': {'documentation_consistency_overall': 0.8},
                'gaps': [{'blocking_approval': False}] * 6,
                'expected': 'medium'
            },
            # Low risk: minimal issues
            {
                'cross_ref': {'documentation_consistency_overall': 0.8},
                'gaps': [{'blocking_approval': False}],
                'expected': 'low'
            }
        ]

        for case in test_cases:
            risk = report_service._assess_risk(case['cross_ref'], case['gaps'])
            assert risk == case['expected']

    def test_generate_html_report(self, report_service):
        """Test HTML report generation."""
        report = report_service.generate_pr_confidence_report(
            workflow_id='wf-123',
            pr_id='pr-456',
            confidence_score=0.9,
            component_scores={'quality': 0.95},
            cross_reference_results={},
            detected_gaps=[],
            recommendations=['Looks good'],
            critical_concerns=[],
            strengths=['Excellent code'],
            improvement_areas=[],
            analysis_duration=1.5
        )

        html = report_service.generate_html_report(report)

        assert '<!DOCTYPE html>' in html
        assert 'PR Confidence Analysis' in html
        assert 'pr-456' in html
        assert '90.0%' in html

    def test_generate_json_report(self, report_service):
        """Test JSON report generation."""
        report = report_service.generate_pr_confidence_report(
            workflow_id='wf-123',
            pr_id='pr-456',
            confidence_score=0.8,
            component_scores={'quality': 0.85},
            cross_reference_results={},
            detected_gaps=[],
            recommendations=["Consider additional testing"],
            critical_concerns=[],
            strengths=[],
            improvement_areas=[],
            analysis_duration=2.0
        )

        json_str = report_service.generate_json_report(report)

        # Parse JSON to verify structure
        import json
        data = json.loads(json_str)

        assert data['workflow_id'] == 'wf-123'
        assert data['pr_id'] == 'pr-456'
        assert data['confidence_score'] == 0.8
        assert 'report_id' in data

    def test_validate_report_data(self, report_service):
        """Test report data validation."""
        # Valid data
        valid_data = {
            'workflow_id': 'wf-123',
            'pr_id': 'pr-456',
            'confidence_score': 0.8
        }
        errors = report_service.validate_report_data(valid_data)
        assert len(errors) == 0

        # Invalid data
        invalid_data = {
            'pr_id': 'pr-456',
            'confidence_score': 1.5  # Invalid score
        }
        errors = report_service.validate_report_data(invalid_data)
        assert len(errors) == 2  # Missing workflow_id and invalid score


class TestSummarizationService:
    """Test SummarizationService domain service."""

    @pytest.fixture
    def summarization_service(self):
        """Create summarization service for testing."""
        return SummarizationService()

    def test_suggest_summarization_providers(self, summarization_service):
        """Test provider suggestion logic."""
        request = SummarizationRequest(
            content="This is a technical document about software architecture and API design.",
            keywords=["architecture", "API"],
            style="technical"
        )

        suggestions = summarization_service.suggest_summarization_providers(request)

        assert 'content_analysis' in suggestions
        assert 'allowed_providers' in suggestions
        assert 'recommended_provider' in suggestions

        # Should analyze content
        analysis = suggestions['content_analysis']
        assert 'word_count' in analysis
        assert 'content_type' in analysis
        assert analysis['content_type'] == 'technical'  # Should detect technical content

    def test_content_analysis(self, summarization_service):
        """Test content analysis functionality."""
        request = SummarizationRequest(
            content="This is a business strategy document discussing revenue growth and market expansion.",
            keywords=["revenue", "market"]
        )

        analysis = summarization_service._analyze_content(request)

        assert analysis['word_count'] == 12
        assert analysis['content_type'] == 'business'
        assert 'complexity_score' in analysis
        assert 'estimated_summary_tokens' in analysis

    def test_provider_policy_compliance(self, summarization_service):
        """Test provider policy compliance logic."""
        # Technical content
        tech_request = SummarizationRequest(
            content="Function to calculate fibonacci numbers using recursion.",
            style="technical"
        )

        tech_analysis = summarization_service._analyze_content(tech_request)
        tech_providers = summarization_service._get_policy_compliant_providers(tech_request, tech_analysis)

        # Should prefer local models for technical/code content
        assert 'local_llm' in tech_providers

        # Business content
        business_request = SummarizationRequest(
            content="Our company strategy focuses on customer satisfaction and revenue growth.",
            style="executive"
        )

        business_analysis = summarization_service._analyze_content(business_request)
        business_providers = summarization_service._get_policy_compliant_providers(business_request, business_analysis)

        # Should allow multiple providers for business content
        assert len(business_providers) > 1

    def test_generate_summarization_prompt(self, summarization_service):
        """Test prompt generation."""
        request = SummarizationRequest(
            content="Sample content for testing.",
            keywords=["test", "sample"],
            max_length=50,
            style="formal"
        )

        prompt = summarization_service.generate_summarization_prompt(request, "openai_gpt4")

        assert "formal summary" in prompt
        assert "under 50 words" in prompt
        assert "test, sample" in prompt
        assert "Sample content for testing" in prompt

    def test_validate_summarization_request(self, summarization_service):
        """Test request validation."""
        # Valid request
        valid_request = SummarizationRequest(content="This is a valid content for summarization.")
        errors = summarization_service.validate_summarization_request(valid_request)
        assert len(errors) == 0

        # Invalid: empty content - this will raise ValueError during construction
        with pytest.raises(ValueError, match="Content cannot be empty"):
            SummarizationRequest(content="")

        # Invalid: max length <= min length - this will raise ValueError during construction
        with pytest.raises(ValueError, match="Min length must be less than max length"):
            SummarizationRequest(
                content="Valid content",
                max_length=50,
                min_length=100
            )
