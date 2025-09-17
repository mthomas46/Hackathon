"""Logging middleware for structured request/response logging."""

import logging
import time
import uuid
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ...shared.logging import fire_and_forget


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    def __init__(self, app, exclude_paths: Optional[list] = None):
        """Initialize middleware."""
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/metrics"]

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log details."""
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate request ID if not present
        request_id = getattr(request.state, 'request_id', None)
        if not request_id:
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Extract request details
        request_details = await self._extract_request_details(request)

        try:
            # Process the request
            response = await call_next(request)

            # Calculate processing time
            processing_time = time.time() - start_time

            # Extract response details
            response_details = self._extract_response_details(response)

            # Log successful request
            await self._log_request(
                request_details,
                response_details,
                processing_time,
                None
            )

            # Add request ID to response headers
            response.headers['X-Request-ID'] = request_id

            return response

        except Exception as exc:
            # Calculate processing time
            processing_time = time.time() - start_time

            # Log failed request
            await self._log_request(
                request_details,
                None,
                processing_time,
                exc
            )

            # Re-raise the exception
            raise

    async def _extract_request_details(self, request: Request) -> Dict[str, Any]:
        """Extract details from the request."""
        # Get request body for logging (be careful with large payloads)
        body = None
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body_bytes = await request.body()
                if len(body_bytes) < 1024:  # Only log small bodies
                    body = body_bytes.decode('utf-8', errors='replace')
            except Exception:
                body = "[Could not read body]"

        return {
            'method': request.method,
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'headers': dict(request.headers),
            'client_ip': self._get_client_ip(request),
            'user_agent': request.headers.get('user-agent'),
            'content_length': request.headers.get('content-length'),
            'body': body
        }

    def _extract_response_details(self, response: Response) -> Dict[str, Any]:
        """Extract details from the response."""
        return {
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'content_length': response.headers.get('content-length')
        }

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

    async def _log_request(
        self,
        request_details: Dict[str, Any],
        response_details: Optional[Dict[str, Any]],
        processing_time: float,
        exception: Optional[Exception]
    ) -> None:
        """Log the request details."""
        log_data = {
            'request_id': getattr(request_details.get('_request'), None),
            'method': request_details['method'],
            'path': request_details['path'],
            'client_ip': request_details['client_ip'],
            'user_agent': request_details.get('user_agent'),
            'processing_time': round(processing_time * 1000, 2),  # Convert to milliseconds
            'query_params': request_details.get('query_params'),
        }

        if response_details:
            log_data.update({
                'status_code': response_details['status_code'],
                'response_size': response_details.get('content_length')
            })

        if exception:
            log_data['error'] = str(exception)
            logger.error("Request failed", extra=log_data, exc_info=exception)
        else:
            # Log based on status code
            if response_details['status_code'] >= 500:
                logger.error("Request error", extra=log_data)
            elif response_details['status_code'] >= 400:
                logger.warning("Request client error", extra=log_data)
            else:
                logger.info("Request completed", extra=log_data)


class LoggingMiddleware:
    """Additional logging utilities and context managers."""

    @staticmethod
    def get_request_logger(request: Request) -> logging.LoggerAdapter:
        """Get a logger adapter with request context."""
        request_id = getattr(request.state, 'request_id', 'unknown')

        extra = {
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'client_ip': LoggingMiddleware._get_client_ip(request)
        }

        return logging.LoggerAdapter(logger, extra)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip

        client = request.client
        return client.host if client else "unknown"

    @staticmethod
    def log_business_event(
        event_type: str,
        event_data: Dict[str, Any],
        request: Optional[Request] = None
    ) -> None:
        """Log business events with context."""
        log_data = {
            'event_type': event_type,
            'event_data': event_data
        }

        if request:
            log_data.update({
                'request_id': getattr(request.state, 'request_id', None),
                'client_ip': LoggingMiddleware._get_client_ip(request)
            })

        logger.info(f"Business event: {event_type}", extra=log_data)

    @staticmethod
    def log_performance_metric(
        operation: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None
    ) -> None:
        """Log performance metrics."""
        log_data = {
            'operation': operation,
            'duration_ms': round(duration * 1000, 2),
            'metadata': metadata or {}
        }

        if request:
            log_data.update({
                'request_id': getattr(request.state, 'request_id', None),
                'path': request.url.path
            })

        logger.info(f"Performance: {operation}", extra=log_data)


class PerformanceLogger:
    """Context manager for logging operation performance."""

    def __init__(self, operation: str, logger_adapter: logging.LoggerAdapter):
        """Initialize performance logger."""
        self.operation = operation
        self.logger = logger_adapter
        self.start_time = None

    async def __aenter__(self):
        """Enter the context."""
        self.start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and log performance."""
        if self.start_time:
            duration = time.time() - self.start_time
            log_data = {
                'operation': self.operation,
                'duration_ms': round(duration * 1000, 2)
            }

            if exc_type:
                log_data['error'] = str(exc_val)
                self.logger.error(f"Operation failed: {self.operation}", extra=log_data)
            else:
                self.logger.info(f"Operation completed: {self.operation}", extra=log_data)
