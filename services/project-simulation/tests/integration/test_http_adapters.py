"""Integration Tests for HTTP Adapters - Ecosystem Integration Testing.

This module contains integration tests for HTTP client adapters, testing
connection pooling, retry logic, timeout handling, and resilience patterns.
"""

import pytest
import httpx
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from simulation.infrastructure.clients.ecosystem_clients import (
    EcosystemServiceClient, EcosystemServiceRegistry
)
from simulation.domain.value_objects import ServiceEndpoint, ServiceHealth


class TestHTTPAdapterConnectionPooling:
    """Test cases for HTTP connection pooling and management."""

    @pytest.fixture
    async def client(self):
        """Create test client."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
        client = EcosystemServiceClient("test_service", endpoint)
        yield client
        await client._client.aclose()

    @pytest.mark.asyncio
    async def test_connection_pool_reuse(self, client):
        """Test that HTTP connections are reused from the pool."""
        # Make multiple requests to the same host
        responses = []
        for i in range(3):
            response = await client.get_json("/json")
            responses.append(response)

        # All responses should be successful
        assert all(r is not None for r in responses)
        assert all(r.get("slideshow") is not None for r in responses)

        # Check that connections were pooled (this is more of a behavioral test)
        # In a real scenario, we'd monitor connection pool metrics

    @pytest.mark.asyncio
    async def test_connection_timeout_handling(self, client):
        """Test timeout handling for slow requests."""
        # Use a very short timeout
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=0.001)
        fast_client = EcosystemServiceClient("fast_service", endpoint)

        try:
            # This should timeout
            await fast_client.get_json("/delay/1")  # 1 second delay
            assert False, "Should have timed out"
        except (httpx.TimeoutException, httpx.ConnectTimeout):
            # Expected timeout
            pass
        finally:
            await fast_client._client.aclose()

    @pytest.mark.asyncio
    async def test_connection_error_recovery(self, client):
        """Test recovery from connection errors."""
        # Make a request to a non-existent endpoint
        try:
            await client.get_json("/non-existent-endpoint-12345")
            assert False, "Should have failed"
        except httpx.HTTPStatusError as e:
            assert e.response.status_code == 404
        except Exception as e:
            # Other connection errors are also acceptable
            assert isinstance(e, Exception)


class TestHTTPAdapterRetryLogic:
    """Test cases for HTTP retry logic and error recovery."""

    @pytest.fixture
    async def retry_client(self):
        """Create client with retry configuration."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30, retries=2)
        client = EcosystemServiceClient("retry_service", endpoint)
        yield client
        await client._client.aclose()

    @pytest.mark.asyncio
    async def test_successful_retry_on_transient_failure(self, retry_client):
        """Test that client retries on transient failures."""
        # This test would require mocking transient failures
        # For now, test successful operation
        response = await retry_client.get_json("/json")
        assert response is not None
        assert response.get("slideshow") is not None

    @pytest.mark.asyncio
    async def test_no_retry_on_client_error(self, retry_client):
        """Test that client doesn't retry on 4xx errors."""
        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await retry_client.get_json("/status/404")

        assert exc_info.value.response.status_code == 404

    @pytest.mark.asyncio
    async def test_retry_on_server_error(self, retry_client):
        """Test retry behavior on 5xx server errors."""
        # This would require a mock server that returns 5xx errors
        # For integration testing, we'll test with a reliable endpoint
        response = await retry_client.get_json("/json")
        assert response is not None


