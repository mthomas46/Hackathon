"""Common HTTP models for pagination, filtering, and search."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Filter operator enumeration."""
    EQ = "eq"           # equals
    NE = "ne"           # not equals
    GT = "gt"           # greater than
    GTE = "gte"         # greater than or equal
    LT = "lt"           # less than
    LTE = "lte"         # less than or equal
    IN = "in"           # in list
    NIN = "nin"         # not in list
    CONTAINS = "contains"  # string contains
    STARTS_WITH = "starts_with"  # string starts with
    ENDS_WITH = "ends_with"     # string ends with


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""

    page: int = Field(1, ge=1, description="Page number (1-based)")
    page_size: int = Field(20, ge=1, le=100, description="Items per page (max 100)")
    offset: Optional[int] = Field(None, ge=0, description="Offset for pagination (alternative to page)")

    @validator('offset', always=True)
    def calculate_offset(cls, v, values):
        """Calculate offset from page and page_size if not provided."""
        if v is None and 'page' in values and 'page_size' in values:
            return (values['page'] - 1) * values['page_size']
        return v


class SortParams(BaseModel):
    """Sorting parameters."""

    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: SortOrder = Field(SortOrder.ASC, description="Sort order")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort field name."""
        if v and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Invalid sort field name")
        return v


class FilterCriteria(BaseModel):
    """Individual filter criteria."""

    field: str = Field(..., description="Field to filter on")
    operator: FilterOperator = Field(..., description="Filter operator")
    value: Any = Field(..., description="Filter value")

    @validator('value')
    def validate_value(cls, v, values):
        """Validate filter value based on operator."""
        if 'operator' in values:
            operator = values['operator']
            if operator in [FilterOperator.IN, FilterOperator.NIN] and not isinstance(v, list):
                raise ValueError(f"Operator {operator} requires a list value")
            elif operator in [FilterOperator.CONTAINS, FilterOperator.STARTS_WITH, FilterOperator.ENDS_WITH]:
                if not isinstance(v, str):
                    raise ValueError(f"Operator {operator} requires a string value")
        return v


class FilterParams(BaseModel):
    """Filtering parameters for list endpoints."""

    filters: Optional[List[FilterCriteria]] = Field(None, description="List of filter criteria")
    filter_preset: Optional[str] = Field(None, description="Predefined filter preset")


class SearchParams(BaseModel):
    """Search parameters for text-based search."""

    query: str = Field(..., min_length=1, max_length=255, description="Search query")
    fields: Optional[List[str]] = Field(None, description="Fields to search in")
    fuzzy: bool = Field(False, description="Enable fuzzy search")
    case_sensitive: bool = Field(False, description="Case sensitive search")


class ListQueryParams(PaginationParams, SortParams, FilterParams, SearchParams):
    """Combined parameters for list endpoints with search, filter, sort, and pagination."""

    include_metadata: bool = Field(False, description="Include metadata in response")
    include_related: bool = Field(False, description="Include related entities")


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations."""

    operation: str = Field(..., description="Operation to perform")
    items: List[Dict[str, Any]] = Field(..., description="Items to process")
    options: Optional[Dict[str, Any]] = Field(None, description="Operation-specific options")

    @validator('operation')
    def validate_operation(cls, v):
        """Validate operation name."""
        valid_operations = [
            'create', 'update', 'delete', 'analyze', 'export',
            'import', 'validate', 'process', 'archive'
        ]
        if v not in valid_operations:
            raise ValueError(f"Invalid operation: {v}. Must be one of {valid_operations}")
        return v

    @validator('items')
    def validate_items(cls, v):
        """Validate items list."""
        if not v:
            raise ValueError("Items list cannot be empty")
        if len(v) > 1000:
            raise ValueError("Maximum 1000 items allowed in bulk operation")
        return v


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations."""

    operation: str = Field(..., description="Operation performed")
    total_items: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Number of successful operations")
    failed: int = Field(..., description="Number of failed operations")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Error details for failed operations")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="Operation results")


class ExportRequest(BaseModel):
    """Request model for data export."""

    format: str = Field(..., description="Export format (json, csv, xml, etc.)")
    fields: Optional[List[str]] = Field(None, description="Fields to include in export")
    filters: Optional[List[FilterCriteria]] = Field(None, description="Filters to apply")
    include_headers: bool = Field(True, description="Include headers in export")

    @validator('format')
    def validate_format(cls, v):
        """Validate export format."""
        valid_formats = ['json', 'csv', 'xml', 'xlsx', 'pdf']
        if v not in valid_formats:
            raise ValueError(f"Invalid format: {v}. Must be one of {valid_formats}")
        return v


class ExportResponse(BaseModel):
    """Response model for data export."""

    export_id: str = Field(..., description="Unique export identifier")
    format: str = Field(..., description="Export format")
    total_records: int = Field(..., description="Total records exported")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL for exported file")
    expires_at: Optional[str] = Field(None, description="Export expiration timestamp")


class ValidationResult(BaseModel):
    """Validation result model."""

    valid: bool = Field(..., description="Whether validation passed")
    errors: Optional[List[str]] = Field(None, description="Validation error messages")
    warnings: Optional[List[str]] = Field(None, description="Validation warnings")
    score: Optional[float] = Field(None, description="Validation score (0-1)")

    @validator('score')
    def validate_score(cls, v):
        """Validate score range."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError("Score must be between 0 and 1")
        return v
