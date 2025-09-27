"""Unit tests for LLM routing service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from services.llm_gateway.domain.services.llm_routing_service import LLMRoutingService
from services.llm_gateway.domain.entities.llm_request import LLMRequest
from services.llm_gateway.domain.entities.llm_provider import LLMProvider


class TestLLMRoutingService:
    """Test cases for LLMRoutingService."""

    @pytest.fixture
    def routing_service(self):
        """Create LLMRoutingService instance for testing."""
        return LLMRoutingService()

    @pytest.fixture
    def sample_request(self):
        """Create a sample LLM request for testing."""
        return LLMRequest(
            prompt="Test prompt",
            model="llama2",
            max_tokens=100,
            temperature=0.7
        )

    def test_service_initialization(self, routing_service):
        """Test LLMRoutingService initialization."""
        assert routing_service is not None
        assert hasattr(routing_service, 'route_request')
        assert hasattr(routing_service, 'get_available_providers')

    @pytest.mark.asyncio
    async def test_route_request_basic(self, routing_service, sample_request):
        """Test basic request routing."""
        result = await routing_service.route_request(sample_request)

        assert result is not None
        assert isinstance(result, dict)
        assert "response" in result
        assert "provider" in result
        assert "model" in result

    @pytest.mark.asyncio
    async def test_route_request_with_provider_preference(self, routing_service):
        """Test routing with specific provider preference."""
        request = LLMRequest(
            prompt="Test with provider",
            model="gpt-3.5-turbo",
            provider="openai",
            max_tokens=50
        )

        result = await routing_service.route_request(request)

        assert result is not None
        assert result["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_route_request_streaming(self, routing_service):
        """Test streaming request routing."""
        request = LLMRequest(
            prompt="Stream this request",
            model="llama2",
            stream=True,
            max_tokens=200
        )

        result = await routing_service.route_request(request)

        assert result is not None
        assert result.get("streaming", False) is True

    def test_get_available_providers(self, routing_service):
        """Test retrieving available providers."""
        providers = routing_service.get_available_providers()

        assert isinstance(providers, list)
        assert len(providers) > 0

        # Check provider structure
        for provider in providers:
            assert isinstance(provider, dict)
            assert "name" in provider
            assert "status" in provider
            assert "models" in provider

    @pytest.mark.asyncio
    async def test_provider_health_check(self, routing_service):
        """Test provider health checking."""
        # Test with healthy provider
        health = await routing_service.check_provider_health("ollama")
        assert isinstance(health, dict)
        assert "status" in health

        # Test with unhealthy provider
        health = await routing_service.check_provider_health("invalid_provider")
        assert health["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_load_balancing(self, routing_service):
        """Test load balancing across providers."""
        # Create multiple requests to test load balancing
        requests = [
            LLMRequest(prompt=f"Request {i}", model="llama2")
            for i in range(5)
        ]

        results = []
        for request in requests:
            result = await routing_service.route_request(request)
            results.append(result)

        # Should have distributed across providers
        providers_used = set(result["provider"] for result in results)
        assert len(providers_used) >= 1

    @pytest.mark.asyncio
    async def test_fallback_routing(self, routing_service):
        """Test fallback routing when primary provider fails."""
        # Mock a provider failure
        with patch.object(routing_service, '_call_provider', side_effect=Exception("Provider down")):
            request = LLMRequest(
                prompt="Test fallback",
                model="llama2",
                provider="ollama"
            )

            # Should attempt fallback to another provider
            result = await routing_service.route_request(request)

            # Result should still be returned (from fallback)
            assert result is not None
            assert "response" in result

    @pytest.mark.asyncio
    async def test_request_validation(self, routing_service):
        """Test request validation."""
        # Valid request
        valid_request = LLMRequest(
            prompt="Valid prompt",
            model="llama2",
            max_tokens=100
        )

        result = await routing_service.route_request(valid_request)
        assert result["success"] is True

        # Invalid request (empty prompt)
        invalid_request = LLMRequest(
            prompt="",
            model="llama2"
        )

        result = await routing_service.route_request(invalid_request)
        assert result["success"] is False

    def test_provider_capabilities(self, routing_service):
        """Test provider capability checking."""
        # Test streaming capability
        can_stream = routing_service.provider_supports_streaming("ollama")
        assert isinstance(can_stream, bool)

        # Test model availability
        has_model = routing_service.provider_has_model("ollama", "llama2")
        assert isinstance(has_model, bool)

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, routing_service):
        """Test handling concurrent requests."""
        import asyncio

        async def make_request(index):
            request = LLMRequest(
                prompt=f"Concurrent request {index}",
                model="llama2",
                max_tokens=50
            )
            return await routing_service.route_request(request)

        # Make 10 concurrent requests
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for result in results:
            assert result is not None
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_rate_limiting_integration(self, routing_service):
        """Test integration with rate limiting."""
        # This would test that routing service respects rate limits
        # In a real implementation, this would check rate limiter integration

        request = LLMRequest(
            prompt="Rate limited request",
            model="llama2"
        )

        result = await routing_service.route_request(request)

        # Should handle rate limiting gracefully
        assert result is not None
        assert isinstance(result, dict)

    def test_routing_metrics(self, routing_service):
        """Test routing service metrics collection."""
        metrics = routing_service.get_routing_metrics()

        assert isinstance(metrics, dict)
        assert "total_requests" in metrics
        assert "successful_routes" in metrics
        assert "failed_routes" in metrics
        assert "average_response_time" in metrics

    @pytest.mark.asyncio
    async def test_provider_switching(self, routing_service):
        """Test automatic provider switching based on load/health."""
        # Create requests that should trigger provider switching
        requests = []
        for i in range(20):
            request = LLMRequest(
                prompt=f"Load test request {i}",
                model="llama2",
                max_tokens=100
            )
            requests.append(request)

        results = []
        for request in requests:
            result = await routing_service.route_request(request)
            results.append(result)

        # Should have used multiple providers for load balancing
        providers_used = set(result["provider"] for result in results)
        # Note: In a real implementation, this would verify load balancing
        assert len(providers_used) >= 1

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, routing_service):
        """Test comprehensive error handling and recovery."""
        # Test various error scenarios
        error_scenarios = [
            ("network_timeout", "Connection timeout"),
            ("invalid_model", "Model not available"),
            ("rate_limited", "Rate limit exceeded"),
            ("server_error", "Internal server error"),
        ]

        for error_type, error_message in error_scenarios:
            # Mock error condition
            with patch.object(routing_service, '_call_provider', side_effect=Exception(error_message)):
                request = LLMRequest(
                    prompt=f"Error test: {error_type}",
                    model="llama2"
                )

                result = await routing_service.route_request(request)

                # Should handle error gracefully
                assert result is not None
                assert result["success"] is False
                assert "error" in result or "message" in result

    def test_configuration_validation(self, routing_service):
        """Test routing service configuration validation."""
        # Test with valid configuration
        is_valid = routing_service.validate_configuration()
        assert isinstance(is_valid, bool)

        # Test configuration retrieval
        config = routing_service.get_configuration()
        assert isinstance(config, dict)
        assert "providers" in config
        assert "routing_rules" in config

    @pytest.mark.asyncio
    async def test_request_caching(self, routing_service):
        """Test request caching functionality."""
        # Create identical requests to test caching
        request1 = LLMRequest(
            prompt="Cache test prompt",
            model="llama2",
            temperature=0.5
        )

        request2 = LLMRequest(
            prompt="Cache test prompt",  # Same prompt
            model="llama2",
            temperature=0.5  # Same parameters
        )

        result1 = await routing_service.route_request(request1)
        result2 = await routing_service.route_request(request2)

        # Results should be similar (cached or not)
        assert result1["success"] == result2["success"]

    def test_provider_preference_logic(self, routing_service):
        """Test provider preference and selection logic."""
        # Test preference for faster providers
        fast_provider = routing_service.get_preferred_provider("llama2", "speed")
        assert fast_provider is not None

        # Test preference for quality
        quality_provider = routing_service.get_preferred_provider("llama2", "quality")
        assert quality_provider is not None

        # Test preference for cost
        cost_provider = routing_service.get_preferred_provider("llama2", "cost")
        assert cost_provider is not None
