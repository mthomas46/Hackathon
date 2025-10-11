"""
Pagination utilities for API endpoints.

Provides standardized pagination with safety limits to prevent database overload.
"""

from typing import Generic, List, TypeVar
from pydantic import BaseModel, Field

from .exceptions import ValidationError


# Pagination limits
MAX_LIMIT = 500  # Maximum items per page
DEFAULT_LIMIT = 50  # Default items per page
MAX_OFFSET = 10_000  # Maximum offset (prevents deep pagination attacks)


T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Standardized pagination parameters.
    
    Validates pagination inputs to prevent database overload.
    """
    limit: int = Field(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description=f"Items per page (max {MAX_LIMIT})")
    offset: int = Field(0, ge=0, le=MAX_OFFSET, description=f"Pagination offset (max {MAX_OFFSET})")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "limit": 50,
                "offset": 0
            }
        }


class PageInfo(BaseModel):
    """
    Pagination metadata for responses.
    
    Provides information about the current page and navigation.
    """
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current offset")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")
    next_offset: int | None = Field(None, description="Offset for next page")
    previous_offset: int | None = Field(None, description="Offset for previous page")
    
    @classmethod
    def from_params(cls, total: int, limit: int, offset: int) -> "PageInfo":
        """
        Create PageInfo from query parameters.
        
        Args:
            total: Total number of items
            limit: Items per page
            offset: Current offset
        
        Returns:
            PageInfo with navigation metadata
        """
        has_next = (offset + limit) < total
        has_previous = offset > 0
        
        next_offset = None
        if has_next:
            next_offset = min(offset + limit, MAX_OFFSET)
        
        previous_offset = None
        if has_previous:
            previous_offset = max(offset - limit, 0)
        
        return cls(
            total=total,
            limit=limit,
            offset=offset,
            has_next=has_next,
            has_previous=has_previous,
            next_offset=next_offset,
            previous_offset=previous_offset
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic paginated response model.
    
    Wraps a list of results with pagination metadata.
    """
    data: List[T] = Field(..., description="Page of results")
    page_info: PageInfo = Field(..., description="Pagination metadata")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "data": [
                    {"id": "123", "name": "Example"}
                ],
                "page_info": {
                    "total": 100,
                    "limit": 50,
                    "offset": 0,
                    "has_next": True,
                    "has_previous": False,
                    "next_offset": 50,
                    "previous_offset": None
                }
            }
        }


def validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    """
    Validate and clamp pagination parameters.
    
    Args:
        limit: Requested items per page
        offset: Requested offset
    
    Returns:
        Tuple of (validated_limit, validated_offset)
    
    Raises:
        ValidationError: If parameters are invalid
    """
    if limit < 1:
        raise ValidationError("Limit must be at least 1")
    
    if limit > MAX_LIMIT:
        raise ValidationError(f"Limit cannot exceed {MAX_LIMIT}")
    
    if offset < 0:
        raise ValidationError("Offset cannot be negative")
    
    if offset > MAX_OFFSET:
        raise ValidationError(
            f"Offset cannot exceed {MAX_OFFSET} (use alternative navigation for deep pagination)"
        )
    
    return limit, offset


def calculate_page_number(offset: int, limit: int) -> int:
    """
    Calculate current page number from offset and limit.
    
    Args:
        offset: Current offset
        limit: Items per page
    
    Returns:
        Current page number (1-indexed)
    
    Examples:
        >>> calculate_page_number(0, 50)
        1
        >>> calculate_page_number(50, 50)
        2
        >>> calculate_page_number(25, 50)
        1
    """
    if limit <= 0:
        return 1
    return (offset // limit) + 1


def calculate_total_pages(total: int, limit: int) -> int:
    """
    Calculate total number of pages.
    
    Args:
        total: Total number of items
        limit: Items per page
    
    Returns:
        Total number of pages
    
    Examples:
        >>> calculate_total_pages(100, 50)
        2
        >>> calculate_total_pages(125, 50)
        3
        >>> calculate_total_pages(0, 50)
        0
    """
    if limit <= 0 or total <= 0:
        return 0
    return (total + limit - 1) // limit  # Ceiling division

