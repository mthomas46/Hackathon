"""Base Models - Common model definitions and utilities."""

from typing import Optional, List, Dict, Any, Union, Callable, Type, ClassVar
from pydantic import BaseModel as PydanticBaseModel, Field, field_validator
from datetime import datetime, timezone


class BaseModel(PydanticBaseModel):
    """Enhanced base model with common functionality."""

    class Config:
        """Pydantic configuration."""
        allow_population_by_field_name: bool = True
        json_encoders: Dict[Type[Any], Callable[[Any], Any]] = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        """Convert model to dictionary with enhanced options."""
        # Default to exclude None values and use alias
        kwargs.setdefault('exclude_none', True)
        kwargs.setdefault('by_alias', True)
        return super().dict(**kwargs)

    def json(self, **kwargs: Any) -> str:
        """Convert model to JSON with enhanced options."""
        kwargs.setdefault('exclude_none', True)
        kwargs.setdefault('by_alias', True)
        return super().json(**kwargs)


class ValidationErrorDetail(BaseModel):
    """Detailed validation error information."""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Human-readable error message")
    error_type: str = Field(..., description="Type of validation error")
    value: Optional[Any] = Field(None, description="Invalid value that was provided")
    constraint: Optional[str] = Field(None, description="Validation constraint that failed")

    @field_validator('field')
    @classmethod
    def validate_field(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Field must be a non-empty string')
        return v.strip()

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Message must be a non-empty string')
        return v.strip()


class ErrorDetail(BaseModel):
    """Standard error response detail."""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc),
                                          description="When the error occurred")

    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Error code must be a non-empty string')
        return v.upper().strip()

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Error message must be a non-empty string')
        return v.strip()


class SuccessResponse(BaseModel):
    """Standard successful response structure."""
    success: bool = Field(True, description="Indicates if the operation was successful")
    message: Optional[str] = Field(None, description="Optional success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data payload")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc),
                                          description="When the response was generated")

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        if v is not None and (not isinstance(v, str) or not v.strip()):
            raise ValueError('Message must be a non-empty string if provided')
        return v.strip() if v else None


class ErrorResponse(BaseModel):
    """Standard error response structure."""
    success: bool = Field(False, description="Indicates if the operation failed")
    error: ErrorDetail = Field(..., description="Primary error information")
    validation_errors: Optional[List[ValidationErrorDetail]] = Field(None,
                                                                      description="Detailed validation errors")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc),
                                          description="When the error occurred")

    @field_validator('validation_errors')
    @classmethod
    def validate_validation_errors(cls, v):
        if v is not None and (not isinstance(v, list) or len(v) > 100):
            raise ValueError('Validation errors must be a list with max 100 items')
        return v


class PaginationInfo(BaseModel):
    """Pagination information for list responses."""
    page: int = Field(1, ge=1, description="Current page number")
    page_size: int = Field(50, ge=1, le=1000, description="Number of items per page")
    total_items: int = Field(0, ge=0, description="Total number of items available")
    total_pages: int = Field(0, ge=0, description="Total number of pages")
    has_next: bool = Field(False, description="Whether there is a next page")
    has_previous: bool = Field(False, description="Whether there is a previous page")

    def __init__(self, **data):
        super().__init__(**data)
        # Calculate derived fields
        if self.total_items > 0 and self.page_size > 0:
            self.total_pages = (self.total_items + self.page_size - 1) // self.page_size
            self.has_next = self.page < self.total_pages
            self.has_previous = self.page > 1


class ListResponse(BaseModel):
    """Generic list response with pagination."""
    items: List[Any] = Field(default_factory=list, description="List of items")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    def __init__(self, **data):
        super().__init__(**data)
        # Set pagination info based on items
        if not hasattr(self.pagination, 'total_items') or self.pagination.total_items == 0:
            self.pagination.total_items = len(self.items)


class RequestMetadata(BaseModel):
    """Common request metadata fields."""
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    user_id: Optional[str] = Field(None, description="User making the request")
    session_id: Optional[str] = Field(None, description="User session identifier")
    client_version: Optional[str] = Field(None, description="Client application version")
    user_agent: Optional[str] = Field(None, description="HTTP user agent string")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc),
                                          description="When the request was made")

    @field_validator('request_id')
    @classmethod
    def validate_request_id(cls, v):
        if v is not None and (not isinstance(v, str) or len(v.strip()) < 8):
            raise ValueError('Request ID must be at least 8 characters if provided')
        return v.strip() if v else None


class ResponseMetadata(BaseModel):
    """Common response metadata fields."""
    request_id: Optional[str] = Field(None, description="Request identifier from request")
    processing_time_seconds: Optional[float] = Field(None, ge=0, description="Time taken to process request")
    server_version: Optional[str] = Field(None, description="Server/API version")
    cache_status: Optional[str] = Field(None, description="Cache status (HIT/MISS)")
    rate_limit_remaining: Optional[int] = Field(None, ge=0, description="Remaining rate limit requests")
    timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc),
                                          description="When the response was generated")

    @field_validator('processing_time_seconds')
    @classmethod
    def validate_processing_time(cls, v):
        if v is not None and (not isinstance(v, (int, float)) or v < 0):
            raise ValueError('Processing time must be a non-negative number')
        return v

    @field_validator('rate_limit_remaining')
    @classmethod
    def validate_rate_limit(cls, v):
        if v is not None and (not isinstance(v, int) or v < 0):
            raise ValueError('Rate limit remaining must be a non-negative integer')
        return v


class HealthStatus(BaseModel):
    """Health check status information."""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Health status (healthy/unhealthy/degraded)")
    version: Optional[str] = Field(None, description="Service version")
    uptime_seconds: Optional[int] = Field(None, ge=0, description="Service uptime in seconds")
    last_check: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc),
                                           description="When health was last checked")
    dependencies: Optional[Dict[str, str]] = Field(None, description="Status of service dependencies")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Health-related metrics")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['healthy', 'unhealthy', 'degraded', 'unknown']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v

    @field_validator('uptime_seconds')
    @classmethod
    def validate_uptime(cls, v):
        if v is not None and (not isinstance(v, int) or v < 0):
            raise ValueError('Uptime must be a non-negative integer')
        return v


class ServiceInfo(BaseModel):
    """Service information and capabilities."""
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    description: Optional[str] = Field(None, description="Service description")
    capabilities: List[str] = Field(default_factory=list, description="List of service capabilities")
    endpoints: Optional[Dict[str, str]] = Field(None, description="Available endpoints")
    dependencies: Optional[List[str]] = Field(None, description="Service dependencies")
    environment: Optional[str] = Field(None, description="Deployment environment")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Service name must be a non-empty string')
        return v.strip()

    @field_validator('version')
    @classmethod
    def validate_version(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Service version must be a non-empty string')
        return v.strip()


class AnalysisContext(BaseModel):
    """Context information for analysis operations."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    analysis_type: str = Field(..., description="Type of analysis being performed")
    user_id: Optional[str] = Field(None, description="User requesting the analysis")
    session_id: Optional[str] = Field(None, description="User session identifier")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for tracing")
    parent_analysis_id: Optional[str] = Field(None, description="Parent analysis if this is a sub-analysis")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context metadata")
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc),
                                           description="When the analysis was initiated")

    @field_validator('analysis_id')
    @classmethod
    def validate_analysis_id(cls, v):
        if not v or not isinstance(v, str) or len(v.strip()) < 8:
            raise ValueError('Analysis ID must be at least 8 characters')
        return v.strip()

    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Analysis type must be a non-empty string')
        return v.strip()
