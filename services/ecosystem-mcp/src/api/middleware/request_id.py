"""
Request ID middleware for distributed tracing.

Adds unique request IDs to all requests and responses.
"""

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to all requests.
    
    Features:
    - Generates UUID for each request
    - Accepts existing X-Request-ID from client
    - Adds X-Request-ID to response headers
    - Makes request_id available in request.state
    
    Usage:
        app.add_middleware(RequestIDMiddleware)
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process request and add request ID."""
        # Get or generate request ID
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store in request state for access in handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


def get_request_id(request: Request) -> str:
    """
    Get request ID from request state.
    
    Args:
        request: FastAPI request object
    
    Returns:
        Request ID string
    
    Example:
        @app.get("/endpoint")
        async def endpoint(request: Request):
            request_id = get_request_id(request)
            logger.info("processing", request_id=request_id)
    """
    return getattr(request.state, "request_id", "unknown")

