"""
Integration tests for service discovery workflows.

Tests the complete discovery workflow from spec to service entity.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch


@pytest.mark.integration
@pytest.mark.discovery
class TestServiceDiscoveryWorkflow:
    """Test complete service discovery workflow."""
    
    @pytest.mark.asyncio
    async def test_discover_service_from_url(self, simple_openapi_spec, mock_http_client):
        """Test discovering a service from OpenAPI URL."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        # Setup mock
        mock_http_client.get.return_value = Mock(
            status_code=200,
            json=lambda: simple_openapi_spec
        )
        
        # Create discovery service with mock
        discovery_service = DiscoveryService(http_client=mock_http_client)
        
        # Create discovery spec
        spec = DiscoverySpec(url="http://test-service:8000/openapi.json")
        
        # Perform discovery
        result = await discovery_service.discover(spec, service_name="test-service")
        
        assert result.success is True
        assert result.service is not None
        assert result.service.name == "test-service"
        assert result.service.endpoint_count >= 2  # /health and /api/v1/items
    
    @pytest.mark.asyncio
    async def test_discover_service_from_content(self, simple_openapi_spec):
        """Test discovering a service from inline OpenAPI content."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        discovery_service = DiscoveryService()
        
        spec = DiscoverySpec(content=simple_openapi_spec)
        result = await discovery_service.discover(spec, service_name="test-service")
        
        assert result.success is True
        assert result.service is not None
        assert len(result.service.endpoints) >= 2
    
    @pytest.mark.asyncio
    async def test_discover_service_invalid_url(self):
        """Test discovery with invalid URL."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        from domain.exceptions import DiscoveryError
        
        discovery_service = DiscoveryService()
        
        spec = DiscoverySpec(url="http://nonexistent-service:8000/openapi.json")
        
        # Should handle error gracefully
        result = await discovery_service.discover(spec, service_name="nonexistent")
        
        assert result.success is False
        assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_discover_service_malformed_spec(self):
        """Test discovery with malformed OpenAPI spec."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        discovery_service = DiscoveryService()
        
        malformed_spec = {
            "invalid": "spec",
            "missing": "required fields"
        }
        
        # Should fail validation
        with pytest.raises(Exception):  # InvalidOpenApiSpecError
            spec = DiscoverySpec(content=malformed_spec)
    
    @pytest.mark.asyncio
    async def test_discover_multiple_services(self, simple_openapi_spec, complex_openapi_spec):
        """Test discovering multiple services."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        discovery_service = DiscoveryService()
        
        # Discover first service
        spec1 = DiscoverySpec(content=simple_openapi_spec)
        result1 = await discovery_service.discover(spec1, service_name="service-1")
        
        # Discover second service
        spec2 = DiscoverySpec(content=complex_openapi_spec)
        result2 = await discovery_service.discover(spec2, service_name="service-2")
        
        assert result1.success is True
        assert result2.success is True
        assert result1.service.name != result2.service.name


@pytest.mark.integration
@pytest.mark.discovery
class TestOpenApiParsing:
    """Test OpenAPI specification parsing."""
    
    @pytest.mark.asyncio
    async def test_parse_openapi_3_0(self, simple_openapi_spec):
        """Test parsing OpenAPI 3.0 specification."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        discovery_service = DiscoveryService()
        spec = DiscoverySpec(content=simple_openapi_spec)
        
        result = await discovery_service.discover(spec, service_name="test")
        
        assert result.success is True
        assert result.service.version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_parse_endpoints_with_parameters(self, complex_openapi_spec):
        """Test parsing endpoints with parameters."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        discovery_service = DiscoveryService()
        spec = DiscoverySpec(content=complex_openapi_spec)
        
        result = await discovery_service.discover(spec, service_name="test")
        
        # Find endpoint with parameters
        analyze_endpoint = result.service.find_endpoint("/api/v1/analyze", "POST")
        assert analyze_endpoint is not None
        assert len(analyze_endpoint.parameters) > 0
    
    @pytest.mark.asyncio
    async def test_parse_endpoints_with_request_body(self, complex_openapi_spec):
        """Test parsing endpoints with request body."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        discovery_service = DiscoveryService()
        spec = DiscoverySpec(content=complex_openapi_spec)
        
        result = await discovery_service.discover(spec, service_name="test")
        
        analyze_endpoint = result.service.find_endpoint("/api/v1/analyze", "POST")
        assert analyze_endpoint is not None
        # Should have parsed request body information
    
    @pytest.mark.asyncio
    async def test_parse_endpoint_tags(self, simple_openapi_spec):
        """Test parsing endpoint tags."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        discovery_service = DiscoveryService()
        spec = DiscoverySpec(content=simple_openapi_spec)
        
        result = await discovery_service.discover(spec, service_name="test")
        
        # Check that tags were parsed
        health_endpoint = result.service.find_endpoint("/health", "GET")
        assert health_endpoint is not None
        assert "monitoring" in health_endpoint.tags


