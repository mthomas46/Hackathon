"""Tests for Application Services - Cross-cutting concerns."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ...application.services.application_service import (
    ApplicationService, ServiceContext, ServiceRegistry, OperationContextManager
)
from ...application.services.logging_service import (
    LoggingService, ApplicationLogger, StructuredFormatter, LogAggregator, RotatingFileHandler
)
from ...application.services.caching_service import (
    CachingService, ApplicationCache, CacheEntry, CacheStats
)
from ...application.services.monitoring_service import (
    MonitoringService, ApplicationMetrics, MetricType, HealthStatus
)
from ...application.services.configuration_service import (
    ConfigurationService, EnvironmentConfig, ConfigValidator
)
from ...application.services.health_service import (
    HealthService, HealthCheck, HealthCheckResult, DependencyStatus
)
from ...application.services.notification_service import (
    NotificationService, NotificationChannel, NotificationTemplate,
    EmailChannel, WebhookChannel, SlackChannel
)
from ...application.services.transaction_service import (
    TransactionService, TransactionManager, TransactionContext, SQLiteTransactionManager
)
from ...application.services.analysis_application_service import AnalysisApplicationService

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence


class TestApplicationService:
    """Test cases for base ApplicationService."""

    def test_application_service_creation(self):
        """Test creating base application service."""
        service = ApplicationService()
        assert service is not None

    def test_service_context_creation(self):
        """Test service context creation."""
        context = ServiceContext(
            service_name="test-service",
            operation_id="op-123",
            user_id="user-456",
            correlation_id="corr-789",
            timestamp=datetime.now(timezone.utc)
        )

        assert context.service_name == "test-service"
        assert context.operation_id == "op-123"
        assert context.user_id == "user-456"
        assert context.correlation_id == "corr-789"
        assert context.timestamp is not None

    def test_service_registry_singleton(self):
        """Test service registry singleton pattern."""
        registry1 = ServiceRegistry()
        registry2 = ServiceRegistry()

        # Should be same instance (singleton)
        assert registry1 is registry2

        # Test service registration
        mock_service = Mock()
        registry1.register("test-service", mock_service)
        retrieved = registry1.get("test-service")

        assert retrieved is mock_service

    @pytest.mark.asyncio
    async def test_operation_context_manager(self):
        """Test operation context manager."""
        context_manager = OperationContextManager()

        async with context_manager.create_context("test-operation") as context:
            assert context.operation_id is not None
            assert context.service_name == "unknown-service"
            assert context.timestamp is not None

        # Context should be cleaned up after exit
        assert len(context_manager._active_contexts) == 0


class TestLoggingService:
    """Test cases for LoggingService."""

    def test_logging_service_creation(self):
        """Test creating logging service."""
        service = LoggingService()
        assert service is not None
        assert isinstance(service.logger, ApplicationLogger)

    def test_application_logger_creation(self):
        """Test application logger creation."""
        logger = ApplicationLogger("test-logger")
        assert logger.name == "test-logger"
        assert logger.level == "INFO"

    def test_structured_formatter(self):
        """Test structured log formatter."""
        formatter = StructuredFormatter()

        # Create a test record
        record = Mock()
        record.levelname = "INFO"
        record.name = "test.logger"
        record.message = "Test message"
        record.created = datetime.now(timezone.utc).timestamp()

        formatted = formatter.format(record)
        assert "INFO" in formatted
        assert "test.logger" in formatted
        assert "Test message" in formatted

    def test_log_aggregator(self):
        """Test log aggregation functionality."""
        aggregator = LogAggregator()

        # Add some log entries
        aggregator.add_entry("INFO", "Test message 1", {"service": "test"})
        aggregator.add_entry("ERROR", "Test error", {"error_code": 500})

        stats = aggregator.get_stats()
        assert stats["total_entries"] == 2
        assert stats["info_count"] == 1
        assert stats["error_count"] == 1

    def test_rotating_file_handler(self):
        """Test rotating file handler."""
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            handler = RotatingFileHandler(temp_path, max_bytes=1024, backup_count=3)
            assert handler.baseFilename == temp_path
            assert handler.maxBytes == 1024
            assert handler.backupCount == 3
        finally:
            os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_logging_service_async_logging(self):
        """Test async logging operations."""
        service = LoggingService()

        # Test structured logging
        await service.log_info(
            "Test operation",
            operation_id="op-123",
            user_id="user-456",
            extra_data={"key": "value"}
        )

        await service.log_error(
            "Test error",
            operation_id="op-123",
            error_code=500,
            stack_trace="mock stack trace"
        )

        # Service should handle async logging without errors
        assert service.logger is not None


class TestCachingService:
    """Test cases for CachingService."""

    def test_caching_service_creation(self):
        """Test creating caching service."""
        service = CachingService()
        assert service is not None
        assert isinstance(service.cache, ApplicationCache)

    def test_application_cache_creation(self):
        """Test application cache creation."""
        cache = ApplicationCache(max_size=100, ttl_seconds=300)
        assert cache.max_size == 100
        assert cache.default_ttl == 300
        assert len(cache._cache) == 0

    @pytest.mark.asyncio
    async def test_cache_operations(self):
        """Test basic cache operations."""
        cache = ApplicationCache(max_size=10, ttl_seconds=60)

        # Test set and get
        await cache.set("key1", "value1")
        value = await cache.get("key1")
        assert value == "value1"

        # Test get non-existent key
        value = await cache.get("non-existent")
        assert value is None

        # Test delete
        await cache.delete("key1")
        value = await cache.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_ttl(self):
        """Test cache TTL functionality."""
        cache = ApplicationCache(max_size=10, ttl_seconds=1)  # 1 second TTL

        # Set a value
        await cache.set("short-lived", "value", ttl_seconds=1)
        value = await cache.get("short-lived")
        assert value == "value"

        # Wait for expiration
        await asyncio.sleep(1.1)
        value = await cache.get("short-lived")
        assert value is None

    @pytest.mark.asyncio
    async def test_cache_eviction(self):
        """Test cache eviction when max size is reached."""
        cache = ApplicationCache(max_size=3, ttl_seconds=300)

        # Fill cache to max
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.set("key3", "value3")

        # Add one more (should evict oldest)
        await cache.set("key4", "value4")

        # Check that we have 3 items (max_size)
        assert len(cache._cache) <= 3

        # Check that key4 exists
        value = await cache.get("key4")
        assert value == "value4"

    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry("test-value", ttl_seconds=60)

        assert entry.value == "test-value"
        assert entry.created_at is not None
        assert entry.expires_at is not None
        assert entry.is_expired() is False

    def test_cache_stats(self):
        """Test cache statistics."""
        stats = CacheStats()

        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0

        # Update stats
        stats.record_hit()
        stats.record_miss()
        stats.record_eviction()

        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.evictions == 1
        assert stats.hit_rate == 0.5


class TestMonitoringService:
    """Test cases for MonitoringService."""

    def test_monitoring_service_creation(self):
        """Test creating monitoring service."""
        service = MonitoringService()
        assert service is not None
        assert isinstance(service.metrics, ApplicationMetrics)

    def test_application_metrics_creation(self):
        """Test application metrics creation."""
        metrics = ApplicationMetrics(service_name="test-service")
        assert metrics.service_name == "test-service"
        assert len(metrics._counters) == 0
        assert len(metrics._gauges) == 0
        assert len(metrics._histograms) == 0

    @pytest.mark.asyncio
    async def test_metrics_operations(self):
        """Test metrics operations."""
        metrics = ApplicationMetrics(service_name="test-service")

        # Test counter
        await metrics.increment_counter("requests_total", labels={"method": "GET"})
        await metrics.increment_counter("requests_total", labels={"method": "GET"})

        # Test gauge
        await metrics.set_gauge("active_connections", 5)
        await metrics.set_gauge("active_connections", 3)

        # Test histogram
        await metrics.record_histogram("request_duration", 0.125, labels={"method": "GET"})
        await metrics.record_histogram("request_duration", 0.089, labels={"method": "POST"})

        # Verify metrics were recorded
        assert len(metrics._counters) > 0
        assert len(metrics._gauges) > 0
        assert len(metrics._histograms) > 0

    def test_metric_types(self):
        """Test metric type enumeration."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"

    def test_health_status(self):
        """Test health status enumeration."""
        assert HealthStatus.HEALTHY.value == "healthy"
        assert HealthStatus.DEGRADED.value == "degraded"
        assert HealthStatus.UNHEALTHY.value == "unhealthy"


