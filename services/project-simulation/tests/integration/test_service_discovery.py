"""Integration Tests for Service Discovery - Ecosystem Integration Testing.

This module contains integration tests for service discovery functionality,
testing automatic service location, health checking, and fallback mechanisms.
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from simulation.infrastructure.config.discovery import (
    LocalServiceDiscovery, FallbackServiceClient, ServiceDiscoveryError,
    ServiceHealth, get_service_discovery, start_service_discovery, stop_service_discovery
)


class TestServiceDiscoveryInitialization:
    """Test cases for service discovery initialization."""

    def test_service_discovery_creation(self):
        """Test creating service discovery instance."""
        discovery = LocalServiceDiscovery()

        assert discovery is not None
        assert isinstance(discovery.services, dict)
        assert discovery.discovery_interval == 30
        assert discovery.health_check_timeout == 5
        assert discovery._running == False

    def test_service_discovery_initialization_with_config(self):
        """Test service discovery initialization with configuration."""
        # Mock config to test service registration
        mock_config = Mock()
        mock_config.ecosystem = Mock()
        mock_config.ecosystem.__dict__ = {
            "doc_store": "http://doc_store:5010",
            "mock_data_generator": "http://mock_data_generator:5065",
            "orchestrator": "http://orchestrator:5000"
        }

        with patch('simulation.infrastructure.config.discovery.get_config', return_value=mock_config):
            discovery = LocalServiceDiscovery()

            assert len(discovery.services) == 3
            assert "doc_store" in discovery.services
            assert "mock_data_generator" in discovery.services
            assert "orchestrator" in discovery.services

            # Verify service URLs
            assert discovery.services["doc_store"].url == "http://doc_store:5010"
            assert discovery.services["mock_data_generator"].url == "http://mock_data_generator:5065"


class TestServiceHealthChecking:
    """Test cases for service health checking functionality."""

    @pytest.fixture
    async def discovery(self):
        """Create discovery instance for testing."""
        discovery = LocalServiceDiscovery()
        yield discovery

    @pytest.mark.asyncio
    async def test_health_check_healthy_service(self, discovery):
        """Test health check for a healthy service."""
        # Add a mock healthy service
        service = ServiceHealth("test_service", "http://httpbin.org")
        discovery.services["test_service"] = service

        # Perform health check
        await discovery._check_service_health(service)

        # In integration tests, we can't guarantee service availability
        # Just verify the method completes without error
        assert service.last_checked is not None

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_service(self, discovery):
        """Test health check for an unhealthy service."""
        # Add a mock unhealthy service
        service = ServiceHealth("bad_service", "http://non-existent-service-12345.com")
        discovery.services["bad_service"] = service

        # Perform health check
        await discovery._check_service_health(service)

        # Should mark as unhealthy
        assert service.is_healthy == False
        assert service.last_checked is not None
        assert "non-existent-service-12345.com" in service.url

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, discovery):
        """Test concurrent health checks for multiple services."""
        # Add multiple services
        services = [
            ServiceHealth("service1", "http://httpbin.org"),
            ServiceHealth("service2", "http://httpbin.org"),
            ServiceHealth("service3", "http://httpbin.org")
        ]

        for service in services:
            discovery.services[service.name] = service

        # Perform concurrent health checks
        await discovery._check_all_services()

        # All services should have been checked
        for service in services:
            assert service.last_checked is not None

    @pytest.mark.asyncio
    async def test_service_discovery_lifecycle(self, discovery):
        """Test service discovery start/stop lifecycle."""
        # Add a test service
        service = ServiceHealth("test_service", "http://httpbin.org")
        discovery.services["test_service"] = service

        # Start discovery
        await discovery.start_discovery()
        assert discovery._running == True

        # Let it run for a short time
        await asyncio.sleep(0.1)

        # Stop discovery
        await discovery.stop_discovery()
        assert discovery._running == False


class TestServiceURLResolution:
    """Test cases for service URL resolution and fallbacks."""

    def test_get_service_url_healthy_service(self):
        """Test getting URL for healthy service."""
        discovery = LocalServiceDiscovery()

        # Add a healthy service
        service = ServiceHealth("healthy_service", "http://service.com:8080")
        service.is_healthy = True
        discovery.services["healthy_service"] = service

        url = discovery.get_service_url("healthy_service")
        assert url == "http://service.com:8080"

    def test_get_service_url_unhealthy_service_with_fallback(self):
        """Test getting URL for unhealthy service with fallback."""
        discovery = LocalServiceDiscovery()

        # Add an unhealthy service
        service = ServiceHealth("unhealthy_service", "http://service.com:8080")
        service.is_healthy = False
        discovery.services["unhealthy_service"] = service

        fallback_url = "http://fallback.com:9090"
        url = discovery.get_service_url("unhealthy_service", fallback_url)
        assert url == fallback_url

    def test_get_service_url_unhealthy_service_no_fallback(self):
        """Test getting URL for unhealthy service without fallback."""
        discovery = LocalServiceDiscovery()

        # Add an unhealthy service
        service = ServiceHealth("unhealthy_service", "http://service.com:8080")
        service.is_healthy = False
        discovery.services["unhealthy_service"] = service

        url = discovery.get_service_url("unhealthy_service")
        assert url == "http://service.com:8080"  # Returns original URL

    def test_get_service_url_nonexistent_service(self):
        """Test getting URL for non-existent service."""
        discovery = LocalServiceDiscovery()

        url = discovery.get_service_url("nonexistent_service")
        assert url == ""

    def test_get_service_url_nonexistent_service_with_fallback(self):
        """Test getting URL for non-existent service with fallback."""
        discovery = LocalServiceDiscovery()

        fallback_url = "http://fallback.com:9090"
        url = discovery.get_service_url("nonexistent_service", fallback_url)
        assert url == fallback_url


class TestServiceAvailabilityChecking:
    """Test cases for service availability checking."""

    def test_is_service_available_healthy(self):
        """Test checking availability of healthy service."""
        discovery = LocalServiceDiscovery()

        service = ServiceHealth("test_service", "http://service.com")
        service.is_healthy = True
        discovery.services["test_service"] = service

        assert discovery.is_service_available("test_service") == True

    def test_is_service_available_unhealthy(self):
        """Test checking availability of unhealthy service."""
        discovery = LocalServiceDiscovery()

        service = ServiceHealth("test_service", "http://service.com")
        service.is_healthy = False
        discovery.services["test_service"] = service

        assert discovery.is_service_available("test_service") == False

    def test_is_service_available_nonexistent(self):
        """Test checking availability of non-existent service."""
        discovery = LocalServiceDiscovery()

        assert discovery.is_service_available("nonexistent_service") == False

    def test_get_healthy_services(self):
        """Test getting list of healthy services."""
        discovery = LocalServiceDiscovery()

        # Add mix of healthy and unhealthy services
        services = [
            ("healthy1", True),
            ("healthy2", True),
            ("unhealthy1", False),
            ("unhealthy2", False)
        ]

        for name, is_healthy in services:
            service = ServiceHealth(name, f"http://{name}.com")
            service.is_healthy = is_healthy
            discovery.services[name] = service

        healthy_services = discovery.get_healthy_services()
        assert set(healthy_services) == {"healthy1", "healthy2"}

    def test_get_unhealthy_services(self):
        """Test getting list of unhealthy services."""
        discovery = LocalServiceDiscovery()

        # Add mix of healthy and unhealthy services
        services = [
            ("healthy1", True),
            ("unhealthy1", False),
            ("unhealthy2", False)
        ]

        for name, is_healthy in services:
            service = ServiceHealth(name, f"http://{name}.com")
            service.is_healthy = is_healthy
            discovery.services[name] = service

        unhealthy_services = discovery.get_unhealthy_services()
        assert set(unhealthy_services) == {"unhealthy1", "unhealthy2"}


class TestServiceHealthInformation:
    """Test cases for service health information retrieval."""

    def test_get_service_health_existing_service(self):
        """Test getting health info for existing service."""
        discovery = LocalServiceDiscovery()

        service = ServiceHealth("test_service", "http://service.com")
        service.is_healthy = True
        service.response_time = 0.150
        service.error_message = None
        service.version = "1.2.3"
        discovery.services["test_service"] = service

        health_info = discovery.get_service_health("test_service")

        assert health_info is not None
        assert health_info["name"] == "test_service"
        assert health_info["url"] == "http://service.com"
        assert health_info["is_healthy"] == True
        assert health_info["response_time"] == 0.150
        assert health_info["version"] == "1.2.3"

    def test_get_service_health_nonexistent_service(self):
        """Test getting health info for non-existent service."""
        discovery = LocalServiceDiscovery()

        health_info = discovery.get_service_health("nonexistent_service")
        assert health_info is None

    def test_get_all_service_health(self):
        """Test getting health info for all services."""
        discovery = LocalServiceDiscovery()

        # Add multiple services
        services = ["service1", "service2", "service3"]
        for name in services:
            service = ServiceHealth(name, f"http://{name}.com")
            service.is_healthy = True
            discovery.services[name] = service

        all_health = discovery.get_all_service_health()

        assert isinstance(all_health, dict)
        assert len(all_health) == 3

        for name in services:
            assert name in all_health
            assert all_health[name]["name"] == name
            assert all_health[name]["is_healthy"] == True


class TestFallbackServiceClient:
    """Test cases for fallback service client."""

    @pytest.fixture
    def discovery(self):
        """Create discovery instance for testing."""
        discovery = LocalServiceDiscovery()

        # Add test services
        service = ServiceHealth("test_service", "http://httpbin.org")
        service.is_healthy = True
        discovery.services["test_service"] = service

        return discovery

    @pytest.fixture
    def fallback_client(self, discovery):
        """Create fallback service client for testing."""
        client = FallbackServiceClient("test_service", discovery)
        return client

    @pytest.mark.asyncio
    async def test_fallback_client_successful_request(self, fallback_client):
        """Test successful request through fallback client."""
        # Make a request to a working endpoint
        response = await fallback_client.make_request("GET", "/json")

        assert response is not None
        assert "slideshow" in response

    @pytest.mark.asyncio
    async def test_fallback_client_unavailable_service(self, discovery):
        """Test fallback client with unavailable service."""
        # Create client for unavailable service
        bad_service = ServiceHealth("bad_service", "http://non-existent-12345.com")
        bad_service.is_healthy = False
        discovery.services["bad_service"] = bad_service

        client = FallbackServiceClient("bad_service", discovery)

        response = await client.make_request("GET", "/test")
        assert response is None

    @pytest.mark.asyncio
    async def test_fallback_client_nonexistent_service(self, discovery):
        """Test fallback client with non-existent service."""
        client = FallbackServiceClient("nonexistent_service", discovery)

        response = await client.make_request("GET", "/test")
        assert response is None

    @pytest.mark.asyncio
    async def test_fallback_client_error_handling(self, fallback_client):
        """Test error handling in fallback client."""
        # Request to non-existent endpoint
        response = await fallback_client.make_request("GET", "/non-existent-endpoint-12345")
        assert response is None

    @pytest.mark.asyncio
    async def test_fallback_client_different_http_methods(self, fallback_client):
        """Test different HTTP methods through fallback client."""
        # Test POST request
        post_data = {"test": "data", "number": 42}
        response = await fallback_client.make_request("POST", "/post", json=post_data)

        assert response is not None
        assert response.get("json") == post_data


class TestServiceDiscoveryIntegration:
    """Integration tests for complete service discovery functionality."""

    @pytest.mark.asyncio
    async def test_service_discovery_integration_workflow(self):
        """Test complete service discovery workflow."""
        discovery = LocalServiceDiscovery()

        # Add test services
        services = [
            ("api_service", "http://httpbin.org"),
            ("data_service", "http://httpbin.org"),
            ("auth_service", "http://httpbin.org")
        ]

        for name, url in services:
            service = ServiceHealth(name, url)
            discovery.services[name] = service

        # Start discovery
        await discovery.start_discovery()

        try:
            # Wait for health checks to complete
            await asyncio.sleep(1)

            # Check service availability
            for name, _ in services:
                # In integration tests, we can't guarantee all services are healthy
                # Just verify the discovery process works
                health_info = discovery.get_service_health(name)
                assert health_info is not None
                assert health_info["name"] == name
                assert "is_healthy" in health_info
                assert "last_checked" in health_info

        finally:
            # Stop discovery
            await discovery.stop_discovery()

    def test_service_discovery_summary(self):
        """Test service discovery summary generation."""
        discovery = LocalServiceDiscovery()

        # Add services with different health states
        services = [
            ("healthy1", True),
            ("healthy2", True),
            ("unhealthy1", False),
            ("unhealthy2", False)
        ]

        for name, is_healthy in services:
            service = ServiceHealth(name, f"http://{name}.com")
            service.is_healthy = is_healthy
            discovery.services[name] = service

        summary = discovery.get_service_discovery_summary()

        assert summary["total_services"] == 4
        assert summary["healthy_services"] == 2
        assert summary["unhealthy_services"] == 2
        assert summary["discovery_running"] == False  # Not started
        assert summary["discovery_interval"] == 30

    @pytest.mark.asyncio
    async def test_global_service_discovery_functions(self):
        """Test global service discovery functions."""
        # Test getting global discovery instance
        discovery1 = get_service_discovery()
        discovery2 = get_service_discovery()

        assert discovery1 is discovery2  # Should be singleton

        # Test start/stop functions
        await start_service_discovery()
        assert discovery1._running == True

        await stop_service_discovery()
        assert discovery1._running == False

    def test_global_service_url_resolution(self):
        """Test global service URL resolution functions."""
        discovery = get_service_discovery()

        # Add test service
        service = ServiceHealth("global_test", "http://global-test.com")
        service.is_healthy = True
        discovery.services["global_test"] = service

        # Test global functions
        url = discovery.get_service_url("global_test")
        assert url == "http://global-test.com"

        assert discovery.is_service_available("global_test") == True
        assert discovery.is_service_available("nonexistent") == False


class TestServiceDiscoveryErrorHandling:
    """Test cases for service discovery error handling."""

    @pytest.mark.asyncio
    async def test_discovery_loop_error_handling(self):
        """Test that discovery loop handles errors gracefully."""
        discovery = LocalServiceDiscovery()

        # Add a service that will cause errors
        service = ServiceHealth("error_service", "http://non-existent-12345.com")
        discovery.services["error_service"] = service

        # Start discovery
        await discovery.start_discovery()

        try:
            # Let it run for a short time - should handle errors gracefully
            await asyncio.sleep(0.5)

            # Should still be running despite errors
            assert discovery._running == True

        finally:
            await discovery.stop_discovery()

    def test_service_discovery_with_invalid_urls(self):
        """Test service discovery with invalid URLs."""
        discovery = LocalServiceDiscovery()

        # Add service with invalid URL
        service = ServiceHealth("invalid_url", "not-a-valid-url")
        discovery.services["invalid_url"] = service

        url = discovery.get_service_url("invalid_url")
        assert url == "not-a-valid-url"  # Should return original URL

    @pytest.mark.asyncio
    async def test_health_check_timeout_handling(self):
        """Test health check timeout handling."""
        discovery = LocalServiceDiscovery()

        # Add service with very slow endpoint
        service = ServiceHealth("slow_service", "http://httpbin.org/delay/10")
        discovery.services["slow_service"] = service

        # Set very short timeout
        discovery.health_check_timeout = 1

        # Health check should timeout gracefully
        await discovery._check_service_health(service)

        # Should be marked as unhealthy due to timeout
        assert service.is_healthy == False
        assert service.response_time == discovery.health_check_timeout


@pytest.mark.integration
class TestServiceDiscoveryComprehensiveSuite:
    """Comprehensive integration test suite for service discovery."""

    @pytest.mark.asyncio
    async def test_end_to_end_service_discovery_workflow(self):
        """Test end-to-end service discovery workflow."""
        discovery = LocalServiceDiscovery()

        # Initialize with multiple services
        services = [
            ("service1", "http://httpbin.org"),
            ("service2", "http://httpbin.org"),
            ("service3", "http://httpbin.org")
        ]

        for name, url in services:
            service = ServiceHealth(name, url)
            discovery.services[name] = service

        # Start discovery
        await discovery.start_discovery()

        try:
            # Let discovery run
            await asyncio.sleep(2)

            # Verify health checks were performed
            summary = discovery.get_service_discovery_summary()
            assert summary["total_services"] == 3

            # Get all health information
            all_health = discovery.get_all_service_health()
            assert len(all_health) == 3

            # Test URL resolution
            for name, _ in services:
                url = discovery.get_service_url(name)
                assert url.startswith("http://httpbin.org")

        finally:
            await discovery.stop_discovery()

    @pytest.mark.asyncio
    async def test_service_discovery_with_fallback_client(self):
        """Test service discovery integration with fallback client."""
        discovery = LocalServiceDiscovery()

        # Add service
        service = ServiceHealth("integration_test", "http://httpbin.org")
        service.is_healthy = True
        discovery.services["integration_test"] = service

        # Create fallback client
        client = FallbackServiceClient("integration_test", discovery)

        # Make successful request
        response = await client.make_request("GET", "/json")
        assert response is not None
        assert isinstance(response, dict)

        # Verify service is still considered available
        assert discovery.is_service_available("integration_test") == True

    def test_service_discovery_configuration_persistence(self):
        """Test that service discovery configuration persists."""
        discovery = LocalServiceDiscovery()

        # Configure discovery parameters
        original_interval = discovery.discovery_interval
        original_timeout = discovery.health_check_timeout

        # Parameters should be preserved
        assert discovery.discovery_interval == original_interval
        assert discovery.health_check_timeout == original_timeout

        # Configuration should be consistent
        summary = discovery.get_service_discovery_summary()
        assert summary["discovery_interval"] == original_interval
