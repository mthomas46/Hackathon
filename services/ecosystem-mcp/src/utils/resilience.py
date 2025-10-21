"""
Resilience Utilities for Production (PHASE 10 - Day 2)

Provides circuit breakers, timeouts, retries, and fallbacks for critical services.
Prevents cascading failures and ensures graceful degradation.
"""

import asyncio
import logging
from typing import Callable, Optional, Any, TypeVar, Dict
from functools import wraps
from datetime import datetime

from .circuit_breaker import get_circuit_breaker, CircuitBreakerOpenError

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================================
# Pre-configured Circuit Breakers for Critical Services
# ============================================================================

def get_embedding_circuit_breaker():
    """
    Circuit breaker for embedding service.
    
    More lenient settings since embedding generation can occasionally fail
    without indicating service is down.
    """
    return get_circuit_breaker(
        name="embedding_service",
        failure_threshold=10,  # Allow more failures (embeddings can be flaky)
        timeout=30.0  # Shorter timeout (embeddings should recover quickly)
    )


def get_llm_circuit_breaker():
    """
    Circuit breaker for LLM services (Ollama).
    
    Moderate settings since LLM calls can be slow but shouldn't fail often.
    """
    return get_circuit_breaker(
        name="llm_service",
        failure_threshold=5,  # Standard threshold
        timeout=60.0  # Standard timeout
    )


def get_database_circuit_breaker():
    """
    Circuit breaker for database operations.
    
    Strict settings since database failures are critical.
    """
    return get_circuit_breaker(
        name="database",
        failure_threshold=3,  # Stricter (database critical)
        timeout=120.0  # Longer timeout (database may take time to recover)
    )


def get_chromadb_circuit_breaker():
    """
    Circuit breaker for ChromaDB operations.
    
    Moderate settings since ChromaDB is important but not critical
    (can continue without embeddings in some cases).
    """
    return get_circuit_breaker(
        name="chromadb",
        failure_threshold=7,  # Moderate threshold
        timeout=45.0  # Moderate timeout
    )


def get_redis_circuit_breaker():
    """
    Circuit breaker for Redis operations.
    
    Lenient settings since Redis is used for caching and can fall back
    to direct computation.
    """
    return get_circuit_breaker(
        name="redis",
        failure_threshold=15,  # Very lenient (cache can fail often)
        timeout=20.0  # Quick recovery
    )


# ============================================================================
# Timeout Protection
# ============================================================================

class TimeoutError(Exception):
    """Operation timed out."""
    pass


def with_timeout(seconds: float):
    """
    Decorator to add timeout protection to async functions.
    
    Usage:
        @with_timeout(30.0)
        async def long_running_operation():
            ...
    
    Args:
        seconds: Timeout in seconds
    
    Raises:
        TimeoutError: If operation exceeds timeout
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                func_name = func.__name__
                logger.error(
                    f"⏱️  Operation timed out: {func_name} "
                    f"(timeout={seconds}s)"
                )
                raise TimeoutError(
                    f"Operation '{func_name}' timed out after {seconds}s"
                )
        
        return wrapper
    return decorator


# ============================================================================
# Combined Resilience Decorator
# ============================================================================

def resilient(
    circuit_breaker_name: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
    fallback: Optional[Callable] = None,
    failure_threshold: int = 5,
    breaker_timeout: float = 60.0
):
    """
    Combined resilience decorator with circuit breaker, timeout, and fallback.
    
    Usage:
        @resilient(
            circuit_breaker_name="my_service",
            timeout_seconds=30.0,
            fallback=lambda: {"success": False}
        )
        async def call_service():
            ...
    
    Args:
        circuit_breaker_name: Name for circuit breaker (None = no breaker)
        timeout_seconds: Timeout in seconds (None = no timeout)
        fallback: Fallback function to call on failure (None = re-raise)
        failure_threshold: Circuit breaker failure threshold
        breaker_timeout: Circuit breaker timeout
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        # Get or create circuit breaker if requested
        breaker = None
        if circuit_breaker_name:
            breaker = get_circuit_breaker(
                name=circuit_breaker_name,
                failure_threshold=failure_threshold,
                timeout=breaker_timeout
            )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            func_name = func.__name__
            
            try:
                # Apply circuit breaker if configured
                if breaker:
                    # Circuit breaker will raise if open
                    if breaker.stats.state.value == "open":
                        raise CircuitBreakerOpenError(
                            f"Circuit breaker '{circuit_breaker_name}' is open"
                        )
                
                # Apply timeout if configured
                if timeout_seconds:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout_seconds
                    )
                else:
                    result = await func(*args, **kwargs)
                
                # Record success with breaker
                if breaker:
                    await breaker._record_success()
                
                return result
            
            except asyncio.TimeoutError:
                logger.error(
                    f"⏱️  {func_name} timed out after {timeout_seconds}s"
                )
                
                # Record failure with breaker
                if breaker:
                    await breaker._record_failure()
                
                # Use fallback if provided
                if fallback:
                    logger.info(f"   Using fallback for {func_name}")
                    return await fallback() if asyncio.iscoroutinefunction(fallback) else fallback()
                
                raise TimeoutError(f"{func_name} timed out after {timeout_seconds}s")
            
            except CircuitBreakerOpenError as e:
                logger.warning(f"🔴 Circuit breaker open for {func_name}: {e}")
                
                # Use fallback if provided
                if fallback:
                    logger.info(f"   Using fallback for {func_name}")
                    return await fallback() if asyncio.iscoroutinefunction(fallback) else fallback()
                
                raise
            
            except Exception as e:
                logger.error(f"❌ {func_name} failed: {e}")
                
                # Record failure with breaker
                if breaker:
                    await breaker._record_failure()
                
                # Use fallback if provided
                if fallback:
                    logger.info(f"   Using fallback for {func_name}")
                    return await fallback() if asyncio.iscoroutinefunction(fallback) else fallback()
                
                raise
        
        return wrapper
    return decorator


