"""Exception handlers for the Analysis Service.

Centralized exception handling for all domain and infrastructure exceptions.
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from services.shared.presentation.responses import create_error_response

from ...domain.exceptions import (
    AnalysisExecutionException,
    AnalysisTimeoutException,
    AuthorizationException,
    DocumentNotFoundException,
    DomainException,
    ExternalServiceException,
    ResourceLimitExceededException,
    ValidationException,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI application."""

    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        """Handle domain-specific exceptions."""
        logger.error(
            f"Domain exception in {request.url.path}: {exc.message}",
            extra={
                "error_code": "DOMAIN_ERROR",
                "path": str(request.url.path),
                "method": request.method,
                "details": exc.details,
            },
        )
        return JSONResponse(
            status_code=400,
            content=create_error_response(
                message=f"Domain error: {exc.message}",
                error_code="DOMAIN_ERROR",
                details=exc.details,
            ),
        )

    @app.exception_handler(ValidationException)
    async def validation_exception_handler(request: Request, exc: ValidationException):
        """Handle validation exceptions."""
        logger.warning(
            f"Validation exception in {request.url.path}: {exc.message}",
            extra={
                "error_code": "VALIDATION_ERROR",
                "path": str(request.url.path),
                "method": request.method,
                "validation_errors": exc.validation_errors,
            },
        )
        return JSONResponse(
            status_code=400,
            content=create_error_response(
                message=f"Validation error: {exc.message}",
                error_code="VALIDATION_ERROR",
                details={"validation_errors": exc.validation_errors},
            ),
        )

    @app.exception_handler(DocumentNotFoundException)
    async def document_not_found_handler(
        request: Request, exc: DocumentNotFoundException
    ):
        """Handle document not found exceptions."""
        logger.warning(
            f"Document not found in {request.url.path}: {exc.message}",
            extra={
                "error_code": "DOCUMENT_NOT_FOUND",
                "path": str(request.url.path),
                "method": request.method,
                "details": exc.details,
            },
        )
        return JSONResponse(
            status_code=404,
            content=create_error_response(
                message=f"Document not found: {exc.message}",
                error_code="DOCUMENT_NOT_FOUND",
                details=exc.details,
            ),
        )

    @app.exception_handler(AnalysisTimeoutException)
    async def analysis_timeout_handler(request: Request, exc: AnalysisTimeoutException):
        """Handle analysis timeout exceptions."""
        return JSONResponse(
            status_code=408,
            content=create_error_response(
                message=f"Analysis timeout: {exc.message}",
                error_code="ANALYSIS_TIMEOUT",
                details=exc.details,
            ),
        )

    @app.exception_handler(AnalysisExecutionException)
    async def analysis_execution_handler(
        request: Request, exc: AnalysisExecutionException
    ):
        """Handle analysis execution exceptions."""
        logger.error(
            f"Analysis execution failed in {request.url.path}: {exc.message}",
            extra={
                "error_code": "ANALYSIS_EXECUTION_ERROR",
                "path": str(request.url.path),
                "method": request.method,
                "details": exc.details,
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                message=f"Analysis execution failed: {exc.message}",
                error_code="ANALYSIS_EXECUTION_ERROR",
                details=exc.details,
            ),
        )

    @app.exception_handler(ExternalServiceException)
    async def external_service_handler(request: Request, exc: ExternalServiceException):
        """Handle external service exceptions."""
        return JSONResponse(
            status_code=502,
            content=create_error_response(
                message=f"External service error: {exc.message}",
                error_code="EXTERNAL_SERVICE_ERROR",
                details=exc.details,
            ),
        )

    @app.exception_handler(AuthorizationException)
    async def authorization_handler(request: Request, exc: AuthorizationException):
        """Handle authorization exceptions."""
        return JSONResponse(
            status_code=403,
            content=create_error_response(
                message=f"Authorization failed: {exc.message}",
                error_code="AUTHORIZATION_ERROR",
                details=exc.details,
            ),
        )

    @app.exception_handler(ResourceLimitExceededException)
    async def resource_limit_handler(
        request: Request, exc: ResourceLimitExceededException
    ):
        """Handle resource limit exceeded exceptions."""
        return JSONResponse(
            status_code=429,
            content=create_error_response(
                message=f"Resource limit exceeded: {exc.message}",
                error_code="RESOURCE_LIMIT_EXCEEDED",
                details=exc.details,
            ),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle any unhandled exceptions."""
        logger.critical(
            f"Unhandled exception in {request.url.path}: {str(exc)}",
            extra={
                "error_code": "INTERNAL_SERVER_ERROR",
                "path": str(request.url.path),
                "method": request.method,
                "exception_type": type(exc).__name__,
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                message="An unexpected error occurred. Please try again later.",
                error_code="INTERNAL_SERVER_ERROR",
                details={"path": str(request.url.path)},
            ),
        )
