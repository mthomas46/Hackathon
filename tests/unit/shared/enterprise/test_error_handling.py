#!/usr/bin/env python3
"""
Tests for Enterprise Error Handling Module

Tests the advanced error handling and recovery framework.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from services.shared.enterprise.error_handling.error_handling import (
    ErrorSeverity,
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    RecoveryStrategy,
    CircuitBreaker,
    ErrorMetrics,
    EnterpriseErrorHandler
)


class TestErrorSeverity:
    """Test error severity levels."""

    def test_error_severity_values(self):
        """Test that error severity values are correct."""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"

    def test_error_severity_ordering(self):
        """Test that severity levels have proper ordering."""
        assert ErrorSeverity.LOW < ErrorSeverity.MEDIUM
        assert ErrorSeverity.MEDIUM < ErrorSeverity.HIGH
        assert ErrorSeverity.HIGH < ErrorSeverity.CRITICAL


class TestErrorCategory:
    """Test error categories."""

    def test_error_category_values(self):
        """Test that error categories have correct values."""
        assert ErrorCategory.NETWORK.value == "network"
        assert ErrorCategory.DATABASE.value == "database"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.TIMEOUT.value == "timeout"
        assert ErrorCategory.EXTERNAL_SERVICE.value == "external_service"


class TestErrorContext:
    """Test error context management."""

    def test_error_context_creation(self):
        """Test creating error context."""
        context = ErrorContext(
            service_name="test-service",
            operation="test_operation",
            error_message="Test error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.VALIDATION
        )

        assert context.service_name == "test-service"
        assert context.operation == "test_operation"
        assert context.severity == ErrorSeverity.HIGH
        assert context.category == ErrorCategory.VALIDATION

    def test_error_context_with_metadata(self):
        """Test error context with additional metadata."""
        metadata = {"user_id": "123", "request_id": "abc"}
        context = ErrorContext(
            service_name="test-service",
            error_message="Test error",
            metadata=metadata
        )

        assert context.metadata == metadata
        assert context.user_id == "123"
        assert context.request_id == "abc"


class TestErrorHandler:
    """Test basic error handler functionality."""

    def test_error_handler_initialization(self):
        """Test error handler initialization."""
        handler = ErrorHandler(service_name="test-service")
        assert handler.service_name == "test-service"
        assert len(handler.error_history) == 0

    def test_handle_error(self):
        """Test basic error handling."""
        handler = ErrorHandler(service_name="test-service")

        try:
            raise ValueError("Test error")
        except ValueError as e:
            context = handler.handle_error(e, operation="test_op")

        assert len(handler.error_history) == 1
        assert handler.error_history[0].error_message == "Test error"
        assert handler.error_history[0].operation == "test_op"


class TestRecoveryStrategy:
    """Test recovery strategy functionality."""

    def test_recovery_strategy_creation(self):
        """Test creating recovery strategies."""
        strategy = RecoveryStrategy(
            name="test_strategy",
            max_attempts=3,
            backoff_factor=2.0,
            timeout=30.0
        )

        assert strategy.name == "test_strategy"
        assert strategy.max_attempts == 3
        assert strategy.backoff_factor == 2.0

    @pytest.mark.asyncio
    async def test_recovery_execution_success(self):
        """Test successful recovery execution."""
        strategy = RecoveryStrategy(name="test", max_attempts=3)

        call_count = 0

        async def recovery_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await strategy.execute(recovery_function)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_recovery_execution_failure(self):
        """Test recovery execution with permanent failure."""
        strategy = RecoveryStrategy(name="test", max_attempts=2)

        call_count = 0

        async def failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")

        with pytest.raises(ValueError, match="Permanent error"):
            await strategy.execute(failing_function)

        assert call_count == 2


class TestCircuitBreaker:
    """Test circuit breaker functionality."""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initialization."""
        cb = CircuitBreaker(
            service_name="test-service",
            failure_threshold=5,
            recovery_timeout=60.0
        )

        assert cb.failure_threshold == 5
        assert cb.recovery_timeout == 60.0
        assert cb.failure_count == 0
        assert cb.state == "closed"

    def test_circuit_breaker_success(self):
        """Test successful operation through circuit breaker."""
        cb = CircuitBreaker(service_name="test", failure_threshold=3)

        # Should allow calls when closed
        assert cb.can_execute() is True

        # Record success
        cb.record_success()
        assert cb.state == "closed"
        assert cb.failure_count == 0

    def test_circuit_breaker_failure(self):
        """Test circuit breaker opening on failures."""
        cb = CircuitBreaker(service_name="test", failure_threshold=2)

        # Record failures
        cb.record_failure()
        assert cb.state == "closed"
        assert cb.failure_count == 1

        cb.record_failure()
        assert cb.state == "open"
        assert cb.failure_count == 2

        # Should not allow calls when open
        assert cb.can_execute() is False

    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery."""
        cb = CircuitBreaker(
            service_name="test",
            failure_threshold=2,
            recovery_timeout=0.1  # Short timeout for testing
        )

        # Open the circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"

        # Wait for recovery timeout
        import time
        time.sleep(0.2)

        # Should allow half-open calls
        assert cb.can_execute() is True
        assert cb.state == "half_open"


class TestErrorMetrics:
    """Test error metrics collection."""

    def test_error_metrics_initialization(self):
        """Test error metrics initialization."""
        metrics = ErrorMetrics(service_name="test-service")

        assert metrics.service_name == "test-service"
        assert metrics.total_errors == 0
        assert len(metrics.errors_by_category) == 0

    def test_record_error(self):
        """Test recording errors in metrics."""
        metrics = ErrorMetrics(service_name="test")

        context = ErrorContext(
            service_name="test",
            error_message="Test error",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.VALIDATION
        )

        metrics.record_error(context)

        assert metrics.total_errors == 1
        assert metrics.errors_by_category[ErrorCategory.VALIDATION] == 1
        assert metrics.errors_by_severity[ErrorSeverity.HIGH] == 1

    def test_get_error_summary(self):
        """Test getting error summary."""
        metrics = ErrorMetrics(service_name="test")

        # Record multiple errors
        for i in range(3):
            context = ErrorContext(
                service_name="test",
                error_message=f"Error {i}",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.NETWORK
            )
            metrics.record_error(context)

        summary = metrics.get_summary()
        assert summary["total_errors"] == 3
        assert summary["errors_by_category"]["network"] == 3
        assert summary["errors_by_severity"]["medium"] == 3


class TestEnterpriseErrorHandler:
    """Test enterprise error handler."""

    def test_enterprise_handler_initialization(self):
        """Test enterprise error handler initialization."""
        handler = EnterpriseErrorHandler(service_name="test-service")

        assert handler.service_name == "test-service"
        assert isinstance(handler.circuit_breaker, CircuitBreaker)
        assert isinstance(handler.metrics, ErrorMetrics)

    @pytest.mark.asyncio
    async def test_handle_error_with_recovery(self):
        """Test error handling with recovery strategy."""
        handler = EnterpriseErrorHandler(service_name="test")

        call_count = 0

        async def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"

        # Configure recovery strategy
        recovery_strategy = RecoveryStrategy(
            name="test_recovery",
            max_attempts=3,
            backoff_factor=0.1
        )

        result = await handler.handle_with_recovery(
            failing_operation,
            recovery_strategy
        )

        assert result == "success"
        assert call_count == 2  # Should succeed on second attempt


if __name__ == "__main__":
    pytest.main([__file__])
