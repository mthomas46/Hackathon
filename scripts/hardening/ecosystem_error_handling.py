#!/usr/bin/env python3
"""
Ecosystem-Wide Error Handling and Recovery Patterns
Standardized error handling, circuit breakers, and recovery mechanisms
"""

import asyncio
import time
import logging
import functools
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategy types"""
    RETRY = "retry"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK = "fallback"
    DEGRADATION = "degradation"
    RESTART = "restart"


@dataclass
class ErrorContext:
    """Context information for errors"""
    service_name: str
    operation: str
    timestamp: float = field(default_factory=time.time)
    error_message: str = ""
    error_type: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""


@dataclass
class CircuitBreakerState:
    """Circuit breaker state management"""
    failures: int = 0
    last_failure_time: float = 0
    state: str = "closed"  # closed, open, half_open
    success_count: int = 0
    total_requests: int = 0


class CircuitBreaker:
    """Circuit breaker implementation for service protection"""

    def __init__(self, service_name: str, failure_threshold: int = 5,
                 recovery_timeout: int = 60, success_threshold: int = 3):
        self.service_name = service_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.state = CircuitBreakerState()
        self._lock = threading.Lock()

    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset"""
        return (time.time() - self.state.last_failure_time) > self.recovery_timeout

    def _record_success(self):
        """Record successful operation"""
        with self._lock:
            self.state.success_count += 1
            self.state.total_requests += 1

            if self.state.state == "half_open" and self.state.success_count >= self.success_threshold:
                self.state.state = "closed"
                self.state.failures = 0
                self.state.success_count = 0
                logger.info(f"Circuit breaker for {self.service_name} reset to closed state")

    def _record_failure(self):
        """Record failed operation"""
        with self._lock:
            self.state.failures += 1
            self.state.last_failure_time = time.time()
            self.state.total_requests += 1

            if self.state.failures >= self.failure_threshold:
                self.state.state = "open"
                logger.warning(f"Circuit breaker for {self.service_name} opened after {self.state.failures} failures")

    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        with self._lock:
            if self.state.state == "closed":
                return True
            elif self.state.state == "open":
                if self._should_attempt_reset():
                    self.state.state = "half_open"
                    self.state.success_count = 0
                    logger.info(f"Circuit breaker for {self.service_name} attempting reset")
                    return True
                return False
            elif self.state.state == "half_open":
                return True
            return False

    @contextmanager
    def execute_context(self):
        """Context manager for circuit breaker execution"""
        if not self.can_execute():
            raise Exception(f"Circuit breaker is open for {self.service_name}")

        try:
            yield
            self._record_success()
        except Exception as e:
            self._record_failure()
            raise e


class RetryMechanism:
    """Retry mechanism with exponential backoff"""

    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0,
                 max_delay: float = 60.0, backoff_factor: float = 2.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt"""
        delay = self.base_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)

    async def execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with retry logic"""
        last_exception = None

        for attempt in range(self.max_attempts):
            try:
                return await operation(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed for operation {operation.__name__}: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.max_attempts} attempts failed for operation {operation.__name__}: {e}")

        raise last_exception


