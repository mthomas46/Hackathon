"""
Metrics middleware for tracking HTTP requests.

Automatically tracks:
- Request duration
- Request counts
- Status codes
- In-progress requests
"""

import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ...utils.metrics import (
    http_requests_total,
    http_request_duration_seconds,
    http_requests_in_progress
)

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track HTTP request metrics.
    
    Tracks:
    - Request count by method, endpoint, and status
    - Request duration by method and endpoint
    - In-progress requests
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and track metrics.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
        
        Returns:
            Response with metrics tracked
        """
        # Get endpoint path (remove query params)
        endpoint = request.url.path
        method = request.method
        
        # Track in-progress requests
        http_requests_in_progress.labels(method=method, endpoint=endpoint).inc()
        
        # Track request duration
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Track metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=response.status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Track error
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=500
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            raise
            
        finally:
            # Decrement in-progress counter
            http_requests_in_progress.labels(method=method, endpoint=endpoint).dec()

