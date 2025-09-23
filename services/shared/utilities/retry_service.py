"""Advanced Retry Service with configurable policies and exponential backoff.

Provides sophisticated retry mechanisms for different types of operations with
adaptive backoff, jitter, and circuit breaker integration.
"""
import asyncio
import random
import time
import logging
from typing import Callable, Awaitable, TypeVar, Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)
T = TypeVar("T")


class RetryStrategy(Enum):
    """Retry strategies for different failure patterns."""
    FIXED = "fixed"  # Fixed delay between retries
    LINEAR = "linear"  # Linearly increasing delay
    EXPONENTIAL = "exponential"  # Exponential backoff
    FIBONACCI = "fibonacci"  # Fibonacci sequence delays
    CUSTOM = "custom"  # Custom delay function


class BackoffStrategy(Enum):
    """Backoff strategies for jitter."""
    NONE = "none"  # No jitter
    FIXED = "fixed"  # Fixed percentage jitter
    RANDOM = "random"  # Random jitter within bounds
    DECORRELATED = "decorrelated"  # Decorrelated jitter (AWS approach)


@dataclass
class RetryPolicy:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    base_delay_ms: int = 100
    max_delay_ms: int = 30000  # 30 seconds
    backoff_multiplier: float = 2.0
    jitter_strategy: BackoffStrategy = BackoffStrategy.RANDOM
    jitter_factor: float = 0.1  # 10% jitter
    retryable_exceptions: Optional[List[type]] = None
    non_retryable_exceptions: Optional[List[type]] = None
    timeout_per_attempt: Optional[float] = None
    circuit_breaker_integration: bool = True


@dataclass
class RetryMetrics:
    """Metrics for retry operations."""
    total_attempts: int = 0
    successful_attempts: int = 0
    failed_attempts: int = 0
    retry_count: int = 0
    total_delay_time: float = 0.0
    average_delay: float = 0.0
    last_attempt_time: float = 0.0


