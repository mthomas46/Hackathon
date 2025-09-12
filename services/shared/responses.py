"""Standardized response models and helpers.

Provides consistent API response patterns across all services.
Reduces code duplication and ensures uniform response structures.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Generic, TypeVar, Union
from pydantic import BaseModel, Field
# Use BaseModel directly for generic responses (Pydantic v2+ compatible)
GenericModel = BaseModel


# ============================================================================
# COMMON RESPONSE MODELS
# ============================================================================

class BaseResponse(BaseModel):
    """Base response model with common fields."""
    success: bool = Field(..., description="Operation success status")
    message: Optional[str] = Field(None, description="Human-readable message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")
    request_id: Optional[str] = Field(None, description="Request correlation ID")


class SuccessResponse(BaseResponse):
    """Standard success response."""
    success: bool = True
    data: Optional[Any] = Field(None, description="Response data payload")


class ErrorResponse(BaseResponse):
    """Standard error response."""
    success: bool = False
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-level details."""
    field_errors: Optional[Dict[str, List[str]]] = Field(None, description="Field-specific validation errors")


# ============================================================================
# PAGINATION MODELS
# ============================================================================

class PaginationInfo(BaseModel):
    """Pagination metadata."""
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


T = TypeVar('T')

class PaginatedResponse(BaseResponse):
    """Paginated response with generic data."""
    success: bool = True
    data: List[Any] = Field(..., description="List of items")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")


class ListResponse(BaseResponse):
    """List response with generic data."""
    success: bool = True
    data: List[Any] = Field(..., description="List of items")
    count: int = Field(..., description="Number of items returned")


# ============================================================================
# CRUD OPERATION RESPONSES
# ============================================================================

class CreateResponse(BaseResponse):
    """Response for create operations."""
    success: bool = True
    id: str = Field(..., description="ID of created resource")
    resource_url: Optional[str] = Field(None, description="URL to access created resource")


class UpdateResponse(BaseResponse):
    """Response for update operations."""
    success: bool = True
    id: str = Field(..., description="ID of updated resource")
    updated_fields: Optional[List[str]] = Field(None, description="Fields that were updated")
    version: Optional[int] = Field(None, description="New version number")


class DeleteResponse(BaseResponse):
    """Response for delete operations."""
    success: bool = True
    id: str = Field(..., description="ID of deleted resource")
    soft_delete: bool = Field(True, description="Whether this was a soft delete")


class BulkOperationResponse(BaseResponse):
    """Response for bulk operations."""
    success: bool = True
    operation: str = Field(..., description="Operation performed")
    total_requested: int = Field(..., description="Total items requested for operation")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed results per item")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Detailed errors per item")


