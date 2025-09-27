"""Tests for discovery agent domain entities."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock

from services.discovery_agent.domain.entities import (
    ServiceInfo, ToolInfo, DiscoveryResult, ServiceHealth
)
from services.discovery_agent.domain.value_objects import (
    ServiceStatus, ToolCategory, DiscoveryMode
)


class TestServiceInfo:
    """Test cases for ServiceInfo entity."""

    def test_service_info_creation(self):
        """Test basic ServiceInfo creation."""
        service = ServiceInfo(
            name="test-service",
            type="api",
            port=8080,
            status=ServiceStatus.HEALTHY
        )

        assert service.name == "test-service"
        assert service.type == "api"
        assert service.port == 8080
        assert service.status == ServiceStatus.HEALTHY
        assert isinstance(service.discovered_at, datetime)
        assert service.last_health_check is None

    def test_service_info_with_metadata(self):
        """Test ServiceInfo with metadata."""
        metadata = {"version": "1.0.0", "environment": "test"}
        service = ServiceInfo(
            name="test-service",
            type="api",
            port=8080,
            metadata=metadata
        )

        assert service.metadata == metadata
        assert service.get_metadata("version") == "1.0.0"
        assert service.get_metadata("nonexistent", "default") == "default"

    def test_service_info_health_update(self):
        """Test updating service health."""
        service = ServiceInfo(
            name="test-service",
            type="api",
            port=8080,
            status=ServiceStatus.UNKNOWN
        )

        service.update_health(ServiceStatus.HEALTHY, response_time=0.5)
        assert service.status == ServiceStatus.HEALTHY
        assert service.response_time == 0.5
        assert service.last_health_check is not None

    def test_service_info_to_dict(self):
        """Test ServiceInfo serialization."""
        service = ServiceInfo(
            name="test-service",
            type="api",
            port=8080,
            status=ServiceStatus.HEALTHY
        )

        data = service.to_dict()
        assert data["name"] == "test-service"
        assert data["type"] == "api"
        assert data["port"] == 8080
        assert data["status"] == "healthy"


class TestToolInfo:
    """Test cases for ToolInfo entity."""

    def test_tool_info_creation(self):
        """Test basic ToolInfo creation."""
        tool = ToolInfo(
            name="test-tool",
            category=ToolCategory.ANALYSIS,
            description="A test tool",
            parameters={"input": "string"}
        )

        assert tool.name == "test-tool"
        assert tool.category == ToolCategory.ANALYSIS
        assert tool.description == "A test tool"
        assert tool.parameters == {"input": "string"}
        assert tool.is_active is True

    def test_tool_info_validation(self):
        """Test ToolInfo parameter validation."""
        tool = ToolInfo(
            name="test-tool",
            category=ToolCategory.ANALYSIS,
            parameters={"input": "string", "optional": None}
        )

        assert tool.validate_parameters({"input": "test_value"})
        assert not tool.validate_parameters({})  # Missing required param

    def test_tool_info_execution_tracking(self):
        """Test tool execution tracking."""
        tool = ToolInfo(
            name="test-tool",
            category=ToolCategory.ANALYSIS
        )

        tool.record_execution(success=True, duration=1.5)
        assert tool.execution_count == 1
        assert tool.success_count == 1
        assert tool.average_execution_time == 1.5

        tool.record_execution(success=False, duration=2.0)
        assert tool.execution_count == 2
        assert tool.success_count == 1
        assert tool.average_execution_time == 1.75


class TestDiscoveryResult:
    """Test cases for DiscoveryResult entity."""

    def test_discovery_result_creation(self):
        """Test basic DiscoveryResult creation."""
        services = [Mock(spec=ServiceInfo)]
        tools = [Mock(spec=ToolInfo)]

        result = DiscoveryResult(
            mode=DiscoveryMode.AUTOMATIC,
            services_discovered=services,
            tools_discovered=tools,
            duration=5.5
        )

        assert result.mode == DiscoveryMode.AUTOMATIC
        assert len(result.services_discovered) == 1
        assert len(result.tools_discovered) == 1
        assert result.duration == 5.5
        assert result.success is True

    def test_discovery_result_with_errors(self):
        """Test DiscoveryResult with errors."""
        result = DiscoveryResult(
            mode=DiscoveryMode.MANUAL,
            services_discovered=[],
            tools_discovered=[],
            duration=2.0,
            errors=["Connection timeout", "Service unavailable"]
        )

        assert result.success is False
        assert len(result.errors) == 2
        assert result.error_count == 2

    def test_discovery_result_summary(self):
        """Test DiscoveryResult summary generation."""
        services = [Mock(spec=ServiceInfo) for _ in range(3)]
        tools = [Mock(spec=ToolInfo) for _ in range(5)]

        result = DiscoveryResult(
            mode=DiscoveryMode.AUTOMATIC,
            services_discovered=services,
            tools_discovered=tools,
            duration=10.0
        )

        summary = result.get_summary()
        assert summary["total_services"] == 3
        assert summary["total_tools"] == 5
        assert summary["duration"] == 10.0
        assert summary["success"] is True


class TestServiceHealth:
    """Test cases for ServiceHealth value object."""

    def test_service_health_creation(self):
        """Test basic ServiceHealth creation."""
        health = ServiceHealth(
            status=ServiceStatus.HEALTHY,
            response_time=0.25,
            last_check=datetime.now(timezone.utc)
        )

        assert health.status == ServiceStatus.HEALTHY
        assert health.response_time == 0.25
        assert health.last_check is not None

    def test_service_health_is_healthy(self):
        """Test health status checking."""
        healthy = ServiceHealth(status=ServiceStatus.HEALTHY, response_time=0.1)
        assert healthy.is_healthy()

        unhealthy = ServiceHealth(status=ServiceStatus.UNHEALTHY, response_time=5.0)
        assert not unhealthy.is_healthy()

    def test_service_health_age(self):
        """Test health check age calculation."""
        past_time = datetime.now(timezone.utc)
        health = ServiceHealth(
            status=ServiceStatus.HEALTHY,
            response_time=0.1,
            last_check=past_time
        )

        # Age should be positive
        assert health.age_seconds() >= 0
