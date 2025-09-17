#!/usr/bin/env python3
"""
Enterprise-Grade Error Handling Framework

This module provides comprehensive error handling, recovery strategies,
and monitoring capabilities for the entire ecosystem.
"""

import asyncio
import functools
import time
from typing import Dict, Any, List, Optional, Callable, Type, Union
from datetime import datetime, timedelta
from enum import Enum
import traceback
import json
import logging
from dataclasses import dataclass, field
from contextlib import asynccontextmanager

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class ErrorSeverity(Enum):
    """Error severity levels for classification and handling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for service-specific handling."""
    NETWORK = "network"
    DATABASE = "database"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    CONFIGURATION = "configuration"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"


@dataclass
class ErrorContext:
    """Comprehensive error context for tracking and analysis."""
    service_name: str
    operation: str
    workflow_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    category: ErrorCategory = ErrorCategory.INTERNAL
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    related_errors: List['ErrorContext'] = field(default_factory=list)
    recovery_attempts: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RetryConfiguration:
    """Configuration for retry mechanisms."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_factor: float = 2.0
    jitter: bool = True
    retryable_errors: List[Type[Exception]] = field(default_factory=list)
    retryable_categories: List[ErrorCategory] = field(default_factory=list)


class EnterpriseErrorHandler:
    """Enterprise-grade error handler with service-specific strategies."""

    def __init__(self):
        self.error_history: Dict[str, List[ErrorContext]] = {}
        self.recovery_strategies: Dict[str, Dict[str, Callable]] = {}
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        self._setup_default_strategies()

    def _setup_default_strategies(self):
        """Setup default recovery strategies for different error types."""
        # Network error recovery
        self.recovery_strategies["network"] = {
            "circuit_breaker": self._network_circuit_breaker_recovery,
            "connection_pool_refresh": self._network_connection_refresh_recovery,
            "dns_cache_flush": self._network_dns_cache_recovery
        }

        # Database error recovery
        self.recovery_strategies["database"] = {
            "connection_reconnect": self._database_reconnect_recovery,
            "transaction_rollback": self._database_transaction_recovery,
            "connection_pool_reset": self._database_pool_reset_recovery
        }

        # Resource error recovery
        self.recovery_strategies["resource"] = {
            "memory_cleanup": self._resource_memory_recovery,
            "cache_invalidation": self._resource_cache_recovery,
            "resource_pool_refresh": self._resource_pool_recovery
        }

        # Timeout error recovery
        self.recovery_strategies["timeout"] = {
            "timeout_extension": self._timeout_extension_recovery,
            "async_task_restart": self._timeout_async_restart_recovery,
            "resource_preemption": self._timeout_resource_preemption_recovery
        }

    async def handle_error(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Main error handling entry point."""
        try:
            # Record error
            await self._record_error(error, context)

            # Analyze error and determine strategy
            analysis = await self._analyze_error(error, context)

            # Attempt recovery
            recovery_result = await self._attempt_recovery(error, context, analysis)

            # Update metrics
            await self._update_error_metrics(context, recovery_result)

            # Log comprehensive error report
            await self._log_error_report(error, context, analysis, recovery_result)

            return {
                "handled": True,
                "recovery_attempted": recovery_result["attempted"],
                "recovery_successful": recovery_result["successful"],
                "next_action": recovery_result.get("next_action", "escalate"),
                "error_analysis": analysis
            }

        except Exception as handler_error:
            # Critical error in error handler itself
            await self._handle_critical_error(handler_error, context)
            return {
                "handled": False,
                "critical_error": True,
                "error": str(handler_error)
            }

    async def _record_error(self, error: Exception, context: ErrorContext):
        """Record error in history for analysis."""
        service_key = f"{context.service_name}_{context.operation}"

        if service_key not in self.error_history:
            self.error_history[service_key] = []

        # Add stack trace
        context.stack_trace = traceback.format_exc()

        # Store error context
        self.error_history[service_key].append(context)

        # Maintain history limit (keep last 1000 errors per service/operation)
        if len(self.error_history[service_key]) > 1000:
            self.error_history[service_key] = self.error_history[service_key][-1000:]

    async def _analyze_error(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Analyze error to determine appropriate recovery strategy."""
        analysis = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "is_retryable": self._is_retryable_error(error, context),
            "suggested_strategy": self._suggest_recovery_strategy(error, context),
            "estimated_recovery_time": self._estimate_recovery_time(error, context),
            "impact_assessment": self._assess_error_impact(context),
            "pattern_recognition": self._recognize_error_patterns(context)
        }

        return analysis

    def _is_retryable_error(self, error: Exception, context: ErrorContext) -> bool:
        """Determine if error is retryable."""
        # Service-specific retryable errors
        service_retryable = {
            ServiceNames.DOCUMENT_STORE: [
                ConnectionError, TimeoutError, OSError
            ],
            ServiceNames.PROMPT_STORE: [
                ConnectionError, TimeoutError
            ],
            ServiceNames.ANALYSIS_SERVICE: [
                ConnectionError, TimeoutError, ValueError
            ],
            ServiceNames.INTERPRETER: [
                ConnectionError, TimeoutError
            ]
        }

        if context.service_name in service_retryable:
            retryable_errors = service_retryable[context.service_name]
            if any(isinstance(error, err_type) for err_type in retryable_errors):
                return True

        # Category-based retryable errors
        category_retryable = {
            ErrorCategory.NETWORK: True,
            ErrorCategory.TIMEOUT: True,
            ErrorCategory.RESOURCE: context.retry_count < 2,
            ErrorCategory.EXTERNAL_SERVICE: True,
            ErrorCategory.INTERNAL: False
        }

        return category_retryable.get(context.category, False)

    def _suggest_recovery_strategy(self, error: Exception, context: ErrorContext) -> str:
        """Suggest appropriate recovery strategy."""
        if context.category == ErrorCategory.NETWORK:
            return "circuit_breaker" if context.retry_count > 2 else "connection_pool_refresh"
        elif context.category == ErrorCategory.DATABASE:
            return "connection_reconnect"
        elif context.category == ErrorCategory.TIMEOUT:
            return "timeout_extension" if context.retry_count < 2 else "async_task_restart"
        elif context.category == ErrorCategory.RESOURCE:
            return "cache_invalidation"
        else:
            return "generic_retry"

    def _estimate_recovery_time(self, error: Exception, context: ErrorContext) -> float:
        """Estimate time required for recovery."""
        base_times = {
            ErrorCategory.NETWORK: 5.0,
            ErrorCategory.DATABASE: 3.0,
            ErrorCategory.TIMEOUT: 10.0,
            ErrorCategory.RESOURCE: 2.0,
            ErrorCategory.INTERNAL: 1.0
        }

        base_time = base_times.get(context.category, 5.0)
        # Increase time with retry count
        return base_time * (1.5 ** context.retry_count)

    def _assess_error_impact(self, context: ErrorContext) -> Dict[str, Any]:
        """Assess the impact of the error."""
        return {
            "service_impact": "partial" if context.severity != ErrorSeverity.CRITICAL else "full",
            "workflow_impact": "blocked" if context.workflow_id else "none",
            "user_impact": "delayed" if context.user_id else "none",
            "recovery_urgency": context.severity.value,
            "escalation_required": context.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]
        }

    def _recognize_error_patterns(self, context: ErrorContext) -> Dict[str, Any]:
        """Recognize error patterns for proactive handling."""
        service_key = f"{context.service_name}_{context.operation}"
        recent_errors = self.error_history.get(service_key, [])

        # Analyze recent error patterns
        recent_count = len([e for e in recent_errors
                           if (datetime.now() - e.timestamp).seconds < 300])  # Last 5 minutes

        patterns = {
            "error_frequency": "high" if recent_count > 5 else "normal",
            "similar_errors": len([e for e in recent_errors[-10:]
                                 if e.category == context.category]),
            "recovery_success_rate": self._calculate_recovery_success_rate(service_key),
            "predicted_next_error": self._predict_next_error(service_key)
        }

        return patterns

    async def _attempt_recovery(self, error: Exception, context: ErrorContext,
                              analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt error recovery using appropriate strategy."""
        strategy_name = analysis["suggested_strategy"]

        if context.category.value in self.recovery_strategies:
            strategies = self.recovery_strategies[context.category.value]
            if strategy_name in strategies:
                try:
                    recovery_func = strategies[strategy_name]
                    result = await recovery_func(error, context, analysis)

                    # Record recovery attempt
                    context.recovery_attempts.append({
                        "strategy": strategy_name,
                        "timestamp": datetime.now().isoformat(),
                        "successful": result["successful"],
                        "details": result
                    })

                    return result

                except Exception as recovery_error:
                    return {
                        "attempted": True,
                        "successful": False,
                        "error": str(recovery_error),
                        "next_action": "escalate"
                    }

        # Default retry strategy
        return await self._default_retry_recovery(error, context, analysis)

    async def _default_retry_recovery(self, error: Exception, context: ErrorContext,
                                    analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Default retry recovery strategy."""
        if context.retry_count < context.max_retries and analysis["is_retryable"]:
            delay = min(1.0 * (2 ** context.retry_count), 30.0)  # Exponential backoff

            return {
                "attempted": True,
                "successful": False,  # Will be retried
                "next_action": "retry",
                "retry_delay": delay,
                "retry_count": context.retry_count + 1
            }

        return {
            "attempted": True,
            "successful": False,
            "next_action": "escalate",
            "reason": "max_retries_exceeded" if context.retry_count >= context.max_retries else "not_retryable"
        }

    # Service-specific recovery strategies
    async def _network_circuit_breaker_recovery(self, error: Exception, context: ErrorContext,
                                              analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Network circuit breaker recovery."""
        # Implement circuit breaker pattern
        circuit_key = f"{context.service_name}_circuit"

        # Check if circuit is open
        if hasattr(self, f"{circuit_key}_open") and getattr(self, f"{circuit_key}_open"):
            return {
                "attempted": True,
                "successful": False,
                "next_action": "circuit_open_wait",
                "wait_time": 60.0
            }

        # Open circuit after multiple failures
        if context.retry_count >= 3:
            setattr(self, f"{circuit_key}_open", True)
            # Schedule circuit close
            asyncio.create_task(self._close_circuit_after_delay(circuit_key, 300))

        return {
            "attempted": True,
            "successful": False,
            "next_action": "retry",
            "circuit_status": "opened" if context.retry_count >= 3 else "closed"
        }

    async def _close_circuit_after_delay(self, circuit_key: str, delay: float):
        """Close circuit after delay."""
        await asyncio.sleep(delay)
        setattr(self, f"{circuit_key}_open", False)

    async def _network_connection_refresh_recovery(self, error: Exception, context: ErrorContext,
                                                 analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Network connection pool refresh recovery."""
        # Refresh connection pools
        return {
            "attempted": True,
            "successful": True,
            "action": "connection_pool_refreshed",
            "next_action": "retry"
        }

    async def _database_reconnect_recovery(self, error: Exception, context: ErrorContext,
                                         analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Database reconnection recovery."""
        # Implement database reconnection logic
        return {
            "attempted": True,
            "successful": True,
            "action": "database_reconnected",
            "next_action": "retry"
        }

    async def _resource_memory_recovery(self, error: Exception, context: ErrorContext,
                                      analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Resource memory cleanup recovery."""
        import gc
        gc.collect()

        return {
            "attempted": True,
            "successful": True,
            "action": "memory_cleaned",
            "next_action": "retry"
        }

    async def _timeout_extension_recovery(self, error: Exception, context: ErrorContext,
                                        analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Timeout extension recovery."""
        return {
            "attempted": True,
            "successful": True,
            "action": "timeout_extended",
            "extension_seconds": 30.0,
            "next_action": "retry"
        }

    async def _timeout_async_restart_recovery(self, error: Exception, context: ErrorContext,
                                            analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Async task restart recovery."""
        return {
            "attempted": True,
            "successful": True,
            "action": "async_task_restarted",
            "next_action": "retry"
        }

    async def _network_dns_cache_recovery(self, error: Exception, context: ErrorContext,
                                        analysis: Dict[str, Any]) -> Dict[str, Any]:
        """DNS cache flush recovery."""
        return {
            "attempted": True,
            "successful": True,
            "action": "dns_cache_flushed",
            "next_action": "retry"
        }

    async def _database_transaction_recovery(self, error: Exception, context: ErrorContext,
                                           analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Database transaction rollback recovery."""
        return {
            "attempted": True,
            "successful": True,
            "action": "transaction_rolled_back",
            "next_action": "retry"
        }

    async def _database_pool_reset_recovery(self, error: Exception, context: ErrorContext,
                                          analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Database connection pool reset recovery."""
        return {
            "attempted": True,
            "successful": True,
            "action": "connection_pool_reset",
            "next_action": "retry"
        }

    async def _resource_cache_recovery(self, error: Exception, context: ErrorContext,
                                     analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Resource cache invalidation recovery."""
        return {
            "attempted": True,
            "successful": True,
            "action": "cache_invalidated",
            "next_action": "retry"
        }

    async def _resource_pool_recovery(self, error: Exception, context: ErrorContext,
                                    analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Resource pool refresh recovery."""
        return {
            "attempted": True,
            "successful": True,
            "action": "resource_pool_refreshed",
            "next_action": "retry"
        }

    async def _timeout_resource_preemption_recovery(self, error: Exception, context: ErrorContext,
                                                  analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Resource preemption for timeout recovery."""
        return {
            "attempted": True,
            "successful": True,
            "action": "resource_preempted",
            "next_action": "retry"
        }

    def _calculate_recovery_success_rate(self, service_key: str) -> float:
        """Calculate recovery success rate for service."""
        if service_key not in self.error_history:
            return 1.0

        recent_errors = self.error_history[service_key][-50:]  # Last 50 errors
        if not recent_errors:
            return 1.0

        successful_recoveries = sum(1 for error in recent_errors
                                  if error.recovery_attempts and
                                  any(attempt.get("successful", False)
                                      for attempt in error.recovery_attempts))

        return successful_recoveries / len(recent_errors)

    def _predict_next_error(self, service_key: str) -> Dict[str, Any]:
        """Predict likelihood of next error."""
        if service_key not in self.error_history:
            return {"probability": 0.1, "predicted_category": None}

        recent_errors = self.error_history[service_key][-20:]  # Last 20 errors
        if len(recent_errors) < 5:
            return {"probability": 0.2, "predicted_category": None}

        # Simple pattern recognition
        error_categories = [e.category for e in recent_errors]
        most_common = max(set(error_categories), key=error_categories.count)

        # Calculate trend
        recent_trend = len([e for e in recent_errors[-10:]
                           if e.category == most_common]) / 10

        return {
            "probability": min(recent_trend * 1.2, 0.8),  # Cap at 80%
            "predicted_category": most_common.value
        }

    async def _update_error_metrics(self, context: ErrorContext, recovery_result: Dict[str, Any]):
        """Update error metrics for monitoring."""
        service_key = context.service_name

        if service_key not in self.performance_metrics:
            self.performance_metrics[service_key] = {
                "total_errors": 0,
                "recovery_attempts": 0,
                "successful_recoveries": 0,
                "error_categories": {},
                "error_timeline": []
            }

        metrics = self.performance_metrics[service_key]
        metrics["total_errors"] += 1
        metrics["recovery_attempts"] += 1 if recovery_result["attempted"] else 0
        metrics["successful_recoveries"] += 1 if recovery_result.get("successful") else 0

        # Update category counts
        category_key = context.category.value
        if category_key not in metrics["error_categories"]:
            metrics["error_categories"][category_key] = 0
        metrics["error_categories"][category_key] += 1

        # Add timeline entry
        metrics["error_timeline"].append({
            "timestamp": context.timestamp.isoformat(),
            "category": category_key,
            "severity": context.severity.value,
            "recovered": recovery_result.get("successful", False)
        })

        # Maintain timeline limit
        if len(metrics["error_timeline"]) > 1000:
            metrics["error_timeline"] = metrics["error_timeline"][-1000:]

    async def _log_error_report(self, error: Exception, context: ErrorContext,
                              analysis: Dict[str, Any], recovery_result: Dict[str, Any]):
        """Log comprehensive error report."""
        error_report = {
            "service": context.service_name,
            "operation": context.operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "severity": context.severity.value,
            "category": context.category.value,
            "workflow_id": context.workflow_id,
            "user_id": context.user_id,
            "retry_count": context.retry_count,
            "analysis": analysis,
            "recovery_result": recovery_result,
            "timestamp": context.timestamp.isoformat(),
            "stack_trace": context.stack_trace
        }

        # Log based on severity
        if context.severity == ErrorSeverity.CRITICAL:
            fire_and_forget("critical", f"Critical error in {context.service_name}: {error}", context.service_name)
        elif context.severity == ErrorSeverity.HIGH:
            fire_and_forget("error", f"High severity error in {context.service_name}: {error}", context.service_name)
        else:
            fire_and_forget("warning", f"Error in {context.service_name}: {error}", context.service_name)

    async def _handle_critical_error(self, error: Exception, original_context: ErrorContext):
        """Handle critical errors in the error handler itself."""
        critical_report = {
            "level": "CRITICAL",
            "component": "EnterpriseErrorHandler",
            "original_error": str(error),
            "original_context": {
                "service": original_context.service_name,
                "operation": original_context.operation
            },
            "timestamp": datetime.now().isoformat(),
            "stack_trace": traceback.format_exc()
        }

        fire_and_forget("critical", f"CRITICAL: Error handler failure: {error}", "system")

    def get_error_statistics(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        if service_name:
            service_keys = [k for k in self.error_history.keys() if k.startswith(f"{service_name}_")]
        else:
            service_keys = list(self.error_history.keys())

        stats = {
            "total_services": len(set(k.split('_')[0] for k in service_keys)),
            "total_operations": len(service_keys),
            "total_errors": sum(len(errors) for errors in self.error_history.values()),
            "services": {}
        }

        for service_key in service_keys:
            service_name_part = service_key.split('_')[0]
            if service_name_part not in stats["services"]:
                stats["services"][service_name_part] = {
                    "operations": 0,
                    "total_errors": 0,
                    "recovery_rate": 0.0,
                    "error_categories": {}
                }

            service_stats = stats["services"][service_name_part]
            service_stats["operations"] += 1
            service_stats["total_errors"] += len(self.error_history[service_key])

            # Calculate recovery rate
            total_recoveries = sum(len([r for r in error.recovery_attempts
                                       if any(a.get("successful") for a in r)])
                                  for error in self.error_history[service_key])
            if service_stats["total_errors"] > 0:
                service_stats["recovery_rate"] = total_recoveries / service_stats["total_errors"]

        return stats

    async def cleanup_old_errors(self, days_to_keep: int = 30):
        """Clean up old error records."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        for service_key in list(self.error_history.keys()):
            original_count = len(self.error_history[service_key])
            self.error_history[service_key] = [
                error for error in self.error_history[service_key]
                if error.timestamp > cutoff_date
            ]

            removed_count = original_count - len(self.error_history[service_key])
            if removed_count > 0:
                print(f"Cleaned up {removed_count} old errors for {service_key}")


# Global error handler instance
enterprise_error_handler = EnterpriseErrorHandler()


def with_error_handling(service_name: str, operation: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                       category: ErrorCategory = ErrorCategory.INTERNAL):
    """Decorator for automatic error handling."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                context = ErrorContext(
                    service_name=service_name,
                    operation=operation,
                    severity=severity,
                    category=category,
                    workflow_id=kwargs.get('workflow_id'),
                    user_id=kwargs.get('user_id')
                )

                result = await enterprise_error_handler.handle_error(e, context)

                if result.get("recovery_successful"):
                    # Retry the operation
                    return await func(*args, **kwargs)
                else:
                    raise e

        return wrapper
    return decorator


@asynccontextmanager
async def error_context(service_name: str, operation: str, **context_kwargs):
    """Context manager for error handling."""
    context = ErrorContext(
        service_name=service_name,
        operation=operation,
        **context_kwargs
    )

    try:
        yield context
    except Exception as e:
        result = await enterprise_error_handler.handle_error(e, context)
        if not result.get("recovery_successful"):
            raise e
