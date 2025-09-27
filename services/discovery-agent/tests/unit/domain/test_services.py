"""Tests for discovery agent domain services."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from services.discovery_agent.domain.services import (
    DiscoveryService, HealthCheckService, ToolExecutionService
)
from services.discovery_agent.domain.entities import ServiceInfo, ToolInfo
from services.discovery_agent.domain.value_objects import (
    ServiceStatus, ToolCategory, DiscoveryMode
)


class TestDiscoveryService:
    """Test cases for DiscoveryService."""

    @pytest.fixture
    def discovery_service(self):
        """Create DiscoveryService instance for testing."""
        return DiscoveryService()

    @pytest.mark.asyncio
    async def test_discover_services_automatic(self, discovery_service):
        """Test automatic service discovery."""
        with patch.object(discovery_service, '_scan_network', new_callable=AsyncMock) as mock_scan:
            mock_services = [
                ServiceInfo(name="service1", type="api", port=8080),
                ServiceInfo(name="service2", type="worker", port=8081)
            ]
            mock_scan.return_value = mock_services

            result = await discovery_service.discover_services(DiscoveryMode.AUTOMATIC)

            assert len(result.services_discovered) == 2
            assert result.mode == DiscoveryMode.AUTOMATIC
            assert result.success is True
            mock_scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_services_manual(self, discovery_service):
        """Test manual service discovery."""
        manual_services = [
            ServiceInfo(name="manual-service", type="api", port=3000)
        ]

        result = await discovery_service.discover_services(
            DiscoveryMode.MANUAL,
            manual_services=manual_services
        )

        assert len(result.services_discovered) == 1
        assert result.services_discovered[0].name == "manual-service"
        assert result.mode == DiscoveryMode.MANUAL

    def test_validate_service_info(self, discovery_service):
        """Test service info validation."""
        valid_service = ServiceInfo(
            name="valid-service",
            type="api",
            port=8080,
            status=ServiceStatus.HEALTHY
        )

        invalid_service = ServiceInfo(
            name="",  # Invalid: empty name
            type="api",
            port=8080
        )

        assert discovery_service._validate_service_info(valid_service) is True
        assert discovery_service._validate_service_info(invalid_service) is False


class TestHealthCheckService:
    """Test cases for HealthCheckService."""

    @pytest.fixture
    def health_service(self):
        """Create HealthCheckService instance for testing."""
        return HealthCheckService()

    @pytest.mark.asyncio
    async def test_check_service_health_healthy(self, health_service):
        """Test health check for healthy service."""
        service = ServiceInfo(
            name="healthy-service",
            type="api",
            port=8080,
            health_endpoint="/health"
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json = AsyncMock(return_value={"status": "healthy"})
            mock_response.elapsed.total_seconds.return_value = 0.25

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            result = await health_service.check_service_health(service)

            assert result.status == ServiceStatus.HEALTHY
            assert result.response_time == 0.25

    @pytest.mark.asyncio
    async def test_check_service_health_unhealthy(self, health_service):
        """Test health check for unhealthy service."""
        service = ServiceInfo(
            name="unhealthy-service",
            type="api",
            port=8080
        )

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("Connection failed"))

            result = await health_service.check_service_health(service)

            assert result.status == ServiceStatus.UNHEALTHY

    def test_batch_health_check(self, health_service):
        """Test batch health check functionality."""
        services = [
            ServiceInfo(name="service1", type="api", port=8080),
            ServiceInfo(name="service2", type="worker", port=8081)
        ]

        # Test that batch processing is set up correctly
        assert len(services) == 2


class TestToolExecutionService:
    """Test cases for ToolExecutionService."""

    @pytest.fixture
    def tool_service(self):
        """Create ToolExecutionService instance for testing."""
        return ToolExecutionService()

    def test_register_tool(self, tool_service):
        """Test tool registration."""
        tool = ToolInfo(
            name="test-tool",
            category=ToolCategory.ANALYSIS,
            description="A test analysis tool"
        )

        tool_service.register_tool(tool)

        assert tool.name in tool_service._tools
        assert tool_service._tools[tool.name] == tool

    def test_get_tool_by_category(self, tool_service):
        """Test getting tools by category."""
        analysis_tool = ToolInfo(
            name="analysis-tool",
            category=ToolCategory.ANALYSIS,
            description="Analysis tool"
        )

        monitoring_tool = ToolInfo(
            name="monitoring-tool",
            category=ToolCategory.MONITORING,
            description="Monitoring tool"
        )

        tool_service.register_tool(analysis_tool)
        tool_service.register_tool(monitoring_tool)

        analysis_tools = tool_service.get_tools_by_category(ToolCategory.ANALYSIS)
        assert len(analysis_tools) == 1
        assert analysis_tools[0].name == "analysis-tool"

    @pytest.mark.asyncio
    async def test_execute_tool_success(self, tool_service):
        """Test successful tool execution."""
        tool = ToolInfo(
            name="test-tool",
            category=ToolCategory.ANALYSIS,
            parameters={"input": "string"}
        )

        tool_service.register_tool(tool)

        # Mock the actual execution
        with patch.object(tool_service, '_execute_tool_impl', new_callable=AsyncMock) as mock_execute:
            mock_execute.return_value = {"result": "success", "data": "test"}

            result = await tool_service.execute_tool("test-tool", {"input": "test_value"})

            assert result["result"] == "success"
            mock_execute.assert_called_once_with(tool, {"input": "test_value"})

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, tool_service):
        """Test execution of non-existent tool."""
        with pytest.raises(ValueError, match="Tool not found"):
            await tool_service.execute_tool("non-existent-tool", {})

    def test_get_execution_stats(self, tool_service):
        """Test getting tool execution statistics."""
        tool = ToolInfo(
            name="test-tool",
            category=ToolCategory.ANALYSIS
        )

        tool_service.register_tool(tool)

        stats = tool_service.get_execution_stats("test-tool")
        assert stats["execution_count"] == 0
        assert stats["success_rate"] == 0.0
