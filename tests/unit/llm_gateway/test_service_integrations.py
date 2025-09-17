"""Unit tests for LLM Gateway Service Integrations.

Tests the integration layer between LLM Gateway and all ecosystem services
including doc_store, prompt_store, memory_agent, interpreter, orchestrator, etc.
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

from modules.service_integrations import ServiceIntegrations

# Test markers for parallel execution
pytestmark = [
    pytest.mark.unit,
    pytest.mark.parallel_safe,
    pytest.mark.integration
]


class TestServiceIntegrations:
    """Test suite for ServiceIntegrations class."""

    @pytest.fixture
    def service_integrations(self):
        """Create a ServiceIntegrations instance for testing."""
        return ServiceIntegrations()

    @pytest.fixture
    def mock_clients(self):
        """Mock the service clients."""
        with patch('services.llm_gateway.modules.service_integrations.ServiceClients') as mock_clients_class:
            mock_clients = MagicMock()
            mock_clients_class.return_value = mock_clients
            yield mock_clients

    def test_service_integrations_initialization(self, service_integrations):
        """Test that ServiceIntegrations initializes correctly."""
        assert isinstance(service_integrations, ServiceIntegrations)
        assert hasattr(service_integrations, 'clients')
        assert hasattr(service_integrations, 'service_endpoints')
        assert hasattr(service_integrations, 'integration_cache')

        # Should have all expected services
        expected_services = [
            'doc_store', 'prompt_store', 'memory_agent', 'interpreter',
            'orchestrator', 'summarizer_hub', 'secure_analyzer',
            'code_analyzer', 'architecture_digitizer', 'analysis_service'
        ]

        for service in expected_services:
            assert service in [s.replace('-', '_') for s in service_integrations.service_endpoints.keys()]

    @pytest.mark.asyncio
    async def test_initialize_integrations(self, service_integrations, mock_clients):
        """Test initialization of service integrations."""
        # Mock connectivity tests
        mock_clients.get_json = AsyncMock(return_value={"status": "healthy"})

        # Mock registration
        mock_clients.post_json = AsyncMock(return_value={"success": True})

        result = await service_integrations.initialize_integrations()

        # Should return connectivity results
        assert isinstance(result, dict)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_integrate_with_doc_store_store(self, service_integrations, mock_clients):
        """Test storing LLM results in document store."""
        mock_clients.post_json.return_value = {
            "success": True,
            "document_id": "doc-123"
        }

        result = await service_integrations.integrate_with_doc_store(
            "store",
            title="LLM Query Result",
            content="Prompt: Hello\nResponse: Hi there!",
            provider="ollama",
            tokens_used=50,
            processing_time=1.2
        )

        assert result["success"] is True
        assert result["document_id"] == "doc-123"

        # Verify correct endpoint was called
        mock_clients.post_json.assert_called_once()
        call_args = mock_clients.post_json.call_args
        assert "/documents" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_integrate_with_doc_store_retrieve(self, service_integrations, mock_clients):
        """Test retrieving documents from document store."""
        mock_clients.get_json.return_value = {
            "document_id": "doc-123",
            "title": "Test Document",
            "content": "Test content"
        }

        result = await service_integrations.integrate_with_doc_store(
            "retrieve",
            doc_id="doc-123"
        )

        assert result["document_id"] == "doc-123"
        assert result["title"] == "Test Document"

        # Verify correct endpoint was called
        mock_clients.get_json.assert_called_once_with("http://doc_store:5087/documents/doc-123")

    @pytest.mark.asyncio
    async def test_integrate_with_prompt_store_get_optimized(self, service_integrations, mock_clients):
        """Test getting optimized prompts from prompt store."""
        mock_clients.post_json.return_value = {
            "content": "You are an expert. {context}",
            "variables": ["context"]
        }

        result = await service_integrations.integrate_with_prompt_store(
            "get_optimized",
            task_type="code_review",
            context={"language": "python"}
        )

        assert "content" in result
        assert "variables" in result

        # Verify correct endpoint was called
        mock_clients.post_json.assert_called_once()
        call_args = mock_clients.post_json.call_args
        assert "/prompts/optimized" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_integrate_with_memory_agent_store_interaction(self, service_integrations, mock_clients):
        """Test storing LLM interactions in memory agent."""
        mock_clients.post_json.return_value = {"status": "stored"}

        result = await service_integrations.integrate_with_memory_agent(
            "store_interaction",
            user_id="test_user",
            prompt="Hello",
            response="Hi there!",
            provider="ollama",
            tokens_used=25,
            processing_time=0.8
        )

        assert result["status"] == "stored"

        # Verify correct endpoint was called
        mock_clients.post_json.assert_called_once()
        call_args = mock_clients.post_json.call_args
        assert "/memory" in call_args[0][0]

        # Verify payload structure
        payload = call_args[0][1]
        assert payload["user_id"] == "test_user"
        assert payload["interaction_type"] == "llm_query"
        assert payload["content"]["prompt"] == "Hello"
        assert payload["content"]["response"] == "Hi there!"

    @pytest.mark.asyncio
    async def test_integrate_with_interpreter_interpret_query(self, service_integrations, mock_clients):
        """Test interpreting queries with interpreter service."""
        mock_clients.post_json.return_value = {
            "intent": "code_analysis",
            "entities": ["python", "function"],
            "confidence": 0.85
        }

        result = await service_integrations.integrate_with_interpreter(
            "interpret_query",
            query="Analyze this Python function",
            context={"language": "python"}
        )

        assert result["intent"] == "code_analysis"
        assert "python" in result["entities"]
        assert result["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_integrate_with_orchestrator_execute_workflow(self, service_integrations, mock_clients):
        """Test executing workflows through orchestrator."""
        mock_clients.post_json.return_value = {
            "workflow_id": "wf-123",
            "status": "completed",
            "result": "Workflow executed successfully"
        }

        result = await service_integrations.integrate_with_orchestrator(
            "execute_workflow",
            workflow_type="document_processing",
            parameters={"doc_id": "doc-123"}
        )

        assert result["workflow_id"] == "wf-123"
        assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_integrate_with_summarizer_hub_summarize(self, service_integrations, mock_clients):
        """Test summarization through summarizer hub."""
        mock_clients.post_json.return_value = {
            "summary": "This is a comprehensive summary of the document.",
            "word_count": 25,
            "compression_ratio": 0.3
        }

        result = await service_integrations.integrate_with_summarizer_hub(
            "summarize",
            text="Long document text here...",
            providers=["ollama"],
            prompt="Summarize the key points"
        )

        assert "summary" in result
        assert result["word_count"] == 25

    @pytest.mark.asyncio
    async def test_integrate_with_secure_analyzer_detect(self, service_integrations, mock_clients):
        """Test security analysis through secure analyzer."""
        mock_clients.post_json.return_value = {
            "sensitive": True,
            "matches": ["API key pattern"],
            "risk_level": "high",
            "recommendations": ["Use secure provider"]
        }

        result = await service_integrations.integrate_with_secure_analyzer(
            "analyze_security",
            content="My API key is sk-1234567890abcdef",
            keywords=["api", "key"]
        )

        assert result["sensitive"] is True
        assert "API key pattern" in result["matches"]
        assert result["risk_level"] == "high"

    @pytest.mark.asyncio
    async def test_service_integration_error_handling(self, service_integrations, mock_clients):
        """Test error handling in service integrations."""
        # Mock a service call that raises an exception
        mock_clients.post_json.side_effect = Exception("Service unavailable")

        result = await service_integrations.integrate_with_doc_store(
            "store",
            title="Test",
            content="Test content"
        )

        assert "error" in result
        assert "Service unavailable" in result["error"]

    @pytest.mark.asyncio
    async def test_enhanced_llm_processing_integration(self, service_integrations, mock_clients):
        """Test enhanced LLM processing with multiple service integrations."""
        # Mock all the services that enhanced processing uses
        mock_clients.post_json.side_effect = [
            # Interpreter response
            {
                "intent": "code_review",
                "entities": ["python", "function"],
                "confidence": 0.9
            },
            # Prompt store response
            {
                "content": "You are a code reviewer. {context}"
            },
            # Memory agent response
            {
                "history": ["Previous code review request"],
                "summary": "User focuses on Python development"
            },
            # Secure analyzer response
            {
                "sensitive": False,
                "risk_level": "low"
            }
        ]

        from services.llm_gateway.modules.models import LLMQuery

        query = LLMQuery(
            prompt="Review this Python function",
            user_id="test_user"
        )

        result = await service_integrations.enhanced_llm_processing(query)

        # Should return an enhanced response
        assert "response" in result
        assert "provider" in result
        assert "tokens_used" in result

    @pytest.mark.asyncio
    async def test_get_service_health_status(self, service_integrations, mock_clients):
        """Test getting comprehensive service health status."""
        # Mock health responses for different services
        mock_clients.get_json.side_effect = [
            {"status": "healthy", "version": "1.0.0"},  # doc_store
            {"status": "healthy", "uptime": "2h"},      # prompt_store
            {"status": "unhealthy", "error": "DB down"}, # memory_agent
            {"status": "healthy"},                      # interpreter
            {"status": "healthy"},                      # orchestrator
        ]

        health_status = await service_integrations.get_service_health_status()

        assert "overall_status" in health_status
        assert "services" in health_status
        assert "total_services" in health_status
        assert "healthy_services" in health_status

        # Should have status for each service
        services = health_status["services"]
        assert "doc_store" in services
        assert "memory_agent" in services

        # Unhealthy service should be marked
        assert services["memory_agent"]["status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_integration_caching(self, service_integrations, mock_clients):
        """Test that service capabilities are cached."""
        mock_clients.get_json.return_value = {
            "capabilities": ["read", "write", "search"],
            "version": "1.0.0"
        }

        # First call should cache the result
        await service_integrations.integrate_with_doc_store("retrieve", doc_id="test")

        # Check that capabilities were cached
        assert "doc_store" in service_integrations.integration_cache

        cached_capabilities = service_integrations.integration_cache["doc_store"]
        assert "capabilities" in cached_capabilities

    def test_service_endpoint_mapping(self, service_integrations):
        """Test that service endpoints are correctly mapped."""
        endpoints = service_integrations.service_endpoints

        # Should have all expected services
        assert "doc_store" in endpoints
        assert "prompt_store" in endpoints
        assert "memory_agent" in endpoints
        assert "interpreter" in endpoints
        assert "orchestrator" in endpoints

        # Endpoints should be properly formatted URLs
        for service, endpoint in endpoints.items():
            assert endpoint.startswith("http://")
            assert ":5" in endpoint  # Port number in URL

    @pytest.mark.asyncio
    async def test_cross_service_data_flow(self, service_integrations, mock_clients):
        """Test data flow between multiple services."""
        # Mock responses that simulate data flow
        call_count = 0

        def mock_post_json(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            if "interpret" in args[0]:
                return {"intent": "document_analysis", "entities": ["pdf", "report"]}
            elif "prompts" in args[0]:
                return {"content": "Analyze this document: {context}"}
            elif "memory" in args[0]:
                return {"history": ["Previous analysis request"]}
            else:
                return {"success": True}

        mock_clients.post_json = AsyncMock(side_effect=mock_post_json)

        # Execute enhanced processing
        from services.llm_gateway.modules.models import LLMQuery
        query = LLMQuery(prompt="Analyze this PDF report", user_id="test_user")

        result = await service_integrations.enhanced_llm_processing(query)

        # Should have made multiple service calls
        assert call_count >= 3  # At least interpreter, prompt store, and memory agent

        assert "response" in result
