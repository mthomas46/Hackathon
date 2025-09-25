"""Tests for Centralized Logging Service."""
import asyncio
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch, AsyncMock

from services.shared.infrastructure.utilities.centralized_logging_service import (
    CentralizedLoggingService,
    LogQuery,
    LogEntry,
    LogLevel,
    LogStorageType,
)


class TestCentralizedLoggingService:
    """Test centralized logging service functionality."""

    @pytest.fixture
    def logging_service(self):
        """Create a test logging service instance."""
        return CentralizedLoggingService(
            service_name="test-service",
            storage_type=LogStorageType.MEMORY
        )

    @pytest.fixture
    def sample_log_entry(self):
        """Create a sample log entry for testing."""
        return LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="Test log message",
            correlation_id="test-correlation-id",
            operation="test_operation",
            timestamp=datetime.now(timezone.utc)
        )

    @pytest.fixture
    def sample_query(self):
        """Create a sample log query for testing."""
        return LogQuery(
            service_name="test-service",
            limit=10,
            offset=0
        )

    @pytest.mark.asyncio
    async def test_store_log(self, logging_service, sample_log_entry):
        """Test storing a log entry."""
        await logging_service.store_log(sample_log_entry)

        # Check that log was stored
        assert len(logging_service._logs) == 1
        assert logging_service._logs[0] == sample_log_entry

    @pytest.mark.asyncio
    async def test_store_multiple_logs(self, logging_service, sample_log_entry):
        """Test storing multiple log entries."""
        # Create multiple log entries
        logs = []
        for i in range(5):
            log = LogEntry(
                service_name="test-service",
                level=LogLevel.INFO,
                message=f"Test log message {i}",
                correlation_id=f"correlation-{i}",
                operation=f"operation-{i}",
                timestamp=datetime.now(timezone.utc)
            )
            logs.append(log)
            await logging_service.store_log(log)

        # Check that all logs were stored
        assert len(logging_service._logs) == 5
        for i, log in enumerate(logs):
            assert logging_service._logs[i] == log

    @pytest.mark.asyncio
    async def test_query_logs_no_filters(self, logging_service, sample_log_entry, sample_query):
        """Test querying logs without filters."""
        await logging_service.store_log(sample_log_entry)

        results = await logging_service.query_logs(sample_query)

        assert len(results) == 1
        assert results[0] == sample_log_entry

    @pytest.mark.asyncio
    async def test_query_logs_by_service_name(self, logging_service, sample_query):
        """Test filtering logs by service name."""
        # Create logs for different services
        log1 = LogEntry(
            service_name="service-a",
            level=LogLevel.INFO,
            message="Log from service A",
            timestamp=datetime.now(timezone.utc)
        )
        log2 = LogEntry(
            service_name="service-b",
            level=LogLevel.INFO,
            message="Log from service B",
            timestamp=datetime.now(timezone.utc)
        )

        await logging_service.store_log(log1)
        await logging_service.store_log(log2)

        # Query for service-a only
        query = LogQuery(service_name="service-a", limit=10, offset=0)
        results = await logging_service.query_logs(query)

        assert len(results) == 1
        assert results[0].service_name == "service-a"

    @pytest.mark.asyncio
    async def test_query_logs_by_level(self, logging_service):
        """Test filtering logs by level."""
        # Create logs with different levels
        log_info = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="Info log",
            timestamp=datetime.now(timezone.utc)
        )
        log_error = LogEntry(
            service_name="test-service",
            level=LogLevel.ERROR,
            message="Error log",
            timestamp=datetime.now(timezone.utc)
        )

        await logging_service.store_log(log_info)
        await logging_service.store_log(log_error)

        # Query for ERROR level only
        query = LogQuery(level=LogLevel.ERROR, limit=10, offset=0)
        results = await logging_service.query_logs(query)

        assert len(results) == 1
        assert results[0].level == LogLevel.ERROR

    @pytest.mark.asyncio
    async def test_query_logs_by_correlation_id(self, logging_service):
        """Test filtering logs by correlation ID."""
        log1 = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="Log 1",
            correlation_id="corr-123",
            timestamp=datetime.now(timezone.utc)
        )
        log2 = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="Log 2",
            correlation_id="corr-456",
            timestamp=datetime.now(timezone.utc)
        )

        await logging_service.store_log(log1)
        await logging_service.store_log(log2)

        query = LogQuery(correlation_id="corr-123", limit=10, offset=0)
        results = await logging_service.query_logs(query)

        assert len(results) == 1
        assert results[0].correlation_id == "corr-123"

    @pytest.mark.asyncio
    async def test_query_logs_by_operation(self, logging_service):
        """Test filtering logs by operation."""
        log1 = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="Operation A",
            operation="op-a",
            timestamp=datetime.now(timezone.utc)
        )
        log2 = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="Operation B",
            operation="op-b",
            timestamp=datetime.now(timezone.utc)
        )

        await logging_service.store_log(log1)
        await logging_service.store_log(log2)

        query = LogQuery(operation="op-a", limit=10, offset=0)
        results = await logging_service.query_logs(query)

        assert len(results) == 1
        assert results[0].operation == "op-a"

    @pytest.mark.asyncio
    async def test_query_logs_time_range_filtering(self, logging_service):
        """Test filtering logs by time range."""
        base_time = datetime.now(timezone.utc)

        log_old = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="Old log",
            timestamp=base_time.replace(hour=10)
        )
        log_new = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="New log",
            timestamp=base_time.replace(hour=14)
        )

        await logging_service.store_log(log_old)
        await logging_service.store_log(log_new)

        # Query for logs after 12:00
        noon = base_time.replace(hour=12)
        query = LogQuery(start_time=noon, limit=10, offset=0)
        results = await logging_service.query_logs(query)

        assert len(results) == 1
        assert results[0].message == "New log"

    @pytest.mark.asyncio
    async def test_query_logs_message_filtering(self, logging_service):
        """Test filtering logs by message content."""
        log1 = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="This is an error message",
            timestamp=datetime.now(timezone.utc)
        )
        log2 = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="This is an info message",
            timestamp=datetime.now(timezone.utc)
        )

        await logging_service.store_log(log1)
        await logging_service.store_log(log2)

        query = LogQuery(message_contains="error", limit=10, offset=0)
        results = await logging_service.query_logs(query)

        assert len(results) == 1
        assert "error" in results[0].message.lower()

    @pytest.mark.asyncio
    async def test_query_logs_ordering_timestamp_desc(self, logging_service):
        """Test ordering logs by timestamp descending."""
        base_time = datetime.now(timezone.utc)

        log1 = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="First log",
            timestamp=base_time.replace(hour=10)
        )
        log2 = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="Second log",
            timestamp=base_time.replace(hour=14)
        )

        await logging_service.store_log(log1)
        await logging_service.store_log(log2)

        query = LogQuery(order_by="timestamp", order_desc=True, limit=10, offset=0)
        results = await logging_service.query_logs(query)

        assert len(results) == 2
        assert results[0].message == "Second log"  # Newer first
        assert results[1].message == "First log"

    @pytest.mark.asyncio
    async def test_query_logs_ordering_level(self, logging_service):
        """Test ordering logs by level."""
        log_debug = LogEntry(
            service_name="test-service",
            level=LogLevel.DEBUG,
            message="Debug log",
            timestamp=datetime.now(timezone.utc)
        )
        log_error = LogEntry(
            service_name="test-service",
            level=LogLevel.ERROR,
            message="Error log",
            timestamp=datetime.now(timezone.utc)
        )
        log_info = LogEntry(
            service_name="test-service",
            level=LogLevel.INFO,
            message="Info log",
            timestamp=datetime.now(timezone.utc)
        )

        await logging_service.store_log(log_debug)
        await logging_service.store_log(log_error)
        await logging_service.store_log(log_info)

        query = LogQuery(order_by="level", order_desc=False, limit=10, offset=0)
        results = await logging_service.query_logs(query)

        assert len(results) == 3
        # Should be ordered by level enum order (DEBUG=0, INFO=1, ERROR=2)
        assert results[0].level == LogLevel.DEBUG
        assert results[1].level == LogLevel.INFO
        assert results[2].level == LogLevel.ERROR

    @pytest.mark.asyncio
    async def test_query_logs_pagination(self, logging_service):
        """Test pagination of query results."""
        # Create 5 log entries
        for i in range(5):
            log = LogEntry(
                service_name="test-service",
                level=LogLevel.INFO,
                message=f"Log {i}",
                timestamp=datetime.now(timezone.utc)
            )
            await logging_service.store_log(log)

        # First page (offset 0, limit 2)
        query1 = LogQuery(limit=2, offset=0)
        results1 = await logging_service.query_logs(query1)

        assert len(results1) == 2
        assert results1[0].message == "Log 0"
        assert results1[1].message == "Log 1"

        # Second page (offset 2, limit 2)
        query2 = LogQuery(limit=2, offset=2)
        results2 = await logging_service.query_logs(query2)

        assert len(results2) == 2
        assert results2[0].message == "Log 2"
        assert results2[1].message == "Log 3"

    @pytest.mark.asyncio
    async def test_get_log_stats(self, logging_service):
        """Test getting log statistics."""
        # Create logs with different services and levels
        services = ["service-a", "service-b", "service-a"]
        levels = [LogLevel.INFO, LogLevel.ERROR, LogLevel.WARNING]

        for i, (service, level) in enumerate(zip(services, levels)):
            log = LogEntry(
                service_name=service,
                level=level,
                message=f"Test log {i}",
                timestamp=datetime.now(timezone.utc)
            )
            await logging_service.store_log(log)

        stats = await logging_service.get_log_stats()

        assert stats["storage_type"] == "memory"
        assert stats["total_logs"] == 3
        assert stats["services"]["service-a"] == 2
        assert stats["services"]["service-b"] == 1
        assert stats["levels"]["INFO"] == 1
        assert stats["levels"]["ERROR"] == 1
        assert stats["levels"]["WARNING"] == 1

    @pytest.mark.asyncio
    async def test_log_retention_policy(self, logging_service):
        """Test that logs are retained according to the retention policy."""
        # Create more than 10,000 logs to test retention
        for i in range(10010):
            log = LogEntry(
                service_name="test-service",
                level=LogLevel.INFO,
                message=f"Log {i}",
                timestamp=datetime.now(timezone.utc)
            )
            await logging_service.store_log(log)

        # Should only keep the last 10,000 logs
        assert len(logging_service._logs) <= 10000

        # The oldest logs should be removed
        # (This is a basic check - in practice we'd want to verify FIFO behavior)

    @pytest.mark.asyncio
    async def test_concurrent_access(self, logging_service):
        """Test concurrent access to logging service."""
        import asyncio

        async def add_logs(service, log_id):
            for i in range(10):
                log = LogEntry(
                    service_name=f"service-{log_id}",
                    level=LogLevel.INFO,
                    message=f"Concurrent log {log_id}-{i}",
                    timestamp=datetime.now(timezone.utc)
                )
                await service.store_log(log)

        # Run multiple concurrent log additions
        tasks = [
            add_logs(logging_service, i) for i in range(5)
        ]
        await asyncio.gather(*tasks)

        # Should have 50 logs total (5 services * 10 logs each)
        assert len(logging_service._logs) == 50

        # Each service should have 10 logs
        for service_id in range(5):
            service_logs = [log for log in logging_service._logs
                          if log.service_name == f"service-{service_id}"]
            assert len(service_logs) == 10
