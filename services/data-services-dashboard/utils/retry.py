"""
Retry logic for network calls.

Provides decorators and utilities for implementing retry logic with exponential backoff.
"""

from functools import wraps
import time
from typing import Callable, Any, Tuple, Type
import httpx


def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (httpx.RequestError, httpx.HTTPStatusError)
):
    """
    Retry decorator for network calls with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        backoff: Multiplier for delay on each retry (default: 2.0)
        exceptions: Tuple of exceptions to catch and retry (default: httpx errors)
        
    Returns:
        Decorated function that retries on specified exceptions
        
    Example:
        @with_retry(max_attempts=3, delay=1.0, backoff=2.0)
        def fetch_data():
            response = httpx.get("http://service/api")
            response.raise_for_status()
            return response.json()
            
    Raises:
        The last exception if all retry attempts fail
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            last_exception = None
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        # Last attempt failed, raise the exception
                        raise
                    
                    # Log retry attempt
                    print(f"⚠️  Attempt {attempt}/{max_attempts} failed: {e}")
                    print(f"🔄 Retrying in {current_delay:.1f}s...")
                    
                    # Wait before next attempt
                    time.sleep(current_delay)
                    
                    # Exponential backoff
                    current_delay *= backoff
                    attempt += 1
            
            # Should never reach here, but handle it just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"Failed after {max_attempts} attempts")
        
        return wrapper
    return decorator


def retry_with_fallback(
    fallback_value: Any = None,
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (httpx.RequestError, httpx.HTTPStatusError)
):
    """
    Retry decorator that returns a fallback value instead of raising an exception.
    
    Args:
        fallback_value: Value to return if all retries fail (default: None)
        max_attempts: Maximum number of retry attempts (default: 3)
        delay: Initial delay between retries in seconds (default: 1.0)
        exceptions: Tuple of exceptions to catch and retry (default: httpx errors)
        
    Returns:
        Decorated function that returns fallback_value on failure
        
    Example:
        @retry_with_fallback(fallback_value=[], max_attempts=2)
        def fetch_logs():
            response = httpx.get("http://log-collector/logs")
            return response.json()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        # All attempts failed, return fallback
                        print(f"❌ All {max_attempts} attempts failed: {e}")
                        print(f"📦 Returning fallback value: {fallback_value}")
                        return fallback_value
                    
                    print(f"⚠️  Attempt {attempt}/{max_attempts} failed: {e}")
                    time.sleep(current_delay)
                    current_delay *= 2.0  # Fixed exponential backoff
                    attempt += 1
            
            return fallback_value
        
        return wrapper
    return decorator

