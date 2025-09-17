#!/usr/bin/env python3
"""
Redis Manager - Enterprise Redis Connection Management

Provides robust Redis connection management with:
- Connection pooling and health monitoring
- Automatic retry logic with exponential backoff
- Circuit breaker pattern for fault tolerance
- Comprehensive error handling and logging
- Event emission integration
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import traceback

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

from services.shared.core.constants_new import ServiceNames
from services.shared.monitoring.logging import fire_and_forget
from services.shared.core.config.config import get_config_value


class RedisConnectionState(Enum):
    """Redis connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    CIRCUIT_OPEN = "circuit_open"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class RedisConnectionMetrics:
    """Redis connection metrics."""
    connection_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    last_connection_attempt: Optional[datetime] = None
    last_successful_operation: Optional[datetime] = None
    last_failed_operation: Optional[datetime] = None


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: Exception = Exception
    success_threshold: int = 3


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = 3
    base_delay: float = 0.1  # seconds
    max_delay: float = 10.0  # seconds
    exponential_base: float = 2.0


class CircuitBreaker:
    """Circuit breaker implementation."""

    def __init__(self, config: CircuitBreakerConfig = None):
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        if self.state != CircuitBreakerState.OPEN:
            return False

        if not self.last_failure_time:
            return True

        time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
        return time_since_failure >= self.config.recovery_timeout

    def _record_success(self):
        """Record successful operation."""
        self.success_count += 1
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                self.success_count = 0
                fire_and_forget("info", "Circuit breaker closed - service recovered", ServiceNames.ORCHESTRATOR)

    def _record_failure(self):
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            self.success_count = 0
            fire_and_forget("warning", f"Circuit breaker opened after failure in half-open state", ServiceNames.ORCHESTRATOR)
        elif self.failure_count >= self.config.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            fire_and_forget("error", f"Circuit breaker opened after {self.failure_count} failures", ServiceNames.ORCHESTRATOR)

    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                fire_and_forget("info", "Circuit breaker half-open - testing service recovery", ServiceNames.ORCHESTRATOR)
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._record_success()
            return result
        except self.config.expected_exception as e:
            self._record_failure()
            raise e


