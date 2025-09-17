"""Standardized Error Handling and Exception Classes

Comprehensive error handling system used across all services in the ecosystem.

This module provides:
- Custom exception classes for different error types
- Standardized error response formatting
- FastAPI exception handlers and middleware
- Error logging and monitoring integration
- Validation error handling and formatting
- Service-specific error codes and categories

All services use these utilities to ensure consistent error handling,
logging, and user experience across the entire ecosystem.
"""

import os
import traceback
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from ..core.responses.responses import ErrorResponse, ValidationErrorResponse, format_error_details, format_validation_errors
from ..monitoring.logging import fire_and_forget
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError


# ============================================================================
# CUSTOM EXCEPTION CLASSES
# ============================================================================

class ServiceException(Exception):
    """Base exception class for service-specific errors.

    All custom exceptions in the ecosystem should inherit from this class
    to ensure consistent error handling, logging, and response formatting.

    Attributes:
        message: Human-readable error message
        error_code: Machine-readable error code for client handling
        status_code: HTTP status code for the response
        details: Additional error details and context
    """

    def __init__(self, message: str, error_code: str = "internal_error",
                 status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class ValidationException(ServiceException):
    """Exception for validation errors."""

    def __init__(self, message: str = "Validation failed",
                 field_errors: Optional[Dict[str, List[str]]] = None):
        super().__init__(message, "validation_error", 422, {"field_errors": field_errors})
        self.field_errors = field_errors


class NotFoundException(ServiceException):
    """Exception for resource not found errors."""

    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} not found: {resource_id}"
        super().__init__(message, "not_found", 404, {
            "resource_type": resource_type,
            "resource_id": resource_id
        })


class ConflictException(ServiceException):
    """Exception for resource conflict errors."""

    def __init__(self, message: str, resource_type: str = "resource"):
        super().__init__(message, "conflict", 409, {"resource_type": resource_type})


