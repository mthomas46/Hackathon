"""Domain Utilities

Utility functions for domain logic that are shared across bounded contexts.
These functions handle common domain operations like validation and data processing.
"""

from typing import Dict, Any, Optional, List


def validate_request_data(data: Dict[str, Any], required_fields: list) -> Optional[str]:
    """Validate that required fields are present in request data."""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
    return None


def validate_string_length(value: str, min_length: int = 0, max_length: int = 1000) -> Optional[str]:
    """Validate string length constraints."""
    if len(value) < min_length:
        return f"String too short (minimum {min_length} characters)"
    if len(value) > max_length:
        return f"String too long (maximum {max_length} characters)"
    return None


def validate_numeric_range(value: float, min_value: Optional[float] = None, max_value: Optional[float] = None) -> Optional[str]:
    """Validate numeric value is within acceptable range."""
    if min_value is not None and value < min_value:
        return f"Value too small (minimum {min_value})"
    if max_value is not None and value > max_value:
        return f"Value too large (maximum {max_value})"
    return None


def validate_list_length(items: List, min_length: int = 0, max_length: int = 1000) -> Optional[str]:
    """Validate list length constraints."""
    if len(items) < min_length:
        return f"List too short (minimum {min_length} items)"
    if len(items) > max_length:
        return f"List too long (maximum {max_length} items)"
    return None


def sanitize_string_input(input_str: str, max_length: int = 1000) -> str:
    """Sanitize string input to prevent injection attacks and XSS."""
    if not isinstance(input_str, str):
        return ""

    # Remove potentially dangerous characters
    import re
    # Remove null bytes and other control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)
    # Remove potential script injection patterns
    sanitized = re.sub(r'[<>\"\'`]', '', sanitized)

    return sanitized.strip()[:max_length]


__all__ = [
    'validate_request_data',
    'validate_string_length',
    'validate_numeric_range',
    'validate_list_length',
    'sanitize_string_input'
]
