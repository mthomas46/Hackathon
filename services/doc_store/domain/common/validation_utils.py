"""Common validation utilities for Doc Store service.

Reduces code duplication by providing reusable validation functions
across all domain services.
"""

from typing import Any, Dict, List, Optional

from services.shared.domain.exceptions import create_validation_error


def validate_required_string(value: Any, field_name: str, max_length: Optional[int] = None) -> str:
    """Validate that a value is a non-empty string.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        max_length: Optional maximum length

    Returns:
        Stripped string value

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        raise create_validation_error(field_name, f"{field_name} is required")

    if not isinstance(value, str):
        raise create_validation_error(field_name, f"{field_name} must be a string")

    stripped = value.strip()
    if not stripped:
        raise create_validation_error(field_name, f"{field_name} cannot be empty")

    if max_length and len(stripped) > max_length:
        raise create_validation_error(
            field_name, f"{field_name} cannot exceed {max_length} characters"
        )

    return stripped


def validate_optional_string(value: Any, field_name: str, max_length: Optional[int] = None) -> Optional[str]:
    """Validate an optional string value.

    Args:
        value: Value to validate (can be None)
        field_name: Name of the field for error messages
        max_length: Optional maximum length

    Returns:
        Stripped string value or None

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        return None

    return validate_required_string(value, field_name, max_length)


def validate_metadata(metadata: Any, field_name: str = "metadata") -> Dict[str, Any]:
    """Validate metadata dictionary.

    Args:
        metadata: Metadata to validate
        field_name: Name of the field for error messages

    Returns:
        Validated metadata dictionary

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(metadata, dict):
        raise create_validation_error(field_name, f"{field_name} must be a dictionary")

    # Check size limits
    if len(metadata) > 50:
        raise create_validation_error(
            field_name, f"{field_name} cannot have more than 50 keys"
        )

    # Validate key names
    for key in metadata.keys():
        if not isinstance(key, str) or len(key) > 100:
            raise create_validation_error(
                field_name, f"{field_name} keys must be strings of 100 characters or less"
            )

    return metadata


def validate_id_format(value: Any, field_name: str = "id") -> str:
    """Validate ID format (basic alphanumeric with dashes/underscores).

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated ID string

    Raises:
        ValidationError: If validation fails
    """
    id_str = validate_required_string(value, field_name)

    # Basic ID format validation (alphanumeric, dashes, underscores)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', id_str):
        raise create_validation_error(
            field_name,
            f"{field_name} must contain only letters, numbers, dashes, and underscores"
        )

    if len(id_str) > 100:
        raise create_validation_error(field_name, f"{field_name} cannot exceed 100 characters")

    return id_str


def validate_numeric_range(
    value: Any,
    field_name: str,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None
) -> float:
    """Validate numeric value within a range.

    Args:
        value: Numeric value to validate
        field_name: Name of the field for error messages
        min_value: Optional minimum value (inclusive)
        max_value: Optional maximum value (inclusive)

    Returns:
        Validated numeric value

    Raises:
        ValidationError: If validation fails
    """
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        raise create_validation_error(field_name, f"{field_name} must be a number")

    if min_value is not None and num_value < min_value:
        raise create_validation_error(
            field_name, f"{field_name} must be at least {min_value}"
        )

    if max_value is not None and num_value > max_value:
        raise create_validation_error(
            field_name, f"{field_name} must be at most {max_value}"
        )

    return num_value


def validate_list_of_strings(
    value: Any,
    field_name: str,
    max_items: Optional[int] = None
) -> List[str]:
    """Validate a list of strings.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        max_items: Optional maximum number of items

    Returns:
        Validated list of strings

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, list):
        raise create_validation_error(field_name, f"{field_name} must be a list")

    if max_items and len(value) > max_items:
        raise create_validation_error(
            field_name, f"{field_name} cannot have more than {max_items} items"
        )

    validated_items = []
    for i, item in enumerate(value):
        try:
            validated_item = validate_required_string(item, f"{field_name}[{i}]")
            validated_items.append(validated_item)
        except Exception as e:
            raise create_validation_error(
                field_name, f"Invalid item at index {i}: {str(e)}"
            ) from e

    return validated_items


def validate_content_size(content: str, field_name: str = "content", max_size: int = 10485760) -> str:
    """Validate content size.

    Args:
        content: Content string to validate
        field_name: Name of the field for error messages
        max_size: Maximum allowed size in bytes (default 10MB)

    Returns:
        Validated content

    Raises:
        ValidationError: If content is too large
    """
    if len(content.encode('utf-8')) > max_size:
        size_mb = max_size / (1024 * 1024)
        raise create_validation_error(
            field_name, f"{field_name} exceeds maximum size of {size_mb}MB"
        )

    return content


def validate_correlation_id(value: Any, field_name: str = "correlation_id") -> Optional[str]:
    """Validate correlation ID format.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated correlation ID or None

    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        return None

    corr_id = validate_required_string(value, field_name)

    # Correlation ID should be a valid UUID or similar format
    import re
    if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', corr_id.lower()):
        # Allow simpler format for backward compatibility
        if not re.match(r'^[a-zA-Z0-9_-]{1,100}$', corr_id):
            raise create_validation_error(
                field_name,
                f"{field_name} must be a valid UUID or alphanumeric identifier"
            )

    return corr_id
