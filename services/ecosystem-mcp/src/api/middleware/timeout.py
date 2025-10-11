"""
Request timeout middleware.

Prevents requests from hanging indefinitely.
"""

import asyncio
import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce request timeouts.
    
    Prevents requests from hanging indefinitely by enforcing a maximum
    execution time. Different timeouts can be configured per endpoint.
    """
    
    # Default timeout (seconds)
    DEFAULT_TIMEOUT = 30.0
    
    # Per-endpoint timeout overrides (seconds)
    ENDPOINT_TIMEOUTS = {
        "/health": 5.0,
        "/api/v1/search": 60.0,  # Search can take longer
        "/api/v1/query": 30.0,
        "/api/v1/admin/ingest": 300.0,  # Ingestion can be long
        "/api/v1/ollama": 120.0,  # LLM calls can be slow
    }
    
    def __init__(self, app: ASGIApp, default_timeout: float = DEFAULT_TIMEOUT):
        """
        Initialize timeout middleware.
        
        Args:
            app: ASGI application
            default_timeout: Default timeout in seconds
        """
        super().__init__(app)
        self.default_timeout = default_timeout
    
    def get_timeout_for_path(self, path: str) -> float:
        """
        Get timeout for a specific path.
        
        Args:
            path: Request path
        
        Returns:
            Timeout in seconds
        """
        # Check for exact match
        if path in self.ENDPOINT_TIMEOUTS:
            return self.ENDPOINT_TIMEOUTS[path]
        
        # Check for prefix match
        for endpoint_path, timeout in self.ENDPOINT_TIMEOUTS.items():
            if path.startswith(endpoint_path):
                return timeout
        
        return self.default_timeout
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request with timeout.
        
        Args:
            request: Incoming request
            call_next: Next middleware/endpoint
        
        Returns:
            Response or timeout error
        """
        # Get timeout for this endpoint
        timeout = self.get_timeout_for_path(request.url.path)
        
        try:
            # Execute request with timeout
            response = await asyncio.wait_for(
                call_next(request),
                timeout=timeout
            )
            return response
            
        except asyncio.TimeoutError:
            # Request timed out
            request_id = getattr(request.state, "request_id", None)
            
            logger.error(
                f"Request timeout after {timeout}s: {request.method} {request.url.path}",
                extra={"request_id": request_id, "timeout": timeout}
            )
            
            # Return timeout error response
            from ..models.errors import create_error_response, ErrorCode
            
            error_response = create_error_response(
                error_message=f"Request timed out after {timeout} seconds",
                error_code=ErrorCode.INTERNAL_ERROR,
                status_code=504,  # Gateway Timeout
                request_id=request_id,
                path=str(request.url.path)
            )
            
            return JSONResponse(
                status_code=504,
                content=error_response.model_dump(mode="json"),
                headers={
                    "X-Timeout": str(timeout),
                    "X-Request-ID": request_id or "unknown"
                }
            )
        
        except Exception as e:
            # Other errors - let them propagate to exception handlers
            raise

