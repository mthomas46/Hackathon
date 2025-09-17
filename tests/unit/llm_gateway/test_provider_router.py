"""Unit tests for LLM Gateway Provider Router.

Tests the intelligent routing of LLM requests to appropriate providers based on
content analysis, availability, cost optimization, and performance requirements.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any

# Adjust path for local imports
import sys
from pathlib import Path

# Add the LLM Gateway service directory to Python path
llm_gateway_path = Path(__file__).parent.parent.parent.parent / "services" / "llm-gateway"
sys.path.insert(0, str(llm_gateway_path))

from modules.provider_router import ProviderRouter, ProviderResponse

# Test markers for parallel execution
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.provider
]


class TestProviderRouter:
    """Test suite for ProviderRouter class."""

    @pytest.fixture
    def provider_router(self):
        """Create a ProviderRouter instance for testing."""
        return ProviderRouter()

    @pytest.fixture
    def mock_request(self):
        """Create a mock LLM request."""
        return {
            "prompt": "Test prompt for LLM processing",
            "provider": "auto",
            "model": "gpt-4o",
            "context": {"test": "context"},
            "user_id": "test_user",
            "temperature": 0.7,
            "max_tokens": 1024
        }

    @pytest.mark.asyncio
    async def test_provider_router_initialization(self, provider_router):
        """Test that ProviderRouter initializes correctly."""
        assert isinstance(provider_router, ProviderRouter)
        assert hasattr(provider_router, 'providers')
        assert 'ollama' in provider_router.providers
        assert 'openai' in provider_router.providers
        assert 'bedrock' in provider_router.providers

    @pytest.mark.asyncio
    async def test_get_available_providers(self, provider_router):
        """Test retrieving available providers."""
        available = await provider_router._get_available_providers()

        # Should return a dictionary of available providers
        assert isinstance(available, dict)

        # Ollama should be available (local)
        assert 'ollama' in available

        # Check provider structure
        if available:
            provider_config = list(available.values())[0]
            assert 'name' in provider_config
            assert 'type' in provider_config
            assert 'endpoint' in provider_config

    @pytest.mark.asyncio
    @patch('services.llm_gateway.modules.provider_router.httpx.AsyncClient')
    async def test_execute_ollama_success(self, mock_client_class, provider_router, mock_request):
        """Test successful Ollama execution."""
        # Mock the HTTP client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {"response": "Test Ollama response"}
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock provider config
        provider_config = {
            "name": "ollama",
            "endpoint": "http://localhost:11434",
            "model": "llama3",
            "timeout": 60
        }

        # Execute Ollama request
        result = await provider_router._execute_ollama(mock_request, provider_config)

        # Verify result
        assert isinstance(result, ProviderResponse)
        assert result.response == "Test Ollama response"
        assert result.provider == "ollama"
        assert result.success is True

        # Verify HTTP call was made correctly
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:11434/api/generate"

    @pytest.mark.asyncio
    @patch('services.llm_gateway.modules.provider_router.httpx.AsyncClient')
    async def test_execute_openai_success(self, mock_client_class, provider_router, mock_request):
        """Test successful OpenAI execution."""
        # Mock the HTTP client
        mock_client = AsyncMock()
        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test OpenAI response"}}],
            "usage": {"total_tokens": 150}
        }
        mock_response.raise_for_status.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock provider config
        provider_config = {
            "name": "openai",
            "endpoint": "https://api.openai.com/v1/chat/completions",
            "model": "gpt-4o",
            "timeout": 30,
            "api_key": "test-key",
            "cost_per_token": 0.00003
        }

        # Execute OpenAI request
        result = await provider_router._execute_openai(mock_request, provider_config)

        # Verify result
        assert isinstance(result, ProviderResponse)
        assert result.response == "Test OpenAI response"
        assert result.provider == "openai"
        assert result.tokens_used == 150
        assert result.success is True

    @pytest.mark.asyncio
    async def test_select_provider_auto_mode(self, provider_router, mock_request):
        """Test provider selection in auto mode."""
        # Test with sensitive content
        sensitive_request = mock_request.copy()
        sensitive_request["prompt"] = "This contains password and secret API key"

        provider = await provider_router._select_provider(sensitive_request)
        assert provider is not None

        # Should prefer secure providers for sensitive content
        if provider:
            assert provider.get('security_level') in ['high', 'medium']

    @pytest.mark.asyncio
    async def test_select_provider_specific_provider(self, provider_router, mock_request):
        """Test provider selection with specific provider requested."""
        # Test with specific provider request
        specific_request = mock_request.copy()
        specific_request["provider"] = "ollama"

        provider = await provider_router._select_provider(specific_request)

        if provider:  # Only if Ollama is available
            assert provider['name'] == 'ollama'

    @pytest.mark.asyncio
    async def test_provider_health_check_ollama(self, provider_router):
        """Test Ollama provider health check."""
        health_status = await provider_router._check_provider_availability(
            provider_router.providers['ollama']
        )

        # Health check should return boolean
        assert isinstance(health_status, bool)

    @pytest.mark.asyncio
    async def test_get_provider_health_status(self, provider_router):
        """Test getting comprehensive provider health status."""
        health_status = await provider_router.check_provider_health()

        assert isinstance(health_status, dict)

        # Should have status for each provider
        for provider_name in provider_router.providers.keys():
            assert provider_name in health_status
            provider_status = health_status[provider_name]
            assert 'available' in provider_status
            assert 'status' in provider_status
            assert 'last_checked' in provider_status

    @pytest.mark.asyncio
    async def test_generate_embeddings_fallback(self, provider_router):
        """Test embeddings generation fallback."""
        embeddings = await provider_router.generate_embeddings(
            "Test text for embeddings",
            "text-embedding-ada-002",
            "openai"
        )

        # Should return a list of floats
        assert isinstance(embeddings, list)
        assert len(embeddings) > 0
        assert all(isinstance(x, float) for x in embeddings)

    @pytest.mark.asyncio
    async def test_stream_response_placeholder(self, provider_router):
        """Test streaming response placeholder."""
        # This tests the placeholder implementation
        chunks = []
        async for chunk in provider_router.stream_response(mock_request):
            chunks.append(chunk)

        # Should have at least one chunk indicating streaming not implemented
        assert len(chunks) > 0
        assert "not yet implemented" in chunks[0]["chunk"].lower()

    @pytest.mark.asyncio
    async def test_route_and_execute_with_unavailable_provider(self, provider_router):
        """Test routing when preferred provider is unavailable."""
        # Request a provider that might not be available
        request = {
            "prompt": "Test prompt",
            "provider": "nonexistent_provider",
            "model": "test-model"
        }

        result = await provider_router.route_and_execute(request)

        # Should still attempt to route to an available provider
        assert isinstance(result, ProviderResponse)

    @pytest.mark.asyncio
    async def test_provider_response_structure(self, provider_router):
        """Test ProviderResponse structure and attributes."""
        response = ProviderResponse(
            response="Test response",
            provider="test_provider",
            tokens_used=100,
            cost=0.03,
            success=True
        )

        assert response.response == "Test response"
        assert response.provider == "test_provider"
        assert response.tokens_used == 100
        assert response.cost == 0.03
        assert response.success is True
        assert response.error == ""

    @pytest.mark.asyncio
    async def test_provider_response_error_handling(self, provider_router):
        """Test ProviderResponse error handling."""
        error_response = ProviderResponse(
            response="",
            provider="failed_provider",
            success=False,
            error="Connection timeout"
        )

        assert error_response.response == ""
        assert error_response.success is False
        assert error_response.error == "Connection timeout"
        assert error_response.tokens_used == 0
        assert error_response.cost == 0.0