class RedisManager:
    """Enterprise Redis connection manager with circuit breaker and retry logic."""

    def __init__(self,
                 host: str = None,
                 port: int = 6379,
                 db: int = 0,
                 password: str = None,
                 max_connections: int = 10,
                 retry_config: RetryConfig = None,
                 circuit_config: CircuitBreakerConfig = None):

        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis dependencies not available")

        self.host = host or get_config_value("REDIS_HOST", "redis", env_key="REDIS_HOST")
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections

        # Connection state
        self.connection_state = RedisConnectionState.DISCONNECTED
        self.redis_client: Optional[redis.Redis] = None
        self.connection_pool = None

        # Circuit breaker and retry
        self.circuit_breaker = CircuitBreaker(circuit_config or CircuitBreakerConfig())
        self.retry_config = retry_config or RetryConfig()

        # Metrics and monitoring
        self.metrics = RedisConnectionMetrics()
        self.health_check_interval = 30  # seconds
        self.last_health_check = 0

        # Event callbacks
        self.connection_listeners: List[Callable] = []
        self.error_listeners: List[Callable] = []

    def add_connection_listener(self, listener: Callable):
        """Add connection state change listener."""
        self.connection_listeners.append(listener)

    def add_error_listener(self, listener: Callable):
        """Add error event listener."""
        self.error_listeners.append(listener)

    def _notify_connection_listeners(self, new_state: RedisConnectionState):
        """Notify connection listeners of state change."""
        for listener in self.connection_listeners:
            try:
                asyncio.create_task(listener(self.connection_state, new_state))
            except Exception as e:
                fire_and_forget("error", f"Connection listener failed: {e}", ServiceNames.ORCHESTRATOR)

    def _notify_error_listeners(self, error: Exception, operation: str):
        """Notify error listeners."""
        for listener in self.error_listeners:
            try:
                asyncio.create_task(listener(error, operation))
            except Exception as e:
                fire_and_forget("error", f"Error listener failed: {e}", ServiceNames.ORCHESTRATOR)

    async def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry with exponential backoff."""
        delay = self.retry_config.base_delay * (self.retry_config.exponential_base ** attempt)
        return min(delay, self.retry_config.max_delay)

    async def _execute_with_retry(self, operation: str, func: Callable, *args, **kwargs):
        """Execute Redis operation with retry logic."""
        last_exception = None

        for attempt in range(self.retry_config.max_attempts):
            try:
                if attempt > 0:
                    delay = await self._calculate_delay(attempt - 1)
                    await asyncio.sleep(delay)
                    fire_and_forget("info", f"Retrying Redis operation {operation} (attempt {attempt + 1})", ServiceNames.ORCHESTRATOR)

                start_time = time.time()
                result = await self.circuit_breaker.call(func, *args, **kwargs)
                response_time = time.time() - start_time

                # Update metrics
                self.metrics.total_operations += 1
                self.metrics.successful_operations += 1
                self.metrics.last_successful_operation = datetime.now()

                # Update average response time
                if self.metrics.average_response_time == 0:
                    self.metrics.average_response_time = response_time
                else:
                    self.metrics.average_response_time = (
                        self.metrics.average_response_time + response_time
                    ) / 2

                return result

            except Exception as e:
                last_exception = e
                self.metrics.total_operations += 1
                self.metrics.failed_operations += 1
                self.metrics.last_failed_operation = datetime.now()

                fire_and_forget("warning", f"Redis operation {operation} failed (attempt {attempt + 1}): {e}", ServiceNames.ORCHESTRATOR)

                # Notify error listeners
                self._notify_error_listeners(e, operation)

                if attempt == self.retry_config.max_attempts - 1:
                    break

        # All retries failed
        fire_and_forget("error", f"Redis operation {operation} failed after {self.retry_config.max_attempts} attempts", ServiceNames.ORCHESTRATOR)
        raise last_exception

    async def _create_connection_pool(self):
        """Create Redis connection pool."""
        try:
            self.connection_pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                max_connections=self.max_connections,
                decode_responses=True
            )

            # Test connection
            test_client = redis.Redis(connection_pool=self.connection_pool)
            await test_client.ping()
            await test_client.aclose()

            return True

        except Exception as e:
            fire_and_forget("error", f"Failed to create Redis connection pool: {e}", ServiceNames.ORCHESTRATOR)
            return False

    async def connect(self) -> bool:
        """Establish Redis connection with retry logic."""
        if self.connection_state == RedisConnectionState.CONNECTED:
            return True

        if self.connection_state == RedisConnectionState.CIRCUIT_OPEN:
            return False

        old_state = self.connection_state
        self.connection_state = RedisConnectionState.CONNECTING
        self.metrics.connection_attempts += 1
        self.metrics.last_connection_attempt = datetime.now()

        try:
            # Create connection pool
            if not await self._create_connection_pool():
                raise Exception("Failed to create connection pool")

            # Create client
            self.redis_client = redis.Redis(connection_pool=self.connection_pool)

            # Test connection
            await self.redis_client.ping()

            # Update state
            self.connection_state = RedisConnectionState.CONNECTED
            self.metrics.successful_connections += 1

            fire_and_forget("info", f"Successfully connected to Redis at {self.host}:{self.port}", ServiceNames.ORCHESTRATOR)
            self._notify_connection_listeners(self.connection_state)

            return True

        except Exception as e:
            self.connection_state = RedisConnectionState.ERROR
            self.metrics.failed_connections += 1

            fire_and_forget("error", f"Failed to connect to Redis: {e}", ServiceNames.ORCHESTRATOR)
            self._notify_error_listeners(e, "connect")

            # Don't change state to CIRCUIT_OPEN here - let circuit breaker handle it
            return False

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.aclose()
            self.redis_client = None

        if self.connection_pool:
            await self.connection_pool.disconnect()
            self.connection_pool = None

        old_state = self.connection_state
        self.connection_state = RedisConnectionState.DISCONNECTED
        self._notify_connection_listeners(self.connection_state)

        fire_and_forget("info", "Disconnected from Redis", ServiceNames.ORCHESTRATOR)

    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check."""
        current_time = time.time()

        # Only check every health_check_interval seconds
        if current_time - self.last_health_check < self.health_check_interval:
            return self._get_health_status()

        self.last_health_check = current_time

        try:
            if not self.redis_client:
                if not await self.connect():
                    return {
                        "status": "unhealthy",
                        "message": "Redis client not available",
                        "details": {"connection_state": self.connection_state.value}
                    }

            # Test basic operations
            await self.redis_client.ping()
            info = await self.redis_client.info()

            return {
                "status": "healthy",
                "message": "Redis connection healthy",
                "details": {
                    "connection_state": self.connection_state.value,
                    "uptime_seconds": info.get("uptime_in_seconds", 0),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                }
            }

        except Exception as e:
            self.connection_state = RedisConnectionState.ERROR
            return {
                "status": "unhealthy",
                "message": f"Redis health check failed: {e}",
                "details": {
                    "connection_state": self.connection_state.value,
                    "error": str(e),
                    "last_attempt": self.metrics.last_connection_attempt.isoformat() if self.metrics.last_connection_attempt else None
                }
            }

    def _get_health_status(self) -> Dict[str, Any]:
        """Get current health status without performing check."""
        if self.connection_state == RedisConnectionState.CONNECTED:
            return {
                "status": "healthy",
                "message": "Redis connection healthy (cached)",
                "details": {"connection_state": self.connection_state.value}
            }
        else:
            return {
                "status": "unhealthy",
                "message": f"Redis connection not healthy: {self.connection_state.value}",
                "details": {"connection_state": self.connection_state.value}
            }

    async def publish_event(self, channel: str, message: Dict[str, Any], event_id: str = None) -> bool:
        """Publish event to Redis channel with error handling."""
        if not event_id:
            event_id = str(uuid.uuid4())

        # Add standard metadata
        enhanced_message = {
            **message,
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "source": "orchestrator",
            "version": "1.0"
        }

        try:
            async def _publish():
                if not self.redis_client:
                    raise Exception("Redis client not available")

                payload = json.dumps(enhanced_message)
                await self.redis_client.publish(channel, payload)
                return True

            await self._execute_with_retry("publish", _publish)

            fire_and_forget("debug", f"Published event to channel {channel}: {event_id}", ServiceNames.ORCHESTRATOR)
            return True

        except Exception as e:
            fire_and_forget("error", f"Failed to publish event to {channel}: {e}", ServiceNames.ORCHESTRATOR)
            return False

    async def set_cache(self, key: str, value: Any, ttl_seconds: int = None) -> bool:
        """Set cache value with TTL."""
        try:
            async def _set():
                if not self.redis_client:
                    raise Exception("Redis client not available")

                serialized_value = json.dumps(value) if isinstance(value, (dict, list)) else str(value)

                if ttl_seconds:
                    await self.redis_client.setex(key, ttl_seconds, serialized_value)
                else:
                    await self.redis_client.set(key, serialized_value)

                return True

            await self._execute_with_retry("set_cache", _set)

            fire_and_forget("debug", f"Set cache key {key} with TTL {ttl_seconds}", ServiceNames.ORCHESTRATOR)
            return True

        except Exception as e:
            fire_and_forget("error", f"Failed to set cache {key}: {e}", ServiceNames.ORCHESTRATOR)
            return False

    async def get_cache(self, key: str) -> Optional[Any]:
        """Get cache value."""
        try:
            async def _get():
                if not self.redis_client:
                    raise Exception("Redis client not available")

                value = await self.redis_client.get(key)
                if value is None:
                    return None

                # Try to parse as JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value

            result = await self._execute_with_retry("get_cache", _get)

            fire_and_forget("debug", f"Retrieved cache key {key}", ServiceNames.ORCHESTRATOR)
            return result

        except Exception as e:
            fire_and_forget("error", f"Failed to get cache {key}: {e}", ServiceNames.ORCHESTRATOR)
            return None

    async def delete_cache(self, key: str) -> bool:
        """Delete cache key."""
        try:
            async def _delete():
                if not self.redis_client:
                    raise Exception("Redis client not available")

                await self.redis_client.delete(key)
                return True

            await self._execute_with_retry("delete_cache", _delete)

            fire_and_forget("debug", f"Deleted cache key {key}", ServiceNames.ORCHESTRATOR)
            return True

        except Exception as e:
            fire_and_forget("error", f"Failed to delete cache {key}: {e}", ServiceNames.ORCHESTRATOR)
            return False

    def get_metrics(self) -> Dict[str, Any]:
        """Get Redis connection metrics."""
        return {
            "connection_state": self.connection_state.value,
            "circuit_breaker_state": self.circuit_breaker.state.value,
            "connection_attempts": self.metrics.connection_attempts,
            "successful_connections": self.metrics.successful_connections,
            "failed_connections": self.metrics.failed_connections,
            "total_operations": self.metrics.total_operations,
            "successful_operations": self.metrics.successful_operations,
            "failed_operations": self.metrics.failed_operations,
            "average_response_time": self.metrics.average_response_time,
            "last_connection_attempt": self.metrics.last_connection_attempt.isoformat() if self.metrics.last_connection_attempt else None,
            "last_successful_operation": self.metrics.last_successful_operation.isoformat() if self.metrics.last_successful_operation else None,
            "last_failed_operation": self.metrics.last_failed_operation.isoformat() if self.metrics.last_failed_operation else None,
            "success_rate": (self.metrics.successful_operations / self.metrics.total_operations) if self.metrics.total_operations > 0 else 0
        }

    async def cleanup(self):
        """Cleanup resources."""
        await self.disconnect()
        self.connection_listeners.clear()
        self.error_listeners.clear()


