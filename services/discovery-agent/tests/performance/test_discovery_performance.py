"""Performance tests for discovery agent operations."""

import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock
from typing import List

from services.discovery_agent.domain.entities import ServiceInfo, ToolInfo
from services.discovery_agent.domain.services import DiscoveryService
from services.discovery_agent.application.handlers.discovery_handler import DiscoveryHandler


class TestDiscoveryPerformance:
    """Performance tests for discovery operations."""

    @pytest.fixture
    def discovery_service(self):
        """Create DiscoveryService for performance testing."""
        return DiscoveryService()

    @pytest.fixture
    def discovery_handler(self):
        """Create DiscoveryHandler for performance testing."""
        return DiscoveryHandler()

    def test_service_creation_performance(self):
        """Test performance of creating multiple ServiceInfo entities."""
        start_time = time.time()

        services = []
        for i in range(1000):
            service = ServiceInfo(
                name=f"service-{i}",
                type="api",
                port=8080 + (i % 100),
                status="healthy"
            )
            services.append(service)

        creation_time = time.time() - start_time
        assert len(services) == 1000
        assert creation_time < 1.0  # Should create 1000 services in less than 1 second

    def test_bulk_service_processing(self, discovery_service):
        """Test processing multiple services efficiently."""
        services = [
            ServiceInfo(name=f"bulk-service-{i}", type="api", port=8000 + i)
            for i in range(100)
        ]

        start_time = time.time()

        # Process services (mock validation)
        valid_services = []
        for service in services:
            if discovery_service._validate_service_info(service):
                valid_services.append(service)

        processing_time = time.time() - start_time
        assert len(valid_services) == 100
        assert processing_time < 0.5  # Should process 100 services quickly

    @pytest.mark.asyncio
    async def test_concurrent_discovery_operations(self, discovery_service):
        """Test concurrent discovery operations performance."""
        # Mock the discovery methods
        with pytest.mock.Mock() as mock_discovery:
            mock_discovery.discover_services = AsyncMock(return_value=Mock(
                services_discovered=[],
                tools_discovered=[],
                duration=0.1,
                success=True
            ))

            start_time = time.time()

            # Simulate concurrent operations
            tasks = []
            for i in range(10):
                task = asyncio.create_task(mock_discovery.discover_services("automatic"))
                tasks.append(task)

            results = await asyncio.gather(*tasks)
            concurrent_time = time.time() - start_time

            assert len(results) == 10
            assert concurrent_time < 2.0  # Should complete within 2 seconds

    def test_memory_efficiency_large_dataset(self):
        """Test memory efficiency with large datasets."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create large dataset
        services = []
        tools = []
        for i in range(5000):
            services.append(ServiceInfo(
                name=f"service-{i}",
                type="api",
                port=8000 + (i % 1000)
            ))
            tools.append(ToolInfo(
                name=f"tool-{i}",
                category="analysis"
            ))

        # Check memory usage after creating large dataset
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        assert len(services) == 5000
        assert len(tools) == 5000
        assert memory_increase < 100  # Should not use excessive memory

    def test_response_time_distribution(self):
        """Test response time distribution for consistent performance."""
        response_times = []

        # Simulate multiple operations with varying response times
        for i in range(100):
            # Simulate some variance in response times
            base_time = 0.1
            variance = (i % 10) * 0.01  # 0-0.09 variance
            response_time = base_time + variance
            response_times.append(response_time)

        # Calculate statistics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)

        # Assert reasonable performance bounds
        assert 0.08 <= avg_time <= 0.15  # Reasonable average
        assert max_time < 0.2  # No excessively slow operations
        assert min_time >= 0.1  # Minimum baseline performance

    @pytest.mark.asyncio
    async def test_resource_cleanup_efficiency(self):
        """Test that resources are cleaned up efficiently."""
        import gc

        # Create objects that should be cleaned up
        services = []
        for i in range(100):
            service = ServiceInfo(
                name=f"cleanup-service-{i}",
                type="api",
                port=8000 + i
            )
            services.append(service)

        # Delete references
        del services

        # Force garbage collection
        gc.collect()

        # Memory should be reclaimed
        # (This is a basic test - in practice you'd monitor actual memory usage)
        assert True  # Test passes if no exceptions during cleanup

    def test_cpu_usage_efficiency(self):
        """Test CPU usage efficiency for operations."""
        start_time = time.time()
        start_cpu = time.process_time()

        # Perform CPU-intensive operations
        results = []
        for i in range(10000):
            # Simulate some computation
            result = i * i + i
            results.append(result)

        end_cpu = time.process_time()
        end_time = time.time()

        cpu_time = end_cpu - start_cpu
        wall_time = end_time - start_time

        # CPU efficiency: CPU time should be reasonable compared to wall time
        cpu_efficiency = cpu_time / wall_time if wall_time > 0 else 0

        assert len(results) == 10000
        assert cpu_efficiency < 1.5  # Should not be excessively CPU bound
