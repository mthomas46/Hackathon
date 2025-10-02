#!/usr/bin/env python3
"""
Ecosystem-Wide Error Handling and Recovery Standardization
Implements consistent error handling patterns across all services
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
import time
import traceback
from abc import ABC, abstractmethod


class ErrorSeverity(Enum):
    """Standardized error severity levels"""
    CRITICAL = "critical"      # System-breaking errors
    HIGH = "high"             # Service-breaking errors
    MEDIUM = "medium"         # Feature-breaking errors
    LOW = "low"              # Warning-level errors
    INFO = "info"            # Informational errors


class ErrorCategory(Enum):
    """Standardized error categories"""
    VALIDATION = "validation"              # Input validation errors
    AUTHENTICATION = "authentication"      # Auth/authorization errors
    NETWORK = "network"                    # Network connectivity errors
    DATABASE = "database"                  # Database operation errors
    EXTERNAL_SERVICE = "external_service"  # External service dependency errors
    BUSINESS_LOGIC = "business_logic"      # Business rule violations
    SYSTEM = "system"                      # System-level errors
    CONFIGURATION = "configuration"        # Configuration errors
    TIMEOUT = "timeout"                    # Timeout errors
    RATE_LIMIT = "rate_limit"             # Rate limiting errors


@dataclass
class StandardError:
    """Standardized error structure"""
    error_id: str
    error_code: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    service_name: str
    timestamp: float
    context: Dict[str, Any]
    stack_trace: Optional[str] = None
    correlation_id: Optional[str] = None
    user_message: Optional[str] = None
    retry_after: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "error_id": self.error_id,
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.value,
            "category": self.category.value,
            "service": self.service_name,
            "timestamp": self.timestamp,
            "context": self.context,
            "correlation_id": self.correlation_id,
            "user_message": self.user_message or self.message,
            "retry_after": self.retry_after
        }


class ErrorHandler(ABC):
    """Abstract base class for error handlers"""
    
    @abstractmethod
    def handle(self, error: StandardError) -> Dict[str, Any]:
        """Handle the error and return response"""
        pass
    
    @abstractmethod
    def should_retry(self, error: StandardError) -> bool:
        """Determine if operation should be retried"""
        pass


class DefaultErrorHandler(ErrorHandler):
    """Default error handler implementation"""
    
    def handle(self, error: StandardError) -> Dict[str, Any]:
        """Handle error with standard response format"""
        response = {
            "success": False,
            "error": error.to_dict(),
            "timestamp": time.time()
        }
        
        # Add retry information if applicable
        if self.should_retry(error):
            response["retry_after"] = error.retry_after or 30
            response["retryable"] = True
        else:
            response["retryable"] = False
        
        return response
    
    def should_retry(self, error: StandardError) -> bool:
        """Determine retry eligibility based on error characteristics"""
        # Network and timeout errors are generally retryable
        if error.category in [ErrorCategory.NETWORK, ErrorCategory.TIMEOUT]:
            return True
        
        # External service errors may be retryable
        if error.category == ErrorCategory.EXTERNAL_SERVICE:
            return True
        
        # High severity errors usually not retryable
        if error.severity == ErrorSeverity.CRITICAL:
            return False
        
        # Database errors may be retryable depending on context
        if error.category == ErrorCategory.DATABASE:
            # Connection errors are retryable, constraint violations are not
            return "connection" in error.message.lower()
        
        return False


class CircuitBreakerErrorHandler(ErrorHandler):
    """Error handler with circuit breaker pattern"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def handle(self, error: StandardError) -> Dict[str, Any]:
        """Handle error with circuit breaker logic"""
        self._update_circuit_state(error)
        
        response = {
            "success": False,
            "error": error.to_dict(),
            "timestamp": time.time(),
            "circuit_breaker": {
                "state": self.state,
                "failure_count": self.failure_count,
                "next_retry_after": self._get_next_retry_time()
            }
        }
        
        return response
    
    def should_retry(self, error: StandardError) -> bool:
        """Determine retry based on circuit breaker state"""
        if self.state == "open":
            return False
        
        return DefaultErrorHandler().should_retry(error)
    
    def _update_circuit_state(self, error: StandardError):
        """Update circuit breaker state based on error"""
        current_time = time.time()
        
        if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            self.failure_count += 1
            self.last_failure_time = current_time
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
        
        # Recovery logic
        if self.state == "open" and current_time - self.last_failure_time > self.recovery_timeout:
            self.state = "half-open"
            self.failure_count = 0
    
    def _get_next_retry_time(self) -> Optional[int]:
        """Calculate next retry time based on circuit state"""
        if self.state == "open":
            return self.recovery_timeout - int(time.time() - self.last_failure_time)
        return None


