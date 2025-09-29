"""Unit tests for Summary domain entity."""

import pytest
from datetime import datetime
from domain.entities.summary import Summary, SummaryId, SummaryType, SummaryMetrics


class TestSummaryId:
    """Test cases for SummaryId value object."""

    def test_generate_creates_unique_ids(self):
        """Test that generated IDs are unique."""
        id1 = SummaryId.generate()
        id2 = SummaryId.generate()

        assert id1 != id2
        assert isinstance(id1.value, str)

    def test_empty_id_raises_error(self):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Summary ID cannot be empty"):
            SummaryId("")


class TestSummaryMetrics:
    """Test cases for SummaryMetrics value object."""

    def test_default_initialization(self):
        """Test default metrics initialization."""
        metrics = SummaryMetrics()
        assert metrics.compression_ratio == 0.0
        assert metrics.readability_score == 0.0
        assert metrics.coherence_score == 0.0
        assert metrics.factual_accuracy == 0.0
        assert metrics.key_points_coverage == 0.0
        assert metrics.custom_metrics == {}

    def test_custom_initialization(self):
        """Test custom metrics initialization."""
        metrics = SummaryMetrics(
            compression_ratio=0.5,
            readability_score=0.8,
            coherence_score=0.9,
            custom_metrics={"novelty_score": 0.7}
        )
        assert metrics.compression_ratio == 0.5
        assert metrics.readability_score == 0.8
        assert metrics.coherence_score == 0.9
        assert metrics.custom_metrics == {"novelty_score": 0.7}


class TestSummaryType:
    """Test cases for SummaryType enum."""

    def test_valid_summary_types(self):
        """Test all valid summary types."""
        assert SummaryType.BRIEF.value == "brief"
        assert SummaryType.COMPREHENSIVE.value == "comprehensive"
        assert SummaryType.EXECUTIVE.value == "executive"
        assert SummaryType.TECHNICAL.value == "technical"


class TestSummary:
    """Test cases for Summary entity."""

    def test_create_summary_success(self):
        """Test successful summary creation."""
        summary = Summary.create(
            document_id="doc-123",
            content="This is a summary of the document.",
            summary_type=SummaryType.BRIEF,
            provider="openai",
            source_length=100
        )

        assert isinstance(summary.id, SummaryId)
        assert summary.document_id == "doc-123"
        assert summary.content == "This is a summary of the document."
        assert summary.summary_type == SummaryType.BRIEF
        assert summary.provider == "openai"
        assert summary.model_version is None
        assert isinstance(summary.created_at, datetime)
        assert summary.tags == []

    def test_create_summary_with_optional_fields(self):
        """Test summary creation with optional fields."""
        summary = Summary.create(
            document_id="doc-123",
            content="Test summary content.",
            summary_type=SummaryType.COMPREHENSIVE,
            provider="anthropic",
            model_version="claude-3",
            parameters={"temperature": 0.7},
            source_length=200
        )

        assert summary.model_version == "claude-3"
        assert summary.parameters == {"temperature": 0.7}

    def test_create_summary_empty_content(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Summary content cannot be empty"):
            Summary.create(
                document_id="doc-123",
                content="",
                summary_type=SummaryType.BRIEF,
                provider="test"
            )

    def test_create_summary_empty_document_id(self):
        """Test that empty document ID raises ValueError."""
        with pytest.raises(ValueError, match="Document ID is required"):
            Summary.create(
                document_id="",
                content="Test content.",
                summary_type=SummaryType.BRIEF,
                provider="test"
            )

    def test_update_content(self):
        """Test content update functionality."""
        summary = Summary.create(
            document_id="doc-123",
            content="Original summary.",
            summary_type=SummaryType.BRIEF,
            provider="test"
        )

        summary.update_content("Updated summary content.")
        assert summary.content == "Updated summary content."

    def test_update_metrics(self):
        """Test metrics update functionality."""
        summary = Summary.create(
            document_id="doc-123",
            content="Test summary.",
            summary_type=SummaryType.BRIEF,
            provider="test"
        )

        summary.update_metrics(readability_score=0.9, coherence_score=0.8)
        assert summary.metrics.readability_score == 0.9
        assert summary.metrics.coherence_score == 0.8

        # Test custom metrics
        summary.update_metrics(novelty_score=0.7)
        assert summary.metrics.custom_metrics["novelty_score"] == 0.7

    def test_add_and_remove_tags(self):
        """Test tag management functionality."""
        summary = Summary.create(
            document_id="doc-123",
            content="Test summary.",
            summary_type=SummaryType.BRIEF,
            provider="test"
        )

        summary.add_tag("important")
        summary.add_tag("reviewed")

        assert "important" in summary.tags
        assert "reviewed" in summary.tags

        summary.remove_tag("reviewed")
        assert "important" in summary.tags
        assert "reviewed" not in summary.tags

    def test_get_quality_score(self):
        """Test quality score calculation."""
        summary = Summary.create(
            document_id="doc-123",
            content="Test summary.",
            summary_type=SummaryType.BRIEF,
            provider="test"
        )

        # All metrics are 0, should return 0
        assert summary.get_quality_score() == 0.0

        # Set some metrics
        summary.update_metrics(
            readability_score=0.8,
            coherence_score=0.9,
            factual_accuracy=0.7,
            key_points_coverage=0.6
        )

        quality_score = summary.get_quality_score()
        expected = (0.8 + 0.9 + 0.7 + 0.6) / 4  # Average of all scores
        assert quality_score == pytest.approx(expected, rel=1e-2)

    def test_is_high_quality(self):
        """Test high quality detection."""
        summary = Summary.create(
            document_id="doc-123",
            content="Test summary.",
            summary_type=SummaryType.BRIEF,
            provider="test"
        )

        # Default should not be high quality
        assert not summary.is_high_quality()

        # Set high scores
        summary.update_metrics(
            readability_score=0.9,
            coherence_score=0.9,
            factual_accuracy=0.9,
            key_points_coverage=0.9
        )

        assert summary.is_high_quality()

    def test_compression_ratio_calculation(self):
        """Test compression ratio calculation during creation."""
        summary = Summary.create(
            document_id="doc-123",
            content="Short summary.",
            summary_type=SummaryType.BRIEF,
            provider="test",
            source_length=100
        )

        # Content is 2 words, source is 100 words
        # Compression ratio should be 2/100 = 0.02
        assert summary.metrics.compression_ratio == 0.02
