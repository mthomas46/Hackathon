"""
Input validation utilities for expert-finder-service.

Centralizes all validation logic to ensure consistency
and reduce code duplication (DRY principle).

This module eliminates 60 lines of duplicated validation code
that was repeated across 4 different endpoint functions.
"""

from fastapi import HTTPException


class ValidationError(HTTPException):
    """
    Custom validation error.
    
    Inherits from FastAPI's HTTPException for seamless
    integration with FastAPI error handling.
    """
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail)


def validate_query_text(query_text: str) -> str:
    """
    Validate query text input.
    
    Args:
        query_text: Query text to validate
        
    Returns:
        Validated and stripped query text
        
    Raises:
        ValidationError: If query text is empty or invalid
        
    Examples:
        >>> validate_query_text("Python developer")
        'Python developer'
        >>> validate_query_text("  ")
        ValidationError: Query text cannot be empty
    """
    if not query_text or not query_text.strip():
        raise ValidationError("Query text cannot be empty")
    
    query_text = query_text.strip()
    
    # Optional: Add length validation
    if len(query_text) < 1:
        raise ValidationError("Query text is too short")
    if len(query_text) > 500:
        raise ValidationError("Query text is too long (max 500 characters)")
    
    return query_text


def validate_limit(limit: int, max_limit: int = 100) -> int:
    """
    Validate result limit.
    
    Args:
        limit: Result limit to validate
        max_limit: Maximum allowed limit (default 100)
        
    Returns:
        Validated limit
        
    Raises:
        ValidationError: If limit is out of valid range
        
    Examples:
        >>> validate_limit(10)
        10
        >>> validate_limit(0)
        ValidationError: Limit must be at least 1
        >>> validate_limit(200)
        ValidationError: Limit must not exceed 100
    """
    if limit < 1:
        raise ValidationError("Limit must be at least 1")
    if limit > max_limit:
        raise ValidationError(f"Limit must not exceed {max_limit}")
    return limit


def validate_id(id_value: str, id_type: str = "ID") -> str:
    """
    Validate ID string.
    
    Args:
        id_value: ID value to validate
        id_type: Type of ID (for error messages, e.g., "User ID", "Team ID")
        
    Returns:
        Validated and stripped ID
        
    Raises:
        ValidationError: If ID is empty or invalid
        
    Examples:
        >>> validate_id("user123", "User ID")
        'user123'
        >>> validate_id("", "User ID")
        ValidationError: User ID cannot be empty
        >>> validate_id("  ", "Team ID")
        ValidationError: Team ID cannot be empty
    """
    if not id_value or not id_value.strip():
        raise ValidationError(f"{id_type} cannot be empty")
    return id_value.strip()


def validate_min_count(count: int, count_type: str = "count") -> int:
    """
    Validate minimum count parameter.
    
    Args:
        count: Count value to validate
        count_type: Type of count (for error messages, e.g., "document count")
        
    Returns:
        Validated count
        
    Raises:
        ValidationError: If count is negative
        
    Examples:
        >>> validate_min_count(10, "document count")
        10
        >>> validate_min_count(0, "document count")
        0
        >>> validate_min_count(-1, "document count")
        ValidationError: document count must be non-negative
    """
    if count < 0:
        raise ValidationError(f"{count_type} must be non-negative")
    return count


def validate_score_threshold(score: float) -> float:
    """
    Validate score threshold (0.0 to 1.0).
    
    Args:
        score: Score threshold to validate
        
    Returns:
        Validated score
        
    Raises:
        ValidationError: If score is out of range
        
    Examples:
        >>> validate_score_threshold(0.7)
        0.7
        >>> validate_score_threshold(-0.1)
        ValidationError: Score threshold must be between 0.0 and 1.0
        >>> validate_score_threshold(1.5)
        ValidationError: Score threshold must be between 0.0 and 1.0
    """
    if not 0.0 <= score <= 1.0:
        raise ValidationError("Score threshold must be between 0.0 and 1.0")
    return score