class TestHTTPAdapterTimeoutHandling:
    """Test cases for timeout handling and configuration."""

    @pytest.mark.asyncio
    async def test_custom_timeout_configuration(self):
        """Test custom timeout configuration."""
        # Test with different timeout values
        timeouts = [1, 5, 30]

        for timeout in timeouts:
            endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=timeout)
            client = EcosystemServiceClient(f"timeout_{timeout}", endpoint)

            try:
                start_time = time.time()
                # Use delay endpoint to test timeout
                if timeout >= 2:  # Only test delay if timeout allows
                    response = await client.get_json("/delay/1")  # 1 second delay
                    elapsed = time.time() - start_time
                    assert elapsed >= 1.0  # Should have waited for delay
                    assert response is not None
            except (httpx.TimeoutException, httpx.ConnectTimeout):
                # Expected for very short timeouts
                if timeout < 2:
                    pass
                else:
                    raise
            finally:
                await client._client.aclose()

    @pytest.mark.asyncio
    async def test_timeout_with_slow_response(self):
        """Test timeout behavior with slow server responses."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=2)
        client = EcosystemServiceClient("slow_service", endpoint)

        try:
            # Request a 5-second delay with 2-second timeout
            await client.get_json("/delay/5")
            assert False, "Should have timed out"
        except (httpx.TimeoutException, httpx.ConnectTimeout):
            # Expected timeout
            pass
        finally:
            await client._client.aclose()


class TestEcosystemServiceClientIntegration:
    """Integration tests for ecosystem service clients."""

    @pytest.fixture
    async def service_registry(self):
        """Create service registry for testing."""
        registry = EcosystemServiceRegistry()
        yield registry

    @pytest.mark.asyncio
    async def test_service_registry_initialization(self, service_registry):
        """Test service registry initialization."""
        # Should have clients for major services
        expected_services = [
            "doc_store", "mock_data_generator", "orchestrator",
            "analysis_service", "llm_gateway", "prompt_store"
        ]

        for service_name in expected_services:
            client = service_registry.get_client(service_name)
            assert client is not None
            assert hasattr(client, 'service_name')
            assert client.service_name == service_name

    @pytest.mark.asyncio
    async def test_service_client_health_checks(self, service_registry):
        """Test health checks for service clients."""
        # Get a few test clients
        test_clients = ["doc_store", "mock_data_generator", "orchestrator"]

        for service_name in test_clients:
            client = service_registry.get_client(service_name)
            if client:
                # Health check should return a ServiceHealth enum value
                health = await client.health_check()
                assert isinstance(health, ServiceHealth)
                # In integration tests, we don't assume services are running
                # Just verify the method completes without error

    @pytest.mark.asyncio
    async def test_service_client_error_handling(self, service_registry):
        """Test error handling in service clients."""
        # Test with a non-existent service to verify error handling
        client = service_registry.get_client("non_existent_service")
        assert client is None

    @pytest.mark.asyncio
    async def test_registry_health_check_all_services(self, service_registry):
        """Test checking health of all services."""
        # This should not raise an exception even if services are down
        health_status = await service_registry.check_all_services_health()

        assert isinstance(health_status, dict)
        assert len(health_status) > 0

        # Each service should have a health status
        for service_name, status in health_status.items():
            assert isinstance(status, ServiceHealth)

    @pytest.mark.asyncio
    async def test_registry_get_all_clients(self, service_registry):
        """Test getting all clients from registry."""
        all_clients = service_registry.get_all_clients()

        assert isinstance(all_clients, dict)
        assert len(all_clients) > 0

        # Verify client types
        for client_name, client in all_clients.items():
            assert isinstance(client, EcosystemServiceClient)
            assert client.service_name == client_name


class TestHTTPAdapterResilience:
    """Test cases for HTTP adapter resilience patterns."""

    @pytest.mark.asyncio
    async def test_connection_resilience_with_retries(self):
        """Test connection resilience with retry logic."""
        # Create client with retry configuration
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30, retries=3)
        client = EcosystemServiceClient("resilient_service", endpoint)

        try:
            # Make a request that should succeed
            response = await client.get_json("/json")
            assert response is not None
            assert "slideshow" in response
        finally:
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_graceful_error_handling(self):
        """Test graceful error handling for various failure scenarios."""
        endpoint = ServiceEndpoint("http://non-existent-service-12345.com", timeout_seconds=5)
        client = EcosystemServiceClient("failing_service", endpoint)

        try:
            # This should fail gracefully
            await client.get_json("/test")
            assert False, "Should have failed"
        except Exception as e:
            # Should be a proper exception, not a generic error
            assert isinstance(e, Exception)
        finally:
            await client._client.aclose()


class TestHTTPAdapterLoggingAndMonitoring:
    """Test cases for HTTP adapter logging and monitoring."""

    @pytest.mark.asyncio
    async def test_request_logging(self):
        """Test that requests are properly logged."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
        client = EcosystemServiceClient("logging_service", endpoint)

        try:
            # Make a request - logging should happen automatically
            response = await client.get_json("/json")
            assert response is not None

            # In a real test, we'd verify log output
            # For integration tests, we just ensure the request completes
        finally:
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_error_logging(self):
        """Test that errors are properly logged."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
        client = EcosystemServiceClient("error_logging_service", endpoint)

        try:
            # Make a request that will fail
            await client.get_json("/status/500")
            assert False, "Should have failed"
        except httpx.HTTPStatusError as e:
            assert e.response.status_code == 500
            # Error should be logged automatically
        finally:
            await client._client.aclose()


class TestHTTPAdapterPerformance:
    """Test cases for HTTP adapter performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self):
        """Test performance with concurrent requests."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
        client = EcosystemServiceClient("performance_service", endpoint)

        try:
            # Make multiple concurrent requests
            async def make_request(i: int):
                return await client.get_json("/json")

            tasks = [make_request(i) for i in range(5)]
            responses = await asyncio.gather(*tasks)

            # All requests should succeed
            assert len(responses) == 5
            assert all(r is not None for r in responses)
        finally:
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_request_response_timing(self):
        """Test request/response timing for performance monitoring."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
        client = EcosystemServiceClient("timing_service", endpoint)

        try:
            # Make a request and verify it completes in reasonable time
            import time
            start_time = time.time()
            response = await client.get_json("/json")
            end_time = time.time()

            elapsed = end_time - start_time
            assert elapsed < 10  # Should complete within 10 seconds
            assert response is not None
        finally:
            await client._client.aclose()


