"""Error Handling Integration - Leverage Shared Error Handling Patterns.

This module integrates with the shared error handling infrastructure to provide
consistent, enterprise-grade error handling across the simulation service and
its ecosystem integrations.
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Type, Union
from datetime import datetime
import traceback
import asyncio
import functools

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.utilities.simulation_utilities import get_simulation_error_handler

# Import shared error handling patterns (with fallbacks)
try:
    from shared.error_handling.handlers import ErrorHandler as SharedErrorHandler
    from shared.error_handling.context import ErrorContext
    from shared.error_handling.classification import ErrorClassifier
    from shared.error_handling.recovery import ErrorRecoveryManager
    from shared.error_handling.logging import ErrorLogger
except ImportError:
    # Fallback implementations
    class ErrorContext:
        def __init__(self, operation: str, service: str = None, user_id: str = None, **kwargs):
            self.operation = operation
            self.service = service
            self.user_id = user_id
            self.metadata = kwargs
            self.timestamp = datetime.now()

    class ErrorClassifier:
        @staticmethod
        def classify_error(error: Exception) -> str:
            error_type = type(error).__name__.lower()
            if "timeout" in error_type or "timeout" in str(error).lower():
                return "timeout"
            elif "connection" in error_type or "connect" in str(error).lower():
                return "connection"
            elif "validation" in error_type or "pydantic" in str(error).lower():
                return "validation"
            elif "authorization" in str(error).lower() or "forbidden" in str(error).lower():
                return "authorization"
            elif "notfound" in error_type or "404" in str(error):
                return "not_found"
            else:
                return "unknown"

    class ErrorRecoveryManager:
        def __init__(self):
            self.recovery_strategies = {}

        def register_strategy(self, error_type: str, strategy: Callable):
            self.recovery_strategies[error_type] = strategy

        def get_recovery_strategy(self, error_type: str) -> Optional[Callable]:
            return self.recovery_strategies.get(error_type)

    class ErrorLogger:
        def __init__(self):
            self.logger = None

        def log_error(self, error: Exception, context: ErrorContext, level: str = "error"):
            print(f"[{level.upper()}] {context.operation}: {error}")

    class SharedErrorHandler:
        def __init__(self):
            self.classifier = ErrorClassifier()
            self.recovery_manager = ErrorRecoveryManager()
            self.error_logger = ErrorLogger()

        def handle_error(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
            error_type = self.classifier.classify_error(error)
            recovery_strategy = self.recovery_manager.get_recovery_strategy(error_type)

            result = {
                "error_type": error_type,
                "error_message": str(error),
                "context": context.__dict__,
                "traceback": traceback.format_exc(),
                "recovery_strategy": recovery_strategy.__name__ if recovery_strategy else None,
                "timestamp": datetime.now()
            }

            self.error_logger.log_error(error, context)
            return result


class SimulationErrorHandlingIntegration:
    """Integration layer for simulation error handling with shared infrastructure."""

    def __init__(self):
        """Initialize error handling integration."""
        self.logger = get_simulation_logger()
        self.simulation_error_handler = get_simulation_error_handler()

        # Shared error handling components
        self.shared_error_handler = SharedErrorHandler()
        self.error_contexts: Dict[str, ErrorContext] = {}

        # Error tracking and metrics
        self.error_counts: Dict[str, int] = {}
        self.error_timestamps: Dict[str, List[datetime]] = {}

        # Recovery strategies
        self._setup_recovery_strategies()

        self.logger.info("Simulation error handling integration initialized")

    def _setup_recovery_strategies(self):
        """Set up error recovery strategies."""
        # Timeout recovery - exponential backoff
        self.shared_error_handler.recovery_manager.register_strategy(
            "timeout", self._timeout_recovery_strategy
        )

        # Connection recovery - circuit breaker pattern
        self.shared_error_handler.recovery_manager.recovery_manager.register_strategy(
            "connection", self._connection_recovery_strategy
        )

        # Validation recovery - user-friendly error messages
        self.shared_error_handler.recovery_manager.register_strategy(
            "validation", self._validation_recovery_strategy
        )

        # Authorization recovery - re-authentication
        self.shared_error_handler.recovery_manager.register_strategy(
            "authorization", self._authorization_recovery_strategy
        )

        # Not found recovery - fallback or creation
        self.shared_error_handler.recovery_manager.register_strategy(
            "not_found", self._not_found_recovery_strategy
        )

    async def handle_simulation_error(self,
                                    error: Exception,
                                    operation: str,
                                    service: str = None,
                                    simulation_id: str = None,
                                    **kwargs) -> Dict[str, Any]:
        """Handle simulation-specific errors using shared patterns."""
        try:
            # Create error context
            context = ErrorContext(
                operation=operation,
                service=service or "simulation_service",
                user_id=kwargs.get("user_id"),
                simulation_id=simulation_id,
                **kwargs
            )

            # Track error metrics
            self._track_error_metrics(error, context)

            # Use shared error handler
            shared_result = self.shared_error_handler.handle_error(error, context)

            # Enhance with simulation-specific handling
            simulation_result = await self._enhance_error_handling(error, context, shared_result)

            # Log comprehensive error information
            await self._log_comprehensive_error(error, context, simulation_result)

            return simulation_result

        except Exception as handler_error:
            # Fallback error handling
            self.logger.error(
                "Error in error handler",
                error=str(handler_error),
                original_error=str(error),
                operation=operation
            )

            return {
                "error_type": "handler_failure",
                "error_message": "Error handler failed",
                "original_error": str(error),
                "handler_error": str(handler_error),
                "timestamp": datetime.now()
            }

    def _track_error_metrics(self, error: Exception, context: ErrorContext):
        """Track error metrics for monitoring and alerting."""
        error_type = self.shared_error_handler.classifier.classify_error(error)

        # Increment error count
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        # Track timestamps for rate calculation
        if error_type not in self.error_timestamps:
            self.error_timestamps[error_type] = []
        self.error_timestamps[error_type].append(datetime.now())

        # Keep only last 100 timestamps for memory efficiency
        if len(self.error_timestamps[error_type]) > 100:
            self.error_timestamps[error_type] = self.error_timestamps[error_type][-100:]

    async def _enhance_error_handling(self,
                                    error: Exception,
                                    context: ErrorContext,
                                    shared_result: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance error handling with simulation-specific logic."""
        enhanced_result = shared_result.copy()

        # Add simulation-specific enhancements
        enhanced_result.update({
            "simulation_context": {
                "operation": context.operation,
                "service": context.service,
                "simulation_id": getattr(context, 'simulation_id', None),
                "user_impact": self._assess_user_impact(error, context),
                "recovery_suggestions": await self._generate_recovery_suggestions(error, context)
            },
            "ecosystem_impact": self._assess_ecosystem_impact(error, context),
            "business_impact": self._assess_business_impact(error, context)
        })

        return enhanced_result

    async def _log_comprehensive_error(self,
                                     error: Exception,
                                     context: ErrorContext,
                                     result: Dict[str, Any]):
        """Log comprehensive error information."""
        log_data = {
            "error_type": result.get("error_type"),
            "operation": context.operation,
            "service": context.service,
            "simulation_id": getattr(context, 'simulation_id', None),
            "user_impact": result.get("simulation_context", {}).get("user_impact"),
            "business_impact": result.get("business_impact"),
            "recovery_strategy": result.get("recovery_strategy"),
            "traceback": result.get("traceback", "").split("\n")[-1]  # Last line only for brevity
        }

        # Log at appropriate level based on business impact
        business_impact = result.get("business_impact", "low")
        if business_impact == "critical":
            self.logger.critical("Critical simulation error", **log_data)
        elif business_impact == "high":
            self.logger.error("High-impact simulation error", **log_data)
        elif business_impact == "medium":
            self.logger.warning("Medium-impact simulation error", **log_data)
        else:
            self.logger.info("Low-impact simulation error", **log_data)

    def _assess_user_impact(self, error: Exception, context: ErrorContext) -> str:
        """Assess user impact of the error."""
        error_type = self.shared_error_handler.classifier.classify_error(error)

        # High impact errors
        if error_type in ["authorization", "not_found"] and context.operation in ["start_simulation", "get_results"]:
            return "high"

        # Medium impact errors
        if error_type == "validation" or "timeout" in str(error).lower():
            return "medium"

        # Low impact errors
        return "low"

    async def _generate_recovery_suggestions(self, error: Exception, context: ErrorContext) -> List[str]:
        """Generate recovery suggestions for the error."""
        suggestions = []
        error_type = self.shared_error_handler.classifier.classify_error(error)

        if error_type == "timeout":
            suggestions.extend([
                "Check network connectivity",
                "Consider increasing timeout values",
                "Retry the operation"
            ])

        elif error_type == "connection":
            suggestions.extend([
                "Verify service availability",
                "Check network configuration",
                "Contact system administrator"
            ])

        elif error_type == "validation":
            suggestions.extend([
                "Review input data format",
                "Check required fields",
                "Validate data constraints"
            ])

        elif error_type == "authorization":
            suggestions.extend([
                "Verify authentication credentials",
                "Check user permissions",
                "Re-authenticate if necessary"
            ])

        elif error_type == "not_found":
            suggestions.extend([
                "Verify resource identifiers",
                "Check if resource exists",
                "Review operation parameters"
            ])

        return suggestions

    def _assess_ecosystem_impact(self, error: Exception, context: ErrorContext) -> str:
        """Assess ecosystem impact of the error."""
        error_type = self.shared_error_handler.classifier.classify_error(error)

        # Critical ecosystem impact
        if error_type == "connection" and context.service in ["mock_data_generator", "doc_store"]:
            return "high"

        # Medium ecosystem impact
        if error_type == "timeout" or context.operation in ["workflow_execution", "service_coordination"]:
            return "medium"

        # Low ecosystem impact
        return "low"

    def _assess_business_impact(self, error: Exception, context: ErrorContext) -> str:
        """Assess business impact of the error."""
        error_type = self.shared_error_handler.classifier.classify_error(error)

        # Critical business impact
        if (error_type in ["connection", "authorization"] and
            context.operation in ["start_simulation", "save_results", "generate_reports"]):
            return "critical"

        # High business impact
        if context.operation in ["process_payment", "send_notifications"] or error_type == "not_found":
            return "high"

        # Medium business impact
        if error_type in ["timeout", "validation"]:
            return "medium"

        # Low business impact
        return "low"

    async def _timeout_recovery_strategy(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Recovery strategy for timeout errors."""
        return {
            "strategy": "exponential_backoff",
            "max_attempts": 3,
            "base_delay": 1.0,
            "max_delay": 30.0,
            "jitter": True
        }

    async def _connection_recovery_strategy(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Recovery strategy for connection errors."""
        return {
            "strategy": "circuit_breaker",
            "failure_threshold": 5,
            "recovery_timeout": 60,
            "expected_exception": "ConnectionError"
        }

    async def _validation_recovery_strategy(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Recovery strategy for validation errors."""
        return {
            "strategy": "user_input_validation",
            "validation_rules": ["required_fields", "data_types", "constraints"],
            "error_messages": {
                "required": "This field is required",
                "type": "Invalid data type",
                "constraint": "Value does not meet requirements"
            }
        }

    async def _authorization_recovery_strategy(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Recovery strategy for authorization errors."""
        return {
            "strategy": "re_authentication",
            "redirect_url": "/auth/login",
            "preserve_context": True,
            "max_attempts": 3
        }

    async def _not_found_recovery_strategy(self, error: Exception, context: ErrorContext) -> Dict[str, Any]:
        """Recovery strategy for not found errors."""
        return {
            "strategy": "fallback_or_create",
            "fallback_options": ["default_value", "create_resource", "search_similar"],
            "auto_create": context.operation.startswith("get_"),
            "user_confirmation": True
        }

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics."""
        now = datetime.now()
        time_window = 3600  # 1 hour in seconds

        statistics = {
            "total_errors": sum(self.error_counts.values()),
            "error_counts_by_type": self.error_counts.copy(),
            "error_rates_per_hour": {},
            "recent_errors": [],
            "top_error_types": sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }

        # Calculate error rates
        for error_type, timestamps in self.error_timestamps.items():
            recent_timestamps = [t for t in timestamps if (now - t).total_seconds() < time_window]
            rate_per_hour = len(recent_timestamps)
            statistics["error_rates_per_hour"][error_type] = rate_per_hour

        # Recent errors (last 10)
        recent_error_types = []
        for error_type, timestamps in self.error_timestamps.items():
            recent_error_types.extend([(error_type, t) for t in timestamps[-5:]])  # Last 5 of each type

        recent_error_types.sort(key=lambda x: x[1], reverse=True)
        statistics["recent_errors"] = recent_error_types[:10]

        return statistics

    async def handle_bulk_errors(self, errors: List[Tuple[Exception, ErrorContext]]) -> Dict[str, Any]:
        """Handle multiple errors efficiently."""
        results = []

        # Process errors in parallel for better performance
        tasks = [self.handle_simulation_error(error, context.operation,
                                            context.service, **context.metadata)
                for error, context in errors]

        bulk_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(bulk_results):
            if isinstance(result, Exception):
                results.append({
                    "error": str(result),
                    "original_context": errors[i][1].__dict__,
                    "processing_failed": True
                })
            else:
                results.append(result)

        # Aggregate bulk statistics
        bulk_stats = {
            "total_errors": len(errors),
            "processed_errors": len([r for r in results if not r.get("processing_failed", False)]),
            "failed_processing": len([r for r in results if r.get("processing_failed", False)]),
            "error_types": {},
            "business_impacts": {}
        }

        for result in results:
            if not result.get("processing_failed"):
                error_type = result.get("error_type", "unknown")
                business_impact = result.get("business_impact", "unknown")

                bulk_stats["error_types"][error_type] = bulk_stats["error_types"].get(error_type, 0) + 1
                bulk_stats["business_impacts"][business_impact] = bulk_stats["business_impacts"].get(business_impact, 0) + 1

        return {
            "results": results,
            "bulk_statistics": bulk_stats,
            "processing_time": datetime.now()
        }


# Error handling decorator
def simulation_error_handler(operation: str = None, service: str = None):
    """Decorator for consistent error handling in simulation operations."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get error handler
            error_integration = get_simulation_error_handling_integration()

            # Extract operation name
            op_name = operation or func.__name__

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Handle the error
                result = await error_integration.handle_simulation_error(
                    e, op_name, service, **kwargs
                )

                # Re-raise with enhanced context
                raise type(e)(f"{str(e)} - See error context: {result.get('simulation_context', {})}")

        return wrapper
    return decorator


# Global integration instance
_simulation_error_integration: Optional[SimulationErrorHandlingIntegration] = None


def get_simulation_error_handling_integration() -> SimulationErrorHandlingIntegration:
    """Get the global simulation error handling integration instance."""
    global _simulation_error_integration
    if _simulation_error_integration is None:
        _simulation_error_integration = SimulationErrorHandlingIntegration()
    return _simulation_error_integration


__all__ = [
    'SimulationErrorHandlingIntegration',
    'simulation_error_handler',
    'get_simulation_error_handling_integration'
]
