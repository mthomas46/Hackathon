"""Base HTTP models for consistent API responses."""

from typing import Optional, Dict, Any, List, Generic, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class ResponseStatus(str, Enum):
    """API response status enumeration."""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class ErrorCode(str, Enum):
    """Standard error codes for API responses."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


class BaseResponse(BaseModel):
    """Base response model for all API responses."""

    status: ResponseStatus = Field(..., description="Response status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Unique request identifier")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorDetail(BaseModel):
    """Detailed error information."""

    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Human-readable error message")
    code: Optional[str] = Field(None, description="Error code")


class ErrorResponse(BaseResponse):
    """Standard error response model."""

    status: ResponseStatus = ResponseStatus.ERROR
    error: ErrorDetail = Field(..., description="Error details")
    details: Optional[List[ErrorDetail]] = Field(None, description="Additional error details")

    @classmethod
    def from_exception(
        cls,
        exception: Exception,
        status_code: int = 500,
        request_id: Optional[str] = None
    ) -> 'ErrorResponse':
        """Create error response from exception."""
        error_detail = ErrorDetail(
            message=str(exception),
            code=getattr(exception, 'code', ErrorCode.INTERNAL_ERROR)
        )

        return cls(
            error=error_detail,
            request_id=request_id
        )


class SuccessResponse(BaseResponse):
    """Standard success response model."""

    status: ResponseStatus = ResponseStatus.SUCCESS
    data: Optional[Any] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Success message")

    @classmethod
    def with_data(
        cls,
        data: Any,
        message: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> 'SuccessResponse':
        """Create success response with data."""
        return cls(
            data=data,
            message=message,
            request_id=request_id
        )


T = TypeVar('T')


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response model."""

    status: ResponseStatus = ResponseStatus.SUCCESS
    data: List[T] = Field(..., description="List of items")
    pagination: Dict[str, Any] = Field(..., description="Pagination metadata")

    @classmethod
    def create(
        cls,
        items: List[T],
        page: int = 1,
        page_size: int = 20,
        total: int = 0,
        request_id: Optional[str] = None
    ) -> 'PaginatedResponse[T]':
        """Create paginated response."""
        total_pages = (total + page_size - 1) // page_size  # Ceiling division

        pagination = {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

        return cls(
            data=items,
            pagination=pagination,
            request_id=request_id
        )


class HealthResponse(BaseResponse):
    """Health check response model."""

    status: ResponseStatus = ResponseStatus.SUCCESS
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="Dependency health status")

    @classmethod
    def healthy(
        cls,
        service: str,
        version: str,
        uptime: Optional[float] = None,
        dependencies: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> 'HealthResponse':
        """Create healthy response."""
        return cls(
            service=service,
            version=version,
            uptime=uptime,
            dependencies=dependencies,
            request_id=request_id
        )


class MetadataResponse(BaseResponse):
    """Metadata response model for API information."""

    status: ResponseStatus = ResponseStatus.SUCCESS
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    description: str = Field(..., description="Service description")
    endpoints: List[str] = Field(..., description="Available endpoints")
    capabilities: List[str] = Field(..., description="Service capabilities")

    @classmethod
    def create(
        cls,
        service: str,
        version: str,
        description: str,
        endpoints: List[str],
        capabilities: List[str],
        request_id: Optional[str] = None
    ) -> 'MetadataResponse':
        """Create metadata response."""
        return cls(
            service=service,
            version=version,
            description=description,
            endpoints=endpoints,
            capabilities=capabilities,
            request_id=request_id
        )