class TestConfigurationService:
    """Test cases for ConfigurationService."""

    def test_configuration_service_creation(self):
        """Test creating configuration service."""
        service = ConfigurationService()
        assert service is not None

    def test_environment_config(self):
        """Test environment configuration."""
        config = EnvironmentConfig(
            environment="development",
            debug=True,
            database_url="sqlite:///test.db",
            redis_url="redis://localhost:6379",
            log_level="DEBUG"
        )

        assert config.environment == "development"
        assert config.debug is True
        assert config.database_url == "sqlite:///test.db"
        assert config.redis_url == "redis://localhost:6379"
        assert config.log_level == "DEBUG"

    def test_config_validator(self):
        """Test configuration validation."""
        validator = ConfigValidator()

        # Valid config
        valid_config = {
            "environment": "production",
            "database_url": "postgresql://user:pass@localhost/db",
            "redis_url": "redis://localhost:6379"
        }

        result = validator.validate(valid_config)
        assert result.is_valid is True
        assert len(result.errors) == 0

        # Invalid config
        invalid_config = {
            "environment": "invalid_env",
            "database_url": "",
            "redis_url": "invalid_url"
        }

        result = validator.validate(invalid_config)
        assert result.is_valid is False
        assert len(result.errors) > 0


class TestHealthService:
    """Test cases for HealthService."""

    def test_health_service_creation(self):
        """Test creating health service."""
        service = HealthService()
        assert service is not None
        assert len(service._health_checks) == 0

    def test_health_check_creation(self):
        """Test health check creation."""
        async def check_func():
            return HealthCheckResult(
                name="test-check",
                status=HealthStatus.HEALTHY,
                response_time=0.05,
                message="All good"
            )

        check = HealthCheck(
            name="test-check",
            check_function=check_func,
            timeout_seconds=5.0,
            interval_seconds=30.0
        )

        assert check.name == "test-check"
        assert check.timeout_seconds == 5.0
        assert check.interval_seconds == 30.0

    @pytest.mark.asyncio
    async def test_health_check_execution(self):
        """Test health check execution."""
        async def mock_check():
            return HealthCheckResult(
                name="database-check",
                status=HealthStatus.HEALTHY,
                response_time=0.023,
                message="Database connection OK"
            )

        check = HealthCheck("database-check", mock_check)
        service = HealthService()

        # Register and run check
        service.register_check(check)
        result = await service.run_check("database-check")

        assert result.name == "database-check"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time == 0.023
        assert result.message == "Database connection OK"

    @pytest.mark.asyncio
    async def test_overall_health_status(self):
        """Test overall health status calculation."""
        service = HealthService()

        # Add healthy check
        async def healthy_check():
            return HealthCheckResult("healthy", HealthStatus.HEALTHY, 0.1, "OK")

        # Add unhealthy check
        async def unhealthy_check():
            return HealthCheckResult("unhealthy", HealthStatus.UNHEALTHY, 0.2, "Failed")

        service.register_check(HealthCheck("healthy-check", healthy_check))
        service.register_check(HealthCheck("unhealthy-check", unhealthy_check))

        # Run all checks
        await service.run_all_checks()

        # Overall status should be unhealthy (worst status wins)
        overall = service.get_overall_health()
        assert overall.status == HealthStatus.UNHEALTHY

    def test_dependency_status(self):
        """Test dependency status enumeration."""
        assert DependencyStatus.AVAILABLE.value == "available"
        assert DependencyStatus.DEGRADED.value == "degraded"
        assert DependencyStatus.UNAVAILABLE.value == "unavailable"