# Global Redis manager instance
redis_manager = RedisManager()


async def initialize_redis_manager():
    """Initialize the global Redis manager."""
    success = await redis_manager.connect()

    if success:
        fire_and_forget("info", "Redis manager initialized successfully", ServiceNames.ORCHESTRATOR)

        # Add health monitoring
        async def health_monitor():
            while True:
                try:
                    health = await redis_manager.health_check()
                    if health["status"] != "healthy":
                        fire_and_forget("warning", f"Redis health check failed: {health['message']}", ServiceNames.ORCHESTRATOR)
                except Exception as e:
                    fire_and_forget("error", f"Redis health monitor error: {e}", ServiceNames.ORCHESTRATOR)

                await asyncio.sleep(redis_manager.health_check_interval)

        asyncio.create_task(health_monitor())

    else:
        fire_and_forget("error", "Failed to initialize Redis manager", ServiceNames.ORCHESTRATOR)

    return success


async def shutdown_redis_manager():
    """Shutdown the global Redis manager."""
    await redis_manager.cleanup()
    fire_and_forget("info", "Redis manager shutdown", ServiceNames.ORCHESTRATOR)


# Convenience functions
async def publish_orchestrator_event(event_type: str, payload: Dict[str, Any], correlation_id: str = None) -> bool:
    """Publish orchestrator event to Redis."""
    return await redis_manager.publish_event(
        "orchestrator.events",
        {
            "event_type": event_type,
            "payload": payload,
            "correlation_id": correlation_id or str(uuid.uuid4())
        }
    )


async def cache_orchestrator_data(key: str, data: Any, ttl_seconds: int = 3600) -> bool:
    """Cache orchestrator data in Redis."""
    return await redis_manager.set_cache(f"orchestrator:{key}", data, ttl_seconds)


async def get_cached_orchestrator_data(key: str) -> Optional[Any]:
    """Get cached orchestrator data from Redis."""
    return await redis_manager.get_cache(f"orchestrator:{key}")


async def get_redis_health() -> Dict[str, Any]:
    """Get Redis health status."""
    return await redis_manager.health_check()


def get_redis_metrics() -> Dict[str, Any]:
    """Get Redis metrics."""
    return redis_manager.get_metrics()
