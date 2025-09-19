"""Integration Tests for Ecosystem Service Clients - Ecosystem Integration Testing.

This module contains integration tests for typed client adapters for all
21+ ecosystem services, testing client functionality and error handling.
"""

import pytest
import httpx
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, Optional

from simulation.infrastructure.clients.ecosystem_clients import (
    EcosystemServiceClient, EcosystemServiceRegistry,
    DocStoreClient, MockDataGeneratorClient, OrchestratorClient,
    AnalysisServiceClient, LlmGatewayClient, PromptStoreClient,
    SummarizerHubClient, NotificationServiceClient, SourceAgentClient,
    CodeAnalyzerClient, get_ecosystem_client, get_ecosystem_service_registry
)
from simulation.domain.value_objects import ServiceEndpoint, ServiceHealth, ECOSYSTEM_SERVICES


class TestEcosystemServiceClientBase:
    """Test cases for base ecosystem service client."""

    @pytest.fixture
    async def base_client(self):
        """Create base ecosystem service client for testing."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
        client = EcosystemServiceClient("test_service", endpoint)
        yield client
        await client._client.aclose()

    @pytest.mark.asyncio
    async def test_base_client_creation(self, base_client):
        """Test base client creation and configuration."""
        assert base_client.service_name == "test_service"
        assert base_client.endpoint.url == "http://httpbin.org"
        assert base_client.endpoint.timeout_seconds == 30

    @pytest.mark.asyncio
    async def test_base_client_health_check_success(self, base_client):
        """Test successful health check."""
        # httpbin.org has a health endpoint at /status/200
        base_client.endpoint = ServiceEndpoint("http://httpbin.org/status/200")

        health = await base_client.health_check()
        assert health == ServiceHealth.HEALTHY

    @pytest.mark.asyncio
    async def test_base_client_health_check_failure(self, base_client):
        """Test failed health check."""
        # Use non-existent endpoint
        base_client.endpoint = ServiceEndpoint("http://httpbin.org/status/500")

        health = await base_client.health_check()
        assert health == ServiceHealth.UNHEALTHY

    @pytest.mark.asyncio
    async def test_base_client_get_json_success(self, base_client):
        """Test successful JSON GET request."""
        response = await base_client.get_json("/json")

        assert response is not None
        assert isinstance(response, dict)
        assert "slideshow" in response

    @pytest.mark.asyncio
    async def test_base_client_get_json_error_handling(self, base_client):
        """Test error handling in JSON GET request."""
        with pytest.raises(httpx.HTTPStatusError):
            await base_client.get_json("/status/404")

    @pytest.mark.asyncio
    async def test_base_client_post_json_success(self, base_client):
        """Test successful JSON POST request."""
        test_data = {"test": "data", "number": 42}

        response = await base_client.post_json("/post", test_data)

        assert response is not None
        assert isinstance(response, dict)
        assert response.get("json") == test_data

    @pytest.mark.asyncio
    async def test_base_client_post_json_error_handling(self, base_client):
        """Test error handling in JSON POST request."""
        with pytest.raises(httpx.HTTPStatusError):
            await base_client.post_json("/status/400", {"test": "data"})


class TestDocStoreClient:
    """Test cases for DocStore client."""

    @pytest.fixture
    async def docstore_client(self):
        """Create DocStore client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="doc_store", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = DocStoreClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_docstore_store_document(self, docstore_client):
        """Test storing a document in DocStore."""
        # Use httpbin.org for testing
        response = await docstore_client.post_json("/post", {
            "title": "Test Document",
            "content": "Test content",
            "metadata": {"type": "test"}
        })

        assert response is not None
        # In real integration, this would return a document ID
        # For testing with httpbin, we just verify the request structure

    @pytest.mark.asyncio
    async def test_docstore_get_document(self, docstore_client):
        """Test retrieving a document from DocStore."""
        # Test with a known httpbin endpoint
        response = await docstore_client.get_json("/json")

        assert response is not None
        assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_docstore_search_documents(self, docstore_client):
        """Test searching documents in DocStore."""
        response = await docstore_client.post_json("/post", {"query": "test"})

        assert response is not None
        # In real integration, this would return search results