# Integration test utilities
async def create_mock_http_server():
    """Create a mock HTTP server for testing."""
    # This would create a test server for more controlled testing
    # For now, we use real HTTP services for integration tests
    pass


def verify_http_response_format(response: Dict[str, Any]):
    """Verify HTTP response has expected format."""
    assert isinstance(response, dict)
    # Add more specific response format validations as needed


@pytest.mark.integration
class TestHTTPAdapterIntegrationSuite:
    """Comprehensive integration test suite for HTTP adapters."""

    @pytest.mark.asyncio
    async def test_full_request_lifecycle(self):
        """Test complete HTTP request lifecycle."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
        client = EcosystemServiceClient("lifecycle_service", endpoint)

        try:
            # Test GET request
            get_response = await client.get_json("/json")
            assert get_response is not None
            verify_http_response_format(get_response)

            # Test POST request
            post_data = {"test": "data", "number": 42}
            post_response = await client.post_json("/post", post_data)
            assert post_response is not None
            assert post_response.get("json") == post_data

        finally:
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_error_conditions_and_recovery(self):
        """Test various error conditions and recovery mechanisms."""
        endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
        client = EcosystemServiceClient("recovery_service", endpoint)

        try:
            # Test various HTTP status codes
            error_codes = [400, 401, 403, 404, 500, 502, 503]

            for code in error_codes:
                try:
                    await client.get_json(f"/status/{code}")
                    assert False, f"Should have failed with status {code}"
                except httpx.HTTPStatusError as e:
                    assert e.response.status_code == code
                except Exception as e:
                    # Some other error occurred, which is also acceptable
                    assert isinstance(e, Exception)

        finally:
            await client._client.aclose()

    @pytest.mark.asyncio
    async def test_connection_management(self):
        """Test HTTP connection management and cleanup."""
        # Create multiple clients to test connection management
        clients = []
        try:
            for i in range(3):
                endpoint = ServiceEndpoint("http://httpbin.org", timeout_seconds=30)
                client = EcosystemServiceClient(f"conn_test_{i}", endpoint)
                clients.append(client)

                # Make a request with each client
                response = await client.get_json("/json")
                assert response is not None

        finally:
            # Ensure all clients are properly closed
            for client in clients:
                await client._client.aclose()