# ============================================================================
# Health Check Utilities
# ============================================================================

async def check_service_health(service_name: str) -> Dict[str, Any]:
    """
    Check health of a service by inspecting its circuit breaker.
    
    Args:
        service_name: Name of the service
    
    Returns:
        Health status dictionary
    """
    breaker = get_circuit_breaker(service_name)
    
    state = breaker.stats.state.value
    is_healthy = state == "closed"
    
    return {
        "service": service_name,
        "healthy": is_healthy,
        "state": state,
        "total_calls": breaker.stats.total_calls,
        "total_failures": breaker.stats.total_failures,
        "total_successes": breaker.stats.total_successes,
        "failure_count": breaker.stats.failure_count,
        "success_count": breaker.stats.success_count,
        "last_failure_time": breaker.stats.last_failure_time,
        "opened_at": breaker.stats.opened_at
    }


async def get_all_service_health() -> Dict[str, Dict[str, Any]]:
    """
    Get health status of all services with circuit breakers.
    
    Returns:
        Dictionary mapping service names to health status
    """
    from .circuit_breaker import get_all_breakers
    
    health = {}
    for name, breaker in get_all_breakers().items():
        health[name] = {
            "healthy": breaker.stats.state.value == "closed",
            "state": breaker.stats.state.value,
            "total_calls": breaker.stats.total_calls,
            "total_failures": breaker.stats.total_failures,
            "failure_rate": (
                breaker.stats.total_failures / breaker.stats.total_calls
                if breaker.stats.total_calls > 0
                else 0.0
            )
        }
    
    return health


# ============================================================================
# Fallback Strategies
# ============================================================================

class FallbackStrategies:
    """Common fallback strategies for different service types."""
    
    @staticmethod
    async def empty_list():
        """Return empty list."""
        return []
    
    @staticmethod
    async def empty_dict():
        """Return empty dictionary."""
        return {}
    
    @staticmethod
    async def none_value():
        """Return None."""
        return None
    
    @staticmethod
    async def default_embedding():
        """Return zero embedding vector."""
        return [0.0] * 768  # Standard embedding size
    
    @staticmethod
    async def skip_operation():
        """Return success with skip indicator."""
        return {"success": True, "skipped": True, "reason": "Service unavailable"}
    
    @staticmethod
    def create_default_value(value: Any):
        """Create fallback that returns specific default value."""
        async def fallback():
            return value
        return fallback


# ============================================================================
# Export All
# ============================================================================

__all__ = [
    # Circuit Breakers
    "get_embedding_circuit_breaker",
    "get_llm_circuit_breaker",
    "get_database_circuit_breaker",
    "get_chromadb_circuit_breaker",
    "get_redis_circuit_breaker",
    
    # Decorators
    "with_timeout",
    "resilient",
    
    # Exceptions
    "TimeoutError",
    "CircuitBreakerOpenError",
    
    # Health Checks
    "check_service_health",
    "get_all_service_health",
    
    # Fallbacks
    "FallbackStrategies",
]