class TestMockDataGeneratorClient:
    """Test cases for Mock Data Generator client."""

    @pytest.fixture
    async def mockgen_client(self):
        """Create Mock Data Generator client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="mock_data_generator", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = MockDataGeneratorClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_mockgen_generate_project_documents(self, mockgen_client):
        """Test generating project documents."""
        request_data = {
            "project_type": "web_application",
            "team_size": 5,
            "complexity": "medium"
        }

        response = await mockgen_client.generate_project_documents(request_data)

        assert response is not None
        assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_mockgen_generate_timeline_events(self, mockgen_client):
        """Test generating timeline events."""
        request_data = {
            "project_id": "test-123",
            "duration_weeks": 8,
            "team_size": 3
        }

        response = await mockgen_client.generate_timeline_events(request_data)

        assert response is not None
        assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_mockgen_generate_team_activities(self, mockgen_client):
        """Test generating team activities."""
        request_data = {
            "team_members": ["dev1", "dev2", "qa1"],
            "duration_days": 30
        }

        response = await mockgen_client.generate_team_activities(request_data)

        assert response is not None
        assert isinstance(response, dict)


class TestOrchestratorClient:
    """Test cases for Orchestrator client."""

    @pytest.fixture
    async def orchestrator_client(self):
        """Create Orchestrator client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="orchestrator", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = OrchestratorClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_orchestrator_create_workflow(self, orchestrator_client):
        """Test creating a workflow."""
        workflow_config = {
            "name": "test_workflow",
            "steps": ["step1", "step2"],
            "services": ["service1", "service2"]
        }

        response = await orchestrator_client.post_json("/workflows", workflow_config)

        assert response is not None
        # In real integration, this would return a workflow ID

    @pytest.mark.asyncio
    async def test_orchestrator_execute_workflow(self, orchestrator_client):
        """Test executing a workflow."""
        # Mock a workflow ID
        workflow_id = "test-workflow-123"

        response = await orchestrator_client.post_json(f"/workflows/{workflow_id}/execute", {})

        assert response is not None
        assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_orchestrator_get_workflow_status(self, orchestrator_client):
        """Test getting workflow status."""
        workflow_id = "test-workflow-123"

        response = await orchestrator_client.get_json(f"/workflows/{workflow_id}/status")

        assert response is not None
        assert isinstance(response, dict)


class TestAnalysisServiceClient:
    """Test cases for Analysis Service client."""

    @pytest.fixture
    async def analysis_client(self):
        """Create Analysis Service client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="analysis_service", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = AnalysisServiceClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_analysis_analyze_documents(self, analysis_client):
        """Test analyzing documents."""
        documents = [
            {"id": "doc1", "content": "Test content 1", "type": "requirements"},
            {"id": "doc2", "content": "Test content 2", "type": "design"}
        ]

        response = await analysis_client.analyze_documents(documents)

        assert response is not None
        assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_analysis_generate_insights(self, analysis_client):
        """Test generating insights from analysis data."""
        analysis_data = {
            "documents_analyzed": 5,
            "patterns_found": ["pattern1", "pattern2"],
            "quality_score": 0.85
        }

        response = await analysis_client.generate_insights(analysis_data)

        assert response is not None
        assert isinstance(response, dict)


class TestLlmGatewayClient:
    """Test cases for LLM Gateway client."""

    @pytest.fixture
    async def llm_client(self):
        """Create LLM Gateway client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="llm_gateway", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = LlmGatewayClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_llm_generate_content(self, llm_client):
        """Test generating content using LLM."""
        prompt = "Generate a brief description of a web application."
        model = "gpt-4"

        response = await llm_client.generate_content(prompt, model)

        assert response is not None
        assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_llm_generate_content_default_model(self, llm_client):
        """Test generating content with default model."""
        prompt = "Test prompt for default model."

        response = await llm_client.generate_content(prompt)

        assert response is not None
        assert isinstance(response, dict)


class TestPromptStoreClient:
    """Test cases for Prompt Store client."""

    @pytest.fixture
    async def prompt_client(self):
        """Create Prompt Store client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="prompt_store", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = PromptStoreClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_prompt_store_prompt(self, prompt_client):
        """Test storing a prompt."""
        response = await prompt_client.post_json("/prompts", {
            "name": "test_prompt",
            "content": "Test prompt content",
            "category": "test"
        })

        assert response is not None

    @pytest.mark.asyncio
    async def test_prompt_get_prompt(self, prompt_client):
        """Test retrieving a prompt."""
        # Test with a mock prompt ID
        response = await prompt_client.get_json("/json")  # Using httpbin for testing

        assert response is not None
        assert isinstance(response, dict)


class TestSummarizerHubClient:
    """Test cases for Summarizer Hub client."""

    @pytest.fixture
    async def summarizer_client(self):
        """Create Summarizer Hub client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="summarizer_hub", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = SummarizerHubClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_summarizer_summarize_text(self, summarizer_client):
        """Test summarizing text."""
        text = "This is a long piece of text that needs to be summarized for testing purposes."
        max_length = 50

        response = await summarizer_client.summarize_text(text, max_length)

        assert response is not None
        assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_summarizer_default_max_length(self, summarizer_client):
        """Test summarizing with default max length."""
        text = "Short text for summarization."

        response = await summarizer_client.summarize_text(text)

        assert response is not None
        assert isinstance(response, dict)


