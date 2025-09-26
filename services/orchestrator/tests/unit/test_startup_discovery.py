"""Tests for startup discovery functionality"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from typing import List, Dict, Any

from services.orchestrator.modules.startup_discovery import (
    StartupDiscoveryService,
    ServiceDiscoveryResult,
    DiscoveryConfig,
    ServiceEndpointInfo
)


class TestServiceDiscoveryResult:
    """Test ServiceDiscoveryResult dataclass."""

    def test_creation(self):
        """Test creating a discovery result."""
        endpoints = [
            ServiceEndpointInfo(
                url="http://service1:8080/api/v1",
                type="rest",
                version="v1"
            )
        ]

        result = ServiceDiscoveryResult(
            service_id="service1",
            service_type="api",
            endpoints=endpoints,
            metadata={"version": "1.0"},
            health_status="healthy"
        )

        assert result.service_id == "service1"
        assert result.service_type == "api"
        assert len(result.endpoints) == 1
        assert result.metadata == {"version": "1.0"}
        assert result.health_status == "healthy"

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ServiceDiscoveryResult(
            service_id="service1",
            service_type="api",
            endpoints=[],
            metadata={"version": "1.0"}
        )

        data = result.to_dict()

        assert data["service_id"] == "service1"
        assert data["service_type"] == "api"
        assert data["endpoints"] == []
        assert data["metadata"] == {"version": "1.0"}


class TestDiscoveryConfig:
    """Test DiscoveryConfig dataclass."""

    def test_creation_minimal(self):
        """Test creating minimal discovery config."""
        config = DiscoveryConfig()

        assert config.scan_interval == 30
        assert config.timeout == 10
        assert config.max_concurrent_scans == 5
        assert config.service_types == ["api", "worker", "storage"]
        assert config.enable_health_checks == True

    def test_creation_custom(self):
        """Test creating custom discovery config."""
        config = DiscoveryConfig(
            scan_interval=60,
            timeout=20,
            max_concurrent_scans=10,
            service_types=["api", "worker"],
            enable_health_checks=False
        )

        assert config.scan_interval == 60
        assert config.timeout == 20
        assert config.max_concurrent_scans == 10
        assert config.service_types == ["api", "worker"]
        assert config.enable_health_checks == False


class TestStartupDiscoveryService:
    """Test StartupDiscoveryService functionality."""

    @pytest.fixture
    def discovery_service(self):
        """Create a discovery service instance."""
        return StartupDiscoveryService()

    @pytest.fixture
    def mock_service_client(self):
        """Create a mock service client."""
        client = Mock()
        client.get_service_info = AsyncMock()
        client.check_health = AsyncMock()
        return client

    def test_initialization(self, discovery_service):
        """Test service initialization."""
        assert discovery_service.discovered_services == {}
        assert discovery_service.is_scanning == False
        assert isinstance(discovery_service.config, DiscoveryConfig)

    @patch('services.orchestrator.modules.startup_discovery.ServiceClients')
    @pytest.mark.asyncio
    async def test_discover_services_basic(self, mock_clients_class, discovery_service, mock_service_client):
        """Test basic service discovery."""
        # Mock the ServiceClients.get_all_clients method
        mock_clients_instance = Mock()
        mock_clients_instance.get_all_clients.return_value = ["service1", "service2"]
        mock_clients_class.return_value = mock_clients_instance

        # Mock get_service_client to return our mock client
        with patch('services.orchestrator.modules.startup_discovery.get_service_client', return_value=mock_service_client):
            # Configure mock responses
            mock_service_client.get_service_info.side_effect = [
                {
                    "service_id": "service1",
                    "service_type": "api",
                    "endpoints": [{"url": "http://service1:8080", "type": "rest"}],
                    "metadata": {"version": "1.0"}
                },
                {
                    "service_id": "service2",
                    "service_type": "worker",
                    "endpoints": [{"url": "http://service2:8081", "type": "grpc"}],
                    "metadata": {"version": "2.0"}
                }
            ]
            mock_service_client.check_health.side_effect = ["healthy", "healthy"]

            results = await discovery_service.discover_services()

            assert len(results) == 2
            assert results[0].service_id == "service1"
            assert results[0].service_type == "api"
            assert results[1].service_id == "service2"
            assert results[1].service_type == "worker"

    @patch('services.orchestrator.modules.startup_discovery.ServiceClients')
    @pytest.mark.asyncio
    async def test_discover_services_with_failures(self, mock_clients_class, discovery_service, mock_service_client):
        """Test service discovery with some failures."""
        mock_clients_instance = Mock()
        mock_clients_instance.get_all_clients.return_value = ["service1", "service2", "service3"]
        mock_clients_class.return_value = mock_clients_instance

        with patch('services.orchestrator.modules.startup_discovery.get_service_client', return_value=mock_service_client):
            # Configure mixed responses - some success, some failure
            mock_service_client.get_service_info.side_effect = [
                {"service_id": "service1", "service_type": "api", "endpoints": [], "metadata": {}},
                Exception("Connection failed"),  # service2 fails
                {"service_id": "service3", "service_type": "worker", "endpoints": [], "metadata": {}}
            ]
            mock_service_client.check_health.side_effect = ["healthy", "unknown", "healthy"]

            results = await discovery_service.discover_services()

            # Should only return successful discoveries
            assert len(results) == 2
            service_ids = [r.service_id for r in results]
            assert "service1" in service_ids
            assert "service3" in service_ids
            assert "service2" not in service_ids

    @pytest.mark.asyncio
    async def test_get_service_info_success(self, discovery_service, mock_service_client):
        """Test getting service info successfully."""
        mock_service_client.get_service_info.return_value = {
            "service_id": "test-service",
            "service_type": "api",
            "endpoints": [{"url": "http://test:8080", "type": "rest"}],
            "metadata": {"version": "1.0"}
        }
        mock_service_client.check_health.return_value = "healthy"

        result = await discovery_service._get_service_info("test-service", mock_service_client)

        assert result.service_id == "test-service"
        assert result.service_type == "api"
        assert result.health_status == "healthy"
        assert len(result.endpoints) == 1

    @pytest.mark.asyncio
    async def test_get_service_info_failure(self, discovery_service, mock_service_client):
        """Test handling service info retrieval failure."""
        mock_service_client.get_service_info.side_effect = Exception("Service unavailable")

        result = await discovery_service._get_service_info("test-service", mock_service_client)

        assert result is None

    def test_validate_service_info_valid(self, discovery_service):
        """Test validating valid service info."""
        info = {
            "service_id": "test-service",
            "service_type": "api",
            "endpoints": [{"url": "http://test:8080", "type": "rest"}],
            "metadata": {"version": "1.0"}
        }

        result = discovery_service._validate_service_info(info)

        assert result["service_id"] == "test-service"
        assert result["service_type"] == "api"

    def test_validate_service_info_invalid(self, discovery_service):
        """Test validating invalid service info."""
        info = {
            "service_type": "api",
            # Missing service_id
            "endpoints": []
        }

        result = discovery_service._validate_service_info(info)

        assert result is None

    def test_create_discovery_result(self, discovery_service):
        """Test creating discovery result from service info."""
        info = {
            "service_id": "test-service",
            "service_type": "api",
            "endpoints": [{"url": "http://test:8080", "type": "rest"}],
            "metadata": {"version": "1.0"}
        }

        result = discovery_service._create_discovery_result(info, "healthy")

        assert isinstance(result, ServiceDiscoveryResult)
        assert result.service_id == "test-service"
        assert result.service_type == "api"
        assert result.health_status == "healthy"
        assert len(result.endpoints) == 1

    def test_filter_service_types(self, discovery_service):
        """Test filtering services by type."""
        discovery_service.config.service_types = ["api", "worker"]

        assert discovery_service._should_discover_service("api") == True
        assert discovery_service._should_discover_service("worker") == True
        assert discovery_service._should_discover_service("storage") == False

    def test_update_discovery_cache(self, discovery_service):
        """Test updating the discovery cache."""
        result1 = ServiceDiscoveryResult(
            service_id="service1",
            service_type="api",
            endpoints=[],
            health_status="healthy"
        )
        result2 = ServiceDiscoveryResult(
            service_id="service2",
            service_type="worker",
            endpoints=[],
            health_status="healthy"
        )

        discovery_service._update_discovery_cache([result1, result2])

        assert "service1" in discovery_service.discovered_services
        assert "service2" in discovery_service.discovered_services
        assert discovery_service.discovered_services["service1"] == result1
        assert discovery_service.discovered_services["service2"] == result2

    def test_get_discovered_service(self, discovery_service):
        """Test getting a discovered service."""
        result = ServiceDiscoveryResult(
            service_id="service1",
            service_type="api",
            endpoints=[],
            health_status="healthy"
        )
        discovery_service.discovered_services["service1"] = result

        found = discovery_service.get_discovered_service("service1")
        assert found == result

        not_found = discovery_service.get_discovered_service("nonexistent")
        assert not_found is None

    def test_list_discovered_services(self, discovery_service):
        """Test listing all discovered services."""
        result1 = ServiceDiscoveryResult(
            service_id="service1",
            service_type="api",
            endpoints=[],
            health_status="healthy"
        )
        result2 = ServiceDiscoveryResult(
            service_id="service2",
            service_type="worker",
            endpoints=[],
            health_status="healthy"
        )

        discovery_service.discovered_services = {
            "service1": result1,
            "service2": result2
        }

        services = discovery_service.list_discovered_services()

        assert len(services) == 2
        service_ids = [s.service_id for s in services]
        assert "service1" in service_ids
        assert "service2" in service_ids

    def test_clear_discovery_cache(self, discovery_service):
        """Test clearing the discovery cache."""
        discovery_service.discovered_services = {"service1": Mock(), "service2": Mock()}

        discovery_service.clear_discovery_cache()

        assert discovery_service.discovered_services == {}
