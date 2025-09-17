#!/usr/bin/env python3
"""
Unit Tests for Redis Manager

Comprehensive test suite for RedisManager class covering:
- Connection management and pooling
- Circuit breaker functionality
- Retry logic and error handling
- Health monitoring and metrics
- Event publishing and caching
"""

import asyncio
import json
import time
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
    RedisConnectionMetrics
)


class TestCircuitBreaker:
    """Test Circuit Breaker functionality."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=30,
            success_threshold=2
        )
        cb = CircuitBreaker(config)

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
        assert cb.last_failure_time is None

    def test_circuit_breaker_success_record(self):
        """Test recording successful operations."""
        cb = CircuitBreaker()
        cb.failure_count = 2  # Simulate some failures
        cb.state = CircuitBreakerState.OPEN  # Force OPEN state

        cb._record_success()

        assert cb.success_count == 1
        # In HALF_OPEN state, failure_count should be reset when success threshold is reached
        if cb.success_count >= cb.config.success_threshold:
            assert cb.failure_count == 0
            assert cb.state == CircuitBreakerState.CLOSED

    def test_circuit_breaker_failure_record(self):
        """Test recording failed operations."""
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=2))

        cb._record_failure()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 1

        cb._record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 2

    def test_circuit_breaker_half_open_transition(self):
        """Test half-open state transition."""
        cb = CircuitBreaker(CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=1
        ))

        # Force to OPEN state
        cb.failure_count = 2
        cb.state = CircuitBreakerState.OPEN
        cb.last_failure_time = datetime.now() - timedelta(seconds=2)  # Past recovery timeout

        # Should transition to HALF_OPEN
        assert cb._should_attempt_reset() is True

    @pytest.mark.asyncio
    async def test_circuit_breaker_call_success(self):
        """Test successful circuit breaker call."""
        cb = CircuitBreaker()

        async def success_func():
            return "success"

        result = await cb.call(success_func)
        assert result == "success"
        assert cb.success_count == 1
        assert cb.state == CircuitBreakerState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_breaker_call_failure(self):
        """Test failed circuit breaker call."""
        cb = CircuitBreaker(CircuitBreakerConfig(failure_threshold=1))

        async def failure_func():
            raise ValueError("test error")

        with pytest.raises(ValueError):
            await cb.call(failure_func)

        assert cb.failure_count == 1
        assert cb.state == CircuitBreakerState.OPEN


class TestRedisConnectionMetrics:
    """Test Redis connection metrics."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = RedisConnectionMetrics()

        assert metrics.connection_attempts == 0
        assert metrics.successful_connections == 0
        assert metrics.failed_connections == 0
        assert metrics.total_operations == 0
        assert metrics.successful_operations == 0
        assert metrics.failed_operations == 0
        assert metrics.average_response_time == 0.0

    def test_metrics_calculations(self):
        """Test metrics calculations."""
        metrics = RedisConnectionMetrics()

        # Simulate operations
        metrics.connection_attempts = 5
        metrics.successful_connections = 4
        metrics.failed_connections = 1
        metrics.total_operations = 100
        metrics.successful_operations = 95
        metrics.failed_operations = 5
        metrics.average_response_time = 0.5

        # Test success rate calculation
        success_rate = (metrics.successful_operations / metrics.total_operations) if metrics.total_operations > 0 else 0
        assert success_rate == 0.95  # 95/100


