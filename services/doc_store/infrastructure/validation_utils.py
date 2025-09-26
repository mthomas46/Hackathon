"""Common validation utilities for Doc Store infrastructure.

Reduces code duplication by providing standardized validation patterns
across infrastructure components.
"""

from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that required fields are present and not None.

    Args:
        data: Dictionary to validate
        required_fields: List of field names that must be present

    Raises:
        ValueError: If any required field is missing or None
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)

    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> None:
    """Validate that fields have the correct types.

    Args:
        data: Dictionary to validate
        field_types: Dictionary mapping field names to expected types

    Raises:
        TypeError: If any field has an incorrect type
    """
    type_errors = []
    for field, expected_type in field_types.items():
        if field in data and data[field] is not None:
            if not isinstance(data[field], expected_type):
                type_errors.append(f"{field} must be {expected_type.__name__}, got {type(data[field]).__name__}")

    if type_errors:
        raise TypeError("; ".join(type_errors))


def validate_string_length(value: str, field_name: str, min_length: int = 0, max_length: int = None) -> None:
    """Validate string length constraints.

    Args:
        value: String value to validate
        field_name: Name of the field for error messages
        min_length: Minimum allowed length (default 0)
        max_length: Maximum allowed length (default None for no limit)

    Raises:
        ValueError: If string length is invalid
    """
    if len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters long")

    if max_length is not None and len(value) > max_length:
        raise ValueError(f"{field_name} must be at most {max_length} characters long")


def validate_list_items(items: List[Any], item_validator: callable, item_name: str = "item") -> None:
    """Validate each item in a list using a validator function.

    Args:
        items: List of items to validate
        item_validator: Function to validate each item (should raise exception on invalid)
        item_name: Name for error messages

    Raises:
        Exception: If any item validation fails
    """
    for i, item in enumerate(items):
        try:
            item_validator(item)
        except Exception as e:
            raise type(e)(f"{item_name} {i}: {e}")


def validate_dict_structure(data: Dict[str, Any], expected_keys: List[str], allow_extra: bool = True) -> None:
    """Validate dictionary structure and required keys.

    Args:
        data: Dictionary to validate
        expected_keys: List of keys that must be present
        allow_extra: Whether to allow extra keys beyond expected ones

    Raises:
        ValueError: If required keys are missing or extra keys are not allowed
    """
    missing_keys = [key for key in expected_keys if key not in data]
    if missing_keys:
        raise ValueError(f"Missing required keys: {', '.join(missing_keys)}")

    if not allow_extra:
        extra_keys = [key for key in data.keys() if key not in expected_keys]
        if extra_keys:
            raise ValueError(f"Unexpected keys: {', '.join(extra_keys)}")


def sanitize_string_input(value: str, field_name: str, max_length: int = 1000) -> str:
    """Sanitize string input by trimming and validating length.

    Args:
        value: String value to sanitize
        field_name: Name of the field for error messages
        max_length: Maximum allowed length

    Returns:
        Sanitized string

    Raises:
        ValueError: If string is invalid
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    sanitized = value.strip()
    validate_string_length(sanitized, field_name, max_length=max_length)

    return sanitized


def validate_and_log_errors(func):
    """Decorator to add validation error logging to infrastructure methods.

    Catches validation errors, logs them, and re-raises.
    Should be used on infrastructure methods that perform validation.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, TypeError) as e:
            logger.warning(
                f"Validation error in {func.__name__}",
                extra={
                    "function": func.__name__,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                }
            )
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error in {func.__name__}",
                extra={
                    "function": func.__name__,
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                },
                exc_info=True
            )
            raise

    return wrapper


class ValidationHelper:
    """Helper class for common validation operations.

    Provides reusable validation methods to reduce code duplication.
    """

    @staticmethod
    def validate_document_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document creation/update request data.

        Args:
            request_data: Request data to validate

        Returns:
            Validated and sanitized data

        Raises:
            ValueError: If validation fails
        """
        required_fields = ["content"]
        validate_required_fields(request_data, required_fields)

        # Validate content
        content = sanitize_string_input(request_data["content"], "content", max_length=100000)

        # Optional metadata validation
        metadata = request_data.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be a dictionary")

        return {
            "content": content,
            "metadata": metadata,
            "correlation_id": request_data.get("correlation_id")
        }

    @staticmethod
    def validate_search_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate search request data.

        Args:
            request_data: Request data to validate

        Returns:
            Validated and sanitized data

        Raises:
            ValueError: If validation fails
        """
        query = request_data.get("query", "").strip()
        if not query:
            raise ValueError("query is required and cannot be empty")

        validate_string_length(query, "query", min_length=1, max_length=500)

        # Validate optional filters
        filters = request_data.get("filters", {})
        if not isinstance(filters, dict):
            raise ValueError("filters must be a dictionary")

        return {
            "query": query,
            "filters": filters,
            "limit": min(request_data.get("limit", 10), 100),  # Cap at 100
            "offset": max(request_data.get("offset", 0), 0)
        }

    @staticmethod
    def validate_bulk_operation_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate bulk operation request data.

        Args:
            request_data: Request data to validate

        Returns:
            Validated and sanitized data

        Raises:
            ValueError: If validation fails
        """
        operation = request_data.get("operation")
        if not operation:
            raise ValueError("operation is required")

        allowed_operations = ["create", "update", "delete", "analyze"]
        if operation not in allowed_operations:
            raise ValueError(f"operation must be one of: {', '.join(allowed_operations)}")

        documents = request_data.get("documents", [])
        if not isinstance(documents, list):
            raise ValueError("documents must be a list")

        if len(documents) > 100:
            raise ValueError("bulk operations limited to 100 documents")

        return {
            "operation": operation,
            "documents": documents,
            "options": request_data.get("options", {})
        }
