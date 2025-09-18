"""Standardized Response Formatting - REST-compliant HTTP responses.

This module provides standardized response formatting following REST conventions
and proper HTTP status code usage.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))
from core.responses.responses import (
    BaseResponse,
    SuccessResponse,
    ErrorResponse,
    create_success_response,
    create_error_response
)

from .hateoas import Links, Link


class HTTPStatus(Enum):
    """HTTP status codes with descriptions."""
    # 2xx Success
    OK = (200, "OK")
    CREATED = (201, "Created")
    ACCEPTED = (202, "Accepted")
    NO_CONTENT = (204, "No Content")

    # 3xx Redirection
    MOVED_PERMANENTLY = (301, "Moved Permanently")
    FOUND = (302, "Found")
    NOT_MODIFIED = (304, "Not Modified")

    # 4xx Client Error
    BAD_REQUEST = (400, "Bad Request")
    UNAUTHORIZED = (401, "Unauthorized")
    FORBIDDEN = (403, "Forbidden")
    NOT_FOUND = (404, "Not Found")
    METHOD_NOT_ALLOWED = (405, "Method Not Allowed")
    CONFLICT = (409, "Conflict")
    UNPROCESSABLE_ENTITY = (422, "Unprocessable Entity")
    TOO_MANY_REQUESTS = (429, "Too Many Requests")

    # 5xx Server Error
    INTERNAL_SERVER_ERROR = (500, "Internal Server Error")
    NOT_IMPLEMENTED = (501, "Not Implemented")
    BAD_GATEWAY = (502, "Bad Gateway")
    SERVICE_UNAVAILABLE = (503, "Service Unavailable")
    GATEWAY_TIMEOUT = (504, "Gateway Timeout")

    def __init__(self, code: int, description: str):
        self.code = code
        self.description = description


class SimulationResponse:
    """Standardized response class for simulation API."""

    def __init__(self,
                 success: bool = True,
                 data: Optional[Any] = None,
                 message: Optional[str] = None,
                 error_code: Optional[str] = None,
                 status: HTTPStatus = HTTPStatus.OK,
                 links: Optional[Links] = None,
                 meta: Optional[Dict[str, Any]] = None):
        """Initialize simulation response."""
        self.success = success
        self.data = data
        self.message = message or ("Operation successful" if success else "Operation failed")
        self.error_code = error_code
        self.status = status
        self.links = links
        self.meta = meta or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        response = {
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp,
            "status_code": self.status.code,
            "version": "1.0.0"
        }

        if self.data is not None:
            response["data"] = self.data

        if self.error_code:
            response["error_code"] = self.error_code

        if self.links:
            response["_links"] = self.links.to_dict()

        if self.meta:
            response["_meta"] = self.meta

        return response

    def to_fastapi_response(self) -> Dict[str, Any]:
        """Convert to FastAPI-compatible response."""
        return self.to_dict()


class SimulationResponseBuilder:
    """Builder for creating standardized simulation responses."""

    @staticmethod
    def success(data: Optional[Any] = None,
               message: Optional[str] = None,
               status: HTTPStatus = HTTPStatus.OK,
               links: Optional[Links] = None,
               meta: Optional[Dict[str, Any]] = None) -> SimulationResponse:
        """Create a successful response."""
        return SimulationResponse(
            success=True,
            data=data,
            message=message or "Operation completed successfully",
            status=status,
            links=links,
            meta=meta
        )

    @staticmethod
    def created(data: Optional[Any] = None,
               message: Optional[str] = None,
               resource_id: Optional[str] = None,
               resource_url: Optional[str] = None,
               links: Optional[Links] = None) -> SimulationResponse:
        """Create a resource created response."""
        meta = {"resource_id": resource_id} if resource_id else {}
        if resource_url:
            meta["resource_url"] = resource_url

        return SimulationResponse(
            success=True,
            data=data,
            message=message or "Resource created successfully",
            status=HTTPStatus.CREATED,
            links=links,
            meta=meta
        )

    @staticmethod
    def accepted(data: Optional[Any] = None,
                message: Optional[str] = None,
                job_id: Optional[str] = None,
                estimated_time: Optional[int] = None,
                links: Optional[Links] = None) -> SimulationResponse:
        """Create an accepted (async operation) response."""
        meta = {}
        if job_id:
            meta["job_id"] = job_id
        if estimated_time:
            meta["estimated_completion_seconds"] = estimated_time

        return SimulationResponse(
            success=True,
            data=data,
            message=message or "Operation accepted for processing",
            status=HTTPStatus.ACCEPTED,
            links=links,
            meta=meta
        )

    @staticmethod
    def no_content(message: Optional[str] = None,
                  links: Optional[Links] = None) -> SimulationResponse:
        """Create a no content response."""
        return SimulationResponse(
            success=True,
            message=message or "Operation completed",
            status=HTTPStatus.NO_CONTENT,
            links=links
        )

    @staticmethod
    def bad_request(message: str = "Invalid request",
                   error_code: str = "INVALID_REQUEST",
                   details: Optional[Dict[str, Any]] = None,
                   links: Optional[Links] = None) -> SimulationResponse:
        """Create a bad request error response."""
        return SimulationResponse(
            success=False,
            message=message,
            error_code=error_code,
            status=HTTPStatus.BAD_REQUEST,
            links=links,
            meta={"details": details} if details else None
        )

    @staticmethod
    def not_found(resource_type: str = "Resource",
                 resource_id: Optional[str] = None,
                 links: Optional[Links] = None) -> SimulationResponse:
        """Create a not found error response."""
        message = f"{resource_type} not found"
        if resource_id:
            message += f": {resource_id}"

        return SimulationResponse(
            success=False,
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status=HTTPStatus.NOT_FOUND,
            links=links
        )

    @staticmethod
    def conflict(message: str = "Resource conflict",
                error_code: str = "RESOURCE_CONFLICT",
                details: Optional[Dict[str, Any]] = None,
                links: Optional[Links] = None) -> SimulationResponse:
        """Create a conflict error response."""
        return SimulationResponse(
            success=False,
            message=message,
            error_code=error_code,
            status=HTTPStatus.CONFLICT,
            links=links,
            meta={"details": details} if details else None
        )

    @staticmethod
    def unprocessable_entity(message: str = "Validation failed",
                           error_code: str = "VALIDATION_ERROR",
                           validation_errors: Optional[List[Dict[str, Any]]] = None,
                           links: Optional[Links] = None) -> SimulationResponse:
        """Create an unprocessable entity error response."""
        meta = {}
        if validation_errors:
            meta["validation_errors"] = validation_errors

        return SimulationResponse(
            success=False,
            message=message,
            error_code=error_code,
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
            links=links,
            meta=meta
        )

    @staticmethod
    def too_many_requests(message: str = "Rate limit exceeded",
                         retry_after: Optional[int] = None,
                         links: Optional[Links] = None) -> SimulationResponse:
        """Create a too many requests error response."""
        meta = {}
        if retry_after:
            meta["retry_after_seconds"] = retry_after

        return SimulationResponse(
            success=False,
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status=HTTPStatus.TOO_MANY_REQUESTS,
            links=links,
            meta=meta
        )

    @staticmethod
    def internal_server_error(message: str = "Internal server error",
                             error_code: str = "INTERNAL_ERROR",
                             trace_id: Optional[str] = None,
                             links: Optional[Links] = None) -> SimulationResponse:
        """Create an internal server error response."""
        meta = {}
        if trace_id:
            meta["trace_id"] = trace_id

        return SimulationResponse(
            success=False,
            message=message,
            error_code=error_code,
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            links=links,
            meta=meta
        )

    @staticmethod
    def service_unavailable(message: str = "Service temporarily unavailable",
                          retry_after: Optional[int] = None,
                          links: Optional[Links] = None) -> SimulationResponse:
        """Create a service unavailable error response."""
        meta = {}
        if retry_after:
            meta["retry_after_seconds"] = retry_after

        return SimulationResponse(
            success=False,
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            links=links,
            meta=meta
        )


# Convenience functions for common responses
def ok_response(data: Optional[Any] = None,
               message: str = "OK",
               links: Optional[Links] = None) -> SimulationResponse:
    """Create a standard OK response."""
    return SimulationResponseBuilder.success(data, message, HTTPStatus.OK, links)


def created_response(data: Optional[Any] = None,
                    message: str = "Resource created",
                    resource_id: Optional[str] = None,
                    links: Optional[Links] = None) -> SimulationResponse:
    """Create a resource created response."""
    return SimulationResponseBuilder.created(data, message, resource_id, links=links)


def accepted_response(data: Optional[Any] = None,
                     message: str = "Request accepted",
                     job_id: Optional[str] = None,
                     links: Optional[Links] = None) -> SimulationResponse:
    """Create an accepted response for async operations."""
    return SimulationResponseBuilder.accepted(data, message, job_id, links=links)


def error_response(status: HTTPStatus,
                  message: str,
                  error_code: Optional[str] = None,
                  links: Optional[Links] = None,
                  meta: Optional[Dict[str, Any]] = None) -> SimulationResponse:
    """Create a standardized error response."""
    return SimulationResponse(
        success=False,
        message=message,
        error_code=error_code or f"HTTP_{status.code}",
        status=status,
        links=links,
        meta=meta
    )


# Response headers utilities
def get_response_headers(status: HTTPStatus,
                        content_type: str = "application/json",
                        cors_origin: str = "*",
                        cache_control: Optional[str] = None) -> Dict[str, str]:
    """Get standard response headers."""
    headers = {
        "Content-Type": content_type,
        "X-API-Version": "1.0.0",
        "X-Response-Time": datetime.now().isoformat(),
    }

    if cors_origin:
        headers.update({
            "Access-Control-Allow-Origin": cors_origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        })

    if cache_control:
        headers["Cache-Control"] = cache_control

    return headers


def get_cors_preflight_headers() -> Dict[str, str]:
    """Get CORS preflight response headers."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        "Access-Control-Max-Age": "86400",  # 24 hours
    }


# Pagination response helpers
def paginated_response(items: List[Any],
                      page: int,
                      page_size: int,
                      total_items: int,
                      base_url: str,
                      links: Optional[Links] = None,
                      meta: Optional[Dict[str, Any]] = None) -> SimulationResponse:
    """Create a paginated response."""
    total_pages = (total_items + page_size - 1) // page_size  # Ceiling division

    pagination_meta = {
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_previous": page > 1,
            "next_page": page + 1 if page < total_pages else None,
            "previous_page": page - 1 if page > 1 else None,
        }
    }

    if meta:
        pagination_meta.update(meta)

    return SimulationResponseBuilder.success(
        data={"items": items},
        message=f"Retrieved {len(items)} items",
        links=links,
        meta=pagination_meta
    )


__all__ = [
    'HTTPStatus',
    'SimulationResponse',
    'SimulationResponseBuilder',
    'ok_response',
    'created_response',
    'accepted_response',
    'error_response',
    'get_response_headers',
    'get_cors_preflight_headers',
    'paginated_response'
]