# ============================================================================
# SERVICE-SPECIFIC RESPONSES
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    version: Optional[str] = Field(None, description="Service version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    uptime_seconds: Optional[float] = None
    environment: Optional[str] = None
    dependencies: Optional[Dict[str, str]] = None


class SystemHealthResponse(BaseModel):
    """System-wide health response."""
    overall_healthy: bool
    services_checked: int
    services_healthy: int
    services_unhealthy: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service_details: Dict[str, Dict[str, Any]]
    environment_info: Dict[str, Any]


class PromptResponse(BaseModel):
    """Prompt operation response."""
    id: str
    name: str
    category: str
    content: Optional[str] = None
    variables: List[str] = []
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime


class WorkflowResponse(BaseModel):
    """Workflow execution response."""
    workflow_id: str
    status: str  # pending, running, completed, failed
    steps_completed: int
    total_steps: int
    results: Optional[List[Dict[str, Any]]] = None
    errors: Optional[List[Dict[str, Any]]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class AnalysisResponse(BaseModel):
    """Analysis operation response."""
    analysis_id: str
    status: str  # pending, running, completed, failed
    target_ids: List[str]
    findings_count: int = 0
    findings: Optional[List[Dict[str, Any]]] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class SearchResponse(BaseModel):
    """Search operation response."""
    query: str
    total_results: int
    results: List[Dict[str, Any]]
    facets: Optional[Dict[str, Any]] = None
    search_time_ms: float


# ============================================================================
# RESPONSE HELPER FUNCTIONS
# ============================================================================

def create_success_response(message: str = "Operation successful", data: Any = None,
                           request_id: Optional[str] = None) -> SuccessResponse:
    """Create a standard success response."""
    return SuccessResponse(
        message=message,
        data=data,
        request_id=request_id
    )


def create_error_response(message: str, error_code: Optional[str] = None,
                         details: Optional[Dict[str, Any]] = None,
                         request_id: Optional[str] = None) -> ErrorResponse:
    """Create a standard error response."""
    return ErrorResponse(
        message=message,
        error_code=error_code,
        details=details,
        request_id=request_id
    )


def create_validation_error_response(field_errors: Dict[str, List[str]],
                                   message: str = "Validation failed",
                                   request_id: Optional[str] = None) -> ValidationErrorResponse:
    """Create a validation error response."""
    return ValidationErrorResponse(
        message=message,
        field_errors=field_errors,
        request_id=request_id
    )


def create_paginated_response(items: List[Any], page: int, page_size: int,
                             total_items: int, request_id: Optional[str] = None) -> PaginatedResponse:
    """Create a paginated response."""
    total_pages = (total_items + page_size - 1) // page_size  # Ceiling division

    return PaginatedResponse(
        data=items,
        pagination=PaginationInfo(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        ),
        request_id=request_id
    )


def create_list_response(items: List[Any], message: str = "Items retrieved",
                        request_id: Optional[str] = None) -> ListResponse:
    """Create a list response."""
    return ListResponse(
        data=items,
        count=len(items),
        message=message,
        request_id=request_id
    )


def create_crud_response(operation: str, resource_id: str, success: bool = True,
                        message: Optional[str] = None, **kwargs) -> Union[CreateResponse, UpdateResponse, DeleteResponse]:
    """Create a CRUD operation response."""
    if not message:
        message = f"Resource {operation}d successfully"

    base_kwargs = {
        "message": message,
        "success": success,
        "id": resource_id,
        **kwargs
    }

    if operation == "create":
        return CreateResponse(**base_kwargs)
    elif operation == "update":
        return UpdateResponse(**base_kwargs)
    elif operation == "delete":
        return DeleteResponse(**base_kwargs)
    else:
        raise ValueError(f"Unknown CRUD operation: {operation}")


# ============================================================================
# HTTP STATUS CODE MAPPINGS
# ============================================================================

HTTP_STATUS_CODES = {
    "success": 200,
    "created": 201,
    "accepted": 202,
    "no_content": 204,
    "bad_request": 400,
    "unauthorized": 401,
    "forbidden": 403,
    "not_found": 404,
    "conflict": 409,
    "unprocessable_entity": 422,
    "internal_server_error": 500,
    "service_unavailable": 503
}


def get_status_code(error_code: Optional[str] = None) -> int:
    """Get HTTP status code from error code."""
    if not error_code:
        return 200

    # Map common error codes to HTTP status codes
    error_mappings = {
        "validation_error": 422,
        "not_found": 404,
        "unauthorized": 401,
        "forbidden": 403,
        "conflict": 409,
        "internal_error": 500,
        "service_unavailable": 503
    }

    return error_mappings.get(error_code.lower(), 400)


# ============================================================================
# RESPONSE FORMATTERS
# ============================================================================

def format_error_details(exc: Exception) -> Dict[str, Any]:
    """Format exception details for error responses."""
    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "module": type(exc).__module__
    }


def format_validation_errors(validation_errors: Dict[str, Any]) -> Dict[str, List[str]]:
    """Format Pydantic validation errors for responses."""
    field_errors = {}

    for error in validation_errors.get("detail", []):
        field = error.get("loc", ["unknown"])[-1]
        message = error.get("msg", "Validation error")

        if field not in field_errors:
            field_errors[field] = []
        field_errors[field].append(message)

    return field_errors
