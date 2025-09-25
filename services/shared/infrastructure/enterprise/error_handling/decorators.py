"""Error handling decorators for enterprise applications."""

import functools
import time
from typing import Any, Callable, Dict, Optional

from .error_handler import EnterpriseErrorHandler


# Global error handler instance
_error_handler = EnterpriseErrorHandler()


def enterprise_error_handler_decorator(service_name: str, operation: str):
    """Decorator for enterprise error handling."""

    def decorator(func: Callable) -> Callable:
        """Create the actual decorator function with enterprise error handling."""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                start_time = time.time()
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                # Log successful operation
                print(f"[SUCCESS] {service_name}.{operation} completed in {duration:.2f}s")

                return result

            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                    "duration": time.time() - start_time if 'start_time' in locals() else 0
                }

                recovery_result = _error_handler.handle_error(
                    e, service_name, operation, context
                )

                # Re-raise the original exception with recovery info
                raise type(e)(f"{str(e)} | Recovery: {recovery_result}") from e

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                start_time = time.time()
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Log successful operation
                print(f"[SUCCESS] {service_name}.{operation} completed in {duration:.2f}s")

                return result

            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                    "duration": time.time() - start_time if 'start_time' in locals() else 0
                }

                recovery_result = _error_handler.handle_error(
                    e, service_name, operation, context
                )

                # Re-raise the original exception with recovery info
                raise type(e)(f"{str(e)} | Recovery: {recovery_result}") from e

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def circuit_breaker(service_name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0):
    """Circuit breaker decorator."""

    def decorator(func: Callable) -> Callable:
        """Create circuit breaker decorator for the function."""
        cb = _error_handler._get_circuit_breaker(service_name)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry decorator for transient failures."""

    def decorator(func: Callable) -> Callable:
        """Create retry decorator with exponential backoff."""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay * (backoff ** attempt))

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay * (backoff ** attempt))

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
