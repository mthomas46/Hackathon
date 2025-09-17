"""HTTP Connection Pool - HTTP client connection pooling for external services."""

import asyncio
import aiohttp
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .connection_pool import ConnectionPool, ConnectionPoolConfig, PooledConnection


class HTTPConnectionPool(ConnectionPool[aiohttp.ClientSession]):
    """HTTP connection pool using aiohttp ClientSession."""

    def __init__(
        self,
        config: ConnectionPoolConfig,
        connector: Optional[aiohttp.BaseConnector] = None,
        timeout: Optional[aiohttp.ClientTimeout] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None
    ):
        """Initialize HTTP connection pool."""
        super().__init__(config)
        self.connector = connector or aiohttp.TCPConnector(limit=self.config.max_size)
        self.timeout = timeout or aiohttp.ClientTimeout(total=30)
        self.default_headers = headers or {}
        self.default_cookies = cookies or {}

        # Override config for HTTP connections
        self.config.min_size = 1  # HTTP connections are lightweight
        self.config.max_size = min(self.config.max_size, 100)  # Reasonable limit

    async def create_connection(self) -> aiohttp.ClientSession:
        """Create HTTP client session."""
        return aiohttp.ClientSession(
            connector=self.connector,
            timeout=self.timeout,
            headers=self.default_headers,
            cookies=self.default_cookies
        )

    async def validate_connection(self, connection: aiohttp.ClientSession) -> bool:
        """Validate HTTP connection."""
        try:
            # Simple validation - check if session is closed
            return not connection.closed
        except Exception:
            return False

    async def close_connection(self, connection: aiohttp.ClientSession) -> None:
        """Close HTTP connection."""
        try:
            await connection.close()
        except Exception:
            pass  # Ignore errors during cleanup

    async def request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Make HTTP request using pooled connection."""
        async with self.acquire() as pooled_conn:
            session = pooled_conn.connection

            # Set default timeout if not provided
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.timeout

            return await session.request(method, url, **kwargs)

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make GET request."""
        return await self.request('GET', url, **kwargs)

    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make POST request."""
        return await self.request('POST', url, **kwargs)

    async def put(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make PUT request."""
        return await self.request('PUT', url, **kwargs)

    async def delete(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make DELETE request."""
        return await self.request('DELETE', url, **kwargs)

    async def patch(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make PATCH request."""
        return await self.request('PATCH', url, **kwargs)

    async def head(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make HEAD request."""
        return await self.request('HEAD', url, **kwargs)


class AIOHTTPConnectionPool(HTTPConnectionPool):
    """Enhanced HTTP connection pool with advanced features."""

    def __init__(
        self,
        config: ConnectionPoolConfig,
        base_url: Optional[str] = None,
        retry_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Initialize enhanced HTTP connection pool."""
        super().__init__(config, **kwargs)
        self.base_url = base_url.rstrip('/') if base_url else None
        self.retry_config = retry_config or {
            'max_retries': 3,
            'backoff_factor': 0.3,
            'retry_status_codes': [429, 500, 502, 503, 504]
        }

    def _build_url(self, url: str) -> str:
        """Build full URL from base URL and relative URL."""
        if self.base_url and not url.startswith(('http://', 'https://')):
            return f"{self.base_url}/{url.lstrip('/')}"
        return url

    async def request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Make HTTP request with retry logic."""
        url = self._build_url(url)
        max_retries = self.retry_config['max_retries']
        backoff_factor = self.retry_config['backoff_factor']
        retry_codes = set(self.retry_config['retry_status_codes'])

        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = await self.request(method, url, **kwargs)

                # Check if we should retry based on status code
                if response.status in retry_codes and attempt < max_retries:
                    await response.text()  # Consume response
                    await asyncio.sleep(backoff_factor * (2 ** attempt))
                    continue

                return response

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < max_retries:
                    await asyncio.sleep(backoff_factor * (2 ** attempt))
                    continue
                break

        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise aiohttp.ClientError("Request failed after all retries")

    async def get_with_retry(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make GET request with retry."""
        return await self.request_with_retry('GET', url, **kwargs)

    async def post_with_retry(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make POST request with retry."""
        return await self.request_with_retry('POST', url, **kwargs)

    async def put_with_retry(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make PUT request with retry."""
        return await self.request_with_retry('PUT', url, **kwargs)

    async def delete_with_retry(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make DELETE request with retry."""
        return await self.request_with_retry('DELETE', url, **kwargs)


class HTTPPoolFactory:
    """Factory for creating HTTP connection pools."""

    @staticmethod
    def create_basic_pool(
        max_connections: int = 20,
        timeout_seconds: int = 30,
        headers: Optional[Dict[str, str]] = None
    ) -> HTTPConnectionPool:
        """Create basic HTTP connection pool."""
        config = ConnectionPoolConfig(
            min_size=1,
            max_size=max_connections,
            acquire_timeout=timeout_seconds
        )

        timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        return HTTPConnectionPool(
            config=config,
            timeout=timeout,
            headers=headers
        )

    @staticmethod
    def create_advanced_pool(
        base_url: str,
        max_connections: int = 20,
        timeout_seconds: int = 30,
        headers: Optional[Dict[str, str]] = None,
        enable_retries: bool = True
    ) -> AIOHTTPConnectionPool:
        """Create advanced HTTP connection pool with retry logic."""
        config = ConnectionPoolConfig(
            min_size=1,
            max_size=max_connections,
            acquire_timeout=timeout_seconds
        )

        timeout = aiohttp.ClientTimeout(total=timeout_seconds)

        retry_config = None
        if enable_retries:
            retry_config = {
                'max_retries': 3,
                'backoff_factor': 0.3,
                'retry_status_codes': [429, 500, 502, 503, 504]
            }

        return AIOHTTPConnectionPool(
            config=config,
            base_url=base_url,
            timeout=timeout,
            headers=headers,
            retry_config=retry_config
        )

    @staticmethod
    def create_service_pool(
        service_name: str,
        service_url: str,
        auth_token: Optional[str] = None,
        **kwargs
    ) -> AIOHTTPConnectionPool:
        """Create HTTP pool for a specific service."""
        headers = {}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'

        headers.update({
            'User-Agent': f'analysis-service/{service_name}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

        return HTTPPoolFactory.create_advanced_pool(
            base_url=service_url,
            headers=headers,
            **kwargs
        )


class CircuitBreakerHTTPPool(AIOHTTPConnectionPool):
    """HTTP connection pool with circuit breaker pattern."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Optional[Exception] = None,
        **kwargs
    ):
        """Initialize circuit breaker HTTP pool."""
        super().__init__(**kwargs)
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception or Exception

        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half-open

    async def request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """Make request with circuit breaker protection."""
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half-open'
            else:
                raise aiohttp.ClientError("Circuit breaker is open")

        try:
            response = await super().request_with_retry(method, url, **kwargs)

            # Success - reset failure count
            if self.state == 'half-open':
                self.state = 'closed'
            self.failure_count = 0

            return response

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.failure_count >= self.failure_threshold:
                self.state = 'open'

            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.last_failure_time is None:
            return True

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def get_circuit_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        return {
            'state': self.state,
            'failure_count': self.failure_count,
            'failure_threshold': self.failure_threshold,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'recovery_timeout': self.recovery_timeout
        }
