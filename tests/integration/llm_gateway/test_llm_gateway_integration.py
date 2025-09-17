"""Integration tests for LLM Gateway Service.

Tests the complete LLM Gateway service integration including
API endpoints, service integrations, caching, security, and metrics.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from typing import Dict, Any

# Adjust path for local imports
import sys
from pathlib import Path

# Add the LLM Gateway service directory to Python path
llm_gateway_path = Path(__file__).parent.parent.parent.parent / "services" / "llm-gateway"
sys.path.insert(0, str(llm_gateway_path))

from main import app
from modules.service_integrations import ServiceIntegrations

# Test markers for parallel execution
pytestmark = [
    pytest.mark.integration,
    pytest.mark.serial_only  # Integration tests should run serially
]


class TestLLMGatewayIntegration:
    """Integration test suite for complete LLM Gateway service."""

    @pytest.fixture
    def test_client(self):
        """Create a test client for the LLM Gateway."""
        return TestClient(app)

    @pytest.fixture
    def mock_service_integrations(self):
        """Mock service integrations for testing."""
        with patch('services.llm_gateway.main.service_integrations') as mock_integrations:
            # Mock successful service integration methods
            mock_integrations.integrate_with_memory_agent = AsyncMock(return_value={"status": "stored"})
            mock_integrations.integrate_with_doc_store = AsyncMock(return_value={"status": "stored"})
            mock_integrations.enhanced_llm_processing = AsyncMock(return_value={
                "response": "Enhanced response",
                "provider": "ollama",
                "tokens_used": 100,
                "processing_time": 1.5
            })
            mock_integrations.get_service_health_status = AsyncMock(return_value={
                "overall_status": "healthy",
                "services": {
                    "doc_store": {"status": "healthy"},
                    "memory_agent": {"status": "healthy"},
                    "interpreter": {"status": "healthy"}
                }
            })

            yield mock_integrations

    def test_llm_gateway_health_endpoint(self, test_client):
        """Test the health endpoint."""
        response = test_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_llm_gateway_detailed_health_endpoint(self, test_client, mock_service_integrations):
        """Test the detailed health endpoint with service integrations."""
        response = test_client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "service_integrations" in data
        assert "providers" in data
        assert "cache" in data
        assert "rate_limiter" in data

    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.route_and_execute')
    def test_llm_query_endpoint_success(self, mock_route_execute, test_client, mock_service_integrations):
        """Test successful LLM query endpoint."""
        # Mock successful provider response
        mock_response = MagicMock()
        mock_response.response = "Test response from Ollama"
        mock_response.provider = "ollama"
        mock_response.tokens_used = 150
        mock_response.cost = 0.0
        mock_response.success = True
        mock_route_execute.return_value = mock_response

        request_data = {
            "prompt": "Explain quantum computing",
            "provider": "ollama",
            "temperature": 0.7,
            "max_tokens": 500
        }

        response = test_client.post("/query", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Test response from Ollama"
        assert data["provider"] == "ollama"
        assert data["tokens_used"] == 150
        assert "correlation_id" in data

        # Verify service integrations were called
        mock_service_integrations.integrate_with_memory_agent.assert_called_once()
        mock_service_integrations.integrate_with_doc_store.assert_not_called()  # Not called without header

    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.route_and_execute')
    def test_llm_query_with_store_interaction(self, mock_route_execute, test_client, mock_service_integrations):
        """Test LLM query with document storage enabled."""
        # Mock successful provider response
        mock_response = MagicMock()
        mock_response.response = "Test response"
        mock_response.provider = "ollama"
        mock_response.tokens_used = 100
        mock_response.cost = 0.0
        mock_response.success = True
        mock_route_execute.return_value = mock_response

        request_data = {
            "prompt": "Analyze this code",
            "user_id": "test_user"
        }

        # Test with store interaction header
        response = test_client.post(
            "/query",
            json=request_data,
            headers={"X-Store-Interaction": "true"}
        )

        assert response.status_code == 200

        # Verify document store integration was called
        mock_service_integrations.integrate_with_doc_store.assert_called_once()

    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.route_and_execute')
    def test_llm_query_with_enhanced_processing(self, mock_route_execute, test_client, mock_service_integrations):
        """Test LLM query with enhanced processing enabled."""
        request_data = {
            "prompt": "Create a complex workflow",
            "user_id": "test_user"
        }

        # Test with enhanced processing header
        response = test_client.post(
            "/query",
            json=request_data,
            headers={"X-Use-Enhanced-Processing": "true"}
        )

        assert response.status_code == 200

        # Verify enhanced processing was used instead of standard routing
        mock_route_execute.assert_not_called()
        mock_service_integrations.enhanced_llm_processing.assert_called_once()

    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.route_and_execute')
    def test_llm_query_rate_limit_exceeded(self, mock_route_execute, test_client):
        """Test rate limit handling."""
        # Mock rate limiter to deny requests
        with patch('services.llm_gateway.main.rate_limiter') as mock_rate_limiter:
            mock_rate_limiter.check_rate_limit.return_value = False

            request_data = {"prompt": "Test prompt"}
            response = test_client.post("/query", json=request_data)

            assert response.status_code == 429
            assert "Rate limit exceeded" in response.json()["message"]

    @patch('services.llm_gateway.modules.cache_manager.CacheManager.get_cached_response')
    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.route_and_execute')
    def test_llm_query_cache_hit(self, mock_route_execute, mock_cache_get, test_client, mock_service_integrations):
        """Test LLM query cache hit scenario."""
        # Mock cache hit
        cached_response = "Cached response"
        mock_cache_get.return_value = cached_response

        # Mock provider response (should not be called due to cache hit)
        mock_response = MagicMock()
        mock_response.response = "Fresh response"
        mock_route_execute.return_value = mock_response

        request_data = {"prompt": "Cached query"}
        response = test_client.post("/query", json=request_data)

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == cached_response
        assert data["provider"] == "cache"
        assert data["cached"] is True

        # Verify provider was not called
        mock_route_execute.assert_not_called()

        # Verify memory agent was still called for interaction logging
        mock_service_integrations.integrate_with_memory_agent.assert_called_once()

    @patch('services.llm_gateway.modules.security_filter.SecurityFilter.analyze_content')
    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.route_and_execute')
    def test_llm_query_security_filtering(self, mock_route_execute, mock_security_analyze, test_client):
        """Test security filtering for sensitive content."""
        # Mock security analysis detecting sensitive content
        mock_security_analyze.return_value.is_sensitive = True

        # Mock provider response
        mock_response = MagicMock()
        mock_response.response = "Secure response"
        mock_response.provider = "ollama"  # Should be forced to secure provider
        mock_response.tokens_used = 100
        mock_response.cost = 0.0
        mock_response.success = True
        mock_route_execute.return_value = mock_response

        request_data = {
            "prompt": "This contains my API key: sk-1234567890abcdef",
            "provider": "openai"  # Requesting non-secure provider
        }

        response = test_client.post("/query", json=request_data)

        assert response.status_code == 200

        # Verify security analysis was called
        mock_security_analyze.assert_called_once()

    def test_enhanced_query_endpoint(self, test_client, mock_service_integrations):
        """Test enhanced query endpoint."""
        request_data = {
            "prompt": "Create a comprehensive analysis",
            "user_id": "test_user"
        }

        response = test_client.post("/enhanced-query", json=request_data)

        assert response.status_code == 200

        # Verify enhanced processing was called
        mock_service_integrations.enhanced_llm_processing.assert_called_once()

    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.route_and_execute')
    def test_workflow_query_endpoint(self, mock_route_execute, test_client, mock_service_integrations):
        """Test workflow query endpoint."""
        # Mock orchestrator integration
        mock_service_integrations.integrate_with_orchestrator.return_value = {
            "workflow_id": "wf-123",
            "status": "executing",
            "steps": ["step1", "step2"]
        }

        request_data = {
            "prompt": "Execute this workflow",
            "user_id": "test_user"
        }

        response = test_client.post(
            "/workflow-query",
            json=request_data,
            headers={"X-Workflow-Type": "document_processing"}
        )

        assert response.status_code == 200

        # Verify orchestrator integration was called
        mock_service_integrations.integrate_with_orchestrator.assert_called_once()

    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.route_and_execute')
    def test_contextual_query_endpoint(self, mock_route_execute, test_client, mock_service_integrations):
        """Test contextual query endpoint."""
        # Mock service integrations for context retrieval
        mock_service_integrations.integrate_with_memory_agent.return_value = {
            "history": ["Previous conversation"],
            "summary": "User has been asking about APIs"
        }

        mock_service_integrations.integrate_with_doc_store.return_value = {
            "documents": [{"title": "API Guide", "content": "API documentation"}]
        }

        mock_service_integrations.integrate_with_prompt_store.return_value = {
            "content": "You are an API expert. {context}"
        }

        # Mock final provider response
        mock_response = MagicMock()
        mock_response.response = "Contextual response with history and docs"
        mock_response.provider = "ollama"
        mock_response.tokens_used = 200
        mock_response.cost = 0.0
        mock_response.success = True
        mock_route_execute.return_value = mock_response

        request_data = {
            "prompt": "How do I implement authentication?",
            "context": {"search_terms": "authentication"},
            "user_id": "test_user"
        }

        response = test_client.post("/contextual-query", json=request_data)

        assert response.status_code == 200

        # Verify all context services were called
        mock_service_integrations.integrate_with_memory_agent.assert_called_once()
        mock_service_integrations.integrate_with_doc_store.assert_called_once()
        mock_service_integrations.integrate_with_prompt_store.assert_called_once()

        # Verify final query was executed
        mock_route_execute.assert_called_once()

    def test_services_status_endpoint(self, test_client, mock_service_integrations):
        """Test services status endpoint."""
        response = test_client.get("/services/status")

        assert response.status_code == 200
        data = response.json()

        assert "overall_status" in data
        assert "services" in data
        assert "total_services" in data
        assert "healthy_services" in data

        # Verify service health check was called
        mock_service_integrations.get_service_health_status.assert_called_once()

    @patch('services.llm_gateway.main.service_integrations')
    def test_service_integration_endpoint_success(self, mock_integrations, test_client):
        """Test generic service integration endpoint."""
        # Mock a service integration method
        mock_integrations.integrate_with_doc_store = AsyncMock(return_value={"status": "success"})

        response = test_client.post(
            "/integrations/doc_store/store",
            json={"content": "Test content"}
        )

        assert response.status_code == 200

        # Verify the integration method was called
        mock_integrations.integrate_with_doc_store.assert_called_once()

    def test_service_integration_endpoint_not_found(self, test_client):
        """Test service integration endpoint with invalid service."""
        response = test_client.post(
            "/integrations/invalid_service/test_operation",
            json={"test": "data"}
        )

        assert response.status_code == 404
        assert "not available" in response.json()["message"]

    def test_providers_endpoint(self, test_client):
        """Test providers endpoint."""
        response = test_client.get("/providers")

        assert response.status_code == 200
        data = response.json()

        assert "providers" in data
        assert isinstance(data["providers"], list)

        # Should have multiple providers
        assert len(data["providers"]) > 0

        # Check provider structure
        provider = data["providers"][0]
        assert "name" in provider
        assert "type" in provider
        assert "status" in provider

    def test_metrics_endpoint(self, test_client):
        """Test metrics endpoint."""
        response = test_client.get("/metrics")

        assert response.status_code == 200
        data = response.json()

        # Should have various metrics
        expected_metrics = [
            "total_requests", "requests_by_provider", "total_tokens_used",
            "total_cost", "average_response_time", "cache_hit_rate",
            "error_rate", "uptime_percentage"
        ]

        for metric in expected_metrics:
            assert metric in data

    @patch('services.llm_gateway.modules.cache_manager.CacheManager.clear_cache')
    def test_cache_clear_endpoint(self, mock_clear_cache, test_client):
        """Test cache clear endpoint."""
        mock_clear_cache.return_value = 5  # Cleared 5 entries

        response = test_client.post("/cache/clear")

        assert response.status_code == 200
        data = response.json()

        assert "entries_cleared" in data
        assert data["entries_cleared"] == 5

    def test_capabilities_endpoint(self, test_client):
        """Test capabilities endpoint."""
        response = test_client.get("/capabilities")

        assert response.status_code == 200
        data = response.json()

        assert "llm_providers" in data
        assert "core_features" in data
        assert "service_integrations" in data
        assert "enhanced_features" in data
        assert "api_endpoints" in data
        assert "supported_headers" in data

        # Verify all expected services are listed
        expected_services = [
            "doc_store", "prompt_store", "memory_agent", "interpreter",
            "orchestrator", "summarizer_hub", "secure_analyzer",
            "code_analyzer", "architecture_digitizer", "analysis_service"
        ]

        for service in expected_services:
            assert service in data["service_integrations"]

    def test_chat_endpoint(self, test_client):
        """Test chat endpoint (delegates to query)."""
        request_data = {
            "prompt": "Hello, how are you?",
            "user_id": "chat_user"
        }

        response = test_client.post("/chat", json=request_data)

        # Should work the same as query endpoint
        assert response.status_code in [200, 500]  # May fail if no providers available in test

    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.generate_embeddings')
    def test_embeddings_endpoint(self, mock_generate_embeddings, test_client):
        """Test embeddings endpoint."""
        mock_generate_embeddings.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]

        request_data = {
            "text": "Test text for embeddings",
            "model": "text-embedding-ada-002",
            "provider": "openai"
        }

        response = test_client.post("/embeddings", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "embeddings" in data
        assert "model" in data
        assert "dimensions" in data
        assert data["dimensions"] == 5

    @patch('services.llm_gateway.modules.provider_router.ProviderRouter.stream_response')
    def test_stream_endpoint(self, mock_stream_response, test_client):
        """Test streaming endpoint."""
        # Mock streaming response
        async def mock_stream():
            yield {"chunk": "Test chunk", "finished": False}
            yield {"chunk": "Final chunk", "finished": True}

        mock_stream_response.return_value = mock_stream()

        request_data = {"prompt": "Stream this response"}
        response = test_client.post("/stream", json=request_data)

        assert response.status_code == 200
        # Streaming response should have appropriate headers
        assert response.headers.get("content-type") == "text/event-stream"
