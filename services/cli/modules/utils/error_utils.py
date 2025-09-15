"""Error handling utilities for CLI operations."""

from typing import Dict, Any
from services.shared.error_handling import ServiceException, ValidationException
from services.shared.logging import fire_and_forget


def handle_cli_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for CLI operations.

    Logs the error and returns a standardized error response.
    """
    # Log the error
    fire_and_forget("error", f"CLI {operation} error: {error}", "cli", context)

    # Create error response based on exception type
    if isinstance(error, ServiceException):
        return {
            'success': False,
            'error': 'service_error',
            'message': error.message,
            'details': error.details,
            'error_code': error.error_code
        }
    elif isinstance(error, ValidationException):
        return {
            'success': False,
            'error': 'validation_error',
            'message': error.message,
            'details': error.details,
            'error_code': error.error_code
        }
    elif isinstance(error, KeyboardInterrupt):
        return {
            'success': False,
            'error': 'interrupted',
            'message': 'Operation was interrupted by user',
            'details': {}
        }
    elif isinstance(error, TimeoutError) or isinstance(error, asyncio.TimeoutError):
        return {
            'success': False,
            'error': 'timeout',
            'message': f'Operation timed out: {operation}',
            'details': {'timeout_seconds': getattr(error, 'timeout', 30)}
        }
    elif isinstance(error, ConnectionError):
        return {
            'success': False,
            'error': 'connection_error',
            'message': 'Connection failed',
            'details': {'original_error': str(error)}
        }
    else:
        # Generic error
        return {
            'success': False,
            'error': 'unknown_error',
            'message': f'Unexpected error during {operation}: {str(error)}',
            'details': {'error_type': type(error).__name__}
        }


def create_user_friendly_error_message(error_response: Dict[str, Any]) -> str:
    """Convert error response to user-friendly message."""
    error_type = error_response.get('error', 'unknown')

    if error_type == 'service_error':
        return f"Service error: {error_response.get('message', 'Unknown service error')}"
    elif error_type == 'validation_error':
        return f"Validation error: {error_response.get('message', 'Invalid input')}"
    elif error_type == 'interrupted':
        return "Operation cancelled by user"
    elif error_type == 'timeout':
        return f"Operation timed out after {error_response.get('details', {}).get('timeout_seconds', 30)} seconds"
    elif error_type == 'connection_error':
        return "Connection failed - please check network and service status"
    else:
        return error_response.get('message', 'An unexpected error occurred')


def should_retry_operation(error_response: Dict[str, Any], attempt: int, max_attempts: int = 3) -> bool:
    """Determine if an operation should be retried based on the error."""
    if attempt >= max_attempts:
        return False

    error_type = error_response.get('error', '')

    # Retry on these error types
    retryable_errors = [
        'timeout',
        'connection_error',
        'service_unavailable'
    ]

    return error_type in retryable_errors


def get_retry_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 30.0) -> float:
    """Calculate retry delay using exponential backoff."""
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)
