"""
Global exception handlers for the API.

Provides consistent error handling across all endpoints.
"""

import logging
from typing import Union

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError, HTTPException
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded

from ..utils.exceptions import (
    EcosystemMCPError,
    DatabaseError,
    ValidationError as CustomValidationError,
    ConfigError,
    StorageError,
    ModelError,
    IngestionError
)
from .models.errors import ErrorResponse, ErrorDetail, ErrorCode, create_error_response

logger = logging.getLogger(__name__)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle generic uncaught exceptions.
    
    Args:
        request: FastAPI request
        exc: Exception instance
    
    Returns:
        JSONResponse with standardized error
    """
    # Get request ID if available
    request_id = getattr(request.state, "request_id", None)
    
    # Log the error
    logger.error(
        f"Unhandled exception: {exc}",
        exc_info=True,
        extra={"request_id": request_id, "path": str(request.url.path)}
    )
    
    # Create error response
    error_response = create_error_response(
        error_message="An internal server error occurred",
        error_code=ErrorCode.INTERNAL_ERROR,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode="json")
    )


async def ecosystem_mcp_error_handler(request: Request, exc: EcosystemMCPError) -> JSONResponse:
    """
    Handle custom EcosystemMCPError exceptions.
    
    Args:
        request: FastAPI request
        exc: EcosystemMCPError instance
    
    Returns:
        JSONResponse with standardized error
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Map exception types to error codes and status codes
    error_mapping = {
        DatabaseError: (ErrorCode.DATABASE_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE),
        CustomValidationError: (ErrorCode.VALIDATION_ERROR, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ConfigError: (ErrorCode.CONFIG_ERROR, status.HTTP_500_INTERNAL_SERVER_ERROR),
        StorageError: (ErrorCode.STORAGE_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE),
        ModelError: (ErrorCode.MODEL_ERROR, status.HTTP_503_SERVICE_UNAVAILABLE),
        IngestionError: (ErrorCode.INGESTION_ERROR, status.HTTP_500_INTERNAL_SERVER_ERROR),
    }
    
    # Get error code and status code
    error_code, status_code = error_mapping.get(
        type(exc),
        (ErrorCode.INTERNAL_ERROR, status.HTTP_500_INTERNAL_SERVER_ERROR)
    )
    
    # Log the error
    logger.error(
        f"{type(exc).__name__}: {exc}",
        extra={"request_id": request_id, "path": str(request.url.path)}
    )
    
    # Create error response
    error_response = create_error_response(
        error_message=str(exc),
        error_code=error_code,
        status_code=status_code,
        request_id=request_id,
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(mode="json")
    )


async def validation_exception_handler(
    request: Request, 
    exc: Union[RequestValidationError, ValidationError]
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Args:
        request: FastAPI request
        exc: ValidationError instance
    
    Returns:
        JSONResponse with standardized error
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Extract validation errors
    details = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        details.append(
            ErrorDetail(
                field=field,
                message=error["msg"],
                code=error["type"]
            )
        )
    
    # Log validation errors
    logger.warning(
        f"Validation error: {len(details)} field(s) failed validation",
        extra={"request_id": request_id, "path": str(request.url.path)}
    )
    
    # Create error response
    error_response = create_error_response(
        error_message="Request validation failed",
        error_code=ErrorCode.VALIDATION_ERROR,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
        request_id=request_id,
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode="json")
    )


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handle rate limit exceeded errors.
    
    Args:
        request: FastAPI request
        exc: RateLimitExceeded instance
    
    Returns:
        JSONResponse with standardized error
    """
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        f"Rate limit exceeded for {request.url.path}",
        extra={"request_id": request_id, "path": str(request.url.path)}
    )
    
    error_response = create_error_response(
        error_message="Rate limit exceeded. Please try again later.",
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        request_id=request_id,
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response.model_dump(mode="json"),
        headers={"Retry-After": "60"}  # Suggest retry after 60 seconds
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions (404, 405, etc).
    
    Args:
        request: FastAPI request
        exc: HTTPException instance
    
    Returns:
        JSONResponse with standardized error
    """
    request_id = getattr(request.state, "request_id", None)
    
    # Map status codes to error codes
    error_code_map = {
        404: ErrorCode.NOT_FOUND,
        401: ErrorCode.AUTHENTICATION_ERROR,
        403: ErrorCode.AUTHORIZATION_ERROR,
        400: ErrorCode.INVALID_INPUT,
    }
    
    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    
    logger.info(
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={"request_id": request_id, "path": str(request.url.path)}
    )
    
    error_response = create_error_response(
        error_message=str(exc.detail),
        error_code=error_code,
        status_code=exc.status_code,
        request_id=request_id,
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json")
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI app.
    
    Args:
        app: FastAPI application instance
    """
    # HTTP exceptions (404, 405, etc) - must be registered before generic handler
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # Rate limiting errors
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    
    # Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    
    # Custom exception handlers
    app.add_exception_handler(EcosystemMCPError, ecosystem_mcp_error_handler)
    app.add_exception_handler(DatabaseError, ecosystem_mcp_error_handler)
    app.add_exception_handler(CustomValidationError, ecosystem_mcp_error_handler)
    app.add_exception_handler(ConfigError, ecosystem_mcp_error_handler)
    app.add_exception_handler(StorageError, ecosystem_mcp_error_handler)
    app.add_exception_handler(ModelError, ecosystem_mcp_error_handler)
    app.add_exception_handler(IngestionError, ecosystem_mcp_error_handler)
    
    # Generic exception handler (catch-all) - MUST BE LAST
    app.add_exception_handler(Exception, generic_exception_handler)
    
    logger.info("✅ Exception handlers registered")

