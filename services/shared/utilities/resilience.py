"""Consolidated resilience utilities for fault tolerance and reliability.

Combines retry, circuit breaker, rate limiting, and resource management functionality.
"""

import asyncio
import random
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

from .utilities import TokenBucket

T = TypeVar("T")


class FailureType(Enum):
    """Types of failures for circuit breaker."""

    NETWORK = "network"
    TIMEOUT = "timeout"
    SERVER_ERROR = "server_error"
    CLIENT_ERROR = "client_error"
    RESOURCE_EXHAUSTED = "resource_exhausted"


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0
    last_state_change: float = field(default_factory=time.time)
    failure_counts: Dict[FailureType, int] = field(default_factory=lambda: defaultdict(int))


class ResourceLimiter:
    """Manages resource limits to prevent cascading failures."""

    def __init__(self, max_concurrent: int = 10, max_memory_mb: float = 512.0):
        self.max_concurrent = max_concurrent
        self.max_memory_mb = max_memory_mb
        self._active_operations = 0
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """Try to acquire resources for an operation."""
        with self._lock:
            if self._active_operations >= self.max_concurrent:
                return False
            self._active_operations += 1
            return True

    def release(self) -> None:
        """Release resources after operation completion."""
        with self._lock:
            self._active_operations = max(0, self._active_operations - 1)

    @property
    def active_operations(self) -> int:
        """Get current active operation count."""
        with self._lock:
            return self._active_operations


