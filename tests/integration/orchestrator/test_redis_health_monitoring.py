#!/usr/bin/env python3
"""
Redis Health Monitoring and Metrics Tests

Comprehensive test suite for Redis health monitoring, metrics collection,
and system reliability features including:
- Health check mechanisms
- Metrics aggregation and reporting
- Circuit breaker monitoring
- Connection pool monitoring
- Performance metrics tracking
- Alerting and notification systems
"""

import asyncio
import time
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch, call
import pytest
from datetime import datetime, timedelta

# Add services to path for testing
import sys
from pathlib import Path
services_path = Path(__file__).parent.parent.parent.parent / "services"
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from services.orchestrator.modules.redis_manager import (
    RedisManager,
    RedisConnectionState,
    CircuitBreakerState,
    CircuitBreaker,
    RetryConfig,
    CircuitBreakerConfig,
    RedisConnectionMetrics,
    redis_manager,
    initialize_redis_manager,
    get_redis_health,
    get_redis_metrics
)

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class TestRedisHealthMonitoring:
    """Test Redis health monitoring functionality."""

    @pytest.fixture
    def redis_manager_instance(self):
        """Create Redis manager instance for testing."""
        return RedisManager(
            host="localhost",
            port=6379,
            db=0,
            max_connections=5,
            retry_config=RetryConfig(max_attempts=3, base_delay=0.01),
            circuit_config=CircuitBreakerConfig(failure_threshold=3)
        )

    @pytest.mark.asyncio
    async def test_health_check_healthy_connection(self, redis_manager_instance):
        """Test health check with healthy Redis connection."""
        with patch.object(redis_manager_instance, 'connect', return_value=True), \
             patch.object(redis_manager_instance, 'redis_client') as mock_client:

            # Mock Redis INFO command
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.info = AsyncMock(return_value={
                "uptime_in_seconds": 3600,
                "connected_clients": 5,
                "used_memory_human": "10M",
                "total_commands_processed": 1000,
                "keyspace_hits": 950,
                "keyspace_misses": 50
            })

            health = await redis_manager_instance.health_check()

            assert health["status"] == "healthy"
            assert health["message"] == "Redis connection healthy"
            assert health["details"]["connection_state"] == "connected"
            assert health["details"]["uptime_seconds"] == 3600
            assert health["details"]["connected_clients"] == 5
            assert health["details"]["used_memory"] == "10M"
            assert health["details"]["total_commands_processed"] == 1000

    @pytest.mark.asyncio
    async def test_health_check_unhealthy_connection(self, redis_manager_instance):
        """Test health check with unhealthy Redis connection."""
        with patch.object(redis_manager_instance, 'connect', return_value=False):
            health = await redis_manager_instance.health_check()

            assert health["status"] == "unhealthy"
            assert "Redis client not available" in health["message"]
            assert health["details"]["connection_state"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_connection_failure_during_check(self, redis_manager_instance):
        """Test health check when connection fails during the check."""
        with patch.object(redis_manager_instance, 'connect', return_value=True), \
             patch.object(redis_manager_instance, 'redis_client') as mock_client:

            # Simulate ping failure
            mock_client.ping = AsyncMock(side_effect=Exception("Connection timeout"))

            health = await redis_manager_instance.health_check()

            assert health["status"] == "unhealthy"
            assert "Redis health check failed" in health["message"]
            assert health["details"]["connection_state"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_cached_status(self, redis_manager_instance):
        """Test cached health status to avoid excessive checks."""
        original_time = time.time()
        redis_manager_instance.last_health_check = original_time

        with patch('time.time', return_value=original_time + 15):  # Less than 30 seconds
            # Should return cached status without performing check
            health = await redis_manager_instance.health_check()

            # Since no actual check was performed, should get cached unhealthy status
            assert health["status"] == "unhealthy"
            assert "Redis connection not healthy" in health["message"]

    @pytest.mark.asyncio
    async def test_health_check_info_command_failure(self, redis_manager_instance):
        """Test health check when INFO command fails."""
        with patch.object(redis_manager_instance, 'connect', return_value=True), \
             patch.object(redis_manager_instance, 'redis_client') as mock_client:

            mock_client.ping = AsyncMock(return_value=True)
            mock_client.info = AsyncMock(side_effect=Exception("INFO command failed"))

            health = await redis_manager_instance.health_check()

            assert health["status"] == "unhealthy"
            assert "Redis health check failed" in health["message"]
            assert "INFO command failed" in health["details"]["error"]


class TestRedisMetricsCollection:
    """Test Redis metrics collection and reporting."""

    @pytest.fixture
    def redis_manager_instance(self):
        """Create Redis manager instance for testing."""
        return RedisManager()

    def test_initial_metrics_state(self, redis_manager_instance):
        """Test initial state of metrics."""
        metrics = redis_manager_instance.get_metrics()

        assert metrics["connection_state"] == "disconnected"
        assert metrics["circuit_breaker_state"] == "closed"
        assert metrics["connection_attempts"] == 0
        assert metrics["successful_connections"] == 0
        assert metrics["failed_connections"] == 0
        assert metrics["total_operations"] == 0
        assert metrics["successful_operations"] == 0
        assert metrics["failed_operations"] == 0
        assert metrics["average_response_time"] == 0.0
        assert metrics["success_rate"] == 0

    @pytest.mark.asyncio
    async def test_connection_attempt_metrics(self, redis_manager_instance):
        """Test metrics collection for connection attempts."""
        # Attempt connection (will fail without Redis)
        await redis_manager_instance.connect()

        metrics = redis_manager_instance.get_metrics()

        assert metrics["connection_attempts"] == 1
        assert metrics["failed_connections"] == 1
        assert metrics["last_connection_attempt"] is not None

    @pytest.mark.asyncio
    async def test_operation_metrics_collection(self, redis_manager_instance):
        """Test metrics collection for Redis operations."""
        with patch.object(redis_manager_instance, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            # Simulate successful operations
            await redis_manager_instance.set_cache("test_key", "test_value")
            await redis_manager_instance.get_cache("test_key")
            await redis_manager_instance.delete_cache("test_key")

            metrics = redis_manager_instance.get_metrics()

            assert metrics["total_operations"] == 3
            assert metrics["successful_operations"] == 3
            assert metrics["failed_operations"] == 0
            assert metrics["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_operation_failure_metrics(self, redis_manager_instance):
        """Test metrics collection for failed operations."""
        with patch.object(redis_manager_instance, '_execute_with_retry') as mock_execute:
            mock_execute.side_effect = Exception("Operation failed")

            # Attempt operations that will fail
            await redis_manager_instance.set_cache("test_key", "test_value")
            await redis_manager_instance.get_cache("test_key")

            metrics = redis_manager_instance.get_metrics()

            assert metrics["total_operations"] == 2
            assert metrics["successful_operations"] == 0
            assert metrics["failed_operations"] == 2
            assert metrics["success_rate"] == 0.0
            assert metrics["last_failed_operation"] is not None

    @pytest.mark.asyncio
    async def test_response_time_tracking(self, redis_manager_instance):
        """Test response time tracking in metrics."""
        with patch.object(redis_manager_instance, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            # First operation
            await redis_manager_instance.set_cache("test_key", "test_value")

            metrics1 = redis_manager_instance.get_metrics()
            first_response_time = metrics1["average_response_time"]

            # Second operation
            await redis_manager_instance.get_cache("test_key")

            metrics2 = redis_manager_instance.get_metrics()
            second_response_time = metrics2["average_response_time"]

            # Response time should be tracked
            assert metrics2["last_successful_operation"] is not None
            # Average should be calculated
            assert isinstance(second_response_time, float)

    @pytest.mark.asyncio
    async def test_circuit_breaker_metrics(self, redis_manager_instance):
        """Test circuit breaker state in metrics."""
        # Initially closed
        metrics = redis_manager_instance.get_metrics()
        assert metrics["circuit_breaker_state"] == "closed"

        # Force circuit breaker to open
        redis_manager_instance.circuit_breaker.failure_count = 5
        redis_manager_instance.circuit_breaker.state = CircuitBreakerState.OPEN

        metrics = redis_manager_instance.get_metrics()
        assert metrics["circuit_breaker_state"] == "open"

    def test_metrics_success_rate_calculation(self, redis_manager_instance):
        """Test success rate calculation with edge cases."""
        # No operations
        metrics = redis_manager_instance.get_metrics()
        assert metrics["success_rate"] == 0

        # All successful operations
        redis_manager_instance.metrics.total_operations = 10
        redis_manager_instance.metrics.successful_operations = 10
        metrics = redis_manager_instance.get_metrics()
        assert metrics["success_rate"] == 1.0

        # Mixed operations
        redis_manager_instance.metrics.total_operations = 100
        redis_manager_instance.metrics.successful_operations = 85
        metrics = redis_manager_instance.get_metrics()
        assert metrics["success_rate"] == 0.85

        # All failed operations
        redis_manager_instance.metrics.total_operations = 5
        redis_manager_instance.metrics.successful_operations = 0
        metrics = redis_manager_instance.get_metrics()
        assert metrics["success_rate"] == 0.0


class TestRedisCircuitBreakerMonitoring:
    """Test circuit breaker monitoring and alerting."""

    @pytest.fixture
    def circuit_breaker(self):
        """Create circuit breaker for testing."""
        return CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30
        ))

    def test_circuit_breaker_state_transitions(self, circuit_breaker):
        """Test circuit breaker state transitions."""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

        # Record failures
        circuit_breaker._record_failure()
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

        circuit_breaker._record_failure()
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

        circuit_breaker._record_failure()
        assert circuit_breaker.state == CircuitBreakerState.OPEN

    def test_circuit_breaker_recovery_timeout(self, circuit_breaker):
        """Test circuit breaker recovery timeout logic."""
        # Force to OPEN state
        circuit_breaker.failure_count = 3
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=35)  # Past timeout

        # Should allow reset attempt
        assert circuit_breaker._should_attempt_reset() is True

        # Recent failure
        circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=10)  # Within timeout

        # Should not allow reset attempt
        assert circuit_breaker._should_attempt_reset() is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_success_recovery(self, circuit_breaker):
        """Test circuit breaker recovery after successful operations."""
        # Force to OPEN state
        circuit_breaker.failure_count = 3
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.last_failure_time = datetime.now() - timedelta(seconds=35)

        # Transition to HALF_OPEN
        assert circuit_breaker._should_attempt_reset() is True

        # Simulate successful operation
        async def success_func():
            return "success"

        result = await circuit_breaker.call(success_func)
        assert result == "success"

        # Should transition to CLOSED after success threshold
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_in_half_open(self, circuit_breaker):
        """Test circuit breaker behavior when failure occurs in half-open state."""
        # Force to HALF_OPEN state
        circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        circuit_breaker.success_count = 1

        # Simulate failed operation
        async def failure_func():
            raise Exception("Operation failed")

        with pytest.raises(Exception):
            await circuit_breaker.call(failure_func)

        # Should transition back to OPEN
        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.success_count == 0


class TestRedisConnectionPoolMonitoring:
    """Test Redis connection pool monitoring."""

    @pytest.fixture
    def redis_manager_instance(self):
        """Create Redis manager instance for testing."""
        return RedisManager(max_connections=10)

    @pytest.mark.asyncio
    async def test_connection_pool_creation_monitoring(self, redis_manager_instance):
        """Test connection pool creation and monitoring."""
        with patch('redis.asyncio.ConnectionPool') as mock_pool, \
             patch('redis.asyncio.Redis') as mock_redis:

            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.aclose = AsyncMock()
            mock_redis.return_value = mock_client

            # Create connection pool
            success = await redis_manager_instance._create_connection_pool()

            assert success is True

            # Verify connection pool was created with correct parameters
            mock_pool.assert_called_once_with(
                host="localhost",
                port=6379,
                db=0,
                password=None,
                max_connections=10,
                decode_responses=True
            )

    @pytest.mark.asyncio
    async def test_connection_pool_health_in_info(self, redis_manager_instance):
        """Test connection pool health information in Redis INFO."""
        with patch.object(redis_manager_instance, 'connect', return_value=True), \
             patch.object(redis_manager_instance, 'redis_client') as mock_client:

            mock_client.ping = AsyncMock(return_value=True)
            mock_client.info = AsyncMock(return_value={
                "connected_clients": 8,
                "blocked_clients": 0,
                "maxclients": 1000,
                "total_connections_received": 150,
                "rejected_connections": 2
            })

            health = await redis_manager_instance.health_check()

            assert health["details"]["connected_clients"] == 8
            assert health["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_connection_pool_exhaustion_detection(self, redis_manager_instance):
        """Test detection of connection pool exhaustion."""
        with patch.object(redis_manager_instance, 'connect', return_value=True), \
             patch.object(redis_manager_instance, 'redis_client') as mock_client:

            mock_client.ping = AsyncMock(return_value=True)
            mock_client.info = AsyncMock(return_value={
                "connected_clients": 12,  # More than max_connections (10)
                "maxclients": 1000,
                "rejected_connections": 5
            })

            health = await redis_manager_instance.health_check()

            # Should still be healthy but we can detect high connection usage
            assert health["status"] == "healthy"
            assert health["details"]["connected_clients"] == 12


class TestRedisPerformanceMetrics:
    """Test Redis performance metrics and monitoring."""

    @pytest.fixture
    def redis_manager_instance(self):
        """Create Redis manager instance for testing."""
        return RedisManager()

    @pytest.mark.asyncio
    async def test_operation_response_time_tracking(self, redis_manager_instance):
        """Test detailed response time tracking for operations."""
        with patch.object(redis_manager_instance, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            # Record start time
            start_time = time.time()

            # Perform operation
            await redis_manager_instance.set_cache("perf_test", "value")

            # Check that response time was tracked
            metrics = redis_manager_instance.get_metrics()

            assert metrics["last_successful_operation"] is not None
            assert metrics["average_response_time"] > 0

    @pytest.mark.asyncio
    async def test_operation_throughput_calculation(self, redis_manager_instance):
        """Test operation throughput calculation."""
        with patch.object(redis_manager_instance, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            # Perform multiple operations
            operations = 50
            for i in range(operations):
                await redis_manager_instance.set_cache(f"key_{i}", f"value_{i}")

            metrics = redis_manager_instance.get_metrics()

            assert metrics["total_operations"] == operations
            assert metrics["successful_operations"] == operations
            assert metrics["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_error_rate_calculation(self, redis_manager_instance):
        """Test error rate calculation and tracking."""
        with patch.object(redis_manager_instance, '_execute_with_retry') as mock_execute:
            # Mix of successes and failures
            call_count = 0

            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 3 == 0:  # Every 3rd call fails
                    raise Exception("Simulated failure")
                return "success"

            mock_execute.side_effect = side_effect

            # Perform 9 operations (should have 3 failures, 6 successes)
            for i in range(9):
                try:
                    await redis_manager_instance.set_cache(f"error_test_{i}", f"value_{i}")
                except:
                    pass  # Expected failures

            metrics = redis_manager_instance.get_metrics()

            assert metrics["total_operations"] == 9
            assert metrics["successful_operations"] == 6
            assert metrics["failed_operations"] == 3
            assert metrics["success_rate"] == (6/9)  # 2/3 success rate

    @pytest.mark.asyncio
    async def test_performance_under_load(self, redis_manager_instance):
        """Test performance metrics under concurrent load."""
        with patch.object(redis_manager_instance, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = "success"

            # Simulate concurrent operations
            async def perform_operation(i):
                await redis_manager_instance.set_cache(f"load_test_{i}", f"value_{i}")

            # Run multiple operations concurrently
            tasks = [perform_operation(i) for i in range(20)]
            await asyncio.gather(*tasks)

            metrics = redis_manager_instance.get_metrics()

            assert metrics["total_operations"] == 20
            assert metrics["successful_operations"] == 20
            assert metrics["average_response_time"] > 0


class TestRedisAlertingAndNotifications:
    """Test Redis alerting and notification systems."""

    @pytest.fixture
    def redis_manager_instance(self):
        """Create Redis manager instance for testing."""
        manager = RedisManager()
        # Add mock listeners
        manager.add_connection_listener(AsyncMock())
        manager.add_error_listener(AsyncMock())
        return manager

    @pytest.mark.asyncio
    async def test_connection_state_change_notifications(self, redis_manager_instance):
        """Test notifications on connection state changes."""
        listener = AsyncMock()
        redis_manager_instance.add_connection_listener(listener)

        # Trigger state change
        redis_manager_instance._notify_connection_listeners(RedisConnectionState.CONNECTED)

        # Allow async task to complete
        await asyncio.sleep(0.01)

        # Verify listener was called
        listener.assert_called_once_with(
            RedisConnectionState.DISCONNECTED,
            RedisConnectionState.CONNECTED
        )

    @pytest.mark.asyncio
    async def test_error_notifications(self, redis_manager_instance):
        """Test error notifications."""
        listener = AsyncMock()
        redis_manager_instance.add_error_listener(listener)

        # Trigger error notification
        test_error = Exception("Test connection error")
        redis_manager_instance._notify_error_listeners(test_error, "connect")

        # Allow async task to complete
        await asyncio.sleep(0.01)

        # Verify listener was called
        listener.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_based_alerting(self, redis_manager_instance):
        """Test health-based alerting mechanisms."""
        with patch('services.orchestrator.modules.redis_manager.fire_and_forget') as mock_fire_and_forget, \
             patch.object(redis_manager_instance, 'connect', return_value=False):

            # Perform health check that will fail
            await redis_manager_instance.health_check()

            # Verify alerting was triggered
            mock_fire_and_forget.assert_called()

    @pytest.mark.asyncio
    async def test_circuit_breaker_alerting(self, redis_manager_instance):
        """Test circuit breaker state change alerting."""
        with patch('services.orchestrator.modules.redis_manager.fire_and_forget') as mock_fire_and_forget:

            # Force circuit breaker to open
            cb = redis_manager_instance.circuit_breaker
            for _ in range(cb.config.failure_threshold):
                cb._record_failure()

            # Verify alert was triggered
            mock_fire_and_forget.assert_called_with(
                "error",
                "Circuit breaker opened after 3 failures",
                "orchestrator"
            )


class TestRedisGlobalManagerFunctions:
    """Test global Redis manager functions."""

    @pytest.mark.asyncio
    async def test_global_manager_initialization(self):
        """Test global Redis manager initialization."""
        with patch('services.orchestrator.modules.redis_manager.redis_manager') as mock_manager, \
             patch('services.orchestrator.modules.redis_manager.fire_and_forget') as mock_fire_and_forget:

            mock_manager.connect = AsyncMock(return_value=True)

            success = await initialize_redis_manager()

            assert success is True
            mock_fire_and_forget.assert_called_with(
                "info",
                "Redis manager initialized successfully",
                "orchestrator"
            )

    @pytest.mark.asyncio
    async def test_global_manager_initialization_failure(self):
        """Test global Redis manager initialization failure."""
        with patch('services.orchestrator.modules.redis_manager.redis_manager') as mock_manager, \
             patch('services.orchestrator.modules.redis_manager.fire_and_forget') as mock_fire_and_forget:

            mock_manager.connect = AsyncMock(return_value=False)

            success = await initialize_redis_manager()

            assert success is False
            mock_fire_and_forget.assert_called_with(
                "error",
                "Redis manager initialization failed - some features may be degraded",
                "orchestrator"
            )

    @pytest.mark.asyncio
    async def test_global_health_function(self):
        """Test global health check function."""
        with patch('services.orchestrator.modules.redis_manager.redis_manager') as mock_manager:

            mock_health = {"status": "healthy", "message": "All good"}
            mock_manager.health_check = AsyncMock(return_value=mock_health)

            health = await get_redis_health()

            assert health == mock_health

    def test_global_metrics_function(self):
        """Test global metrics function."""
        with patch('services.orchestrator.modules.redis_manager.redis_manager') as mock_manager:

            mock_metrics = {"total_operations": 100, "success_rate": 0.95}
            mock_manager.get_metrics = MagicMock(return_value=mock_metrics)

            metrics = get_redis_metrics()

            assert metrics == mock_metrics


if __name__ == "__main__":
    pytest.main([__file__])