class TestNotificationService:
    """Test cases for NotificationService."""

    def test_notification_service_creation(self):
        """Test creating notification service."""
        service = NotificationService()
        assert service is not None
        assert len(service._channels) == 0

    def test_notification_channel_creation(self):
        """Test notification channel creation."""
        channel = NotificationChannel(
            name="email-channel",
            channel_type="email",
            config={"smtp_server": "smtp.example.com"}
        )

        assert channel.name == "email-channel"
        assert channel.channel_type == "email"
        assert channel.config["smtp_server"] == "smtp.example.com"

    def test_email_channel(self):
        """Test email notification channel."""
        channel = EmailChannel(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            username="test@example.com",
            password="password123"
        )

        assert channel.smtp_server == "smtp.gmail.com"
        assert channel.smtp_port == 587
        assert channel.username == "test@example.com"

    def test_webhook_channel(self):
        """Test webhook notification channel."""
        channel = WebhookChannel(
            url="https://hooks.slack.com/services/...",
            headers={"Authorization": "Bearer token"}
        )

        assert channel.url == "https://hooks.slack.com/services/..."
        assert channel.headers["Authorization"] == "Bearer token"

    def test_slack_channel(self):
        """Test Slack notification channel."""
        channel = SlackChannel(
            webhook_url="https://hooks.slack.com/services/...",
            channel="#alerts",
            username="analysis-bot"
        )

        assert channel.webhook_url == "https://hooks.slack.com/services/..."
        assert channel.channel == "#alerts"
        assert channel.username == "analysis-bot"

    def test_notification_template(self):
        """Test notification template."""
        template = NotificationTemplate(
            name="alert-template",
            subject_template="Alert: {{title}}",
            body_template="Description: {{description}}\nSeverity: {{severity}}"
        )

        assert template.name == "alert-template"
        assert "title" in template.subject_template
        assert "description" in template.body_template

    @pytest.mark.asyncio
    async def test_notification_sending(self):
        """Test notification sending."""
        service = NotificationService()

        # Mock channel
        mock_channel = Mock()
        mock_channel.send = AsyncMock(return_value=True)
        service.register_channel(mock_channel)

        # Send notification
        success = await service.send_notification(
            channel_name=mock_channel.name,
            subject="Test Alert",
            message="This is a test notification",
            priority="high"
        )

        assert success is True
        mock_channel.send.assert_called_once()


