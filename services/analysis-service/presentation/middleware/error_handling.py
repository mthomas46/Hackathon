"""Error handling middleware for consistent API error responses."""

import logging
import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from ...presentation.models.base import ErrorResponse, ErrorCode


logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for handling and formatting API errors consistently."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and handle errors."""
        try:
            # Process the request
            response = await call_next(request)
            return response

        except HTTPException as exc:
            # Handle FastAPI HTTP exceptions
            return await self._handle_http_exception(request, exc)

        except Exception as exc:
            # Handle unexpected exceptions
            return await self._handle_unexpected_exception(request, exc)

    async def _handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        # Map HTTP status codes to error codes
        status_to_error_code = {
            400: ErrorCode.VALIDATION_ERROR,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            409: ErrorCode.CONFLICT,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
        }

        error_code = status_to_error_code.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

        # Log the error
        await self._log_error(request, exc, error_code)

        # Create error response
        error_response = ErrorResponse(
            error={
                "field": None,
                "message": exc.detail,
                "code": error_code
            },
            request_id=getattr(request.state, 'request_id', None)
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.dict()
        )

    async def _handle_unexpected_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        # Log the full exception
        logger.error(
            f"Unexpected error in {request.method} {request.url.path}",
            exc_info=True,
            extra={
                'request_id': getattr(request.state, 'request_id', None),
                'user_agent': request.headers.get('user-agent'),
                'client_ip': self._get_client_ip(request)
            }
        )

        # Create generic error response
        error_response = ErrorResponse(
            error={
                "field": None,
                "message": "An unexpected error occurred",
                "code": ErrorCode.INTERNAL_ERROR
            },
            request_id=getattr(request.state, 'request_id', None)
        )

        return JSONResponse(
            status_code=500,
            content=error_response.dict()
        )

    async def _log_error(self, request: Request, exc: Exception, error_code: str) -> None:
        """Log error with appropriate level."""
        log_data = {
            'method': request.method,
            'path': request.url.path,
            'query_params': str(request.query_params),
            'user_agent': request.headers.get('user-agent'),
            'client_ip': self._get_client_ip(request),
            'request_id': getattr(request.state, 'request_id', None),
            'error_code': error_code,
            'error_message': str(exc)
        }

        if isinstance(exc, HTTPException):
            # Log HTTP exceptions as warnings for client errors, errors for server errors
            if 400 <= exc.status_code < 500:
                logger.warning("Client error", extra=log_data)
            else:
                logger.error("Server error", extra=log_data)
        else:
            # Log unexpected exceptions as errors
            logger.error("Unexpected error", extra=log_data, exc_info=True)

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()

        # Check for other proxy headers
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip

        # Fall back to direct client
        client = request.client
        return client.host if client else "unknown"


class DomainExceptionHandler:
    """Handler for domain-specific exceptions."""

    @staticmethod
    def handle_validation_error(exc: Exception, request_id: Optional[str] = None) -> JSONResponse:
        """Handle domain validation errors."""
        error_response = ErrorResponse(
            error={
                "field": getattr(exc, 'field', None),
                "message": str(exc),
                "code": ErrorCode.VALIDATION_ERROR
            },
            request_id=request_id
        )

        return JSONResponse(
            status_code=400,
            content=error_response.dict()
        )

    @staticmethod
    def handle_not_found_error(exc: Exception, request_id: Optional[str] = None) -> JSONResponse:
        """Handle domain not found errors."""
        error_response = ErrorResponse(
            error={
                "field": None,
                "message": str(exc),
                "code": ErrorCode.NOT_FOUND
            },
            request_id=request_id
        )

        return JSONResponse(
            status_code=404,
            content=error_response.dict()
        )

    @staticmethod
    def handle_business_rule_error(exc: Exception, request_id: Optional[str] = None) -> JSONResponse:
        """Handle domain business rule violations."""
        error_response = ErrorResponse(
            error={
                "field": None,
                "message": str(exc),
                "code": ErrorCode.CONFLICT
            },
            request_id=request_id
        )

        return JSONResponse(
            status_code=409,
            content=error_response.dict()
        )
