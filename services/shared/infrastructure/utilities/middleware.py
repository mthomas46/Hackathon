"""Consolidated middleware utilities for common service patterns.

Combines request ID, metrics, and rate limiting middleware.
"""

import time
import uuid
from typing import Callable, Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Add Optional to imports if not already there
try:
    Optional
except NameError:
    from typing import Optional

from .utilities import TokenBucket


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware for request correlation ID propagation."""

    def __init__(self, app):
        """Initialize request ID middleware.

        Args:
            app: ASGI application
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        rid = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request.state.correlation_id = rid
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = rid
        return response


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for request metrics collection."""

    def __init__(self, app, service_name: Optional[str] = None):
        """Initialize request metrics middleware.

        Args:
            app: ASGI application
            service_name: Name of the service for metrics tagging
        """
        super().__init__(app)
        self.service_name = service_name or "unknown-service"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            duration_ms = int((time.perf_counter() - start) * 1000)
            correlation_id = getattr(request.state, "correlation_id", None)

            # Import here to avoid circular dependency
            try:
                from ...monitoring.logging import fire_and_forget

                fire_and_forget(
                    "info",
                    "http_request",
                    self.service_name,
                    {
                        "path": request.url.path,
                        "method": request.method,
                        "duration_ms": duration_ms,
                        "status": locals().get("status", 0),
                        "correlation_id": correlation_id,
                    },
                )
            except ImportError:
                pass


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limiter per-path.

    Disabled by default unless RATE_LIMIT_ENABLED env var is set truthy.
    Configure limits via code: RateLimitMiddleware(..., limits={"/analyze": (5, 10)})
    """

    def __init__(self, app, limits: Optional[Dict[str, tuple[float, int]]] = None):
        """Initialize rate limiting middleware.

        Args:
            app: ASGI application
            limits: Dict mapping paths to (rate, burst) tuples for token buckets
        """
        super().__init__(app)
        self._buckets: Dict[str, TokenBucket] = {}
        limits = limits or {}
        for path, (rate, burst) in limits.items():
            self._buckets[path] = TokenBucket(rate, burst)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        bucket = self._buckets.get(request.url.path)
        if bucket and not bucket.allow():
            from starlette.responses import JSONResponse

            return JSONResponse({"detail": "rate_limited"}, status_code=429)
        return await call_next(request)


class ServiceMiddleware:
    """Combined middleware stack for services."""

    def __init__(
        self,
        service_name: str,
        rate_limits: Optional[Dict[str, tuple[float, int]]] = None,
        enable_rate_limit: bool = False,
    ):
        """Initialize combined service middleware stack.

        Args:
            service_name: Name of the service
            rate_limits: Optional rate limiting configuration
            enable_rate_limit: Whether to enable rate limiting
        """
        self.service_name = service_name
        self.rate_limits = rate_limits
        self.enable_rate_limit = enable_rate_limit

    def get_middlewares(self):
        """Get list of middleware instances for FastAPI app."""
        middlewares = [
            lambda app: RequestIdMiddleware(app),
            lambda app: RequestMetricsMiddleware(app, self.service_name),
        ]

        if self.enable_rate_limit and self.rate_limits:
            middlewares.append(lambda app: RateLimitMiddleware(app, self.rate_limits))

        return middlewares


class MiddlewareManager:
    """Manager for configuring middleware across services."""

    def __init__(self, service_name: str, **kwargs):
        """Initialize middleware manager.

        Args:
            service_name: Name of the service
            **kwargs: Additional configuration options
        """
        self.service_name = service_name
        self.config = kwargs

    def get_middlewares(self):
        """Get list of middleware factories for this service."""
        from fastapi.middleware.cors import CORSMiddleware

        return [
            lambda app: CORSMiddleware(
                app,
                allow_origins=["*"],  # Configure appropriately for production
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            ),
            lambda app: RequestIdMiddleware(app),
            lambda app: RequestMetricsMiddleware(app, self.service_name),
            lambda app: RateLimitMiddleware(app),
        ]


# Convenience function for setting up common middleware
def setup_common_middleware(app, service_name: str, **kwargs):
    """Setup common middleware for a FastAPI application.

    Args:
        app: FastAPI application instance
        service_name: Name of the service for metrics
        **kwargs: Additional configuration options
    """
    manager = MiddlewareManager(service_name=service_name, **kwargs)
    for middleware_factory in manager.get_middlewares():
        app.add_middleware(middleware_factory)


# Convenience function for getting request ID
def get_request_id():
    """Get current request ID from context."""
    # This would typically get the request ID from asyncio context
    # For now, return a placeholder
    return "request-id-placeholder"
