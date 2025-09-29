"""Unit tests for Summarization domain service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from domain.services.summarization_service import SummarizationService
from domain.entities.document import Document
from domain.entities.summary import Summary, SummaryType


class TestSummarizationService:
    """Test cases for SummarizationService domain service."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return SummarizationService()

    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document.create(
            content="This is a comprehensive test document with enough content to be properly summarized and analyzed for various aspects of the summarization process. It contains multiple sentences and provides sufficient context for testing summarization algorithms.",
            title="Test Document",
            source="test"
        )

    def test_service_initialization(self, service):
        """Test service initialization."""
        assert service.logger is not None
        assert hasattr(service, '_generate_summary_content')
        assert hasattr(service, '_calculate_summary_metrics')

    @pytest.mark.asyncio
    async def test_create_summary_success(self, service, sample_document):
        """Test successful summary creation."""
        summary = await service.create_summary(
            document=sample_document,
            summary_type=SummaryType.BRIEF,
            provider="test_provider"
        )

        assert isinstance(summary, Summary)
        assert summary.document_id == sample_document.id.value
        assert summary.summary_type == SummaryType.BRIEF
        assert summary.provider == "test_provider"
        assert summary.content is not None
        assert len(summary.content) > 0
        assert isinstance(summary.metrics, object)

    @pytest.mark.asyncio
    async def test_create_summary_with_parameters(self, service, sample_document):
        """Test summary creation with custom parameters."""
        parameters = {"temperature": 0.7, "max_tokens": 150}

        summary = await service.create_summary(
            document=sample_document,
            summary_type=SummaryType.COMPREHENSIVE,
            provider="test_provider",
            parameters=parameters
        )

        assert summary.parameters == parameters
        assert summary.summary_type == SummaryType.COMPREHENSIVE

    @pytest.mark.asyncio
    async def test_create_summary_document_too_short(self, service):
        """Test summary creation with document that's too short."""
        short_doc = Document.create(content="Short")

        with pytest.raises(ValueError, match="Document content too short"):
            await service.create_summary(
                document=short_doc,
                summary_type=SummaryType.BRIEF,
                provider="test"
            )

    @pytest.mark.asyncio
    async def test_validate_summary_quality_perfect_scores(self, service, sample_document):
        """Test quality validation with perfect scores."""
        summary = Summary.create(
            document_id=sample_document.id.value,
            content="Perfect summary.",
            summary_type=SummaryType.BRIEF,
            provider="test",
            source_length=len(sample_document.content)
        )

        # Mock perfect metrics
        summary.update_metrics(
            readability_score=1.0,
            coherence_score=1.0,
            factual_accuracy=1.0,
            key_points_coverage=1.0
        )

        result = await service.validate_summary_quality(summary, sample_document)

        assert result["is_valid"] is True
        assert result["quality_score"] == 1.0
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_validate_summary_quality_poor_scores(self, service, sample_document):
        """Test quality validation with poor scores."""
        summary = Summary.create(
            document_id=sample_document.id.value,
            content="Poor summary.",
            summary_type=SummaryType.BRIEF,
            provider="test",
            source_length=len(sample_document.content)
        )

        # Set poor metrics
        summary.update_metrics(
            readability_score=0.3,
            coherence_score=0.2,
            factual_accuracy=0.4,
            key_points_coverage=0.1
        )

        result = await service.validate_summary_quality(summary, sample_document)

        assert result["is_valid"] is False
        assert result["quality_score"] < 0.6
        assert len(result["issues"]) > 0
        assert len(result["recommendations"]) > 0

    @pytest.mark.asyncio
    async def test_optimize_summary_improvement_needed(self, service, sample_document):
        """Test summary optimization when improvement is needed."""
        summary = Summary.create(
            document_id=sample_document.id.value,
            content="Poor summary that needs optimization.",
            summary_type=SummaryType.BRIEF,
            provider="test",
            source_length=len(sample_document.content)
        )

        # Set poor quality scores
        summary.update_metrics(
            readability_score=0.3,
            coherence_score=0.2,
            factual_accuracy=0.4
        )

        optimized = await service.optimize_summary(summary, sample_document, target_quality=0.8)

        # Should return an optimized version
        assert isinstance(optimized, Summary)
        assert optimized.id != summary.id  # New summary created
        assert "[VERIFIED]" in optimized.content or "[KEY POINTS INCLUDED]" in optimized.content

    @pytest.mark.asyncio
    async def test_optimize_summary_already_good(self, service, sample_document):
        """Test summary optimization when already good quality."""
        summary = Summary.create(
            document_id=sample_document.id.value,
            content="Already good summary.",
            summary_type=SummaryType.BRIEF,
            provider="test",
            source_length=len(sample_document.content)
        )

        # Set good quality scores
        summary.update_metrics(
            readability_score=0.9,
            coherence_score=0.9,
            factual_accuracy=0.9
        )

        optimized = await service.optimize_summary(summary, sample_document, target_quality=0.8)

        # Should return the same summary since it's already good
        assert optimized is summary

    def test_generate_summary_content_brief(self, service):
        """Test brief summary content generation."""
        content = "This is a long document with many words that should be summarized briefly."
        result = service._generate_summary_content(
            content, SummaryType.BRIEF, "test", {}
        )

        assert isinstance(result, str)
        assert len(result) < len(content)  # Should be shorter

    def test_generate_summary_content_comprehensive(self, service):
        """Test comprehensive summary content generation."""
        content = "This is a long document with many words that should be summarized comprehensively."
        result = service._generate_summary_content(
            content, SummaryType.COMPREHENSIVE, "test", {}
        )

        assert isinstance(result, str)
        assert len(result) > 0

    def test_calculate_summary_metrics(self, service):
        """Test summary metrics calculation."""
        original = "This is the original document content with multiple sentences."
        summary = "This is the summary."

        metrics = service._calculate_summary_metrics(original, summary)

        assert hasattr(metrics, 'compression_ratio')
        assert hasattr(metrics, 'readability_score')
        assert metrics.compression_ratio > 0
        assert 0 <= metrics.readability_score <= 1

    def test_assess_readability(self, service):
        """Test readability assessment."""
        # Test with simple sentence
        simple_text = "This is a simple sentence."
        simple_score = service._assess_readability(simple_text)

        # Test with complex sentence
        complex_text = "This is a very long and complex sentence that contains many words and makes the readability assessment much more challenging to process correctly."
        complex_score = service._assess_readability(complex_text)

        assert 0 <= simple_score <= 1
        assert 0 <= complex_score <= 1

    def test_apply_optimization_strategies_factual_accuracy(self, service):
        """Test optimization strategies for factual accuracy."""
        content = "Poor summary with factual issues."
        original = "Original document content."
        issues = ["Low factual accuracy"]

        optimized = service._apply_optimization_strategies(content, original, issues)

        assert "[VERIFIED]" in optimized

    def test_apply_optimization_strategies_key_points(self, service):
        """Test optimization strategies for key points."""
        content = "Summary missing key points."
        original = "Original document content."
        issues = ["Insufficient key points coverage"]

        optimized = service._apply_optimization_strategies(content, original, issues)

        assert "[KEY POINTS INCLUDED]" in optimized

    def test_apply_optimization_strategies_readability(self, service):
        """Test optimization strategies for readability."""
        content = "Summary utilizing complex language."
        original = "Original document content."
        issues = ["Poor readability"]

        optimized = service._apply_optimization_strategies(content, original, issues)

        # Should replace complex words with simpler ones
        assert "utilizing" not in optimized or "using" in optimized