class FallbackMechanism:
    """Fallback mechanism for graceful degradation"""

    def __init__(self, primary_operation: Callable, fallback_operation: Callable):
        self.primary_operation = primary_operation
        self.fallback_operation = fallback_operation

    async def execute_with_fallback(self, *args, **kwargs) -> Any:
        """Execute primary operation with fallback"""
        try:
            return await self.primary_operation(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary operation failed, executing fallback: {e}")
            try:
                return await self.fallback_operation(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Both primary and fallback operations failed: {fallback_error}")
                raise fallback_error


class ErrorHandler:
    """Centralized error handling and recovery orchestration"""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_mechanisms: Dict[str, RetryMechanism] = {}
        self.fallback_mechanisms: Dict[str, FallbackMechanism] = {}
        self.error_history: List[ErrorContext] = []
        self.recovery_actions: Dict[str, Callable] = {}

    def register_circuit_breaker(self, service_name: str, circuit_breaker: CircuitBreaker):
        """Register a circuit breaker for a service"""
        self.circuit_breakers[service_name] = circuit_breaker
        logger.info(f"Registered circuit breaker for {service_name}")

    def register_retry_mechanism(self, operation_name: str, retry_mechanism: RetryMechanism):
        """Register a retry mechanism for an operation"""
        self.retry_mechanisms[operation_name] = retry_mechanism

    def register_fallback_mechanism(self, operation_name: str, fallback_mechanism: FallbackMechanism):
        """Register a fallback mechanism for an operation"""
        self.fallback_mechanisms[operation_name] = fallback_mechanism

    def register_recovery_action(self, error_pattern: str, recovery_action: Callable):
        """Register a recovery action for specific error patterns"""
        self.recovery_actions[error_pattern] = recovery_action

    def record_error(self, error_context: ErrorContext):
        """Record an error for analysis and recovery"""
        self.error_history.append(error_context)

        # Keep only last 1000 errors to prevent memory issues
        if len(self.error_history) > 1000:
            self.error_history = self.error_history[-1000:]

        logger.error(f"Error recorded: {error_context.service_name}:{error_context.operation} - {error_context.error_message}")

        # Trigger recovery actions based on error patterns
        self._trigger_recovery_actions(error_context)

    def _trigger_recovery_actions(self, error_context: ErrorContext):
        """Trigger appropriate recovery actions based on error"""
        error_key = f"{error_context.service_name}:{error_context.error_type}"

        if error_key in self.recovery_actions:
            try:
                recovery_action = self.recovery_actions[error_key]
                asyncio.create_task(recovery_action(error_context))
                logger.info(f"Triggered recovery action for {error_key}")
            except Exception as e:
                logger.error(f"Recovery action failed for {error_key}: {e}")

    async def execute_with_protection(self, service_name: str, operation_name: str,
                                    operation: Callable, *args, **kwargs) -> Any:
        """Execute operation with full error handling protection"""
        circuit_breaker = self.circuit_breakers.get(service_name)
        retry_mechanism = self.retry_mechanisms.get(operation_name)
        fallback_mechanism = self.fallback_mechanisms.get(operation_name)

        # Circuit breaker protection
        if circuit_breaker:
            with circuit_breaker.execute_context():
                return await self._execute_with_retry_and_fallback(
                    service_name, operation_name, operation,
                    retry_mechanism, fallback_mechanism, *args, **kwargs
                )
        else:
            return await self._execute_with_retry_and_fallback(
                service_name, operation_name, operation,
                retry_mechanism, fallback_mechanism, *args, **kwargs
            )

    async def _execute_with_retry_and_fallback(self, service_name: str, operation_name: str,
                                             operation: Callable, retry_mechanism: Optional[RetryMechanism],
                                             fallback_mechanism: Optional[FallbackMechanism],
                                             *args, **kwargs) -> Any:
        """Execute with retry and fallback protection"""
        try:
            if retry_mechanism:
                return await retry_mechanism.execute_with_retry(operation, *args, **kwargs)
            else:
                return await operation(*args, **kwargs)
        except Exception as e:
            # Record the error
            error_context = ErrorContext(
                service_name=service_name,
                operation=operation_name,
                error_message=str(e),
                error_type=type(e).__name__,
                severity=ErrorSeverity.MEDIUM
            )
            self.record_error(error_context)

            # Try fallback if available
            if fallback_mechanism:
                try:
                    return await fallback_mechanism.execute_with_fallback(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed for {service_name}:{operation_name}: {fallback_error}")
                    raise fallback_error
            else:
                raise e

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        if not self.error_history:
            return {"total_errors": 0}

        # Group errors by service and type
        service_errors = {}
        type_errors = {}
        severity_counts = {severity.value: 0 for severity in ErrorSeverity}

        for error in self.error_history:
            # Count by service
            if error.service_name not in service_errors:
                service_errors[error.service_name] = 0
            service_errors[error.service_name] += 1

            # Count by error type
            if error.error_type not in type_errors:
                type_errors[error.error_type] = 0
            type_errors[error.error_type] += 1

            # Count by severity
            severity_counts[error.severity.value] += 1

        return {
            "total_errors": len(self.error_history),
            "errors_by_service": service_errors,
            "errors_by_type": type_errors,
            "errors_by_severity": severity_counts,
            "circuit_breaker_states": {
                name: cb.state.state for name, cb in self.circuit_breakers.items()
            }
        }


# Global error handler instance
error_handler = ErrorHandler()


# Decorators for easy error handling integration
def with_error_handling(service_name: str, operation_name: str,
                       recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY):
    """Decorator to add error handling to functions"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await error_handler.execute_with_protection(
                service_name, operation_name, func, *args, **kwargs
            )
        return wrapper
    return decorator


def circuit_breaker(service_name: str, failure_threshold: int = 5, recovery_timeout: int = 60):
    """Decorator to add circuit breaker protection"""
    def decorator(func):
        cb = CircuitBreaker(service_name, failure_threshold, recovery_timeout)
        error_handler.register_circuit_breaker(service_name, cb)

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with cb.execute_context():
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions for common error scenarios
async def handle_service_unavailable(service_name: str, error_context: ErrorContext):
    """Handle service unavailable errors with automatic recovery"""
    logger.info(f"Handling service unavailable for {service_name}")

    # Check if service container is running and restart if needed
    # This would integrate with Docker/container management
    pass


async def handle_network_timeout(service_name: str, error_context: ErrorContext):
    """Handle network timeout errors"""
    logger.info(f"Handling network timeout for {service_name}")

    # Implement network-specific recovery logic
    pass


async def handle_database_connection_error(service_name: str, error_context: ErrorContext):
    """Handle database connection errors"""
    logger.info(f"Handling database connection error for {service_name}")

    # Implement database-specific recovery logic
    pass


# Initialize common recovery actions
def initialize_common_recovery_actions():
    """Initialize common recovery actions for typical error patterns"""
    error_handler.register_recovery_action("doc_store:ConnectionError", handle_database_connection_error)
    error_handler.register_recovery_action("llm-gateway:TimeoutError", handle_network_timeout)
    error_handler.register_recovery_action("frontend:ConnectionError", handle_service_unavailable)


# Initialize on module import
initialize_common_recovery_actions()


if __name__ == "__main__":
    # Example usage and testing
    async def test_error_handling():
        """Test the error handling framework"""

        # Register circuit breakers for services
        error_handler.register_circuit_breaker("doc_store", CircuitBreaker("doc_store"))
        error_handler.register_circuit_breaker("llm-gateway", CircuitBreaker("llm-gateway"))

        # Register retry mechanisms for operations
        error_handler.register_retry_mechanism("api_call", RetryMechanism(max_attempts=3))
        error_handler.register_retry_mechanism("database_query", RetryMechanism(max_attempts=5))

        # Test successful operation
        async def successful_operation():
            return "success"

        # Test failing operation
        async def failing_operation():
            raise ConnectionError("Service unavailable")

        try:
            # Test successful execution
            result = await error_handler.execute_with_protection(
                "doc_store", "api_call", successful_operation
            )
            print(f"Successful operation result: {result}")

            # Test error handling
            result = await error_handler.execute_with_protection(
                "llm-gateway", "api_call", failing_operation
            )
        except Exception as e:
            print(f"Expected error caught: {e}")

        # Print error statistics
        stats = error_handler.get_error_statistics()
        print(f"Error statistics: {json.dumps(stats, indent=2)}")

    # Run test
    asyncio.run(test_error_handling())