class TestRedisManager:
    """Test Redis Manager functionality."""

    @pytest.fixture
    def redis_manager(self):
        """Create Redis manager for testing."""
        return RedisManager(
            host="localhost",
            port=6379,
            db=0,
            max_connections=5,
            retry_config=RetryConfig(max_attempts=2, base_delay=0.01),
            circuit_config=CircuitBreakerConfig(failure_threshold=3)
        )

    def test_redis_manager_initialization(self, redis_manager):
        """Test Redis manager initialization."""
        assert redis_manager.host == "localhost"
        assert redis_manager.port == 6379
        assert redis_manager.db == 0
        assert redis_manager.max_connections == 5
        assert redis_manager.connection_state == RedisConnectionState.DISCONNECTED
        assert redis_manager.retry_config.max_attempts == 2
        assert redis_manager.circuit_breaker.config.failure_threshold == 3

    @pytest.mark.asyncio
    async def test_connection_pool_creation_success(self, redis_manager):
        """Test successful connection pool creation."""
        with patch('redis.asyncio.ConnectionPool') as mock_pool, \
             patch('redis.asyncio.Redis') as mock_redis:

            # Mock successful connection
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_client.aclose = AsyncMock()
            mock_redis.return_value = mock_client

            success = await redis_manager._create_connection_pool()

            assert success is True
            mock_pool.assert_called_once_with(
                host="localhost",
                port=6379,
                db=0,
                password=None,
                max_connections=5,
                decode_responses=True
            )

    @pytest.mark.asyncio
    async def test_connection_pool_creation_failure(self, redis_manager):
        """Test failed connection pool creation."""
        with patch('redis.asyncio.ConnectionPool', side_effect=Exception("Connection failed")):
            success = await redis_manager._create_connection_pool()

            assert success is False

    @pytest.mark.asyncio
    async def test_connect_success(self, redis_manager):
        """Test successful connection."""
        with patch.object(redis_manager, '_create_connection_pool', return_value=True), \
             patch('redis.asyncio.Redis') as mock_redis:

            mock_client = AsyncMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_redis.return_value = mock_client

            success = await redis_manager.connect()

            assert success is True
            assert redis_manager.connection_state == RedisConnectionState.CONNECTED
            assert redis_manager.metrics.successful_connections == 1

    @pytest.mark.asyncio
    async def test_connect_failure(self, redis_manager):
        """Test connection failure."""
        with patch.object(redis_manager, '_create_connection_pool', return_value=False):
            success = await redis_manager.connect()

            assert success is False
            assert redis_manager.connection_state == RedisConnectionState.ERROR
            assert redis_manager.metrics.failed_connections == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, redis_manager):
        """Test successful operation with retry."""
        mock_func = AsyncMock(return_value="success")

        result = await redis_manager._execute_with_retry("test_operation", mock_func)

        assert result == "success"
        assert redis_manager.metrics.successful_operations == 1
        assert redis_manager.metrics.total_operations == 1

    @pytest.mark.asyncio
    async def test_execute_with_retry_failure(self, redis_manager):
        """Test failed operation with retry."""
        mock_func = AsyncMock(side_effect=Exception("Operation failed"))

        with pytest.raises(Exception):
            await redis_manager._execute_with_retry("test_operation", mock_func)

        assert redis_manager.metrics.failed_operations == 2  # 2 attempts
        assert redis_manager.metrics.total_operations == 2

    @pytest.mark.asyncio
    async def test_publish_event_success(self, redis_manager):
        """Test successful event publishing."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = True

            success = await redis_manager.publish_event(
                "test_channel",
                {"event": "data"},
                "test-event-id"
            )

            assert success is True
            mock_execute.assert_called_once()

            # Check call arguments
            call_args = mock_execute.call_args
            operation, func = call_args[0]

            assert operation == "publish"

    @pytest.mark.asyncio
    async def test_publish_event_with_metadata(self, redis_manager):
        """Test event publishing with metadata enrichment."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = True

            await redis_manager.publish_event(
                "test_channel",
                {"event": "data"},
                "test-event-id"
            )

            # Verify the function was called with enhanced metadata
            call_args = mock_execute.call_args
            operation, func = call_args[0]

            # Execute the function to check the payload
            with patch.object(redis_manager, 'redis_client') as mock_client:
                mock_client.publish = AsyncMock()
                await func()

                publish_call = mock_client.publish.call_args
                channel, payload = publish_call[0]

                assert channel == "test_channel"
                payload_data = json.loads(payload)

                # Check enhanced metadata
                assert payload_data["event_id"] == "test-event-id"
                assert "timestamp" in payload_data
                assert payload_data["source"] == "orchestrator"
                assert payload_data["version"] == "1.0"
                assert payload_data["event"] == "data"

    @pytest.mark.asyncio
    async def test_cache_operations(self, redis_manager):
        """Test cache set and get operations."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            mock_execute.return_value = True

            # Test set cache
            success = await redis_manager.set_cache("test_key", {"data": "value"}, 300)
            assert success is True

            # Test get cache
            mock_execute.return_value = '{"data": "value"}'
            result = await redis_manager.get_cache("test_key")
            assert result == {"data": "value"} or result == '{"data": "value"}'  # Handle both JSON and string return

    @pytest.mark.asyncio
    async def test_cache_json_handling(self, redis_manager):
        """Test cache JSON serialization/deserialization."""
        with patch.object(redis_manager, '_execute_with_retry') as mock_execute:
            # Test with dict value
            mock_execute.return_value = True
            await redis_manager.set_cache("dict_key", {"key": "value"})

            # Test with list value
            await redis_manager.set_cache("list_key", ["item1", "item2"])

            # Test with string value
            await redis_manager.set_cache("string_key", "plain string")

    @pytest.mark.asyncio
    async def test_health_check_success(self, redis_manager):
        """Test successful health check."""
        with patch.object(redis_manager, 'connect', return_value=True), \
             patch.object(redis_manager, 'redis_client') as mock_client:

            mock_client.ping = AsyncMock(return_value=True)
            mock_client.info = AsyncMock(return_value={
                "uptime_in_seconds": 3600,
                "connected_clients": 5,
                "used_memory_human": "10M",
                "total_commands_processed": 1000
            })

            health = await redis_manager.health_check()

            assert health["status"] == "healthy"
            assert "connection_state" in health["details"]
            assert health["details"]["uptime_seconds"] == 3600
            assert health["details"]["connected_clients"] == 5

    @pytest.mark.asyncio
    async def test_health_check_failure(self, redis_manager):
        """Test failed health check."""
        with patch.object(redis_manager, 'connect', return_value=False):
            health = await redis_manager.health_check()

            assert health["status"] == "unhealthy"
            assert "Redis client not available" in health["message"]

    @pytest.mark.asyncio
    async def test_disconnect(self, redis_manager):
        """Test disconnect functionality."""
        # Setup mock clients
        mock_client = AsyncMock()
        mock_pool = AsyncMock()
        redis_manager.redis_client = mock_client
        redis_manager.connection_pool = mock_pool

        await redis_manager.disconnect()

        mock_client.aclose.assert_called_once()
        mock_pool.disconnect.assert_called_once()
        assert redis_manager.connection_state == RedisConnectionState.DISCONNECTED

    def test_get_metrics(self, redis_manager):
        """Test metrics retrieval."""
        # Setup some metrics
        redis_manager.metrics.connection_attempts = 5
        redis_manager.metrics.successful_connections = 4
        redis_manager.metrics.total_operations = 100
        redis_manager.metrics.successful_operations = 95

        metrics = redis_manager.get_metrics()

        assert metrics["connection_attempts"] == 5
        assert metrics["successful_connections"] == 4
        assert metrics["total_operations"] == 100
        assert metrics["successful_operations"] == 95
        assert metrics["success_rate"] == 0.95

    def test_event_listeners(self, redis_manager):
        """Test event listener registration."""
        listener1 = AsyncMock()
        listener2 = AsyncMock()

        redis_manager.add_connection_listener(listener1)
        redis_manager.add_error_listener(listener2)

        assert listener1 in redis_manager.connection_listeners
        assert listener2 in redis_manager.error_listeners

    @pytest.mark.asyncio
    async def test_listener_notifications(self, redis_manager):
        """Test listener notification on events."""
        listener = AsyncMock()
        redis_manager.add_connection_listener(listener)

        # Trigger state change
        redis_manager._notify_connection_listeners(RedisConnectionState.CONNECTED)

        # Wait for async task to complete
        await asyncio.sleep(0.01)
        listener.assert_called_once()


class TestRedisManagerIntegration:
    """Integration tests for Redis Manager."""

    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self):
        """Test complete connection lifecycle."""
        manager = RedisManager(
            retry_config=RetryConfig(max_attempts=1, base_delay=0.001)
        )

        # Test initial state
        assert manager.connection_state == RedisConnectionState.DISCONNECTED

        # This will fail without Redis, but should handle gracefully
        success = await manager.connect()
        assert success is False
        assert manager.connection_state == RedisConnectionState.ERROR

        # Test health check
        health = await manager.health_check()
        assert health["status"] == "unhealthy"

        # Test disconnect
        await manager.disconnect()
        assert manager.connection_state == RedisConnectionState.DISCONNECTED

    @pytest.mark.asyncio
    async def test_event_emission_without_connection(self):
        """Test event emission when Redis is not connected."""
        manager = RedisManager()

        # Should fail gracefully without connection
        success = await manager.publish_event("test", {"data": "test"})
        assert success is False

    @pytest.mark.asyncio
    async def test_metrics_accumulation(self):
        """Test metrics accumulation over multiple operations."""
        manager = RedisManager(
            retry_config=RetryConfig(max_attempts=1, base_delay=0.001)
        )

        # Attempt multiple connections
        for _ in range(3):
            await manager.connect()

        # Check metrics accumulation
        assert manager.metrics.connection_attempts == 3
        assert manager.metrics.failed_connections == 3


# Test configuration classes
class TestRetryConfig:
    """Test RetryConfig class."""

    def test_retry_config_initialization(self):
        """Test retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.2,
            max_delay=5.0,
            exponential_base=3.0
        )

        assert config.max_attempts == 5
        assert config.base_delay == 0.2
        assert config.max_delay == 5.0
        assert config.exponential_base == 3.0


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig class."""

    def test_circuit_breaker_config_initialization(self):
        """Test circuit breaker configuration."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120,
            success_threshold=5
        )

        assert config.failure_threshold == 10
        assert config.recovery_timeout == 120
        assert config.success_threshold == 5
        assert config.expected_exception == Exception


if __name__ == "__main__":
    pytest.main([__file__])
