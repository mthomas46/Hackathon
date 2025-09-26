"""Tests for Multi-Model Summarization"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from services.summarizer_hub.modules.multi_model_summarization import MultiModelSummarization


class TestMultiModelSummarization:
    """Test cases for MultiModelSummarization."""

    @pytest.fixture
    def multi_model(self):
        """Create MultiModelSummarization instance."""
        return MultiModelSummarization()

    @pytest.fixture
    def mock_provider_manager(self):
        """Create mock provider manager."""
        manager = Mock()
        manager.get_provider = AsyncMock()
        manager.list_providers = AsyncMock(return_value=["ollama", "bedrock"])
        return manager

    def test_init(self, multi_model):
        """Test multi-model summarization initialization."""
        assert multi_model.consensus_threshold == 0.7
        assert multi_model.max_retries == 3
        assert multi_model.timeout == 30

    @pytest.mark.asyncio
    async def test_summarize_with_consensus_success(self, multi_model, mock_provider_manager):
        """Test successful consensus summarization."""
        # Mock providers
        mock_provider1 = Mock()
        mock_provider1.summarize = AsyncMock(return_value="Summary from provider 1")

        mock_provider2 = Mock()
        mock_provider2.summarize = AsyncMock(return_value="Summary from provider 2")

        mock_provider_manager.get_provider.side_effect = [mock_provider1, mock_provider2]

        # Mock consensus calculation
        with patch.object(multi_model, '_calculate_consensus', return_value="Consensus summary"):
            result = await multi_model.summarize_with_consensus(
                mock_provider_manager,
                "Test content",
                ["ollama", "bedrock"],
                {"max_length": 100}
            )

            assert result == "Consensus summary"
            assert mock_provider_manager.get_provider.call_count == 2

    @pytest.mark.asyncio
    async def test_summarize_with_consensus_provider_failure(self, multi_model, mock_provider_manager):
        """Test consensus summarization with provider failure."""
        # Mock provider that fails
        mock_provider = Mock()
        mock_provider.summarize = AsyncMock(side_effect=Exception("Provider failed"))

        mock_provider_manager.get_provider.return_value = mock_provider

        with patch.object(multi_model, '_calculate_consensus', return_value="Fallback summary"):
            result = await multi_model.summarize_with_consensus(
                mock_provider_manager,
                "Test content",
                ["ollama"],
                {}
            )

            assert result == "Fallback summary"

    def test_calculate_consensus_high_agreement(self, multi_model):
        """Test consensus calculation with high agreement."""
        summaries = [
            "The quick brown fox jumps over the lazy dog.",
            "A quick brown fox jumps over a lazy dog.",
            "The quick brown fox leaps over the lazy dog."
        ]

        result = multi_model._calculate_consensus(summaries)

        # Should return one of the summaries as they are similar
        assert isinstance(result, str)
        assert len(result) > 0

    def test_calculate_consensus_low_agreement(self, multi_model):
        """Test consensus calculation with low agreement."""
        summaries = [
            "The weather is sunny today.",
            "Politics is complicated.",
            "Cooking requires patience."
        ]

        result = multi_model._calculate_consensus(summaries)

        # Should return combined summary
        assert isinstance(result, str)
        assert len(result) > 0

    def test_calculate_consensus_empty_summaries(self, multi_model):
        """Test consensus calculation with empty summaries."""
        result = multi_model._calculate_consensus([])

        assert result == "No summaries available for consensus."

    def test_calculate_consensus_single_summary(self, multi_model):
        """Test consensus calculation with single summary."""
        summaries = ["Single summary content."]

        result = multi_model._calculate_consensus(summaries)

        assert result == "Single summary content."

    @pytest.mark.asyncio
    async def test_fallback_summarization_success(self, multi_model, mock_provider_manager):
        """Test successful fallback summarization."""
        mock_provider = Mock()
        mock_provider.summarize = AsyncMock(return_value="Fallback summary")

        mock_provider_manager.get_provider.return_value = mock_provider

        result = await multi_model._fallback_summarization(
            mock_provider_manager, "Test content", ["ollama"], {}
        )

        assert result == "Fallback summary"

    @pytest.mark.asyncio
    async def test_fallback_summarization_all_fail(self, multi_model, mock_provider_manager):
        """Test fallback summarization when all providers fail."""
        mock_provider = Mock()
        mock_provider.summarize = AsyncMock(side_effect=Exception("Provider failed"))

        mock_provider_manager.get_provider.return_value = mock_provider

        result = await multi_model._fallback_summarization(
            mock_provider_manager, "Test content", ["ollama"], {}
        )

        assert "consensus summarization failed" in result.lower()

    @pytest.mark.asyncio
    async def test_validate_summarization_request_valid(self, multi_model):
        """Test validation of valid summarization request."""
        request = {
            "content": "Test content to summarize",
            "providers": ["ollama", "bedrock"],
            "options": {"max_length": 100}
        }

        is_valid, error = await multi_model.validate_summarization_request(request)

        assert is_valid == True
        assert error is None

    @pytest.mark.asyncio
    async def test_validate_summarization_request_missing_content(self, multi_model):
        """Test validation with missing content."""
        request = {
            "providers": ["ollama"],
            "options": {}
        }

        is_valid, error = await multi_model.validate_summarization_request(request)

        assert is_valid == False
        assert "content" in error.lower()

    @pytest.mark.asyncio
    async def test_validate_summarization_request_empty_providers(self, multi_model):
        """Test validation with empty providers list."""
        request = {
            "content": "Test content",
            "providers": [],
            "options": {}
        }

        is_valid, error = await multi_model.validate_summarization_request(request)

        assert is_valid == False
        assert "providers" in error.lower()

    def test_get_similarity_score_identical(self, multi_model):
        """Test similarity score for identical texts."""
        score = multi_model._get_similarity_score("test text", "test text")

        assert score == 1.0

    def test_get_similarity_score_different(self, multi_model):
        """Test similarity score for different texts."""
        score = multi_model._get_similarity_score("hello world", "goodbye universe")

        assert score < 0.5  # Should be low similarity

    def test_get_similarity_score_empty(self, multi_model):
        """Test similarity score with empty texts."""
        score = multi_model._get_similarity_score("", "")

        assert score == 1.0  # Empty strings are identical

    def test_merge_summaries_high_similarity(self, multi_model):
        """Test merging summaries with high similarity."""
        summaries = [
            "The quick brown fox jumps over the lazy dog.",
            "A quick brown fox jumps over a lazy dog.",
        ]

        result = multi_model._merge_summaries(summaries)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_merge_summaries_low_similarity(self, multi_model):
        """Test merging summaries with low similarity."""
        summaries = [
            "Weather is sunny.",
            "Politics is complex.",
            "Cooking takes time."
        ]

        result = multi_model._merge_summaries(summaries)

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain key elements from different summaries
        assert "weather" in result.lower() or "politics" in result.lower() or "cooking" in result.lower()

    def test_configure_consensus_settings(self, multi_model):
        """Test configuring consensus settings."""
        multi_model.configure_consensus_settings(
            threshold=0.8,
            max_retries=5,
            timeout=60
        )

        assert multi_model.consensus_threshold == 0.8
        assert multi_model.max_retries == 5
        assert multi_model.timeout == 60

    def test_get_consensus_stats(self, multi_model):
        """Test getting consensus statistics."""
        # Set up some mock state
        multi_model.consensus_threshold = 0.8
        multi_model.max_retries = 5

        stats = multi_model.get_consensus_stats()

        assert stats["consensus_threshold"] == 0.8
        assert stats["max_retries"] == 5
        assert stats["timeout"] == 30  # Default value

    @pytest.mark.asyncio
    async def test_health_check_success(self, multi_model, mock_provider_manager):
        """Test successful health check."""
        mock_provider_manager.list_providers.return_value = ["ollama", "bedrock"]

        mock_provider = Mock()
        mock_provider.get_health_status = AsyncMock(return_value={"status": "healthy"})
        mock_provider_manager.get_provider.return_value = mock_provider

        result = await multi_model.health_check(mock_provider_manager)

        assert result["status"] == "healthy"
        assert "providers" in result

    @pytest.mark.asyncio
    async def test_health_check_failure(self, multi_model, mock_provider_manager):
        """Test health check with failures."""
        mock_provider_manager.list_providers.return_value = ["ollama"]

        mock_provider = Mock()
        mock_provider.get_health_status = AsyncMock(return_value={"status": "unhealthy"})
        mock_provider_manager.get_provider.return_value = mock_provider

        result = await multi_model.health_check(mock_provider_manager)

        assert result["status"] == "degraded"
        assert "providers" in result