class AuthenticationException(ServiceException):
    """Exception for authentication errors."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, "unauthorized", 401)


class AuthorizationException(ServiceException):
    """Exception for authorization errors."""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, "forbidden", 403)


class ExternalServiceException(ServiceException):
    """Exception for external service errors."""

    def __init__(self, service_name: str, original_error: str):
        message = f"External service error: {service_name}"
        super().__init__(message, "service_unavailable", 503, {
            "service_name": service_name,
            "original_error": original_error
        })


class DatabaseException(ServiceException):
    """Exception for database-related errors."""

    def __init__(self, operation: str, original_error: str):
        message = f"Database operation failed: {operation}"
        super().__init__(message, "internal_error", 500, {
            "operation": operation,
            "original_error": original_error
        })


# ============================================================================
# ERROR HANDLING UTILITIES
# ============================================================================

def handle_service_exception(exc: ServiceException, request: Optional[Request] = None) -> JSONResponse:
    """Handle ServiceException and return appropriate JSON response."""
    # Log the error
    log_error(exc, request)

    # Create error response
    error_response = ErrorResponse(
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        request_id=get_request_id(request),
        timestamp=datetime.now(timezone.utc)
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )


def handle_validation_exception(exc: ValidationError, request: Optional[Request] = None) -> JSONResponse:
    """Handle Pydantic ValidationError and return appropriate JSON response."""
    # Log the error
    log_error(exc, request)

    # Format field errors safely
    try:
        field_errors = format_validation_errors({"detail": exc.errors()})
    except Exception:
        # Fallback if formatting fails
        field_errors = {"detail": [{"msg": "Validation error occurred", "type": "validation_error"}]}

    # Create validation error response
    error_response = ValidationErrorResponse(
        message="Validation failed",
        error_code="validation_error",
        field_errors=field_errors,
        request_id=get_request_id(request),
        timestamp=datetime.now(timezone.utc)
    )

    return JSONResponse(
        status_code=422,
        content=error_response.dict()
    )


def handle_generic_exception(exc: Exception, request: Optional[Request] = None) -> JSONResponse:
    """Handle generic exceptions and return appropriate JSON response."""
    # Log the error with full traceback
    log_error(exc, request, include_traceback=True)

    # Create generic error response
    error_response = ErrorResponse(
        message="An unexpected error occurred",
        error_code="internal_error",
        details=format_error_details(exc) if os.environ.get("DEBUG", "").lower() == "true" else None,
        request_id=get_request_id(request),
        timestamp=datetime.now(timezone.utc)
    )

    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )


def log_error(exc: Exception, request: Optional[Request] = None,
              include_traceback: bool = False):
    """Log an error with appropriate context."""
    try:
        log_data = {
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "request_id": get_request_id(request),
            "user_agent": request.headers.get("user-agent") if request else None,
            "method": request.method if request else None,
            "url": str(request.url) if request else None,
        }

        if include_traceback:
            log_data["traceback"] = traceback.format_exc()

        # Use fire_and_forget for async logging
        fire_and_forget("error", f"Exception occurred: {type(exc).__name__}",
                       "error_handler", log_data)

    except Exception:
        # Don't let logging errors break the error handler
        pass


def get_request_id(request: Optional[Request] = None) -> Optional[str]:
    """Extract request ID from request headers."""
    if request:
        return (request.headers.get("x-request-id") or
                request.headers.get("x-correlation-id"))
    return None


# ============================================================================
# HTTP EXCEPTION HELPERS
# ============================================================================

def raise_not_found(resource_type: str, resource_id: str):
    """Raise a standardized not found exception."""
    raise NotFoundException(resource_type, resource_id)


def raise_validation_error(message: str = "Validation failed",
                          field_errors: Optional[Dict[str, List[str]]] = None):
    """Raise a standardized validation exception."""
    raise ValidationException(message, field_errors)


def raise_conflict(message: str, resource_type: str = "resource"):
    """Raise a standardized conflict exception."""
    raise ConflictException(message, resource_type)


def raise_unauthorized(message: str = "Authentication required"):
    """Raise a standardized authentication exception."""
    raise AuthenticationException(message)


def raise_forbidden(message: str = "Insufficient permissions"):
    """Raise a standardized authorization exception."""
    raise AuthorizationException(message)


def raise_external_service_error(service_name: str, original_error: str):
    """Raise a standardized external service exception."""
    raise ExternalServiceException(service_name, original_error)


def raise_database_error(operation: str, original_error: str):
    """Raise a standardized database exception."""
    raise DatabaseException(operation, original_error)


# ============================================================================
# VALIDATION HELPERS
# ============================================================================

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that required fields are present in data."""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        raise_validation_error(
            f"Missing required fields: {', '.join(missing_fields)}",
            {field: ["This field is required"] for field in missing_fields}
        )


def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> None:
    """Validate field types in data."""
    type_errors = {}

    for field, expected_type in field_types.items():
        if field in data:
            value = data[field]
            if not isinstance(value, expected_type):
                if field not in type_errors:
                    type_errors[field] = []
                type_errors[field].append(f"Must be of type {expected_type.__name__}")

    if type_errors:
        raise_validation_error("Type validation failed", type_errors)


def validate_string_length(value: str, field_name: str,
                          min_length: Optional[int] = None,
                          max_length: Optional[int] = None) -> None:
    """Validate string length constraints."""
    errors = []

    if min_length is not None and len(value) < min_length:
        errors.append(f"Must be at least {min_length} characters long")

    if max_length is not None and len(value) > max_length:
        errors.append(f"Must be at most {max_length} characters long")

    if errors:
        raise_validation_error(f"Invalid {field_name} length", {field_name: errors})


def validate_numeric_range(value: Union[int, float], field_name: str,
                          min_value: Optional[Union[int, float]] = None,
                          max_value: Optional[Union[int, float]] = None) -> None:
    """Validate numeric range constraints."""
    errors = []

    if min_value is not None and value < min_value:
        errors.append(f"Must be at least {min_value}")

    if max_value is not None and value > max_value:
        errors.append(f"Must be at most {max_value}")

    if errors:
        raise_validation_error(f"Invalid {field_name} value", {field_name: errors})


