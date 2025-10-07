"""
Base HTTP client for service-to-service communication.

Provides retry logic, timeout handling, and error management for
resilient inter-service communication.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
import httpx
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent cascade failures.
    
    Tracks failures and opens circuit when threshold is exceeded.
    Automatically attempts recovery after cooldown period.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_duration: int = 30,
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes to close circuit from half-open
            timeout_duration: Seconds to wait before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_duration = timeout_duration
        
        self.failure_count = 0
        self.success_count = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time: Optional[datetime] = None
        
        logger.info(
            f"Circuit breaker initialized "
            f"(failure_threshold={failure_threshold}, timeout={timeout_duration}s)"
        )
    
    def record_success(self):
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self._open_circuit()
    
    def can_execute(self) -> bool:
        """Check if request can be executed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_duration:
                    self._half_open_circuit()
                    return True
            return False
        
        # HALF_OPEN: allow limited requests
        return True
    
    def _open_circuit(self):
        """Open circuit (stop requests)."""
        self.state = CircuitState.OPEN
        logger.warning(
            f"Circuit breaker OPEN after {self.failure_count} failures "
            f"(cooldown: {self.timeout_duration}s)"
        )
    
    def _half_open_circuit(self):
        """Half-open circuit (test recovery)."""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        logger.info("Circuit breaker HALF_OPEN (testing recovery)")
    
    def _close_circuit(self):
        """Close circuit (resume normal operation)."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info("Circuit breaker CLOSED (service recovered)")


class ServiceHTTPClient:
    """
    Base HTTP client for service-to-service communication.
    
    Features:
    - Automatic retries with exponential backoff
    - Circuit breaker pattern
    - Timeout configuration
    - Request/response logging
    - Error handling
    """
    
    def __init__(
        self,
        base_url: str,
        service_name: str,
        timeout: int = 30,
        max_retries: int = 3,
        enable_circuit_breaker: bool = True,
    ):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL of target service (e.g., "http://localhost:5649")
            service_name: Name of target service (for logging)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            enable_circuit_breaker: Whether to use circuit breaker
        """
        self.base_url = base_url.rstrip("/")
        self.service_name = service_name
        self.timeout = timeout
        self.max_retries = max_retries
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker() if enable_circuit_breaker else None
        
        logger.info(
            f"HTTP client initialized for {service_name} at {base_url} "
            f"(timeout={timeout}s, retries={max_retries})"
        )
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    async def _make_request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., "/api/v1/executions")
            **kwargs: Additional arguments for httpx request
        
        Returns:
            HTTP response
        
        Raises:
            httpx.HTTPError: If request fails after retries
        """
        # Check circuit breaker
        if self.circuit_breaker and not self.circuit_breaker.can_execute():
            raise httpx.HTTPError(
                f"Circuit breaker OPEN for {self.service_name}"
            )
        
        url = f"{self.base_url}{path}"
        
        for attempt in range(self.max_retries + 1):
            try:
                start_time = datetime.now()
                
                response = await self.client.request(method, path, **kwargs)
                response.raise_for_status()
                
                duration = (datetime.now() - start_time).total_seconds()
                logger.debug(
                    f"{method} {url} → {response.status_code} "
                    f"({duration*1000:.0f}ms)"
                )
                
                # Record success in circuit breaker
                if self.circuit_breaker:
                    self.circuit_breaker.record_success()
                
                return response
            
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                is_last_attempt = attempt == self.max_retries
                
                # Record failure in circuit breaker
                if self.circuit_breaker:
                    self.circuit_breaker.record_failure()
                
                if is_last_attempt:
                    logger.error(
                        f"{method} {url} failed after {attempt + 1} attempts: {e}"
                    )
                    raise
                
                # Calculate backoff delay
                delay = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                logger.warning(
                    f"{method} {url} failed (attempt {attempt + 1}/{self.max_retries + 1}), "
                    f"retrying in {delay}s: {e}"
                )
                await asyncio.sleep(delay)
        
        # Should not reach here
        raise httpx.HTTPError(f"Failed to make request to {url}")
    
    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request.
        
        Args:
            path: Request path
            params: Query parameters
            headers: Request headers
        
        Returns:
            Response JSON
        """
        response = await self._make_request(
            "GET",
            path,
            params=params,
            headers=headers
        )
        return response.json()
    
    async def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict[str, Any], bytes]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make POST request.
        
        Args:
            path: Request path
            json: JSON body
            data: Form data or bytes
            headers: Request headers
        
        Returns:
            Response JSON
        """
        response = await self._make_request(
            "POST",
            path,
            json=json,
            data=data,
            headers=headers
        )
        return response.json()
    
    async def put(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make PUT request.
        
        Args:
            path: Request path
            json: JSON body
            headers: Request headers
        
        Returns:
            Response JSON
        """
        response = await self._make_request(
            "PUT",
            path,
            json=json,
            headers=headers
        )
        return response.json()
    
    async def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make DELETE request.
        
        Args:
            path: Request path
            headers: Request headers
        
        Returns:
            Response JSON
        """
        response = await self._make_request(
            "DELETE",
            path,
            headers=headers
        )
        return response.json()
    
    async def health_check(self) -> bool:
        """
        Check if service is healthy.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = await self.get("/health")
            return response.get("status") == "ok"
        except Exception as e:
            logger.warning(f"Health check failed for {self.service_name}: {e}")
            return False