class TestTransactionService:
    """Test cases for TransactionService."""

    def test_transaction_service_creation(self):
        """Test creating transaction service."""
        service = TransactionService()
        assert service is not None

    def test_transaction_context_creation(self):
        """Test transaction context creation."""
        context = TransactionContext(
            transaction_id="tx-123",
            isolation_level="SERIALIZABLE",
            timeout_seconds=30.0
        )

        assert context.transaction_id == "tx-123"
        assert context.isolation_level == "SERIALIZABLE"
        assert context.timeout_seconds == 30.0
        assert context.start_time is not None

    def test_sqlite_transaction_manager(self):
        """Test SQLite transaction manager."""
        manager = SQLiteTransactionManager(database_path=":memory:")

        assert manager.database_path == ":memory:"
        assert manager.connection is None  # Not connected yet

    @pytest.mark.asyncio
    async def test_transaction_lifecycle(self):
        """Test transaction lifecycle."""
        manager = SQLiteTransactionManager(database_path=":memory:")

        # Begin transaction
        async with manager.begin_transaction() as tx:
            assert tx is not None
            assert tx.transaction_id is not None

            # Execute some operations within transaction
            # In a real scenario, this would be database operations

        # Transaction should be committed automatically

    @pytest.mark.asyncio
    async def test_transaction_rollback(self):
        """Test transaction rollback."""
        manager = SQLiteTransactionManager(database_path=":memory:")

        try:
            async with manager.begin_transaction() as tx:
                # Simulate an error that should cause rollback
                raise ValueError("Simulated error")
        except ValueError:
            pass  # Expected

        # Transaction should have been rolled back