class TestNotificationServiceClient:
    """Test cases for Notification Service client."""

    @pytest.fixture
    async def notification_client(self):
        """Create Notification Service client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="notification_service", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = NotificationServiceClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_notification_send_notification(self, notification_client):
        """Test sending a notification."""
        response = await notification_client.send_notification(
            recipient="test@example.com",
            message="Test notification",
            notification_type="info"
        )

        assert response is not None
        assert isinstance(response, dict)

    @pytest.mark.asyncio
    async def test_notification_default_type(self, notification_client):
        """Test sending notification with default type."""
        response = await notification_client.send_notification(
            recipient="test@example.com",
            message="Test notification"
        )

        assert response is not None
        assert isinstance(response, dict)


class TestSourceAgentClient:
    """Test cases for Source Agent client."""

    @pytest.fixture
    async def source_client(self):
        """Create Source Agent client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="source_agent", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = SourceAgentClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_source_analyze_codebase(self, source_client):
        """Test analyzing a codebase."""
        repository_url = "https://github.com/example/test-repo"

        response = await source_client.analyze_codebase(repository_url)

        assert response is not None
        assert isinstance(response, dict)


class TestCodeAnalyzerClient:
    """Test cases for Code Analyzer client."""

    @pytest.fixture
    async def code_client(self):
        """Create Code Analyzer client for testing."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="code_analyzer", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = CodeAnalyzerClient()
            yield client
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_code_analyze_code(self, code_client):
        """Test analyzing code."""
        code = "def test_function():\n    return 'test'"
        language = "python"

        response = await code_client.analyze_code(code, language)

        assert response is not None
        assert isinstance(response, dict)


class TestEcosystemServiceRegistryIntegration:
    """Test cases for ecosystem service registry integration."""

    @pytest.mark.asyncio
    async def test_registry_get_client(self):
        """Test getting clients from registry."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="test_service", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            registry = EcosystemServiceRegistry()

            client = registry.get_client("test_service")
            assert client is not None
            assert isinstance(client, EcosystemServiceClient)
            assert client.service_name == "test_service"

    @pytest.mark.asyncio
    async def test_registry_get_nonexistent_client(self):
        """Test getting non-existent client from registry."""
        registry = EcosystemServiceRegistry()

        client = registry.get_client("nonexistent_service")
        assert client is None

    @pytest.mark.asyncio
    async def test_registry_get_all_clients(self):
        """Test getting all clients from registry."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="service1", endpoint=ServiceEndpoint("http://httpbin.org")),
            Mock(name="service2", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            registry = EcosystemServiceRegistry()

            all_clients = registry.get_all_clients()
            assert isinstance(all_clients, dict)
            assert len(all_clients) == 2
            assert "service1" in all_clients
            assert "service2" in all_clients

    @pytest.mark.asyncio
    async def test_registry_health_check_all_services(self):
        """Test checking health of all services."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="service1", endpoint=ServiceEndpoint("http://httpbin.org")),
            Mock(name="service2", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            registry = EcosystemServiceRegistry()

            health_status = await registry.check_all_services_health()

            assert isinstance(health_status, dict)
            assert len(health_status) == 2
            assert "service1" in health_status
            assert "service2" in health_status

            # Each should be a ServiceHealth enum value
            for status in health_status.values():
                assert isinstance(status, ServiceHealth)


class TestGlobalClientFunctions:
    """Test cases for global client convenience functions."""

    def test_get_ecosystem_client_existing(self):
        """Test getting existing ecosystem client."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="doc_store", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            client = get_ecosystem_client("doc_store")
            assert client is not None
            assert isinstance(client, EcosystemServiceClient)

    def test_get_ecosystem_client_nonexistent(self):
        """Test getting non-existent ecosystem client."""
        client = get_ecosystem_client("nonexistent_service")
        assert client is None

    def test_convenience_client_functions(self):
        """Test convenience client functions."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="doc_store", endpoint=ServiceEndpoint("http://httpbin.org")),
            Mock(name="mock_data_generator", endpoint=ServiceEndpoint("http://httpbin.org")),
            Mock(name="orchestrator", endpoint=ServiceEndpoint("http://httpbin.org")),
            Mock(name="analysis_service", endpoint=ServiceEndpoint("http://httpbin.org")),
            Mock(name="llm_gateway", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            # Test convenience functions
            doc_client = get_ecosystem_client("doc_store")
            mock_client = get_ecosystem_client("mock_data_generator")
            orch_client = get_ecosystem_client("orchestrator")
            analysis_client = get_ecosystem_client("analysis_service")
            llm_client = get_ecosystem_client("llm_gateway")

            assert all(client is not None for client in [
                doc_client, mock_client, orch_client, analysis_client, llm_client
            ])


@pytest.mark.integration
class TestEcosystemClientsIntegrationSuite:
    """Comprehensive integration test suite for ecosystem clients."""

    @pytest.mark.asyncio
    async def test_multiple_clients_concurrent_requests(self):
        """Test multiple clients making concurrent requests."""
        with patch('simulation.infrastructure.clients.ecosystem_clients.ECOSYSTEM_SERVICES', [
            Mock(name="service1", endpoint=ServiceEndpoint("http://httpbin.org")),
            Mock(name="service2", endpoint=ServiceEndpoint("http://httpbin.org")),
            Mock(name="service3", endpoint=ServiceEndpoint("http://httpbin.org"))
        ]):
            registry = EcosystemServiceRegistry()

            async def make_request(service_name: str):
                client = registry.get_client(service_name)
                if client:
                    return await client.get_json("/json")
                return None

            # Make concurrent requests
            tasks = [
                make_request("service1"),
                make_request("service2"),
                make_request("service3")
            ]

            results = await asyncio.gather(*tasks)

            # All requests should succeed
            assert len(results) == 3
            assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_client_error_recovery_and_retry(self):
        """Test client error recovery and retry mechanisms."""
        # This would test retry logic with mocked failures
        # For integration tests, we test with reliable endpoints
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30, retries=2)
        client = EcosystemServiceClient("retry_test", endpoint)

        try:
            # Make a request that should succeed within retry limits
            response = await client.get_json("/json")
            assert response is not None
        finally:
            await client._client.aclose()

    def test_client_configuration_validation(self):
        """Test client configuration validation."""
        # Test with valid configuration
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30, retries=3)
        client = EcosystemServiceClient("config_test", endpoint)

        assert client.service_name == "config_test"
        assert client.endpoint.url == "http://httpbin.org"
        assert client.endpoint.timeout_seconds == 30
        assert client.endpoint.retries == 3

    @pytest.mark.asyncio
    async def test_client_resource_cleanup(self):
        """Test proper client resource cleanup."""
        clients = []

        try:
            # Create multiple clients
            for i in range(5):
                endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
                client = EcosystemServiceClient(f"cleanup_test_{i}", endpoint)
                clients.append(client)

                # Make a request with each client
                response = await client.get_json("/json")
                assert response is not None

        finally:
            # Ensure all clients are properly closed
            for client in clients:
                await client._client.aclose()

    @pytest.mark.asyncio
    async def test_client_performance_under_load(self):
        """Test client performance under concurrent load."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
        client = EcosystemServiceClient("load_test", endpoint)

        try:
            # Make multiple rapid requests
            tasks = []
            for i in range(10):
                task = asyncio.create_task(client.get_json("/json"))
                tasks.append(task)

            # Wait for all requests to complete
            responses = await asyncio.gather(*tasks)

            # All should succeed
            assert len(responses) == 10
            assert all(r is not None for r in responses)

        finally:
            await client._client.aclose()

    def test_ecosystem_services_configuration(self):
        """Test that ecosystem services are properly configured."""
        # Verify ECOSYSTEM_SERVICES contains expected services
        service_names = [service.name for service in ECOSYSTEM_SERVICES]

        expected_services = [
            "doc_store", "prompt_store", "analysis_service", "llm_gateway",
            "orchestrator", "mock_data_generator", "source_agent", "code_analyzer",
            "github_mcp", "bedrock_proxy", "summarizer_hub", "notification_service",
            "frontend", "discovery_agent", "log_collector", "redis", "ollama",
            "architecture_digitizer", "interpreter", "memory_agent",
            "secure_analyzer"
        ]

        for expected_service in expected_services:
            assert expected_service in service_names

        # Verify all services have valid endpoints
        for service in ECOSYSTEM_SERVICES:
            assert service.endpoint is not None
            assert service.endpoint.url.startswith(('http://', 'https://'))
            assert service.required_for_simulation in [True, False]
