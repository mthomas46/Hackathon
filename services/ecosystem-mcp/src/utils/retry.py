"""
Retry utilities with exponential backoff.

Provides decorators and utilities for resilient operations.
"""

import logging
from functools import wraps
from typing import Callable, Any, Type, Tuple

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log,
)

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exception types to retry on
    
    Returns:
        Decorated function with retry logic
    
    Example:
        @retry_with_backoff(max_attempts=3)
        async def fetch_data():
            response = await httpx.get("https://api.example.com")
            return response.json()
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        reraise=True,
    )


def retry_health_check(func: Callable) -> Callable:
    """
    Specialized retry decorator for health checks.
    
    - 3 attempts
    - 1-5 second exponential backoff
    - Retries on any exception
    - Logs warnings on retry
    """
    @wraps(func)
    @retry_with_backoff(max_attempts=3, min_wait=1, max_wait=5)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    
    return wrapper


def retry_external_call(func: Callable) -> Callable:
    """
    Specialized retry decorator for external API calls.
    
    - 5 attempts
    - 2-10 second exponential backoff
    - Retries on connection/timeout errors
    - Logs warnings on retry
    """
    import httpx
    
    retry_exceptions = (
        httpx.ConnectError,
        httpx.TimeoutException,
        httpx.NetworkError,
        ConnectionError,
        TimeoutError,
    )
    
    @wraps(func)
    @retry_with_backoff(max_attempts=5, min_wait=2, max_wait=10, exceptions=retry_exceptions)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    
    return wrapper


def retry_database_operation(func: Callable) -> Callable:
    """
    Specialized retry decorator for database operations.
    
    - 3 attempts
    - 1-5 second exponential backoff
    - Retries on connection errors
    - Logs warnings on retry
    """
    from sqlalchemy.exc import OperationalError, DBAPIError
    
    retry_exceptions = (
        OperationalError,
        DBAPIError,
        ConnectionError,
    )
    
    @wraps(func)
    @retry_with_backoff(max_attempts=3, min_wait=1, max_wait=5, exceptions=retry_exceptions)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    
    return wrapper


# Sync versions for non-async code
def retry_sync(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Synchronous version of retry_with_backoff.
    
    For use with synchronous functions.
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.DEBUG),
        reraise=True,
    )

