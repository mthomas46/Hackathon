"""Tests for configuration and utility functions."""

import pytest
import os
from unittest.mock import patch

from ..main import (
    load_service_config,
    get_llm_gateway_client,
    get_doc_store_client,
    ConfigurationError,
    LLMGatewayClient,
    DocStoreClient,
)


class TestConfiguration:
    """Test configuration loading and management."""

    @patch.dict(os.environ, {
        'LLM_GATEWAY_URL': 'http://test-gateway:5055',
        'DOC_STORE_URL': 'http://test-store:5010',
        'ENVIRONMENT': 'testing'
    })
    def test_load_service_config_with_env_vars(self):
        """Test loading configuration with environment variables."""
        config = load_service_config()

        assert hasattr(config, 'service_name')
        assert config.service_name == 'mock-data-generator'

    def test_load_service_config_defaults(self):
        """Test loading configuration with defaults."""
        # Clear environment variables for this test
        with patch.dict(os.environ, {}, clear=True):
            config = load_service_config()

            assert hasattr(config, 'service_name')
            assert config.service_name == 'mock-data-generator'

    @patch('builtins.open')
    def test_load_service_config_with_file(self, mock_open):
        """Test loading configuration from file."""
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = """
service_name: custom-mock-generator
service_description: Custom Mock Data Generator
service_version: 2.0.0
server:
  host: 0.0.0.0
  port: 9000
"""

        config = load_service_config(config_file="test_config.yaml")

        mock_open.assert_called_with("test_config.yaml", 'r')
        assert config.service_name == 'custom-mock-generator'


class TestLLMGatewayClient:
    """Test LLM Gateway client functionality."""

    def test_initialization(self):
        """Test LLMGatewayClient initialization."""
        client = LLMGatewayClient("http://test-gateway:5055")
        assert client.base_url == "http://test-gateway:5055"
        assert client.timeout == 30.0

    def test_initialization_custom_timeout(self):
        """Test LLMGatewayClient with custom timeout."""
        client = LLMGatewayClient("http://test-gateway:5055", timeout=60.0)
        assert client.timeout == 60.0

    @patch('httpx.AsyncClient')
    async def test_generate_content_success(self, mock_client):
        """Test successful content generation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": "Generated mock content",
            "metadata": {"tokens": 150}
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        client = LLMGatewayClient("http://test-gateway:5055")
        result = await client.generate_content(
            prompt="Generate test content",
            content_type="text",
            parameters={"temperature": 0.7}
        )

        assert result["content"] == "Generated mock content"
        assert result["metadata"]["tokens"] == 150

    @patch('httpx.AsyncClient')
    async def test_generate_content_failure(self, mock_client):
        """Test content generation failure."""
        # Mock exception
        mock_client.return_value.__aenter__.side_effect = Exception("Connection failed")

        client = LLMGatewayClient("http://test-gateway:5055")

        with pytest.raises(ConfigurationError, match="Failed to generate content"):
            await client.generate_content("Test prompt")


class TestDocStoreClient:
    """Test Doc Store client functionality."""

    def test_initialization(self):
        """Test DocStoreClient initialization."""
        client = DocStoreClient("http://test-store:5010")
        assert client.base_url == "http://test-store:5010"
        assert client.timeout == 30.0

    @patch('httpx.AsyncClient')
    async def test_store_document_success(self, mock_client):
        """Test successful document storage."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "doc_123",
            "status": "stored"
        }
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response

        client = DocStoreClient("http://test-store:5010")
        result = await client.store_document({
            "title": "Test Document",
            "content": "Test content",
            "type": "mock_data"
        })

        assert result["id"] == "doc_123"
        assert result["status"] == "stored"

    @patch('httpx.AsyncClient')
    async def test_store_document_failure(self, mock_client):
        """Test document storage failure."""
        # Mock exception
        mock_client.return_value.__aenter__.side_effect = Exception("Storage failed")

        client = DocStoreClient("http://test-store:5010")

        with pytest.raises(ConfigurationError, match="Failed to store document"):
            await client.store_document({"title": "Test"})


class TestClientInitialization:
    """Test client initialization functions."""

    @patch.dict(os.environ, {'LLM_GATEWAY_URL': 'http://env-gateway:5055'})
    def test_get_llm_gateway_client_with_env(self):
        """Test getting LLM Gateway client with environment variable."""
        client = get_llm_gateway_client()
        assert isinstance(client, LLMGatewayClient)
        assert "env-gateway" in client.base_url

    def test_get_llm_gateway_client_default(self):
        """Test getting LLM Gateway client with default URL."""
        with patch.dict(os.environ, {}, clear=True):
            client = get_llm_gateway_client()
            assert isinstance(client, LLMGatewayClient)
            assert client.base_url is not None

    @patch.dict(os.environ, {'DOC_STORE_URL': 'http://env-store:5010'})
    def test_get_doc_store_client_with_env(self):
        """Test getting Doc Store client with environment variable."""
        client = get_doc_store_client()
        assert isinstance(client, DocStoreClient)
        assert "env-store" in client.base_url

    def test_get_doc_store_client_default(self):
        """Test getting Doc Store client with default URL."""
        with patch.dict(os.environ, {}, clear=True):
            client = get_doc_store_client()
            assert isinstance(client, DocStoreClient)
            assert client.base_url is not None


class TestErrorHandling:
    """Test error handling in configuration."""

    def test_configuration_error_inheritance(self):
        """Test ConfigurationError inherits from Exception."""
        error = ConfigurationError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_configuration_error_with_cause(self):
        """Test ConfigurationError with underlying cause."""
        cause = ValueError("Original error")
        error = ConfigurationError("Wrapper error", cause)

        assert isinstance(error, Exception)
        assert "Wrapper error" in str(error)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_validate_data_type_enum_values(self):
        """Test that data type validation uses correct enum values."""
        from ..main import MockDataType

        # Test that all enum values are valid
        for data_type in MockDataType:
            # Should not raise exception
            assert isinstance(data_type.value, str)
            assert len(data_type.value) > 0

    def test_enum_uniqueness(self):
        """Test that enum values are unique."""
        from ..main import MockDataType

        values = [dt.value for dt in MockDataType]
        assert len(values) == len(set(values))  # All unique

    def test_enum_completeness(self):
        """Test that enum contains expected data types."""
        from ..main import MockDataType

        expected_types = {
            "confluence_page", "github_repo", "github_pr",
            "jira_ticket", "jira_epic", "project_doc", "api_doc"
        }

        actual_types = {dt.value for dt in MockDataType}
        assert expected_types.issubset(actual_types)


class TestIntegrationHealth:
    """Test integration health checks."""

    @patch('httpx.AsyncClient')
    async def test_llm_gateway_health_check(self, mock_client):
        """Test LLM Gateway health check."""
        # Mock healthy response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        client = LLMGatewayClient("http://test-gateway:5055")
        is_healthy = await client.health_check()

        assert is_healthy is True

    @patch('httpx.AsyncClient')
    async def test_llm_gateway_health_check_failure(self, mock_client):
        """Test LLM Gateway health check failure."""
        # Mock unhealthy response
        mock_client.return_value.__aenter__.side_effect = Exception("Connection failed")

        client = LLMGatewayClient("http://test-gateway:5055")
        is_healthy = await client.health_check()

        assert is_healthy is False

    @patch('httpx.AsyncClient')
    async def test_doc_store_health_check(self, mock_client):
        """Test Doc Store health check."""
        # Mock healthy response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        client = DocStoreClient("http://test-store:5010")
        is_healthy = await client.health_check()

        assert is_healthy is True
