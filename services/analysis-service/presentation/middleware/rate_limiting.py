"""Rate limiting middleware to protect API endpoints from abuse."""

import time
import asyncio
from typing import Dict, Any, Optional, Tuple
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from ...presentation.models.base import ErrorResponse, ErrorCode


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        """Initialize rate limit exception."""
        super().__init__(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)}
        )


class InMemoryRateLimiter:
    """Simple in-memory rate limiter using token bucket algorithm."""

    def __init__(self):
        """Initialize rate limiter."""
        self.requests: Dict[str, list] = defaultdict(list)
        self._cleanup_task: Optional[asyncio.Task] = None

    def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, int]:
        """Check if request is allowed under rate limit."""
        now = time.time()

        # Get existing requests for this key
        request_times = self.requests[key]

        # Remove expired requests
        request_times[:] = [t for t in request_times if now - t < window]

        # Check if under limit
        if len(request_times) < limit:
            request_times.append(now)
            return True, 0

        # Calculate retry after time
        oldest_request = min(request_times)
        retry_after = int(window - (now - oldest_request))

        return False, retry_after

    def start_cleanup_task(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def _cleanup_expired(self):
        """Periodically clean up expired entries."""
        while True:
            await asyncio.sleep(60)  # Clean up every minute
            now = time.time()

            # Clean up expired entries
            for key in list(self.requests.keys()):
                self.requests[key][:] = [t for t in self.requests[key] if now - t < 3600]  # 1 hour window
                if not self.requests[key]:
                    del self.requests[key]


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""

    def __init__(self, app, rate_limiter: Optional[InMemoryRateLimiter] = None):
        """Initialize rate limiting middleware."""
        super().__init__(app)
        self.rate_limiter = rate_limiter or InMemoryRateLimiter()
        self.rate_limiter.start_cleanup_task()

        # Default rate limits by endpoint type
        self.rate_limits = {
            'analysis': (10, 60),    # 10 requests per minute for analysis endpoints
            'reports': (5, 60),      # 5 requests per minute for report endpoints
            'admin': (20, 60),       # 20 requests per minute for admin endpoints
            'default': (30, 60),     # 30 requests per minute default
        }

        # Endpoints that bypass rate limiting
        self.exempt_paths = [
            '/health',
            '/metrics',
            '/docs',
            '/redoc',
            '/openapi.json'
        ]

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Generate rate limit key (IP + path pattern)
        client_ip = self._get_client_ip(request)
        endpoint_type = self._get_endpoint_type(request.url.path)
        rate_limit_key = f"{client_ip}:{endpoint_type}"

        # Get rate limit for this endpoint type
        limit, window = self.rate_limits.get(endpoint_type, self.rate_limits['default'])

        # Check rate limit
        allowed, retry_after = self.rate_limiter.is_allowed(rate_limit_key, limit, window)

        if not allowed:
            # Return rate limit exceeded response
            error_response = ErrorResponse(
                error={
                    "field": None,
                    "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "code": ErrorCode.RATE_LIMIT_EXCEEDED
                },
                request_id=getattr(request.state, 'request_id', None)
            )

            return JSONResponse(
                status_code=429,
                content=error_response.dict(),
                headers={"Retry-After": str(retry_after)}
            )

        # Add rate limit headers to response
        response = await call_next(request)

        # Calculate remaining requests
        now = time.time()
        request_times = self.rate_limiter.requests[rate_limit_key]
        request_times[:] = [t for t in request_times if now - t < window]
        remaining = max(0, limit - len(request_times))

        # Add rate limit headers
        response.headers['X-RateLimit-Limit'] = str(limit)
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        response.headers['X-RateLimit-Reset'] = str(int(now + window))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip

        client = request.client
        return client.host if client else "unknown"

    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type from path."""
        if path.startswith('/analyze'):
            return 'analysis'
        elif path.startswith('/reports'):
            return 'reports'
        elif path.startswith('/admin') or path.startswith('/internal'):
            return 'admin'
        else:
            return 'default'


class AdaptiveRateLimiter(InMemoryRateLimiter):
    """Adaptive rate limiter that adjusts limits based on system load."""

    def __init__(self):
        """Initialize adaptive rate limiter."""
        super().__init__()
        self.system_load = 1.0  # System load factor (1.0 = normal)
        self.adjustment_interval = 60  # Adjust every 60 seconds

    def is_allowed(self, key: str, base_limit: int, window: int) -> Tuple[bool, int]:
        """Check if request is allowed with adaptive limits."""
        # Adjust limit based on system load
        adjusted_limit = int(base_limit * (1.0 / self.system_load))

        return super().is_allowed(key, max(1, adjusted_limit), window)

    def update_system_load(self, load_factor: float):
        """Update system load factor."""
        self.system_load = max(0.1, min(5.0, load_factor))  # Clamp between 0.1 and 5.0


class EndpointRateLimiter:
    """Rate limiter with different limits for different endpoints."""

    def __init__(self):
        """Initialize endpoint-specific rate limiter."""
        self.endpoint_limits: Dict[str, Tuple[int, int]] = {}
        self.rate_limiter = InMemoryRateLimiter()

    def set_endpoint_limit(self, endpoint_pattern: str, limit: int, window: int):
        """Set rate limit for specific endpoint pattern."""
        self.endpoint_limits[endpoint_pattern] = (limit, window)

    def is_allowed(self, endpoint: str, client_ip: str) -> Tuple[bool, int]:
        """Check if request is allowed for endpoint."""
        # Find matching endpoint limit
        limit, window = self.endpoint_limits.get(endpoint, (30, 60))  # Default: 30 per minute

        key = f"{client_ip}:{endpoint}"
        return self.rate_limiter.is_allowed(key, limit, window)


# Global rate limiter instances
default_rate_limiter = InMemoryRateLimiter()
adaptive_rate_limiter = AdaptiveRateLimiter()
endpoint_rate_limiter = EndpointRateLimiter()

# Pre-configure endpoint-specific limits
endpoint_rate_limiter.set_endpoint_limit('/analyze/*', 10, 60)  # 10 per minute for analysis
endpoint_rate_limiter.set_endpoint_limit('/distributed/*', 5, 60)  # 5 per minute for distributed tasks
endpoint_rate_limiter.set_endpoint_limit('/reports/*', 3, 60)    # 3 per minute for reports
