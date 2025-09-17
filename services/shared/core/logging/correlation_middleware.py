"""Correlation Middleware - Automatic correlation ID management for requests."""

import uuid
from typing import Callable, Any, Optional
from contextlib import asynccontextmanager

from .logger import set_correlation_id, get_correlation_id, generate_correlation_id


class CorrelationMiddleware:
    """Middleware for automatic correlation ID management.

    This middleware automatically:
    - Generates correlation IDs for incoming requests
    - Sets correlation IDs in logging context
    - Propagates correlation IDs through async operations
    - Cleans up correlation IDs after request completion
    """

    def __init__(self, header_name: str = "X-Correlation-ID") -> None:
        """Initialize correlation middleware.

        Args:
            header_name: HTTP header name for correlation ID
        """
        self.header_name = header_name

    def extract_correlation_id(self, headers: dict) -> Optional[str]:
        """Extract correlation ID from request headers.

        Args:
            headers: Request headers dictionary

        Returns:
            Correlation ID from headers or None
        """
        header_value = headers.get(self.header_name.lower()) or headers.get(self.header_name)
        return header_value if header_value else None

    def set_response_header(self, response_headers: dict, correlation_id: str) -> None:
        """Set correlation ID in response headers.

        Args:
            response_headers: Response headers dictionary
            correlation_id: Correlation ID to set
        """
        response_headers[self.header_name] = correlation_id

    @asynccontextmanager
    async def handle_request(self, request_headers: dict, response_headers: dict):
        """Context manager for handling request correlation.

        Args:
            request_headers: Incoming request headers
            response_headers: Outgoing response headers

        Yields:
            Correlation ID for the request
        """
        # Extract or generate correlation ID
        correlation_id = self.extract_correlation_id(request_headers)
        if not correlation_id:
            correlation_id = generate_correlation_id()

        # Set correlation ID in context
        previous_id = get_correlation_id()
        set_correlation_id(correlation_id)

        try:
            # Set correlation ID in response headers
            self.set_response_header(response_headers, correlation_id)

            yield correlation_id
        finally:
            # Restore previous correlation ID
            set_correlation_id(previous_id)


def correlation_context(correlation_id: Optional[str] = None):
    """Decorator/context manager for setting correlation ID.

    Args:
        correlation_id: Correlation ID to set (generates new one if None)

    Returns:
        Context manager for correlation ID management

    Example:
        @correlation_context()
        async def my_function():
            logger.info("This will have correlation ID")

        # Or as context manager
        with correlation_context("custom-id"):
            logger.info("This will use custom-id")
    """
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _correlation_context(corr_id: Optional[str]):
        previous_id = get_correlation_id()
        new_id = corr_id or generate_correlation_id()
        set_correlation_id(new_id)

        try:
            yield new_id
        finally:
            set_correlation_id(previous_id)

    return _correlation_context(correlation_id)


def with_correlation_id(correlation_id: Optional[str] = None):
    """Alias for correlation_context for backward compatibility."""
    return correlation_context(correlation_id)