class TestAnalysisApplicationService:
    """Test cases for AnalysisApplicationService."""

    @pytest.fixture
    def mock_domain_services(self):
        """Mock domain services for testing."""
        return {
            'analysis_service': Mock(),
            'document_service': Mock(),
            'finding_service': Mock()
        }

    @pytest.fixture
    def mock_application_services(self):
        """Mock application services for testing."""
        return {
            'logging_service': Mock(),
            'caching_service': Mock(),
            'monitoring_service': Mock(),
            'transaction_service': Mock()
        }

    def test_analysis_application_service_creation(self, mock_domain_services, mock_application_services):
        """Test creating analysis application service."""
        service = AnalysisApplicationService(
            domain_services=mock_domain_services,
            application_services=mock_application_services
        )

        assert service.domain_services == mock_domain_services
        assert service.application_services == mock_application_services

    @pytest.mark.asyncio
    async def test_perform_analysis_workflow(self, mock_domain_services, mock_application_services):
        """Test complete analysis workflow."""
        # Setup mocks
        mock_analysis_service = mock_domain_services['analysis_service']
        mock_analysis_service.start_analysis = AsyncMock(return_value=Mock(id='analysis-123'))
        mock_analysis_service.complete_analysis = AsyncMock(return_value=Mock(id='analysis-123', status=AnalysisStatus.COMPLETED))

        service = AnalysisApplicationService(
            domain_services=mock_domain_services,
            application_services=mock_application_services
        )

        # Execute workflow
        result = await service.perform_analysis_workflow(
            document_id='doc-123',
            analysis_type=AnalysisType.SEMANTIC_SIMILARITY
        )

        # Verify calls
        mock_analysis_service.start_analysis.assert_called_once()
        mock_analysis_service.complete_analysis.assert_called_once()

        assert result.id == 'analysis-123'
        assert result.status == AnalysisStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(self, mock_domain_services, mock_application_services):
        """Test error handling in analysis workflow."""
        # Setup mock to raise exception
        mock_analysis_service = mock_domain_services['analysis_service']
        mock_analysis_service.start_analysis = AsyncMock(side_effect=Exception("Analysis failed"))

        service = AnalysisApplicationService(
            domain_services=mock_domain_services,
            application_services=mock_application_services
        )

        # Execute and expect error handling
        with pytest.raises(Exception, match="Analysis failed"):
            await service.perform_analysis_workflow(
                document_id='doc-123',
                analysis_type=AnalysisType.CODE_QUALITY
            )

    @pytest.mark.asyncio
    async def test_caching_integration(self, mock_domain_services, mock_application_services):
        """Test caching integration in application service."""
        mock_cache = Mock()
        mock_cache.get = AsyncMock(return_value=None)  # Cache miss
        mock_cache.set = AsyncMock()

        mock_application_services['caching_service'] = Mock()
        mock_application_services['caching_service'].cache = mock_cache

        service = AnalysisApplicationService(
            domain_services=mock_domain_services,
            application_services=mock_application_services
        )

        # This would typically cache analysis results
        # For testing, we verify the cache methods are available
        assert hasattr(service, 'application_services')
        assert 'caching_service' in service.application_services

    @pytest.mark.asyncio
    async def test_monitoring_integration(self, mock_domain_services, mock_application_services):
        """Test monitoring integration in application service."""
        mock_monitoring = Mock()
        mock_monitoring.increment_counter = AsyncMock()

        mock_application_services['monitoring_service'] = mock_monitoring

        service = AnalysisApplicationService(
            domain_services=mock_domain_services,
            application_services=mock_application_services
        )

        # This would typically record metrics
        # For testing, we verify the monitoring methods are available
        assert hasattr(service, 'application_services')
        assert 'monitoring_service' in service.application_services

    @pytest.mark.asyncio
    async def test_transaction_integration(self, mock_domain_services, mock_application_services):
        """Test transaction integration in application service."""
        mock_transaction = Mock()
        mock_transaction.begin_transaction = AsyncMock()

        mock_application_services['transaction_service'] = mock_transaction

        service = AnalysisApplicationService(
            domain_services=mock_domain_services,
            application_services=mock_application_services
        )

        # This would typically wrap operations in transactions
        # For testing, we verify the transaction methods are available
        assert hasattr(service, 'application_services')
        assert 'transaction_service' in service.application_services