class RetryManager:
    """Manages retry logic with exponential backoff"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for retry attempt with exponential backoff"""
        delay = self.base_delay * (2 ** attempt)
        return min(delay, self.max_delay)
    
    def should_retry(self, attempt: int, error: StandardError) -> bool:
        """Determine if retry should be attempted"""
        if attempt >= self.max_retries:
            return False
        
        # Use error handler to determine retry eligibility
        handler = DefaultErrorHandler()
        return handler.should_retry(error)


class StandardErrorFactory:
    """Factory for creating standardized errors"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.error_counter = 0
    
    def create_error(self, 
                    error_code: str,
                    message: str,
                    severity: ErrorSeverity,
                    category: ErrorCategory,
                    context: Dict[str, Any] = None,
                    correlation_id: str = None,
                    user_message: str = None,
                    include_stack_trace: bool = False) -> StandardError:
        """Create a standardized error"""
        
        self.error_counter += 1
        error_id = f"{self.service_name}_{int(time.time())}_{self.error_counter}"
        
        stack_trace = None
        if include_stack_trace:
            stack_trace = traceback.format_exc()
        
        return StandardError(
            error_id=error_id,
            error_code=error_code,
            message=message,
            severity=severity,
            category=category,
            service_name=self.service_name,
            timestamp=time.time(),
            context=context or {},
            stack_trace=stack_trace,
            correlation_id=correlation_id,
            user_message=user_message
        )
    
    def validation_error(self, field: str, value: Any, message: str) -> StandardError:
        """Create a validation error"""
        return self.create_error(
            error_code="VALIDATION_ERROR",
            message=f"Validation failed for field '{field}': {message}",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION,
            context={"field": field, "value": str(value)},
            user_message=f"Invalid value for {field}: {message}"
        )
    
    def network_error(self, target_service: str, operation: str, details: str) -> StandardError:
        """Create a network connectivity error"""
        return self.create_error(
            error_code="NETWORK_ERROR",
            message=f"Failed to connect to {target_service} for {operation}: {details}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK,
            context={"target_service": target_service, "operation": operation},
            user_message="Service temporarily unavailable. Please try again later.",
            retry_after=30
        )
    
    def database_error(self, operation: str, details: str) -> StandardError:
        """Create a database operation error"""
        return self.create_error(
            error_code="DATABASE_ERROR",
            message=f"Database operation failed: {operation} - {details}",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            context={"operation": operation},
            user_message="Data operation failed. Please try again.",
            include_stack_trace=True
        )
    
    def external_service_error(self, service: str, endpoint: str, status_code: int) -> StandardError:
        """Create an external service error"""
        return self.create_error(
            error_code="EXTERNAL_SERVICE_ERROR",
            message=f"External service {service} returned error: {status_code}",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_SERVICE,
            context={"service": service, "endpoint": endpoint, "status_code": status_code},
            user_message="External service unavailable. Please try again later.",
            retry_after=60
        )


class ErrorRecoveryManager:
    """Manages error recovery strategies"""
    
    def __init__(self):
        self.recovery_strategies = {}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default recovery strategies"""
        
        def database_recovery(error: StandardError, context: Dict[str, Any]) -> Dict[str, Any]:
            """Recovery strategy for database errors"""
            return {
                "strategy": "database_fallback",
                "actions": [
                    "retry_with_backoff",
                    "use_cached_data_if_available",
                    "degrade_functionality_gracefully"
                ],
                "fallback_data": context.get("cached_data"),
                "degraded_mode": True
            }
        
        def network_recovery(error: StandardError, context: Dict[str, Any]) -> Dict[str, Any]:
            """Recovery strategy for network errors"""
            return {
                "strategy": "network_fallback",
                "actions": [
                    "retry_with_exponential_backoff",
                    "try_alternative_endpoint",
                    "use_local_cache"
                ],
                "retry_delay": 5,
                "max_retries": 3,
                "alternative_endpoints": context.get("alternative_endpoints", [])
            }
        
        def validation_recovery(error: StandardError, context: Dict[str, Any]) -> Dict[str, Any]:
            """Recovery strategy for validation errors"""
            return {
                "strategy": "validation_recovery",
                "actions": [
                    "sanitize_input",
                    "use_default_values",
                    "request_user_correction"
                ],
                "requires_user_action": True,
                "suggested_corrections": context.get("validation_suggestions", [])
            }
        
        self.recovery_strategies[ErrorCategory.DATABASE] = database_recovery
        self.recovery_strategies[ErrorCategory.NETWORK] = network_recovery
        self.recovery_strategies[ErrorCategory.VALIDATION] = validation_recovery
    
    def get_recovery_strategy(self, error: StandardError, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get recovery strategy for an error"""
        context = context or {}
        
        if error.category in self.recovery_strategies:
            return self.recovery_strategies[error.category](error, context)
        
        # Default recovery strategy
        return {
            "strategy": "default_recovery",
            "actions": ["log_error", "return_user_friendly_message"],
            "requires_manual_intervention": error.severity == ErrorSeverity.CRITICAL
        }


class EcosystemErrorManager:
    """Central error management for the entire ecosystem"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.error_factory = StandardErrorFactory(service_name)
        self.error_handler = DefaultErrorHandler()
        self.circuit_breaker_handler = CircuitBreakerErrorHandler()
        self.retry_manager = RetryManager()
        self.recovery_manager = ErrorRecoveryManager()
        self.error_log = []
    
    def handle_error(self, 
                    error_code: str,
                    message: str,
                    severity: ErrorSeverity,
                    category: ErrorCategory,
                    context: Dict[str, Any] = None,
                    use_circuit_breaker: bool = False) -> Dict[str, Any]:
        """Handle an error with full ecosystem error management"""
        
        # Create standardized error
        error = self.error_factory.create_error(
            error_code=error_code,
            message=message,
            severity=severity,
            category=category,
            context=context
        )
        
        # Log error
        self.error_log.append(error)
        
        # Choose appropriate handler
        handler = self.circuit_breaker_handler if use_circuit_breaker else self.error_handler
        
        # Handle error
        response = handler.handle(error)
        
        # Add recovery strategy
        recovery_strategy = self.recovery_manager.get_recovery_strategy(error, context)
        response["recovery"] = recovery_strategy
        
        return response
    
    def with_error_handling(self, operation_name: str):
        """Decorator for automatic error handling"""
        def decorator(func: Callable):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Automatically handle unexpected errors
                    return self.handle_error(
                        error_code="UNEXPECTED_ERROR",
                        message=f"Unexpected error in {operation_name}: {str(e)}",
                        severity=ErrorSeverity.HIGH,
                        category=ErrorCategory.SYSTEM,
                        context={"operation": operation_name, "args": str(args)[:200]}
                    )
            return wrapper
        return decorator
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        if not self.error_log:
            return {"total_errors": 0}
        
        total_errors = len(self.error_log)
        
        # Count by severity
        severity_counts = {}
        for error in self.error_log:
            severity = error.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count by category
        category_counts = {}
        for error in self.error_log:
            category = error.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Recent errors (last hour)
        recent_cutoff = time.time() - 3600
        recent_errors = [e for e in self.error_log if e.timestamp > recent_cutoff]
        
        return {
            "total_errors": total_errors,
            "recent_errors": len(recent_errors),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "error_rate_per_hour": len(recent_errors),
            "most_common_category": max(category_counts.items(), key=lambda x: x[1])[0] if category_counts else None
        }


# Example usage and testing
def create_service_error_manager(service_name: str) -> EcosystemErrorManager:
    """Create a configured error manager for a service"""
    return EcosystemErrorManager(service_name)


def test_error_handling():
    """Test the error handling system"""
    
    # Create error manager for doc_store service
    error_manager = create_service_error_manager("doc_store")
    
    # Test various error scenarios
    print("Testing Error Handling System")
    print("=" * 40)
    
    # Validation error
    validation_response = error_manager.handle_error(
        error_code="INVALID_DOCUMENT_FORMAT",
        message="Document content must be a string",
        severity=ErrorSeverity.MEDIUM,
        category=ErrorCategory.VALIDATION,
        context={"field": "content", "provided_type": "int"}
    )
    print("Validation Error Response:")
    print(json.dumps(validation_response, indent=2))
    
    # Network error with circuit breaker
    network_response = error_manager.handle_error(
        error_code="SERVICE_UNREACHABLE",
        message="Cannot connect to analysis-service",
        severity=ErrorSeverity.HIGH,
        category=ErrorCategory.NETWORK,
        context={"target_service": "analysis-service", "operation": "analyze_document"},
        use_circuit_breaker=True
    )
    print("\nNetwork Error with Circuit Breaker:")
    print(json.dumps(network_response, indent=2))
    
    # Get error statistics
    stats = error_manager.get_error_statistics()
    print("\nError Statistics:")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    test_error_handling()
