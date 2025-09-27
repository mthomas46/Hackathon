"""Unit tests for memory agent infrastructure repositories."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from services.memory_agent.infrastructure.repositories import MemoryMetricsRepository
from services.memory_agent.domain.entities import MemoryMetrics, MemoryAnalysis


class TestMemoryMetricsRepository:
    """Test cases for MemoryMetricsRepository."""

    @pytest.fixture
    def repository(self):
        """Create repository instance for testing."""
        return MemoryMetricsRepository()

    @pytest.fixture
    async def populated_repository(self):
        """Create repository with sample data."""
        repo = MemoryMetricsRepository()

        # Add sample metrics
        metrics1 = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=4000,
            available_memory_mb=4000,
            memory_usage_percent=50.0,
            service_name="test-service"
        )

        metrics2 = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=4800,
            available_memory_mb=3200,
            memory_usage_percent=60.0,
            service_name="test-service"
        )

        await repo.save(metrics1)
        await repo.save(metrics2)

        return repo

    @pytest.mark.asyncio
    async def test_save_and_retrieve_metrics(self, repository):
        """Test saving and retrieving memory metrics."""
        metrics = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=4000,
            available_memory_mb=4000,
            memory_usage_percent=50.0,
            service_name="test-service"
        )

        # Save metrics
        await repository.save(metrics)

        # Retrieve by ID
        retrieved = await repository.find_by_id(metrics.id)
        assert retrieved is not None
        assert retrieved.id == metrics.id
        assert retrieved.total_memory_mb == 8000
        assert retrieved.service_name == "test-service"

    @pytest.mark.asyncio
    async def test_find_by_service_name(self, populated_repository):
        """Test finding metrics by service name."""
        metrics_list = await populated_repository.find_by_service("test-service")

        assert len(metrics_list) == 2
        for metrics in metrics_list:
            assert metrics.service_name == "test-service"

    @pytest.mark.asyncio
    async def test_find_recent_metrics(self, populated_repository):
        """Test finding recent metrics."""
        recent_metrics = await populated_repository.find_recent(limit=1)

        assert len(recent_metrics) == 1
        # Should return the most recent metric

    @pytest.mark.asyncio
    async def test_find_by_time_range(self, repository):
        """Test finding metrics within time range."""
        start_time = datetime.now(timezone.utc)
        end_time = start_time

        # Add metrics at different times (would need time manipulation in real test)
        metrics = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=4000,
            available_memory_mb=4000,
            memory_usage_percent=50.0,
            service_name="time-test"
        )

        await repository.save(metrics)

        # Test time range query (implementation would vary)
        time_range_metrics = await repository.find_by_time_range(start_time, end_time)
        assert isinstance(time_range_metrics, list)

    @pytest.mark.asyncio
    async def test_update_metrics(self, repository):
        """Test updating existing metrics."""
        # Create initial metrics
        metrics = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=4000,
            available_memory_mb=4000,
            memory_usage_percent=50.0,
            service_name="update-test"
        )

        await repository.save(metrics)

        # Update metrics
        metrics.used_memory_mb = 4500
        metrics.memory_usage_percent = 56.25
        await repository.update(metrics)

        # Verify update
        updated = await repository.find_by_id(metrics.id)
        assert updated.used_memory_mb == 4500
        assert updated.memory_usage_percent == 56.25

    @pytest.mark.asyncio
    async def test_delete_metrics(self, repository):
        """Test deleting metrics."""
        metrics = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=4000,
            available_memory_mb=4000,
            memory_usage_percent=50.0,
            service_name="delete-test"
        )

        await repository.save(metrics)

        # Verify exists
        assert await repository.find_by_id(metrics.id) is not None

        # Delete
        deleted = await repository.delete(metrics.id)
        assert deleted is True

        # Verify no longer exists
        assert await repository.find_by_id(metrics.id) is None

    @pytest.mark.asyncio
    async def test_get_memory_stats(self, populated_repository):
        """Test getting memory statistics."""
        stats = await populated_repository.get_memory_stats("test-service")

        assert "total_metrics" in stats
        assert "average_usage_percent" in stats
        assert "peak_usage_percent" in stats
        assert "total_services" in stats

    @pytest.mark.asyncio
    async def test_search_metrics(self, repository):
        """Test searching metrics with filters."""
        # Add metrics with different characteristics
        metrics1 = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=4000,
            available_memory_mb=4000,
            memory_usage_percent=50.0,
            service_name="search-test-1"
        )

        metrics2 = MemoryMetrics(
            total_memory_mb=8000,
            used_memory_mb=6000,
            available_memory_mb=2000,
            memory_usage_percent=75.0,
            service_name="search-test-2"
        )

        await repository.save(metrics1)
        await repository.save(metrics2)

        # Search with filters
        high_usage = await repository.search({"usage_percent_gt": 70})
        assert len(high_usage) >= 1

        low_usage = await repository.search({"usage_percent_lt": 60})
        assert len(low_usage) >= 1

    @pytest.mark.asyncio
    async def test_bulk_operations(self, repository):
        """Test bulk save and retrieve operations."""
        # Create multiple metrics
        metrics_list = []
        for i in range(10):
            metrics = MemoryMetrics(
                total_memory_mb=8000,
                used_memory_mb=4000 + (i * 100),
                available_memory_mb=4000 - (i * 100),
                memory_usage_percent=50.0 + (i * 1.25),
                service_name=f"bulk-test-{i}"
            )
            metrics_list.append(metrics)

        # Bulk save
        await repository.bulk_save(metrics_list)

        # Bulk retrieve
        service_names = [f"bulk-test-{i}" for i in range(10)]
        bulk_results = await repository.find_by_services(service_names)

        assert len(bulk_results) == 10

    def test_repository_metrics(self, repository):
        """Test repository performance metrics."""
        # Test repository exposes metrics about its operations
        assert hasattr(repository, 'get_operation_metrics')

        metrics = repository.get_operation_metrics()
        assert isinstance(metrics, dict)
        assert "total_operations" in metrics
        assert "cache_hit_rate" in metrics

    @pytest.mark.asyncio
    async def test_concurrent_access(self, repository):
        """Test concurrent access to repository."""
        import asyncio

        async def save_metrics(index):
            metrics = MemoryMetrics(
                total_memory_mb=8000,
                used_memory_mb=4000,
                available_memory_mb=4000,
                memory_usage_percent=50.0,
                service_name=f"concurrent-test-{index}"
            )
            await repository.save(metrics)
            return metrics.id

        # Run multiple concurrent saves
        tasks = [save_metrics(i) for i in range(5)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert len(set(results)) == 5  # All IDs should be unique