# ============================================================================
# FASTAPI EXCEPTION HANDLERS
# ============================================================================

def register_exception_handlers(app):
    """Register global exception handlers on FastAPI app."""

    @app.exception_handler(ServiceException)
    async def service_exception_handler(request: Request, exc: ServiceException):
        return handle_service_exception(exc, request)

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return handle_validation_exception(exc, request)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        return handle_generic_exception(exc, request)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        # Log HTTP exceptions too
        log_error(exc, request)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "message": exc.detail,
                "error_code": f"http_{exc.status_code}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": get_request_id(request)
            }
        )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_execute(func, *args, **kwargs):
    """Execute a function safely and handle exceptions."""
    try:
        return func(*args, **kwargs)
    except ServiceException:
        raise  # Re-raise service exceptions as-is
    except ValidationError as e:
        raise ValidationException("Validation failed", format_validation_errors({"detail": e.errors()}))
    except Exception as e:
        raise ServiceException(f"Operation failed: {str(e)}", "internal_error", 500)


async def safe_execute_async(func, *args, **kwargs):
    """Execute an async function safely and handle exceptions."""
    try:
        return await func(*args, **kwargs)
    except ServiceException:
        raise  # Re-raise service exceptions as-is
    except ValidationError as e:
        raise ValidationException("Validation failed", format_validation_errors({"detail": e.errors()}))
    except Exception as e:
        raise ServiceException(f"Operation failed: {str(e)}", "internal_error", 500)


def create_error_response_dict(message: str, error_code: str = "internal_error",
                              status_code: int = 500, details: Optional[Dict[str, Any]] = None,
                              request: Optional[Request] = None) -> Dict[str, Any]:
    """Create a standardized error response dictionary."""
    return {
        "success": False,
        "message": message,
        "error_code": error_code,
        "status_code": status_code,
        "details": details or {},
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": get_request_id(request)
    }


def create_success_response_dict(message: str = "Operation successful",
                                data: Any = None, request: Optional[Request] = None) -> Dict[str, Any]:
    """Create a standardized success response dictionary."""
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": get_request_id(request)
    }


# ============================================================================
# FASTAPI ERROR HANDLERS
# ============================================================================

def install_error_handlers(app: FastAPI) -> None:
    """Install standardized error handlers for FastAPI applications."""
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):  # type: ignore
        # Convert errors to serializable format
        errors = []
        for error in exc.errors():
            errors.append({
                "type": error.get("type", "validation_error"),
                "loc": error.get("loc", []),
                "msg": error.get("msg", str(error)),
                "input": str(error.get("input", "")) if error.get("input") is not None else None
            })

        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": errors,
                "path": str(request.url),
            },
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError):  # type: ignore
        # Convert errors to serializable format
        errors = []
        for error in exc.errors():
            errors.append({
                "type": error.get("type", "validation_error"),
                "loc": error.get("loc", []),
                "msg": error.get("msg", str(error)),
                "input": str(error.get("input", "")) if error.get("input") is not None else None
            })

        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "detail": errors,
                "path": str(request.url),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):  # type: ignore
        # Ensure the exception message is JSON serializable
        try:
            message = str(exc)
            # Test JSON serialization
            import json
            json.dumps(message)
        except (TypeError, ValueError):
            message = f"Validation error: {type(exc).__name__}"

        return JSONResponse(
            status_code=400,
            content={
                "error": "validation_error",
                "message": message,
                "path": str(request.url),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):  # type: ignore
        # Handle non-JSON serializable exceptions
        try:
            message = str(exc)
        except Exception:
            message = f"{type(exc).__name__}: {repr(exc)}"

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": message,
                "path": str(request.url),
            },
        )
