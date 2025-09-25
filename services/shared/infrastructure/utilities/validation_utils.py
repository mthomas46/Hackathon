"""Common Validation Utilities

Reduces code duplication by providing standardized validation patterns
used throughout the shared service and ecosystem.

This module provides:
- Field validation utilities
- Data structure validation
- Business rule validation
- Input sanitization
- Configuration validation
"""

import re
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timezone

from .error_handling import ServiceException


# ============================================================================
# FIELD VALIDATION UTILITIES (REDUCING DUPLICATION)
# ============================================================================

def validate_required_fields(data: Dict[str, Any], required_fields: List[str],
                           field_name: str = "data") -> None:
    """Validate that required fields are present in data.

    Common pattern used across services for input validation.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        field_name: Name of the data structure for error messages

    Raises:
        ServiceException: If required fields are missing
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        raise ServiceException(
            f"Missing required fields in {field_name}: {', '.join(missing_fields)}",
            "validation_error",
            400,
            {"missing_fields": missing_fields}
        )

def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type],
                        field_name: str = "data") -> None:
    """Validate that fields have correct types.

    Common pattern for type validation across services.

    Args:
        data: Data dictionary to validate
        field_types: Dictionary mapping field names to expected types
        field_name: Name of the data structure for error messages

    Raises:
        ServiceException: If field types don't match
    """
    type_errors = []
    for field, expected_type in field_types.items():
        if field in data:
            value = data[field]
            if not isinstance(value, expected_type):
                type_errors.append(f"{field}: expected {expected_type.__name__}, got {type(value).__name__}")

    if type_errors:
        raise ServiceException(
            f"Type validation failed in {field_name}: {'; '.join(type_errors)}",
            "validation_error",
            400,
            {"type_errors": type_errors}
        )

def validate_string_length(value: str, field_name: str, min_length: int = None,
                          max_length: int = None) -> None:
    """Validate string length constraints.

    Common pattern for string validation.

    Args:
        value: String value to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length (optional)
        max_length: Maximum allowed length (optional)

    Raises:
        ServiceException: If length constraints are violated
    """
    if not isinstance(value, str):
        raise ServiceException(
            f"Field {field_name} must be a string",
            "validation_error",
            400
        )

    length = len(value)

    if min_length is not None and length < min_length:
        raise ServiceException(
            f"Field {field_name} must be at least {min_length} characters long",
            "validation_error",
            400,
            {"field": field_name, "min_length": min_length, "actual_length": length}
        )

    if max_length is not None and length > max_length:
        raise ServiceException(
            f"Field {field_name} must be at most {max_length} characters long",
            "validation_error",
            400,
            {"field": field_name, "max_length": max_length, "actual_length": length}
        )

def validate_numeric_range(value: Union[int, float], field_name: str,
                          min_value: Union[int, float] = None,
                          max_value: Union[int, float] = None) -> None:
    """Validate numeric value ranges.

    Common pattern for numeric validation.

    Args:
        value: Numeric value to validate
        field_name: Name of the field for error messages
        min_value: Minimum allowed value (optional)
        max_value: Maximum allowed value (optional)

    Raises:
        ServiceException: If range constraints are violated
    """
    if not isinstance(value, (int, float)):
        raise ServiceException(
            f"Field {field_name} must be a number",
            "validation_error",
            400
        )

    if min_value is not None and value < min_value:
        raise ServiceException(
            f"Field {field_name} must be at least {min_value}",
            "validation_error",
            400,
            {"field": field_name, "min_value": min_value, "actual_value": value}
        )

    if max_value is not None and value > max_value:
        raise ServiceException(
            f"Field {field_name} must be at most {max_value}",
            "validation_error",
            400,
            {"field": field_name, "max_value": max_value, "actual_value": value}
        )


# ============================================================================
# DATA STRUCTURE VALIDATION (REDUCING DUPLICATION)
# ============================================================================

def validate_list_items(items: List[Any], item_validator: Callable,
                       list_name: str = "list") -> None:
    """Validate each item in a list using a validator function.

    Common pattern for validating lists of items.

    Args:
        items: List of items to validate
        item_validator: Function to validate each item
        list_name: Name of the list for error messages

    Raises:
        ServiceException: If any item validation fails
    """
    validation_errors = []

    for i, item in enumerate(items):
        try:
            item_validator(item)
        except ServiceException as e:
            validation_errors.append(f"Item {i}: {e.message}")
        except Exception as e:
            validation_errors.append(f"Item {i}: {str(e)}")

    if validation_errors:
        raise ServiceException(
            f"Validation failed for {list_name}: {'; '.join(validation_errors)}",
            "validation_error",
            400,
            {"item_errors": validation_errors}
        )

def validate_dict_structure(data: Dict[str, Any], required_keys: List[str],
                           allowed_keys: List[str] = None,
                           dict_name: str = "dictionary") -> None:
    """Validate dictionary structure and keys.

    Common pattern for validating dictionary structures.

    Args:
        data: Dictionary to validate
        required_keys: Keys that must be present
        allowed_keys: Keys that are allowed (None = any key allowed)
        dict_name: Name of the dictionary for error messages

    Raises:
        ServiceException: If structure validation fails
    """
    errors = []

    # Check required keys
    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        errors.append(f"Missing required keys: {', '.join(missing_keys)}")

    # Check allowed keys
    if allowed_keys is not None:
        extra_keys = [key for key in data.keys() if key not in allowed_keys]
        if extra_keys:
            errors.append(f"Unexpected keys: {', '.join(extra_keys)}")

    if errors:
        raise ServiceException(
            f"Dictionary structure validation failed for {dict_name}: {'; '.join(errors)}",
            "validation_error",
            400,
            {"validation_errors": errors}
        )


# ============================================================================
# BUSINESS RULE VALIDATION (REDUCING DUPLICATION)
# ============================================================================

def validate_unique_values(items: List[Any], field_getter: Callable = None,
                          collection_name: str = "collection") -> None:
    """Validate that all items in a collection are unique.

    Common pattern for uniqueness validation.

    Args:
        items: List of items to check for uniqueness
        field_getter: Function to extract comparison value from each item (optional)
        collection_name: Name of the collection for error messages

    Raises:
        ServiceException: If duplicate values are found
    """
    seen = set()
    duplicates = []

    for item in items:
        value = field_getter(item) if field_getter else item

        if value in seen:
            duplicates.append(str(value))
        else:
            seen.add(value)

    if duplicates:
        raise ServiceException(
            f"Duplicate values found in {collection_name}: {', '.join(duplicates)}",
            "validation_error",
            400,
            {"duplicates": duplicates}
        )

def validate_date_range(start_date: datetime, end_date: datetime,
                       field_name: str = "date_range") -> None:
    """Validate that start date is before end date.

    Common pattern for date range validation.

    Args:
        start_date: Start date
        end_date: End date
        field_name: Name of the date range for error messages

    Raises:
        ServiceException: If date range is invalid
    """
    if start_date >= end_date:
        raise ServiceException(
            f"Invalid {field_name}: start date must be before end date",
            "validation_error",
            400,
            {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )


# ============================================================================
# INPUT SANITIZATION (REDUCING DUPLICATION)
# ============================================================================

def sanitize_string(input_str: str, max_length: int = 1000,
                   allow_newlines: bool = False) -> str:
    """Sanitize string input by removing potentially harmful content.

    Common pattern for input sanitization across services.

    Args:
        input_str: String to sanitize
        max_length: Maximum allowed length
        allow_newlines: Whether to preserve newlines

    Returns:
        Sanitized string

    Raises:
        ServiceException: If input is invalid or too long
    """
    if not isinstance(input_str, str):
        raise ServiceException(
            "Input must be a string",
            "validation_error",
            400
        )

    # Remove null bytes and other control characters
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', input_str)

    # Handle newlines
    if not allow_newlines:
        sanitized = sanitized.replace('\n', ' ').replace('\r', ' ')

    # Trim whitespace
    sanitized = sanitized.strip()

    # Check length
    if len(sanitized) > max_length:
        raise ServiceException(
            f"Input exceeds maximum length of {max_length} characters",
            "validation_error",
            400,
            {"max_length": max_length, "actual_length": len(sanitized)}
        )

    return sanitized

def validate_email_format(email: str, field_name: str = "email") -> None:
    """Validate email address format.

    Common pattern for email validation.

    Args:
        email: Email address to validate
        field_name: Name of the field for error messages

    Raises:
        ServiceException: If email format is invalid
    """
    email_pattern = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    if not email_pattern.match(email):
        raise ServiceException(
            f"Invalid {field_name} format",
            "validation_error",
            400,
            {"field": field_name, "provided_value": email}
        )


# ============================================================================
# CONFIGURATION VALIDATION (REDUCING DUPLICATION)
# ============================================================================

def validate_service_config(config: Dict[str, Any], service_name: str) -> None:
    """Validate service configuration structure.

    Common pattern for service configuration validation.

    Args:
        config: Configuration dictionary
        service_name: Name of the service for error messages

    Raises:
        ServiceException: If configuration is invalid
    """
    required_config_keys = ["service_name", "version", "environment"]

    validate_required_fields(config, required_config_keys, f"{service_name} config")
    validate_field_types(config, {
        "service_name": str,
        "version": str,
        "environment": str
    }, f"{service_name} config")

    # Validate version format (basic semantic versioning check)
    version = config.get("version", "")
    if not re.match(r'^\d+\.\d+\.\d+', version):
        raise ServiceException(
            f"Invalid version format for {service_name}: {version}",
            "validation_error",
            400,
            {"service": service_name, "version": version}
        )

def validate_port_number(port: Union[int, str], field_name: str = "port") -> int:
    """Validate and convert port number.

    Common pattern for port validation across services.

    Args:
        port: Port number to validate
        field_name: Name of the field for error messages

    Returns:
        Validated port number as integer

    Raises:
        ServiceException: If port is invalid
    """
    try:
        port_num = int(port)
    except (ValueError, TypeError):
        raise ServiceException(
            f"Invalid {field_name}: must be a valid port number",
            "validation_error",
            400,
            {"field": field_name, "provided_value": port}
        )

    if not (1 <= port_num <= 65535):
        raise ServiceException(
            f"Invalid {field_name}: must be between 1 and 65535",
            "validation_error",
            400,
            {"field": field_name, "provided_value": port_num}
        )

    return port_num
