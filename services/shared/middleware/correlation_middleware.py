"""Correlation ID Middleware for request tracking."""

import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for correlation ID
_correlation_id: ContextVar[Optional[str]] = ContextVar(
    "correlation_id",
    default=None
)


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID from context.
    
    Returns:
        Correlation ID or None
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: str):
    """
    Set correlation ID in context.
    
    Args:
        correlation_id: Correlation ID to set
    """
    _correlation_id.set(correlation_id)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that adds correlation ID to all requests.
    
    Features:
    - Extracts correlation ID from X-Correlation-ID header
    - Generates new correlation ID if not present
    - Adds correlation ID to response headers
    - Stores correlation ID in request state and context
    
    Usage:
        app = FastAPI()
        app.add_middleware(CorrelationMiddleware)
    """
    
    def __init__(
        self,
        app,
        header_name: str = "X-Correlation-ID",
    ):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            header_name: Name of correlation ID header
        """
        super().__init__(app)
        self.header_name = header_name
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and add correlation ID.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
        
        Returns:
            HTTP response
        """
        # Get or generate correlation ID
        correlation_id = request.headers.get(
            self.header_name,
            str(uuid.uuid4())
        )
        
        # Store in request state
        request.state.correlation_id = correlation_id
        
        # Store in context variable
        set_correlation_id(correlation_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers[self.header_name] = correlation_id
        
        return response


async def correlation_middleware(request: Request, call_next):
    """
    Simple function-based correlation middleware.
    
    Can be used as a FastAPI dependency or middleware function.
    
    Args:
        request: HTTP request
        call_next: Next handler
    
    Returns:
        HTTP response with correlation ID
    """
    # Get or generate correlation ID
    correlation_id = request.headers.get(
        "X-Correlation-ID",
        str(uuid.uuid4())
    )
    
    # Store in request state
    request.state.correlation_id = correlation_id
    
    # Store in context variable
    set_correlation_id(correlation_id)
    
    # Process request
    response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response


def get_request_id(request: Request) -> str:
    """
    Get or generate request ID.
    
    Args:
        request: HTTP request
    
    Returns:
        Request ID
    """
    return getattr(
        request.state,
        "request_id",
        str(uuid.uuid4())
    )

