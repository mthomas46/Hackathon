"""Main enterprise error handler implementation."""

import asyncio
import traceback
from typing import Any, Dict, Optional

from .error_context import ErrorContext, RecoveryAction
from .error_types import ErrorSeverity, ErrorCategory, RecoveryStrategy
from .circuit_breaker import CircuitBreaker


class EnterpriseErrorHandler:
    """Enterprise-grade error handler with recovery strategies."""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.error_counts: Dict[str, int] = {}
        self.recovery_actions: Dict[str, RecoveryAction] = {}

    def handle_error(
        self,
        error: Exception,
        service_name: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle an error with appropriate recovery strategy."""

        # Create error context
        error_context = ErrorContext(
            service_name=service_name,
            operation=operation,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            metadata=context or {}
        )

        # Classify error
        self._classify_error(error_context, error)

        # Get recovery action
        recovery_action = self._determine_recovery_action(error_context)

        # Execute recovery
        result = self._execute_recovery(error_context, recovery_action, error)

        # Update metrics
        self._update_error_metrics(error_context)

        return result

    def _classify_error(self, context: ErrorContext, error: Exception):
        """Classify the error type and severity."""
        error_type = type(error).__name__

        # Network-related errors
        if any(keyword in error_type.lower() for keyword in ['connection', 'timeout', 'http']):
            context.category = ErrorCategory.NETWORK
            context.severity = ErrorSeverity.HIGH

        # Database errors
        elif any(keyword in error_type.lower() for keyword in ['database', 'sqlite', 'postgres']):
            context.category = ErrorCategory.DATABASE
            context.severity = ErrorSeverity.CRITICAL

        # Validation errors
        elif any(keyword in error_type.lower() for keyword in ['validation', 'value']):
            context.category = ErrorCategory.VALIDATION
            context.severity = ErrorSeverity.MEDIUM

        # Security errors
        elif any(keyword in error_type.lower() for keyword in ['auth', 'permission', 'security']):
            context.category = ErrorCategory.SECURITY
            context.severity = ErrorSeverity.CRITICAL

        else:
            context.category = ErrorCategory.UNKNOWN
            context.severity = ErrorSeverity.MEDIUM

    def _determine_recovery_action(self, context: ErrorContext) -> RecoveryAction:
        """Determine the appropriate recovery action."""

        # Critical errors should escalate
        if context.severity == ErrorSeverity.CRITICAL:
            return RecoveryAction(
                strategy=RecoveryStrategy.ESCALATE,
                description="Critical error - requires manual intervention"
            )

        # Network errors can be retried
        if context.category == ErrorCategory.NETWORK:
            return RecoveryAction(
                strategy=RecoveryStrategy.RETRY,
                parameters={"delay": 1.0, "max_retries": 3},
                description="Retry network operation"
            )

        # Validation errors should not be retried
        if context.category == ErrorCategory.VALIDATION:
            return RecoveryAction(
                strategy=RecoveryStrategy.LOG_AND_CONTINUE,
                description="Validation error - log and continue"
            )

        # Default recovery
        return RecoveryAction(
            strategy=RecoveryStrategy.LOG_AND_CONTINUE,
            description="Log error and continue operation"
        )

    def _execute_recovery(
        self,
        context: ErrorContext,
        action: RecoveryAction,
        original_error: Exception
    ) -> Dict[str, Any]:
        """Execute the recovery action."""

        if action.strategy == RecoveryStrategy.RETRY and context.retry_count < context.max_retries:
            return {
                "action": "retry",
                "retry_count": context.retry_count + 1,
                "delay": action.get_retry_delay(),
                "message": action.description
            }

        elif action.strategy == RecoveryStrategy.CIRCUIT_BREAKER:
            circuit_breaker = self._get_circuit_breaker(context.service_name)
            if circuit_breaker.state.name == "OPEN":
                return {
                    "action": "circuit_breaker_open",
                    "message": f"Circuit breaker open for {context.service_name}"
                }

        elif action.strategy == RecoveryStrategy.ESCALATE:
            return {
                "action": "escalate",
                "severity": context.severity.value,
                "message": "Error escalated for manual review"
            }

        # Default: log and continue
        return {
            "action": "logged",
            "severity": context.severity.value,
            "category": context.category.value,
            "message": action.description
        }

    def _get_circuit_breaker(self, service_name: str) -> CircuitBreaker:
        """Get or create circuit breaker for service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(service_name)
        return self.circuit_breakers[service_name]

    def _update_error_metrics(self, context: ErrorContext):
        """Update error metrics for monitoring."""
        key = f"{context.service_name}:{context.category.value}"
        self.error_counts[key] = self.error_counts.get(key, 0) + 1

    def get_error_metrics(self) -> Dict[str, Any]:
        """Get error metrics for monitoring."""
        return {
            "error_counts": self.error_counts.copy(),
            "circuit_breakers": {
                name: cb.to_dict() for name, cb in self.circuit_breakers.items()
            }
        }

    def reset_circuit_breaker(self, service_name: str):
        """Reset circuit breaker for a service."""
        if service_name in self.circuit_breakers:
            self.circuit_breakers[service_name].reset()
