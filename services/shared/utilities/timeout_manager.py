"""
Timeout Manager for preventing service hangs.

This module provides utilities to prevent service hangs by implementing
comprehensive timeout management for async operations, HTTP requests,
and service lifecycle events.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Callable, Optional, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class TimeoutManager:
    """Centralized timeout management for service operations."""

    # Default timeout values
    DEFAULT_HEALTH_CHECK_TIMEOUT = 5.0
    DEFAULT_STARTUP_TIMEOUT = 30.0
    DEFAULT_SHUTDOWN_TIMEOUT = 10.0
    DEFAULT_HTTP_TIMEOUT = 30.0
    DEFAULT_DB_OPERATION_TIMEOUT = 10.0

    @staticmethod
    async def with_timeout(
        coro: Callable[[], Any],
        timeout: float,
        operation_name: str = "operation"
    ) -> Any:
        """Execute a coroutine with timeout protection."""
        try:
            return await asyncio.wait_for(coro(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"{operation_name} timed out after {timeout}s")
            raise
        except Exception as e:
            logger.error(f"{operation_name} failed: {e}")
            raise

    @staticmethod
    @asynccontextmanager
    async def timeout_context(timeout: float, operation_name: str = "operation"):
        """Async context manager for timeout protection."""
        try:
            async with asyncio.timeout(timeout):
                yield
        except asyncio.TimeoutError:
            logger.error(f"{operation_name} timed out after {timeout}s")
            raise
        except Exception as e:
            logger.error(f"{operation_name} failed: {e}")
            raise

    @staticmethod
    def timeout_wrapper(timeout: float, operation_name: str = "operation"):
        """Decorator for adding timeout protection to async functions."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    async with asyncio.timeout(timeout):
                        return await func(*args, **kwargs)
                except asyncio.TimeoutError:
                    logger.error(f"{operation_name} timed out after {timeout}s")
                    raise
                except Exception as e:
                    logger.error(f"{operation_name} failed: {e}")
                    raise
            return wrapper
        return decorator

class HealthCheckTimeout:
    """Timeout protection for health check operations."""

    @staticmethod
    async def protected_health_check(
        health_func: Callable[[], Any],
        timeout: float = TimeoutManager.DEFAULT_HEALTH_CHECK_TIMEOUT
    ) -> dict:
        """Execute health check with timeout protection."""
        try:
            async with asyncio.timeout(timeout):
                result = await health_func()
                # Ensure timestamp is included
                if isinstance(result, dict) and "timestamp" not in result:
                    from datetime import datetime
                    result["timestamp"] = datetime.utcnow().isoformat()
                return result
        except asyncio.TimeoutError:
            return {
                "status": "degraded",
                "error": "health_check_timeout",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

class StartupTimeout:
    """Timeout protection for startup operations."""

    @staticmethod
    async def protected_startup(
        startup_funcs: list[Callable[[], Any]],
        overall_timeout: float = TimeoutManager.DEFAULT_STARTUP_TIMEOUT,
        individual_timeout: float = 10.0
    ) -> None:
        """Execute startup functions with timeout protection."""
        try:
            async with asyncio.timeout(overall_timeout):
                for func in startup_funcs:
                    try:
                        await asyncio.wait_for(func(), timeout=individual_timeout)
                    except asyncio.TimeoutError:
                        func_name = getattr(func, '__name__', str(func))
                        logger.warning(f"Startup function {func_name} timed out")
                    except Exception as e:
                        func_name = getattr(func, '__name__', str(func))
                        logger.warning(f"Startup function {func_name} failed: {e}")
        except asyncio.TimeoutError:
            logger.error("Overall startup timed out")
            raise
        except Exception as e:
            logger.error(f"Critical startup error: {e}")
            # Allow service to start in degraded state

class ShutdownTimeout:
    """Timeout protection for shutdown operations."""

    @staticmethod
    async def protected_shutdown(
        shutdown_funcs: list[Callable[[], Any]],
        overall_timeout: float = TimeoutManager.DEFAULT_SHUTDOWN_TIMEOUT,
        individual_timeout: float = 5.0
    ) -> None:
        """Execute shutdown functions with timeout protection."""
        try:
            async with asyncio.timeout(overall_timeout):
                for func in shutdown_funcs:
                    try:
                        await asyncio.wait_for(func(), timeout=individual_timeout)
                    except asyncio.TimeoutError:
                        func_name = getattr(func, '__name__', str(func))
                        logger.warning(f"Shutdown function {func_name} timed out")
                    except Exception as e:
                        func_name = getattr(func, '__name__', str(func))
                        logger.warning(f"Shutdown function {func_name} failed: {e}")
        except asyncio.TimeoutError:
            logger.error("Overall shutdown timed out")
        except Exception as e:
            logger.error(f"Critical shutdown error: {e}")

# Convenience functions for easy use
def with_health_timeout(timeout: float = TimeoutManager.DEFAULT_HEALTH_CHECK_TIMEOUT):
    """Decorator for health check functions."""
    return TimeoutManager.timeout_wrapper(timeout, "health_check")

def with_startup_timeout(timeout: float = TimeoutManager.DEFAULT_STARTUP_TIMEOUT):
    """Decorator for startup functions."""
    return TimeoutManager.timeout_wrapper(timeout, "startup")

def with_shutdown_timeout(timeout: float = TimeoutManager.DEFAULT_SHUTDOWN_TIMEOUT):
    """Decorator for shutdown functions."""
    return TimeoutManager.timeout_wrapper(timeout, "shutdown")

def with_http_timeout(timeout: float = TimeoutManager.DEFAULT_HTTP_TIMEOUT):
    """Decorator for HTTP operations."""
    return TimeoutManager.timeout_wrapper(timeout, "http_request")

def with_db_timeout(timeout: float = TimeoutManager.DEFAULT_DB_OPERATION_TIMEOUT):
    """Decorator for database operations."""
    return TimeoutManager.timeout_wrapper(timeout, "db_operation")
