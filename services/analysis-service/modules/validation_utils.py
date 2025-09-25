"""Validation Utilities for Analysis Service.

This module provides common validation patterns and data validation functions
to reduce code duplication across analysis modules.
"""

import re
from typing import Any, Dict, List, Optional, Union


def validate_analysis_type(analysis_type: str) -> Optional[str]:
    """Validate analysis type string.

    Args:
        analysis_type: Analysis type to validate

    Returns:
        Error message if invalid, None if valid
    """
    valid_types = {
        "semantic_similarity",
        "sentiment_analysis",
        "content_quality",
        "code_analysis",
        "architecture_review",
        "security_scan",
        "performance_analysis",
        "trend_analysis",
        "risk_assessment"
    }

    if analysis_type not in valid_types:
        return f"Invalid analysis type '{analysis_type}'. Must be one of: {', '.join(sorted(valid_types))}"

    return None


def validate_severity(severity: str) -> Optional[str]:
    """Validate severity level.

    Args:
        severity: Severity string to validate

    Returns:
        Error message if invalid, None if valid
    """
    valid_severities = {"critical", "high", "medium", "low", "info"}

    if severity not in valid_severities:
        return f"Invalid severity '{severity}'. Must be one of: {', '.join(sorted(valid_severities))}"

    return None


def validate_confidence(confidence: Union[int, float]) -> Optional[str]:
    """Validate confidence score.

    Args:
        confidence: Confidence value to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(confidence, (int, float)):
        return "Confidence must be a number"

    if not (0.0 <= confidence <= 1.0):
        return "Confidence must be between 0.0 and 1.0"

    return None


def validate_document_data(document_data: Dict[str, Any]) -> Optional[str]:
    """Validate basic document data structure.

    Args:
        document_data: Document data to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(document_data, dict):
        return "Document data must be a dictionary"

    required_fields = ["id", "title", "content"]
    for field in required_fields:
        if field not in document_data:
            return f"Document missing required field: {field}"

        if not document_data[field]:
            return f"Document field '{field}' cannot be empty"

    return None


def validate_analysis_config(config: Dict[str, Any]) -> Optional[str]:
    """Validate analysis configuration.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(config, dict):
        return "Configuration must be a dictionary"

    # Validate timeout if present
    if "timeout_seconds" in config:
        timeout = config["timeout_seconds"]
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return "timeout_seconds must be a positive number"

    # Validate priority if present
    if "priority" in config:
        priority = config["priority"]
        valid_priorities = {"low", "normal", "high", "urgent"}
        if priority not in valid_priorities:
            return f"Invalid priority '{priority}'. Must be one of: {', '.join(sorted(valid_priorities))}"

    return None


def validate_file_path(file_path: str) -> Optional[str]:
    """Validate file path for security.

    Args:
        file_path: File path to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not file_path:
        return "File path cannot be empty"

    # Check for directory traversal attempts
    if ".." in file_path or file_path.startswith("/"):
        return "Invalid file path: directory traversal not allowed"

    # Check for suspicious characters
    if any(char in file_path for char in ["<", ">", "|", "&", "$", "`"]):
        return "Invalid file path: contains suspicious characters"

    return None


def validate_url(url: str) -> Optional[str]:
    """Validate URL format.

    Args:
        url: URL string to validate

    Returns:
        Error message if invalid, None if valid
    """
    if not url:
        return "URL cannot be empty"

    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # path

    if not url_pattern.match(url):
        return "Invalid URL format"

    return None


def validate_list_of_strings(items: List[Any], field_name: str = "items") -> Optional[str]:
    """Validate that a list contains only strings.

    Args:
        items: List to validate
        field_name: Name of the field for error messages

    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(items, list):
        return f"{field_name} must be a list"

    for i, item in enumerate(items):
        if not isinstance(item, str):
            return f"{field_name}[{i}] must be a string, got {type(item).__name__}"
        if not item.strip():
            return f"{field_name}[{i}] cannot be empty"

    return None


def validate_numeric_range(
    value: Union[int, float],
    field_name: str,
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None
) -> Optional[str]:
    """Validate numeric value is within range.

    Args:
        value: Numeric value to validate
        field_name: Field name for error messages
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)

    Returns:
        Error message if invalid, None if valid
    """
    if not isinstance(value, (int, float)):
        return f"{field_name} must be a number"

    if min_val is not None and value < min_val:
        return f"{field_name} must be >= {min_val}"

    if max_val is not None and value > max_val:
        return f"{field_name} must be <= {max_val}"

    return None


def validate_enum_value(value: str, valid_values: set, field_name: str) -> Optional[str]:
    """Validate value is in allowed set.

    Args:
        value: Value to validate
        valid_values: Set of valid values
        field_name: Field name for error messages

    Returns:
        Error message if invalid, None if valid
    """
    if value not in valid_values:
        return f"Invalid {field_name} '{value}'. Must be one of: {', '.join(sorted(valid_values))}"

    return None