@pytest.mark.integration
@pytest.mark.discovery
class TestDiscoveryErrorHandling:
    """Test error handling in discovery workflows."""
    
    @pytest.mark.asyncio
    async def test_network_timeout(self):
        """Test handling network timeout."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        import asyncio
        
        # Mock HTTP client that times out
        mock_client = AsyncMock()
        mock_client.get.side_effect = asyncio.TimeoutError()
        
        discovery_service = DiscoveryService(http_client=mock_client)
        spec = DiscoverySpec(url="http://slow-service:8000/openapi.json")
        
        result = await discovery_service.discover(spec, service_name="slow-service")
        
        assert result.success is False
        assert "timeout" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test handling connection error."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        import aiohttp
        
        # Mock HTTP client that fails to connect
        mock_client = AsyncMock()
        mock_client.get.side_effect = aiohttp.ClientError("Connection refused")
        
        discovery_service = DiscoveryService(http_client=mock_client)
        spec = DiscoverySpec(url="http://down-service:8000/openapi.json")
        
        result = await discovery_service.discover(spec, service_name="down-service")
        
        assert result.success is False
        assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_http_404_error(self):
        """Test handling HTTP 404 error."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        # Mock HTTP client that returns 404
        mock_client = AsyncMock()
        mock_client.get.return_value = Mock(status_code=404)
        
        discovery_service = DiscoveryService(http_client=mock_client)
        spec = DiscoverySpec(url="http://service:8000/nonexistent.json")
        
        result = await discovery_service.discover(spec, service_name="test")
        
        assert result.success is False
        assert "404" in result.error_message or "not found" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_json_response(self):
        """Test handling invalid JSON response."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        
        # Mock HTTP client that returns invalid JSON
        mock_client = AsyncMock()
        mock_response = Mock(status_code=200)
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.get.return_value = mock_response
        
        discovery_service = DiscoveryService(http_client=mock_client)
        spec = DiscoverySpec(url="http://service:8000/openapi.json")
        
        result = await discovery_service.discover(spec, service_name="test")
        
        assert result.success is False
        assert result.error_message is not None


@pytest.mark.integration
@pytest.mark.discovery
class TestDiscoveryPerformance:
    """Test discovery performance."""
    
    @pytest.mark.asyncio
    async def test_discovery_completes_quickly(self, simple_openapi_spec):
        """Test that discovery completes in reasonable time."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        import time
        
        discovery_service = DiscoveryService()
        spec = DiscoverySpec(content=simple_openapi_spec)
        
        start_time = time.time()
        result = await discovery_service.discover(spec, service_name="test")
        duration = time.time() - start_time
        
        assert result.success is True
        assert duration < 1.0  # Should complete in less than 1 second
    
    @pytest.mark.asyncio
    async def test_multiple_discoveries_perform_well(self, simple_openapi_spec):
        """Test that multiple discoveries perform well."""
        from domain.services.discovery_service import DiscoveryService
        from domain.value_objects import DiscoverySpec
        import time
        
        discovery_service = DiscoveryService()
        
        start_time = time.time()
        
        for i in range(10):
            spec = DiscoverySpec(content=simple_openapi_spec)
            result = await discovery_service.discover(spec, service_name=f"test-{i}")
            assert result.success is True
        
        duration = time.time() - start_time
        
        # 10 discoveries should complete in less than 5 seconds
        assert duration < 5.0
        
        # Average time per discovery
        avg_duration = duration / 10
        assert avg_duration < 0.5  # Less than 500ms per discovery