class RetryService:
    """Advanced retry service with configurable policies."""

    def __init__(self):
        self._policies: Dict[str, RetryPolicy] = {}
        self._metrics: Dict[str, RetryMetrics] = defaultdict(RetryMetrics)
        self._circuit_breaker_service = None

    def register_policy(self, policy_name: str, policy: RetryPolicy) -> None:
        """Register a named retry policy."""
        self._policies[policy_name] = policy
        logger.info(f"Registered retry policy: {policy_name}")

    def get_default_policies(self) -> Dict[str, RetryPolicy]:
        """Get a set of sensible default policies for common scenarios."""
        return {
            "fast_network": RetryPolicy(
                max_attempts=3,
                strategy=RetryStrategy.EXPONENTIAL,
                base_delay_ms=50,
                max_delay_ms=2000,
                jitter_strategy=BackoffStrategy.RANDOM,
                jitter_factor=0.2
            ),
            "database": RetryPolicy(
                max_attempts=5,
                strategy=RetryStrategy.EXPONENTIAL,
                base_delay_ms=200,
                max_delay_ms=10000,
                jitter_strategy=BackoffStrategy.DECORRELATED,
                retryable_exceptions=[ConnectionError, TimeoutError]
            ),
            "external_api": RetryPolicy(
                max_attempts=4,
                strategy=RetryStrategy.EXPONENTIAL,
                base_delay_ms=100,
                max_delay_ms=5000,
                jitter_strategy=BackoffStrategy.RANDOM,
                jitter_factor=0.15,
                timeout_per_attempt=10.0
            ),
            "file_operations": RetryPolicy(
                max_attempts=2,
                strategy=RetryStrategy.FIXED,
                base_delay_ms=500,
                jitter_strategy=BackoffStrategy.NONE
            ),
            "critical_operation": RetryPolicy(
                max_attempts=8,
                strategy=RetryStrategy.FIBONACCI,
                base_delay_ms=100,
                max_delay_ms=30000,
                jitter_strategy=BackoffStrategy.DECORRELATED
            )
        }

    async def execute_with_retry(
        self,
        operation: Callable[[], Awaitable[T]],
        policy_name: str = "default",
        operation_name: str = "unknown",
        custom_policy: Optional[RetryPolicy] = None
    ) -> T:
        """Execute operation with retry logic."""
        policy = custom_policy or self._policies.get(policy_name)
        if not policy:
            # Use a sensible default
            policy = RetryPolicy()

        metrics = self._metrics[operation_name]
        metrics.total_attempts += 1
        start_time = time.time()

        last_exception = None

        for attempt in range(policy.max_attempts):
            try:
                # Apply timeout if specified
                if policy.timeout_per_attempt:
                    result = await asyncio.wait_for(operation(), timeout=policy.timeout_per_attempt)
                else:
                    result = await operation()

                # Success
                metrics.successful_attempts += 1
                metrics.last_attempt_time = time.time()
                return result

            except Exception as e:
                last_exception = e
                metrics.failed_attempts += 1
                metrics.last_attempt_time = time.time()

                # Check if exception is retryable
                if not self._should_retry(e, policy):
                    logger.debug(f"Non-retryable exception in {operation_name}: {e}")
                    break

                # Don't retry on last attempt
                if attempt == policy.max_attempts - 1:
                    break

                # Calculate delay
                delay_ms = self._calculate_delay(attempt, policy)
                delay_seconds = delay_ms / 1000.0

                metrics.retry_count += 1
                metrics.total_delay_time += delay_seconds

                logger.warning(
                    f"Attempt {attempt + 1}/{policy.max_attempts} failed for {operation_name}: {e}. "
                    f"Retrying in {delay_seconds:.2f}s"
                )

                await asyncio.sleep(delay_seconds)

        # All attempts failed
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"Retry operation {operation_name} failed with unknown error")

    def _should_retry(self, exception: Exception, policy: RetryPolicy) -> bool:
        """Determine if an exception should trigger a retry."""
        exception_type = type(exception)

        # Check non-retryable exceptions first
        if policy.non_retryable_exceptions:
            for non_retryable in policy.non_retryable_exceptions:
                if issubclass(exception_type, non_retryable):
                    return False

        # Check retryable exceptions
        if policy.retryable_exceptions:
            for retryable in policy.retryable_exceptions:
                if issubclass(exception_type, retryable):
                    return True
            return False  # If retryable list exists but doesn't match, don't retry

        # Default behavior: retry on common network/transient errors
        default_retryable = (
            ConnectionError, TimeoutError, OSError,
            asyncio.TimeoutError
        )

        return any(issubclass(exception_type, retryable) for retryable in default_retryable)

    def _calculate_delay(self, attempt: int, policy: RetryPolicy) -> float:
        """Calculate delay for the given attempt using the configured strategy."""
        base_delay = policy.base_delay_ms

        if policy.strategy == RetryStrategy.FIXED:
            delay = base_delay
        elif policy.strategy == RetryStrategy.LINEAR:
            delay = base_delay * (attempt + 1)
        elif policy.strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (policy.backoff_multiplier ** attempt)
        elif policy.strategy == RetryStrategy.FIBONACCI:
            # Fibonacci: 1, 1, 2, 3, 5, 8, 13, ...
            if attempt == 0:
                delay = base_delay
            else:
                # Approximate Fibonacci growth
                delay = base_delay * (1.618 ** attempt)
        else:
            delay = base_delay

        # Apply maximum delay cap
        delay = min(delay, policy.max_delay_ms)

        # Apply jitter
        if policy.jitter_strategy != BackoffStrategy.NONE:
            delay = self._apply_jitter(delay, attempt, policy)

        return delay

    def _apply_jitter(self, delay: float, attempt: int, policy: RetryPolicy) -> float:
        """Apply jitter to the delay based on the jitter strategy."""
        if policy.jitter_strategy == BackoffStrategy.FIXED:
            # Fixed percentage jitter
            jitter_range = delay * policy.jitter_factor
            jitter = random.uniform(-jitter_range, jitter_range)
            return max(0, delay + jitter)

        elif policy.jitter_strategy == BackoffStrategy.RANDOM:
            # Random jitter within bounds
            min_delay = delay * (1 - policy.jitter_factor)
            max_delay = delay * (1 + policy.jitter_factor)
            return random.uniform(min_delay, max_delay)

        elif policy.jitter_strategy == BackoffStrategy.DECORRELATED:
            # AWS-style decorrelated jitter: sleep = random_between(base, delay * 3)
            return random.uniform(policy.base_delay_ms, delay * 3)

        return delay

    def get_metrics(self, operation_name: str) -> RetryMetrics:
        """Get retry metrics for an operation."""
        return self._metrics[operation_name]

    def get_all_metrics(self) -> Dict[str, RetryMetrics]:
        """Get all retry metrics."""
        return dict(self._metrics)

    def reset_metrics(self, operation_name: Optional[str] = None) -> None:
        """Reset metrics for an operation or all operations."""
        if operation_name:
            self._metrics[operation_name] = RetryMetrics()
        else:
            self._metrics.clear()

    def get_policy(self, policy_name: str) -> Optional[RetryPolicy]:
        """Get a registered policy by name."""
        return self._policies.get(policy_name)


# Global instance
_retry_service: Optional[RetryService] = None


def get_retry_service() -> RetryService:
    """Get the global retry service instance."""
    global _retry_service
    if _retry_service is None:
        _retry_service = RetryService()
        # Register default policies
        for name, policy in _retry_service.get_default_policies().items():
            _retry_service.register_policy(name, policy)
    return _retry_service


async def retry_with_policy(
    operation: Callable[[], Awaitable[T]],
    policy_name: str = "external_api",
    operation_name: str = "unknown"
) -> T:
    """Convenience function to retry with a named policy."""
    service = get_retry_service()
    return await service.execute_with_retry(operation, policy_name, operation_name)


async def retry_with_custom_policy(
    operation: Callable[[], Awaitable[T]],
    policy: RetryPolicy,
    operation_name: str = "unknown"
) -> T:
    """Convenience function to retry with a custom policy."""
    service = get_retry_service()
    return await service.execute_with_retry(operation, custom_policy=policy, operation_name=operation_name)
