"""
Rate Limiting Middleware

⚡ QUICK WIN #10: API Rate Limiting
Prevents abuse and ensures fair resource allocation.

Features:
- Redis-backed rate limiting
- Configurable limits per endpoint
- Sliding window algorithm
- IP-based tracking
- Custom rate limit headers
"""

import logging
import time
import os
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from ...utils.redis_client import get_redis_client
from ...config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis sliding window.
    
    Algorithm: Sliding Window Counter
    - Tracks requests in a time window
    - Uses Redis ZSET with timestamps
    - Automatically expires old entries
    - O(log N) time complexity
    """
    
    def __init__(
        self,
        app,
        enabled: bool = True,
        requests_per_window: int = 100,
        window_seconds: int = 60
    ):
        """
        Initialize rate limiter.
        
        Args:
            app: FastAPI application
            enabled: Whether rate limiting is enabled
            requests_per_window: Max requests per window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        
        # Configuration from environment
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", str(enabled)).lower() == "true"
        self.max_requests = int(os.getenv("RATE_LIMIT_REQUESTS", str(requests_per_window)))
        self.window_seconds = int(os.getenv("RATE_LIMIT_WINDOW", str(window_seconds)))
        
        # Exempt paths (health checks, metrics)
        self.exempt_paths = {
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
        
        if self.enabled:
            logger.info(
                f"⚡ Rate limiting enabled: "
                f"{self.max_requests} requests per {self.window_seconds}s"
            )
        else:
            logger.info("⚠️  Rate limiting disabled")
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """Process request with rate limiting."""
        
        # Skip if disabled
        if not self.enabled:
            return await call_next(request)
        
        # Skip exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        try:
            allowed, remaining, reset_time = await self._check_rate_limit(
                client_ip,
                request.url.path
            )
            
            # Add rate limit headers
            headers = {
                "X-RateLimit-Limit": str(self.max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
            }
            
            if not allowed:
                # Rate limit exceeded
                retry_after = int(reset_time - time.time())
                headers["Retry-After"] = str(retry_after)
                
                logger.warning(
                    f"⚠️  Rate limit exceeded: {client_ip} on {request.url.path} "
                    f"(reset in {retry_after}s)"
                )
                
                return JSONResponse(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Please try again in {retry_after} seconds.",
                        "retry_after": retry_after,
                        "limit": self.max_requests,
                        "window": self.window_seconds
                    },
                    headers=headers
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            for key, value in headers.items():
                response.headers[key] = value
            
            return response
        
        except Exception as e:
            # If rate limiting fails, allow request (fail open)
            logger.error(f"Rate limiting error: {e}")
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check X-Forwarded-For header (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get first IP (client)
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"
    
    async def _check_rate_limit(
        self,
        client_id: str,
        path: str
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Args:
            client_id: Client identifier (IP)
            path: Request path
        
        Returns:
            Tuple of (allowed, remaining_requests, reset_timestamp)
        """
        redis = get_redis_client()
        
        # Redis key: ratelimit:client_id:path
        key = f"ratelimit:{client_id}:{path}"
        
        now = time.time()
        window_start = now - self.window_seconds
        
        # Remove old entries (outside window)
        await redis.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        request_count = await redis.zcard(key)
        
        # Calculate remaining requests
        remaining = max(0, self.max_requests - request_count)
        
        # Calculate reset time (end of current window)
        reset_time = int(now + self.window_seconds)
        
        # Check if limit exceeded
        if request_count >= self.max_requests:
            return False, remaining, reset_time
        
        # Add current request to window
        await redis.zadd(key, {str(now): now})
        
        # Set expiry on key (cleanup)
        await redis.expire(key, self.window_seconds * 2)
        
        # Update remaining count
        remaining -= 1
        
        return True, remaining, reset_time


def get_rate_limit_middleware(app):
    """
    Get configured rate limit middleware.
    
    Usage:
        from fastapi import FastAPI
        from src.api.middleware.rate_limiter import get_rate_limit_middleware
        
        app = FastAPI()
        app.add_middleware(get_rate_limit_middleware(app))
    """
    return RateLimitMiddleware(
        app,
        enabled=settings.rate_limit_enabled if hasattr(settings, 'rate_limit_enabled') else True,
        requests_per_window=100,
        window_seconds=60
    )


# Export for easy import
__all__ = ["RateLimitMiddleware", "get_rate_limit_middleware"]