class EnhancedCircuitBreaker:
    """Enhanced circuit breaker with metrics, failure types, and resource limits."""

    def __init__(
        self,
        failure_threshold: int = 3,
        reset_timeout: float = 30.0,
        resource_limiter: Optional[ResourceLimiter] = None,
        success_threshold: int = 2,  # consecutive successes to close from half-open
        slow_call_duration: float = 5.0,  # calls slower than this are considered slow
        slow_call_rate_threshold: float = 0.5,  # ratio of slow calls that trigger circuit
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.success_threshold = success_threshold
        self.slow_call_duration = slow_call_duration
        self.slow_call_rate_threshold = slow_call_rate_threshold

        self._state = "closed"  # closed|open|half-open
        self._failures = 0
        self._successes = 0
        self._last_failure_time: float = 0.0
        self._metrics = CircuitBreakerMetrics()
        self._resource_limiter = resource_limiter or ResourceLimiter()
        self._lock = threading.Lock()

    def allow(self) -> bool:
        """Check if call should be allowed."""
        with self._lock:
            self._metrics.total_calls += 1

            if self._state == "open":
                if time.time() - self._last_failure_time >= self.reset_timeout:
                    self._state = "half-open"
                    self._successes = 0
                    self._metrics.state_changes += 1
                    self._metrics.last_state_change = time.time()
                    return True
                else:
                    self._metrics.rejected_calls += 1
                    return False
            return True

    def on_success(self, call_duration: float = 0.0) -> None:
        """Record successful call."""
        with self._lock:
            self._metrics.successful_calls += 1

            if self._state == "half-open":
                self._successes += 1
                if self._successes >= self.success_threshold:
                    self._state = "closed"
                    self._failures = 0
                    self._metrics.state_changes += 1
                    self._metrics.last_state_change = time.time()
            elif self._state == "closed":
                self._failures = max(0, self._failures - 1)  # gradual recovery

    def on_failure(self, failure_type: FailureType = FailureType.SERVER_ERROR, call_duration: float = 0.0) -> None:
        """Record failed call."""
        with self._lock:
            self._metrics.failed_calls += 1
            self._metrics.failure_counts[failure_type] += 1

            self._failures += 1
            self._last_failure_time = time.time()

            if self._failures >= self.failure_threshold:
                self._state = "open"
                self._metrics.state_changes += 1
                self._metrics.last_state_change = time.time()

    def can_acquire_resources(self) -> bool:
        """Check if resources are available."""
        return self._resource_limiter.acquire()

    def release_resources(self) -> None:
        """Release acquired resources."""
        self._resource_limiter.release()

    @property
    def state(self) -> str:
        """Get current circuit state."""
        with self._lock:
            return self._state

    @property
    def metrics(self) -> CircuitBreakerMetrics:
        """Get circuit breaker metrics."""
        with self._lock:
            return self._metrics

    @property
    def resource_usage(self) -> int:
        """Get current resource usage."""
        return self._resource_limiter.active_operations


class CircuitBreaker:
    """Tracks consecutive failures and gates calls for a cooldown window.

    State transitions:
    - closed: calls pass, failures increment counter
    - open: calls blocked until reset_timeout passes
    - half-open: first call allowed after timeout, success closes circuit
    """

    def __init__(self, failure_threshold: int = 3, reset_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._state = "closed"  # closed|open|half-open
        self._failures = 0
        self._last_failure_time: float = 0.0

    def allow(self) -> bool:
        if self._state == "open":
            if time.time() - self._last_failure_time >= self.reset_timeout:
                self._state = "half-open"
                return True
            return False
        return True

    def on_success(self) -> None:
        self._state = "closed"
        self._failures = 0

    def on_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.time()
        if self._failures >= self.failure_threshold:
            self._state = "open"


async def with_circuit(cb: CircuitBreaker, func: Callable[[], Awaitable[T]]) -> T:
    """Execute function under circuit protection."""
    if not cb.allow():
        raise RuntimeError("circuit_open")
    try:
        result = await func()
        cb.on_success()
        return result
    except Exception:
        cb.on_failure()
        raise


async def with_retries(operation: Callable[[], Awaitable[T]], attempts: int = 3, base_delay_ms: int = 100) -> T:
    """Execute operation with exponential backoff retry logic."""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return await operation()
        except Exception as e:
            last_exc = e
            if i == attempts - 1:
                break
            jitter = random.randint(0, base_delay_ms)
            await asyncio.sleep((base_delay_ms + jitter) / 1000.0)

    # This should never happen, but ensure we have an exception to raise
    if last_exc is None:
        raise RuntimeError("Retry logic error: no exception captured")
    raise last_exc


class ResilienceManager:
    """Unified resilience management for services with enhanced circuit breaking."""

    def __init__(
        self,
        circuit_failure_threshold: int = 3,
        circuit_reset_timeout: float = 30.0,
        retry_attempts: int = 3,
        retry_base_delay_ms: int = 150,
        rate_limits: Optional[Dict[str, tuple[float, int]]] = None,
        max_concurrent_operations: int = 10,
        enable_enhanced_circuit_breaker: bool = True,
    ):
        # Use enhanced circuit breaker by default
        if enable_enhanced_circuit_breaker:
            resource_limiter = ResourceLimiter(max_concurrent_operations)
            self.circuit_breaker = EnhancedCircuitBreaker(
                failure_threshold=circuit_failure_threshold,
                reset_timeout=circuit_reset_timeout,
                resource_limiter=resource_limiter,
            )
        else:
            self.circuit_breaker = CircuitBreaker(circuit_failure_threshold, circuit_reset_timeout)

        self.retry_attempts = retry_attempts
        self.retry_base_delay_ms = retry_base_delay_ms
        self.rate_buckets: Dict[str, TokenBucket] = {}
        self._operation_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)

        if rate_limits:
            for path, (rate, burst) in rate_limits.items():
                self.rate_buckets[path] = TokenBucket(rate, burst)

    async def execute_with_resilience(
        self,
        operation: Callable[[], Awaitable[T]],
        operation_name: str = "unknown",
        timeout_seconds: Optional[float] = None,
    ) -> T:
        """Execute operation with full resilience (circuit + retry + resource limits)."""
        import time as time_module

        # Check rate limiting
        if hasattr(self.circuit_breaker, "can_acquire_resources"):
            if not self.circuit_breaker.can_acquire_resources():
                raise RuntimeError(f"Resource limit exceeded for {operation_name}")

        try:
            start_time = time_module.time()

            async def _timed_operation():
                if timeout_seconds:
                    return await asyncio.wait_for(operation(), timeout=timeout_seconds)
                return await operation()

            async def _circuit_operation():
                return await with_retries(_timed_operation, self.retry_attempts, self.retry_base_delay_ms)

            result = await with_circuit(self.circuit_breaker, _circuit_operation)

            # Record success
            call_duration = time_module.time() - start_time
            if hasattr(self.circuit_breaker, "on_success"):
                self.circuit_breaker.on_success(call_duration)

            # Update operation metrics
            self._update_operation_metrics(operation_name, "success", call_duration)

            return result

        except asyncio.TimeoutError:
            self._handle_failure(operation_name, FailureType.TIMEOUT, timeout_seconds or 0)
            raise
        except Exception as e:
            # Determine failure type
            failure_type = self._classify_exception(e)
            self._handle_failure(operation_name, failure_type, 0)
            raise
        finally:
            # Always release resources
            if hasattr(self.circuit_breaker, "release_resources"):
                self.circuit_breaker.release_resources()

    def _handle_failure(self, operation_name: str, failure_type: FailureType, duration: float) -> None:
        """Handle operation failure."""
        if hasattr(self.circuit_breaker, "on_failure"):
            self.circuit_breaker.on_failure(failure_type, duration)
        self._update_operation_metrics(operation_name, "failure", duration, failure_type)

    def _classify_exception(self, exc: Exception) -> FailureType:
        """Classify exception type for circuit breaker."""
        exc_str = str(exc).lower()
        exc_type = type(exc).__name__.lower()

        if "timeout" in exc_str or "timeout" in exc_type:
            return FailureType.TIMEOUT
        elif "connection" in exc_str or "network" in exc_str:
            return FailureType.NETWORK
        elif hasattr(exc, "status_code"):
            status = getattr(exc, "status_code", 500)
            if 400 <= status < 500:
                return FailureType.CLIENT_ERROR
            elif status >= 500:
                return FailureType.SERVER_ERROR
        elif "resource" in exc_str or "exhausted" in exc_str:
            return FailureType.RESOURCE_EXHAUSTED

        return FailureType.SERVER_ERROR

    def _update_operation_metrics(
        self, operation_name: str, result: str, duration: float, failure_type: Optional[FailureType] = None
    ) -> None:
        """Update operation-specific metrics."""
        metrics = self._operation_metrics[operation_name]
        metrics["total_calls"] = metrics.get("total_calls", 0) + 1

        if result == "success":
            metrics["successful_calls"] = metrics.get("successful_calls", 0) + 1
        else:
            metrics["failed_calls"] = metrics.get("failed_calls", 0) + 1
            if failure_type:
                failure_key = f"failures_{failure_type.value}"
                metrics[failure_key] = metrics.get(failure_key, 0) + 1

        # Update timing metrics
        if "avg_duration" not in metrics:
            metrics["avg_duration"] = duration
        else:
            count = metrics["total_calls"]
            metrics["avg_duration"] = (metrics["avg_duration"] * (count - 1) + duration) / count

    def check_rate_limit(self, path: str) -> bool:
        """Check if request should be rate limited."""
        bucket = self.rate_buckets.get(path)
        if bucket:
            return bucket.allow()
        return True

    def get_operation_metrics(self, operation_name: str) -> Dict[str, Any]:
        """Get metrics for a specific operation."""
        return dict(self._operation_metrics.get(operation_name, {}))

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status and metrics."""
        status = {"state": self.circuit_breaker._state if hasattr(self.circuit_breaker, "_state") else "unknown"}

        if hasattr(self.circuit_breaker, "metrics"):
            status["metrics"] = {
                "total_calls": self.circuit_breaker.metrics.total_calls,
                "successful_calls": self.circuit_breaker.metrics.successful_calls,
                "failed_calls": self.circuit_breaker.metrics.failed_calls,
                "rejected_calls": self.circuit_breaker.metrics.rejected_calls,
                "state_changes": self.circuit_breaker.metrics.state_changes,
            }
        else:
            # Fallback for basic circuit breaker
            status["metrics"] = {"basic_circuit_breaker": True}

        if hasattr(self.circuit_breaker, "resource_usage"):
            status["resource_usage"] = self.circuit_breaker.resource_usage

        return status
