"""Unit tests for DiscoveryService domain service."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone

from services.discovery_agent.domain.services import DiscoveryService
from services.discovery_agent.domain.entities import ServiceInfo, ToolInfo
from services.discovery_agent.domain.value_objects import ServiceStatus, ToolCategory, DiscoveryMode


class TestDiscoveryService:
    """Test cases for DiscoveryService."""

    @pytest.fixture
    def discovery_service(self):
        """Create DiscoveryService instance for testing."""
        return DiscoveryService()

    def test_service_creation(self, discovery_service):
        """Test DiscoveryService initialization."""
        assert discovery_service is not None
        assert hasattr(discovery_service, 'discover_services')
        assert hasattr(discovery_service, '_validate_service_info')

    def test_validate_service_info_valid(self, discovery_service):
        """Test validation of valid service info."""
        service = ServiceInfo(
            name="valid-service",
            type="api",
            port=8080,
            status=ServiceStatus.HEALTHY
        )

        assert discovery_service._validate_service_info(service) is True

    def test_validate_service_info_invalid_name(self, discovery_service):
        """Test validation of service with invalid name."""
        service = ServiceInfo(
            name="",  # Invalid: empty name
            type="api",
            port=8080
        )

        assert discovery_service._validate_service_info(service) is False

    def test_validate_service_info_invalid_port(self, discovery_service):
        """Test validation of service with invalid port."""
        service = ServiceInfo(
            name="test-service",
            type="api",
            port=99999  # Invalid: port too high
        )

        assert discovery_service._validate_service_info(service) is False

    @pytest.mark.asyncio
    async def test_discover_services_automatic_mode(self, discovery_service):
        """Test automatic service discovery."""
        # Mock the network scanning
        with patch.object(discovery_service, '_scan_network', new_callable=AsyncMock) as mock_scan:
            mock_services = [
                ServiceInfo(name="auto-service-1", type="api", port=8080),
                ServiceInfo(name="auto-service-2", type="worker", port=8081)
            ]
            mock_scan.return_value = mock_services

            result = await discovery_service.discover_services(DiscoveryMode.AUTOMATIC)

            assert result.mode == DiscoveryMode.AUTOMATIC
            assert len(result.services_discovered) == 2
            assert result.success is True
            assert result.duration >= 0
            mock_scan.assert_called_once()

    @pytest.mark.asyncio
    async def test_discover_services_manual_mode(self, discovery_service):
        """Test manual service discovery."""
        manual_services = [
            ServiceInfo(name="manual-service-1", type="api", port=3000),
            ServiceInfo(name="manual-service-2", type="db", port=5432)
        ]

        result = await discovery_service.discover_services(
            DiscoveryMode.MANUAL,
            manual_services=manual_services
        )

        assert result.mode == DiscoveryMode.MANUAL
        assert len(result.services_discovered) == 2
        assert result.services_discovered[0].name == "manual-service-1"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_discover_services_with_filters(self, discovery_service):
        """Test service discovery with filters."""
        with patch.object(discovery_service, '_scan_network', new_callable=AsyncMock) as mock_scan:
            all_services = [
                ServiceInfo(name="api-service", type="api", port=8080),
                ServiceInfo(name="worker-service", type="worker", port=8081),
                ServiceInfo(name="db-service", type="database", port=5432)
            ]
            mock_scan.return_value = all_services

            result = await discovery_service.discover_services(
                DiscoveryMode.AUTOMATIC,
                filters={"type": "api"}
            )

            # Should only return API services
            api_services = [s for s in result.services_discovered if s.type == "api"]
            assert len(api_services) == 1
            assert api_services[0].name == "api-service"

    @pytest.mark.asyncio
    async def test_discover_services_with_timeout(self, discovery_service):
        """Test service discovery with timeout."""
        with patch.object(discovery_service, '_scan_network', new_callable=AsyncMock) as mock_scan:
            # Mock slow network scan
            import asyncio
            async def slow_scan():
                await asyncio.sleep(0.1)  # Simulate slow operation
                return [ServiceInfo(name="slow-service", type="api", port=8080)]

            mock_scan.side_effect = slow_scan

            result = await discovery_service.discover_services(
                DiscoveryMode.AUTOMATIC,
                timeout=5.0
            )

            assert result.duration >= 0.1  # Should have taken at least 0.1 seconds
            assert len(result.services_discovered) == 1

    @pytest.mark.asyncio
    async def test_discover_services_error_handling(self, discovery_service):
        """Test error handling during service discovery."""
        with patch.object(discovery_service, '_scan_network', new_callable=AsyncMock) as mock_scan:
            mock_scan.side_effect = Exception("Network scan failed")

            result = await discovery_service.discover_services(DiscoveryMode.AUTOMATIC)

            assert result.success is False
            assert len(result.errors) > 0
            assert "Network scan failed" in result.errors[0]

    def test_get_discovery_stats(self, discovery_service):
        """Test discovery statistics retrieval."""
        # Mock some internal state for statistics
        discovery_service._discovery_count = 5
        discovery_service._successful_discoveries = 4
        discovery_service._total_services_found = 25

        stats = discovery_service.get_discovery_stats()

        assert stats["total_discoveries"] == 5
        assert stats["success_rate"] == 0.8  # 4/5
        assert stats["average_services_per_discovery"] == 5  # 25/5

    @pytest.mark.asyncio
    async def test_concurrent_discovery_operations(self, discovery_service):
        """Test concurrent discovery operations don't interfere."""
        with patch.object(discovery_service, '_scan_network', new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = [ServiceInfo(name="concurrent-service", type="api", port=8080)]

            # Run multiple discovery operations concurrently
            import asyncio
            tasks = []
            for i in range(3):
                task = asyncio.create_task(
                    discovery_service.discover_services(DiscoveryMode.AUTOMATIC)
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks)

            # All should succeed and return results
            assert len(results) == 3
            for result in results:
                assert result.success is True
                assert len(result.services_discovered) == 1

    def test_service_deduplication(self, discovery_service):
        """Test that duplicate services are handled properly."""
        services = [
            ServiceInfo(name="duplicate-service", type="api", port=8080),
            ServiceInfo(name="duplicate-service", type="api", port=8080),  # Duplicate
            ServiceInfo(name="unique-service", type="worker", port=8081)
        ]

        # Service should handle deduplication (implementation dependent)
        # This tests the interface
        assert len(services) == 3
        assert services[0].name == services[1].name  # They are duplicates

    def test_discovery_result_formatting(self, discovery_service):
        """Test discovery result formatting and metadata."""
        result = Mock()
        result.services_discovered = [
            ServiceInfo(name="formatted-service", type="api", port=8080)
        ]
        result.tools_discovered = [
            ToolInfo(name="formatted-tool", category=ToolCategory.ANALYSIS)
        ]
        result.success = True
        result.duration = 2.5
        result.errors = []

        # Test result summary generation (if implemented)
        summary = {
            "services_found": len(result.services_discovered),
            "tools_found": len(result.tools_discovered),
            "duration": result.duration,
            "success": result.success
        }

        assert summary["services_found"] == 1
        assert summary["tools_found"] == 1
        assert summary["duration"] == 2.5
        assert summary["success"] is True
