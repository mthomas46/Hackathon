"""Unit tests for log-collector infrastructure repositories."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone, timedelta

from services.log_collector.infrastructure.repositories import LogRepository


class TestLogRepository:
    """Test cases for LogRepository."""

    @pytest.fixture
    def repository(self):
        """Create LogRepository instance for testing."""
        return LogRepository()

    @pytest.mark.asyncio
    async def test_save_and_retrieve_log_entry(self, repository):
        """Test saving and retrieving a log entry."""
        from services.log_collector.domain.entities import LogEntry, LogLevel

        entry = LogEntry(
            id="log-123",
            service_name="api-gateway",
            level=LogLevel.INFO,
            message="Test log message",
            timestamp=datetime.now(timezone.utc)
        )

        # Save entry
        await repository.save_log_entry(entry)

        # Retrieve by ID
        retrieved = await repository.get_log_entry_by_id(entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id
        assert retrieved.message == "Test log message"

    @pytest.mark.asyncio
    async def test_find_log_entries_by_service(self, repository):
        """Test finding log entries by service."""
        from services.log_collector.domain.entities import LogEntry, LogLevel

        entries = [
            LogEntry(id="log-1", service_name="api-gateway", level=LogLevel.INFO, message="API request", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="log-2", service_name="api-gateway", level=LogLevel.ERROR, message="API error", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="log-3", service_name="worker-service", level=LogLevel.INFO, message="Worker task", timestamp=datetime.now(timezone.utc))
        ]

        for entry in entries:
            await repository.save_log_entry(entry)

        # Find by service
        api_entries = await repository.get_log_entries_by_service("api-gateway")
        assert len(api_entries) == 2
        assert all(entry.service_name == "api-gateway" for entry in api_entries)

    @pytest.mark.asyncio
    async def test_find_log_entries_by_level(self, repository):
        """Test finding log entries by level."""
        from services.log_collector.domain.entities import LogEntry, LogLevel

        entries = [
            LogEntry(id="err-1", service_name="service-1", level=LogLevel.ERROR, message="Error 1", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="err-2", service_name="service-1", level=LogLevel.ERROR, message="Error 2", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="info-1", service_name="service-1", level=LogLevel.INFO, message="Info 1", timestamp=datetime.now(timezone.utc))
        ]

        for entry in entries:
            await repository.save_log_entry(entry)

        # Find by level
        error_entries = await repository.get_log_entries_by_level("service-1", LogLevel.ERROR)
        assert len(error_entries) == 2
        assert all(entry.level == LogLevel.ERROR for entry in error_entries)

    @pytest.mark.asyncio
    async def test_search_log_entries(self, repository):
        """Test searching log entries."""
        from services.log_collector.domain.entities import LogEntry, LogLevel

        entries = [
            LogEntry(id="search-1", service_name="api", level=LogLevel.ERROR, message="Database connection failed", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="search-2", service_name="api", level=LogLevel.INFO, message="User authentication successful", timestamp=datetime.now(timezone.utc)),
            LogEntry(id="search-3", service_name="worker", level=LogLevel.WARNING, message="High memory usage detected", timestamp=datetime.now(timezone.utc))
        ]

        for entry in entries:
            await repository.save_log_entry(entry)

        # Search by text
        db_results = await repository.search_log_entries("api", "database")
        assert len(db_results) >= 1

        auth_results = await repository.search_log_entries("api", "authentication")
        assert len(auth_results) >= 1

    @pytest.mark.asyncio
    async def test_get_log_statistics(self, repository):
        """Test getting log statistics."""
        from services.log_collector.domain.entities import LogEntry, LogLevel

        # Create entries with different levels
        base_time = datetime.now(timezone.utc)
        entries = [
            LogEntry(id="stat-1", service_name="test-service", level=LogLevel.ERROR, message="Error", timestamp=base_time),
            LogEntry(id="stat-2", service_name="test-service", level=LogLevel.WARNING, message="Warning", timestamp=base_time),
            LogEntry(id="stat-3", service_name="test-service", level=LogLevel.INFO, message="Info", timestamp=base_time),
            LogEntry(id="stat-4", service_name="test-service", level=LogLevel.DEBUG, message="Debug", timestamp=base_time),
            LogEntry(id="stat-5", service_name="test-service", level=LogLevel.INFO, message="Info 2", timestamp=base_time)
        ]

        for entry in entries:
            await repository.save_log_entry(entry)

        # Get statistics
        stats = await repository.get_log_statistics("test-service", base_time - timedelta(minutes=5), base_time + timedelta(minutes=5))

        assert stats.total_entries == 5
        assert stats.error_count == 1
        assert stats.warning_count == 1
        assert stats.info_count == 2
        assert stats.debug_count == 1

    @pytest.mark.asyncio
    async def test_time_range_queries(self, repository):
        """Test querying log entries by time range."""
        from services.log_collector.domain.entities import LogEntry, LogLevel

        base_time = datetime.now(timezone.utc)
        entries = [
            LogEntry(id="time-1", service_name="service-1", level=LogLevel.INFO, message="Old log", timestamp=base_time - timedelta(hours=2)),
            LogEntry(id="time-2", service_name="service-1", level=LogLevel.INFO, message="Recent log", timestamp=base_time - timedelta(minutes=30)),
            LogEntry(id="time-3", service_name="service-1", level=LogLevel.INFO, message="Very recent log", timestamp=base_time - timedelta(minutes=5))
        ]

        for entry in entries:
            await repository.save_log_entry(entry)

        # Query last hour
        recent_entries = await repository.get_log_entries_in_time_range("service-1", base_time - timedelta(hours=1), base_time)
        assert len(recent_entries) == 2  # Should exclude the 2-hour old entry

    @pytest.mark.asyncio
    async def test_bulk_operations(self, repository):
        """Test bulk save operations."""
        from services.log_collector.domain.entities import LogEntry, LogLevel

        # Create multiple entries
        entries = []
        for i in range(10):
            entry = LogEntry(
                id=f"bulk-{i}",
                service_name="bulk-service",
                level=LogLevel.INFO,
                message=f"Bulk log message {i}",
                timestamp=datetime.now(timezone.utc)
            )
            entries.append(entry)

        # Save all entries
        for entry in entries:
            await repository.save_log_entry(entry)

        # Verify all were saved
        retrieved = await repository.get_log_entries_by_service("bulk-service")
        assert len(retrieved) == 10

    def test_repository_initialization(self, repository):
        """Test repository initialization."""
        assert repository is not None
        assert hasattr(repository, 'save_log_entry')
        assert hasattr(repository, 'get_log_entry_by_id')
        assert hasattr(repository, 'get_log_entries_by_service')
        assert hasattr(repository, 'get_log_entries_by_level')
        assert hasattr(repository, 'search_log_entries')
        assert hasattr(repository, 'get_log_statistics')
        assert hasattr(repository, 'get_log_entries_in_time_range')

    @pytest.mark.asyncio
    async def test_error_handling(self, repository):
        """Test error handling in repository operations."""
        # Test finding non-existent entry
        result = await repository.get_log_entry_by_id("non-existent-id")
        assert result is None

        # Test searching with no matches
        results = await repository.search_log_entries("service-1", "nonexistentterm")
        assert isinstance(results, list)
        assert len(results) == 0

        # Test statistics for service with no logs
        stats = await repository.get_log_statistics("empty-service", datetime.now(timezone.utc) - timedelta(hours=1), datetime.now(timezone.utc))
        assert stats.total_entries == 0
        assert stats.error_count == 0

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, repository):
        """Test concurrent repository operations."""
        import asyncio
        from services.log_collector.domain.entities import LogEntry, LogLevel

        async def create_and_save_log(index):
            entry = LogEntry(
                id=f"concurrent-{index}",
                service_name="concurrent-service",
                level=LogLevel.INFO,
                message=f"Concurrent log {index}",
                timestamp=datetime.now(timezone.utc)
            )
            await repository.save_log_entry(entry)
            return entry.id

        # Create multiple concurrent operations
        tasks = [create_and_save_log(i) for i in range(5)]
        log_ids = await asyncio.gather(*tasks)

        # Verify all logs were created
        assert len(log_ids) == 5
        assert len(set(log_ids)) == 5  # All IDs should be unique

        # Verify all can be retrieved
        retrieved = await repository.get_log_entries_by_service("concurrent-service")
        assert len(retrieved) == 5

    @pytest.mark.asyncio
    async def test_complex_queries(self, repository):
        """Test complex query operations."""
        from services.log_collector.domain.entities import LogEntry, LogLevel

        # Create diverse log entries
        entries = [
            LogEntry(id="complex-1", service_name="api", level=LogLevel.ERROR, message="DB timeout", timestamp=datetime.now(timezone.utc), metadata={"endpoint": "/api/users", "method": "GET"}),
            LogEntry(id="complex-2", service_name="api", level=LogLevel.WARNING, message="Rate limit warning", timestamp=datetime.now(timezone.utc), metadata={"endpoint": "/api/data", "method": "POST"}),
            LogEntry(id="complex-3", service_name="worker", level=LogLevel.ERROR, message="Job failed", timestamp=datetime.now(timezone.utc), metadata={"job_type": "email", "priority": "high"}),
            LogEntry(id="complex-4", service_name="api", level=LogLevel.INFO, message="Cache hit", timestamp=datetime.now(timezone.utc), metadata={"endpoint": "/api/cache", "method": "GET"})
        ]

        for entry in entries:
            await repository.save_log_entry(entry)

        # Complex search: errors in API service
        api_errors = await repository.get_log_entries_by_level("api", LogLevel.ERROR)
        assert len(api_errors) == 1
        assert api_errors[0].message == "DB timeout"

        # Search by metadata content
        endpoint_results = await repository.search_log_entries("api", "/api/")
        assert len(endpoint_results) >= 2  # At least 2 API endpoint logs
