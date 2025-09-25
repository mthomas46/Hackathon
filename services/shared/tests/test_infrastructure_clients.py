"""Tests for infrastructure client classes.

Comprehensive test coverage for:
- HTTP client resilience and error handling
- Database connection pooling
- External service integrations
- Client configuration and validation
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import MagicMock, patch, AsyncMock
from typing import Dict, Any, Optional

from services.shared.infrastructure.external.clients.clients import (
    BaseClient,
    HttpClient,
    ServiceClient,
    ClientConfig,
    ClientError,
    ConnectionError,
    TimeoutError,
    RateLimitError
)


class TestBaseClient:
    """Test base client functionality."""

    def test_initialization(self):
        """Test client initialization with config."""
        config = ClientConfig(
            base_url="https://api.example.com",
            timeout=30.0,
            retries=3,
            headers={"Authorization": "Bearer token"}
        )
        client = BaseClient(config)

        assert client.config == config
        assert client.session is None

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client context manager."""
        config = ClientConfig(base_url="https://api.example.com")
        client = BaseClient(config)

        async with client:
            assert client.session is not None

        assert client.session is None

    @pytest.mark.asyncio
    async def test_request_with_retry(self):
        """Test request with retry logic."""
        config = ClientConfig(
            base_url="https://api.example.com",
            retries=2,
            retry_delay=0.1
        )
        client = BaseClient(config)

        # Mock session and response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"data": "test"})

        mock_session = AsyncMock()
        mock_session.request = AsyncMock(return_value=mock_response)

        with patch.object(client, '_get_session', return_value=mock_session):
            result = await client.request("GET", "/test")
            assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_request_failure_with_retry(self):
        """Test request failure and retry logic."""
        config = ClientConfig(
            base_url="https://api.example.com",
            retries=2,
            retry_delay=0.1
        )
        client = BaseClient(config)

        # Mock session to raise exceptions
        mock_session = AsyncMock()
        mock_session.request = AsyncMock(side_effect=[
            aiohttp.ClientError("Connection failed"),
            aiohttp.ClientError("Connection failed"),
            MagicMock(status=200, json=AsyncMock(return_value={"success": True}))
        ])

        with patch.object(client, '_get_session', return_value=mock_session):
            result = await client.request("GET", "/test")
            assert result == {"success": True}
            assert mock_session.request.call_count == 3  # Initial + 2 retries


class TestHttpClient:
    """Test HTTP client functionality."""

    def test_initialization(self):
        """Test HTTP client initialization."""
        config = ClientConfig(
            base_url="https://api.example.com",
            timeout=60.0,
            headers={"Content-Type": "application/json"}
        )
        client = HttpClient(config)

        assert client.config.base_url == "https://api.example.com"
        assert client.config.timeout == 60.0
        assert "Content-Type" in client.config.headers

    @pytest.mark.asyncio
    async def test_get_request(self):
        """Test GET request."""
        config = ClientConfig(base_url="https://api.example.com")
        client = HttpClient(config)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"users": []})

        with patch.object(client, 'request', return_value=mock_response) as mock_request:
            result = await client.get("/users")
            mock_request.assert_called_once_with("GET", "/users")
            assert result.status == 200

    @pytest.mark.asyncio
    async def test_post_request(self):
        """Test POST request with data."""
        config = ClientConfig(base_url="https://api.example.com")
        client = HttpClient(config)

        data = {"name": "test", "value": 123}
        mock_response = AsyncMock()
        mock_response.status = 201
        mock_response.json = AsyncMock(return_value={"id": 1, **data})

        with patch.object(client, 'request', return_value=mock_response) as mock_request:
            result = await client.post("/users", json=data)
            mock_request.assert_called_once_with("POST", "/users", json=data)
            assert result.status == 201


class TestServiceClient:
    """Test service client functionality."""

    def test_initialization(self):
        """Test service client initialization."""
        config = ClientConfig(
            base_url="https://service.example.com",
            service_name="test-service",
            circuit_breaker_enabled=True
        )
        client = ServiceClient(config)

        assert client.config.service_name == "test-service"
        assert client.config.circuit_breaker_enabled is True

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test service health check."""
        config = ClientConfig(
            base_url="https://service.example.com",
            health_check_endpoint="/health"
        )
        client = ServiceClient(config)

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "healthy"})

        with patch.object(client, 'get', return_value=mock_response) as mock_get:
            is_healthy = await client.health_check()
            assert is_healthy is True
            mock_get.assert_called_once_with("/health")

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test service health check failure."""
        config = ClientConfig(base_url="https://service.example.com")
        client = ServiceClient(config)

        with patch.object(client, 'get', side_effect=Exception("Connection failed")):
            is_healthy = await client.health_check()
            assert is_healthy is False


class TestClientConfig:
    """Test client configuration."""

    def test_valid_config(self):
        """Test valid client configuration."""
        config = ClientConfig(
            base_url="https://api.example.com",
            timeout=30.0,
            retries=3,
            headers={"User-Agent": "TestClient/1.0"}
        )

        assert config.base_url == "https://api.example.com"
        assert config.timeout == 30.0
        assert config.retries == 3
        assert config.headers["User-Agent"] == "TestClient/1.0"

    def test_config_defaults(self):
        """Test configuration defaults."""
        config = ClientConfig(base_url="https://api.example.com")

        assert config.timeout == 30.0  # default
        assert config.retries == 3     # default
        assert config.retry_delay == 1.0  # default
        assert config.headers == {}    # default

    def test_invalid_base_url(self):
        """Test invalid base URL."""
        with pytest.raises(ValueError):
            ClientConfig(base_url="invalid-url")

    def test_invalid_timeout(self):
        """Test invalid timeout value."""
        with pytest.raises(ValueError):
            ClientConfig(base_url="https://api.example.com", timeout=-1)
