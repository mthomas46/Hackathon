"""Unified Service Client System.

This module provides a standardized service-to-service communication layer
for the LLM Documentation Ecosystem. Consolidates 3+ duplicate service client
implementations into a single, resilient client system.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Union
import httpx

from .utilities.retry_service import RetryService
from .utilities.circuit_breaker_service import CircuitBreakerService

logger = logging.getLogger(__name__)


class ServiceClient:
    """Unified service client for inter-service communication with resilience patterns."""

    def __init__(
        self,
        service_name: str,
        base_url: str,
        timeout: int = 30,
        retry_service: Optional[RetryService] = None,
        circuit_breaker: Optional[CircuitBreakerService] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize service client with resilience patterns.

        Args:
            service_name: Name of the target service
            base_url: Base URL of the target service
            timeout: Request timeout in seconds
            retry_service: Optional retry service instance
            circuit_breaker: Optional circuit breaker instance
            headers: Additional headers to include in requests
        """
        self.service_name = service_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_service = retry_service or RetryService()
        self.circuit_breaker = circuit_breaker

        # Default headers
        default_headers = {
            "User-Agent": f"service-client/{service_name}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if headers:
            default_headers.update(headers)

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers=default_headers,
            follow_redirects=True,
        )

    async def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform GET request with resilience patterns.

        Args:
            path: API endpoint path (without leading slash)
            params: Query parameters
            headers: Additional headers for this request
            **kwargs: Additional arguments for httpx

        Returns:
            JSON response data
        """
        return await self._request(
            "GET", path, params=params, headers=headers, **kwargs
        )

    async def post(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform POST request with resilience patterns.

        Args:
            path: API endpoint path
            data: Raw request data
            json: JSON request data
            headers: Additional headers
            **kwargs: Additional httpx arguments

        Returns:
            JSON response data
        """
        return await self._request(
            "POST", path, data=data, json=json, headers=headers, **kwargs
        )

    async def put(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform PUT request with resilience patterns."""
        return await self._request(
            "PUT", path, data=data, json=json, headers=headers, **kwargs
        )

    async def patch(
        self,
        path: str,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Perform PATCH request with resilience patterns."""
        return await self._request(
            "PATCH", path, data=data, json=json, headers=headers, **kwargs
        )

    async def delete(
        self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> Dict[str, Any]:
        """Perform DELETE request with resilience patterns."""
        return await self._request("DELETE", path, headers=headers, **kwargs)

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Execute HTTP request with resilience patterns.

        Args:
            method: HTTP method
            path: Request path
            **kwargs: Request arguments

        Returns:
            JSON response data

        Raises:
            ServiceClientError: For client-related errors
            httpx.HTTPStatusError: For HTTP error responses
        """
        url = f"{self.base_url}/{path.lstrip('/')}"

        async def _execute_request():
            try:
                # Apply circuit breaker if available
                if self.circuit_breaker:
                    async with self.circuit_breaker.call(url):
                        response = await self.client.request(method, url, **kwargs)
                else:
                    response = await self.client.request(method, url, **kwargs)

                # Raise for HTTP error status
                response.raise_for_status()

                # Return JSON response
                return response.json()

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error calling {self.service_name}",
                    extra={
                        "service": self.service_name,
                        "method": method,
                        "url": url,
                        "status_code": e.response.status_code,
                        "error": str(e),
                    },
                )
                raise

            except Exception as e:
                logger.error(
                    f"Request error calling {self.service_name}",
                    extra={
                        "service": self.service_name,
                        "method": method,
                        "url": url,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    },
                )
                raise ServiceClientError(
                    f"Error calling {self.service_name}: {str(e)}"
                ) from e

        # Execute with retry logic
        return await self.retry_service.execute_with_retry(_execute_request)

    async def health_check(self) -> bool:
        """Perform health check on the service.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            await self.get("/health")
            return True
        except Exception:
            return False

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class ServiceClientFactory:
    """Factory for creating and managing service clients."""

    def __init__(self, service_registry: Dict[str, str]):
        """Initialize factory with service registry.

        Args:
            service_registry: Mapping of service names to base URLs
        """
        self.service_registry = service_registry
        self.clients: Dict[str, ServiceClient] = {}
        self._closed = False

    def get_client(
        self,
        service_name: str,
        timeout: int = 30,
        retry_service: Optional[RetryService] = None,
        circuit_breaker: Optional[CircuitBreakerService] = None,
    ) -> ServiceClient:
        """Get or create service client.

        Args:
            service_name: Name of the service
            timeout: Request timeout
            retry_service: Optional retry service
            circuit_breaker: Optional circuit breaker

        Returns:
            Service client instance

        Raises:
            ValueError: If service is not registered
        """
        if self._closed:
            raise RuntimeError("Service client factory has been closed")

        if service_name not in self.service_registry:
            raise ValueError(f"Unknown service: {service_name}")

        if service_name not in self.clients:
            self.clients[service_name] = ServiceClient(
                service_name=service_name,
                base_url=self.service_registry[service_name],
                timeout=timeout,
                retry_service=retry_service,
                circuit_breaker=circuit_breaker,
            )

        return self.clients[service_name]

    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health checks on all registered services.

        Returns:
            Dictionary mapping service names to health status
        """
        results = {}
        for service_name in self.service_registry.keys():
            try:
                client = self.get_client(service_name)
                results[service_name] = await client.health_check()
            except Exception:
                results[service_name] = False
        return results

    async def close_all(self):
        """Close all service clients."""
        if self._closed:
            return

        self._closed = True

        close_tasks = []
        for client in self.clients.values():
            close_tasks.append(client.close())

        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)

        self.clients.clear()


class ServiceClientError(Exception):
    """Exception raised for service client errors."""

    pass


# Global factory instance
_service_client_factory: Optional[ServiceClientFactory] = None


def initialize_service_clients(service_registry: Dict[str, str]):
    """Initialize global service client factory.

    Args:
        service_registry: Mapping of service names to URLs
    """
    global _service_client_factory
    _service_client_factory = ServiceClientFactory(service_registry)


def get_service_client(service_name: str, timeout: int = 30) -> ServiceClient:
    """Get service client from global factory.

    Args:
        service_name: Name of the service
        timeout: Request timeout

    Returns:
        Service client instance

    Raises:
        RuntimeError: If service clients not initialized
    """
    if not _service_client_factory:
        raise RuntimeError(
            "Service clients not initialized. Call initialize_service_clients() first."
        )
    return _service_client_factory.get_client(service_name, timeout=timeout)


async def close_service_clients():
    """Close all global service clients."""
    if _service_client_factory:
        await _service_client_factory.close_all()


async def health_check_services() -> Dict[str, bool]:
    """Perform health checks on all services.

    Returns:
        Dictionary mapping service names to health status
    """
    if not _service_client_factory:
        raise RuntimeError("Service clients not initialized")
    return await _service_client_factory.health_check_all()


# Legacy compatibility functions
def create_service_client(*args, **kwargs) -> ServiceClient:
    """Legacy alias for ServiceClient constructor."""
    return ServiceClient(*args, **kwargs)


def get_client_factory() -> ServiceClientFactory:
    """Get the global service client factory."""
    if not _service_client_factory:
        raise RuntimeError("Service clients not initialized")
    return _service_client_factory
