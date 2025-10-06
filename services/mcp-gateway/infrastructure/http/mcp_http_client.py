"""HTTP Client for MCP communication with circuit breaker."""

import logging
from typing import Any, Dict, Optional

import httpx
from pybreaker import CircuitBreaker, CircuitBreakerError

from services.mcp_gateway.infrastructure.config.settings import Settings

logger = logging.getLogger(__name__)


class MCPHttpClient:
    """
    HTTP client for communicating with MCP instances.
    
    Includes circuit breaker for fault tolerance and automatic retries.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the HTTP client.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self.client = httpx.AsyncClient(
            timeout=settings.default_request_timeout_seconds,
            follow_redirects=True
        )
        
        # Circuit breaker per instance (keyed by instance_id)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _get_circuit_breaker(self, instance_id: str) -> CircuitBreaker:
        """
        Get or create circuit breaker for an instance.
        
        Args:
            instance_id: Instance ID
        
        Returns:
            Circuit breaker for the instance
        """
        if instance_id not in self.circuit_breakers:
            self.circuit_breakers[instance_id] = CircuitBreaker(
                fail_max=self.settings.circuit_breaker_failure_threshold,
                timeout_duration=self.settings.circuit_breaker_timeout_seconds,
                name=f"mcp-{instance_id}"
            )
        return self.circuit_breakers[instance_id]
    
    async def request(
        self,
        instance_id: str,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        query_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to an MCP instance.
        
        Args:
            instance_id: Instance ID (for circuit breaker)
            method: HTTP method (GET, POST, etc.)
            url: Full URL to request
            headers: Optional request headers
            body: Optional request body
            query_params: Optional query parameters
        
        Returns:
            Response dictionary with status_code, headers, and body
        
        Raises:
            CircuitBreakerError: If circuit is open
            httpx.HTTPError: If request fails
        """
        if not self.settings.circuit_breaker_enabled:
            return await self._do_request(method, url, headers, body, query_params)
        
        # Use circuit breaker
        circuit_breaker = self._get_circuit_breaker(instance_id)
        
        try:
            return await circuit_breaker.call_async(
                self._do_request,
                method,
                url,
                headers,
                body,
                query_params
            )
        except CircuitBreakerError as e:
            logger.warning(
                f"Circuit breaker open for instance {instance_id}: {e}"
            )
            raise
    
    async def _do_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        query_params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Execute the actual HTTP request.
        
        Args:
            method: HTTP method
            url: Full URL
            headers: Optional headers
            body: Optional body
            query_params: Optional query parameters
        
        Returns:
            Response dictionary
        """
        try:
            response = await self.client.request(
                method=method,
                url=url,
                headers=headers,
                json=body if body is not None else None,
                params=query_params
            )
            
            # Try to parse JSON response
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text
            
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response_body
            }
        
        except httpx.TimeoutException as e:
            logger.warning(f"Request timeout: {url}")
            raise
        except httpx.RequestError as e:
            logger.warning(f"Request error: {url} - {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in request: {e}", exc_info=True)
            raise

