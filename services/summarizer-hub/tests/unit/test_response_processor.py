"""Tests for Response Processor"""

import pytest
from unittest.mock import Mock, AsyncMock

from services.summarizer-hub.modules.response_processor import ResponseProcessor


class TestResponseProcessor:
    """Test cases for ResponseProcessor."""

    @pytest.fixture
    def processor(self):
        """Create ResponseProcessor instance."""
        return ResponseProcessor()

    def test_init(self, processor):
        """Test response processor initialization."""
        assert processor.quality_threshold == 0.7
        assert processor.min_length == 10
        assert processor.max_length == 1000

    def test_process_response_success(self, processor):
        """Test successful response processing."""
        raw_response = {
            "summary": "This is a test summary.",
            "confidence": 0.85,
            "metadata": {"provider": "ollama"}
        }

        result = processor.process_response(raw_response)

        assert result["processed_summary"] == "This is a test summary."
        assert result["quality_score"] >= processor.quality_threshold
        assert result["word_count"] > 0
        assert "processing_timestamp" in result

    def test_process_response_low_quality(self, processor):
        """Test processing low-quality response."""
        raw_response = {
            "summary": "Bad",  # Too short
            "confidence": 0.3,  # Low confidence
            "metadata": {}
        }

        result = processor.process_response(raw_response)

        assert result["quality_score"] < processor.quality_threshold
        assert "needs_review" in result
        assert result["needs_review"] == True

    def test_process_response_missing_summary(self, processor):
        """Test processing response with missing summary."""
        raw_response = {
            "confidence": 0.8,
            "metadata": {}
        }

        result = processor.process_response(raw_response)

        assert result["quality_score"] == 0.0
        assert result["needs_review"] == True
        assert "error" in result

    def test_calculate_quality_score_high_quality(self, processor):
        """Test quality score calculation for high-quality response."""
        response = {
            "summary": "This is a comprehensive summary with good length and structure.",
            "confidence": 0.9,
            "metadata": {"provider": "ollama"}
        }

        score = processor._calculate_quality_score(response)

        assert score >= processor.quality_threshold

    def test_calculate_quality_score_low_quality(self, processor):
        """Test quality score calculation for low-quality response."""
        response = {
            "summary": "Bad",
            "confidence": 0.2,
            "metadata": {}
        }

        score = processor._calculate_quality_score(response)

        assert score < processor.quality_threshold

    def test_validate_response_structure_valid(self, processor):
        """Test validation of valid response structure."""
        response = {
            "summary": "Valid summary",
            "confidence": 0.8,
            "metadata": {"provider": "ollama"}
        }

        is_valid, errors = processor._validate_response_structure(response)

        assert is_valid == True
        assert errors == []

    def test_validate_response_structure_invalid(self, processor):
        """Test validation of invalid response structure."""
        response = {
            "confidence": 0.8
            # Missing summary
        }

        is_valid, errors = processor._validate_response_structure(response)

        assert is_valid == False
        assert len(errors) > 0
        assert "summary" in str(errors[0])

    def test_validate_response_structure_wrong_types(self, processor):
        """Test validation with wrong data types."""
        response = {
            "summary": 123,  # Should be string
            "confidence": "high",  # Should be number
            "metadata": "not a dict"  # Should be dict
        }

        is_valid, errors = processor._validate_response_structure(response)

        assert is_valid == False
        assert len(errors) >= 2  # At least summary and confidence type errors

    def test_analyze_summary_length_optimal(self, processor):
        """Test summary length analysis for optimal length."""
        summary = "This is a summary of optimal length that should score well."

        score = processor._analyze_summary_length(summary)

        assert score > 0.8  # Should be high score

    def test_analyze_summary_length_too_short(self, processor):
        """Test summary length analysis for too short summary."""
        summary = "Short"

        score = processor._analyze_summary_length(summary)

        assert score < 0.5  # Should be low score

    def test_analyze_summary_length_too_long(self, processor):
        """Test summary length analysis for too long summary."""
        # Create a very long summary
        summary = "This is a very long summary. " * 100  # Repeat to make it long

        score = processor._analyze_summary_length(summary)

        assert score < 0.7  # Should be penalized for length

    def test_extract_key_phrases(self, processor):
        """Test key phrase extraction."""
        summary = "The quick brown fox jumps over the lazy dog. This is important information."

        phrases = processor._extract_key_phrases(summary)

        assert isinstance(phrases, list)
        assert len(phrases) > 0
        # Should extract meaningful phrases
        assert any("fox" in phrase.lower() for phrase in phrases)

    def test_extract_key_phrases_empty(self, processor):
        """Test key phrase extraction with empty summary."""
        phrases = processor._extract_key_phrases("")

        assert phrases == []

    def test_enhance_response_with_metadata(self, processor):
        """Test response enhancement with metadata."""
        response = {
            "summary": "Test summary",
            "confidence": 0.8
        }

        enhanced = processor._enhance_response_with_metadata(response)

        assert enhanced["processing_timestamp"] is not None
        assert enhanced["quality_score"] >= 0.0
        assert enhanced["word_count"] > 0

    def test_get_processing_stats(self, processor):
        """Test getting processing statistics."""
        # Process a few responses to generate stats
        processor.process_response({"summary": "Test 1", "confidence": 0.8})
        processor.process_response({"summary": "Test 2", "confidence": 0.6})

        stats = processor.get_processing_stats()

        assert "total_processed" in stats
        assert "average_quality" in stats
        assert "quality_distribution" in stats
        assert stats["total_processed"] == 2

    def test_get_processing_stats_empty(self, processor):
        """Test getting processing statistics with no processed responses."""
        stats = processor.get_processing_stats()

        assert stats["total_processed"] == 0
        assert stats["average_quality"] == 0.0
        assert stats["quality_distribution"]["high"] == 0

    def test_configure_processing_settings(self, processor):
        """Test configuring processing settings."""
        processor.configure_processing_settings(
            quality_threshold=0.8,
            min_length=20,
            max_length=2000
        )

        assert processor.quality_threshold == 0.8
        assert processor.min_length == 20
        assert processor.max_length == 2000

    def test_reset_processing_stats(self, processor):
        """Test resetting processing statistics."""
        # Add some data
        processor.process_response({"summary": "Test", "confidence": 0.8})

        # Reset
        processor.reset_processing_stats()

        stats = processor.get_processing_stats()
        assert stats["total_processed"] == 0

    def test_is_response_cacheable_high_quality(self, processor):
        """Test cacheability check for high-quality response."""
        response = {
            "summary": "Good summary",
            "confidence": 0.9,
            "quality_score": 0.85
        }

        assert processor._is_response_cacheable(response) == True

    def test_is_response_cacheable_low_quality(self, processor):
        """Test cacheability check for low-quality response."""
        response = {
            "summary": "Bad",
            "confidence": 0.3,
            "quality_score": 0.4
        }

        assert processor._is_response_cacheable(response) == False

    @pytest.mark.asyncio
    async def test_batch_process_responses(self, processor):
        """Test batch processing of responses."""
        responses = [
            {"summary": "Summary 1", "confidence": 0.8},
            {"summary": "Summary 2", "confidence": 0.7},
            {"summary": "Summary 3", "confidence": 0.6}
        ]

        results = await processor.batch_process_responses(responses)

        assert len(results) == 3
        assert all("processed_summary" in result for result in results)
        assert all("quality_score" in result for result in results)

    @pytest.mark.asyncio
    async def test_batch_process_responses_empty(self, processor):
        """Test batch processing with empty response list."""
        results = await processor.batch_process_responses([])

        assert results == []

    def test_format_response_for_output(self, processor):
        """Test response formatting for output."""
        processed_response = {
            "processed_summary": "Test summary",
            "quality_score": 0.85,
            "word_count": 15,
            "processing_timestamp": "2024-01-01T10:00:00Z"
        }

        formatted = processor.format_response_for_output(processed_response, "json")

        assert "summary" in formatted
        assert "metadata" in formatted
        assert formatted["metadata"]["quality_score"] == 0.85

    def test_format_response_for_output_text(self, processor):
        """Test response formatting for text output."""
        processed_response = {
            "processed_summary": "Test summary",
            "quality_score": 0.85,
            "word_count": 15,
            "processing_timestamp": "2024-01-01T10:00:00Z"
        }

        formatted = processor.format_response_for_output(processed_response, "text")

        assert isinstance(formatted, str)
        assert "Test summary" in formatted
        assert "Quality Score: 0.85" in formatted
