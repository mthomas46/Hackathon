"""Shared utilities for Summarizer Hub service modules.

This module contains common utilities used across all summarizer-hub modules
to eliminate code duplication and ensure consistency.
"""

import os
from typing import Any, Dict, List, Optional

from services.shared.presentation.responses import (
    create_error_response,
    create_success_response,
)
from services.shared.monitoring.logging import fire_and_forget
from services.shared.utilities.error_handling import ServiceException

# Global configuration for summarizer hub service
_DEFAULT_TIMEOUT = int(os.environ.get("SUMMARIZER_TIMEOUT", "60"))
_MAX_SUMMARY_LENGTH = int(os.environ.get("MAX_SUMMARY_LENGTH", "2000"))
_SUPAPI_PORTED_PROVIDERS = ["ollama", "openai", "anthropic", "grok", "bedrock"]


def get_default_timeout() -> int:
    """Get default summarization timeout in seconds."""
    return _DEFAULT_TIMEOUT


def get_max_summary_length() -> int:
    """Get maximum allowed summary length."""
    return _MAX_SUMMARY_LENGTH


def get_supported_providers() -> List[str]:
    """Get list of supported summarization providers."""
    return _SUPAPI_PORTED_PROVIDERS.copy()


def validate_provider_name(provider_name: str) -> str:
    """Validate and normalize provider name.

    Args:
        provider_name: Provider name to validate

    Returns:
        Normalized provider name

    Raises:
        ValueError: If provider is not supported
    """
    normalized = provider_name.lower().strip()
    if normalized not in _SUPAPI_PORTED_PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider_name}. Supported: {_SUPAPI_PORTED_PROVIDERS}")
    return normalized


def handle_summarizer_error(
    operation: str, error: Exception, **context
) -> Dict[str, Any]:
    """Standardized error handling for summarizer operations.

    Logs the error and returns a standardized error response.
    """
    fire_and_forget(
        "error",
        f"Summarizer operation '{operation}' failed: {str(error)}",
        "summarizer-hub",
        {"operation": operation, "error_type": type(error).__name__, **context}
    )

    return create_error_response(
        message=f"Summarization operation '{operation}' failed",
        error_code="SUMMARIZATION_ERROR",
        details=str(error)
    )


def create_summarizer_success_response(
    data: Any,
    message: str = "Summarization completed successfully",
    execution_time: Optional[float] = None,
    **additional_fields
) -> Dict[str, Any]:
    """Create standardized success response for summarizer operations.

    Args:
        data: Response data
        message: Success message
        execution_time: Operation execution time in seconds
        **additional_fields: Additional response fields

    Returns:
        Standardized success response
    """
    response = create_success_response(
        message=message,
        data=data,
        **additional_fields
    )

    if execution_time is not None:
        response["execution_time_seconds"] = round(execution_time, 3)

    return response


def validate_summary_request(text: str, provider: str) -> None:
    """Validate summarization request parameters.

    Args:
        text: Text to summarize
        provider: Provider name

    Raises:
        ValueError: If validation fails
    """
    if not text or not text.strip():
        raise ValueError("Text to summarize cannot be empty")

    if len(text.strip()) < 10:
        raise ValueError("Text to summarize must be at least 10 characters")

    if len(text.strip()) > 50000:  # 50KB limit
        raise ValueError("Text to summarize cannot exceed 50,000 characters")

    validate_provider_name(provider)


def sanitize_summary_output(summary: str) -> str:
    """Sanitize and clean summary output.

    Args:
        summary: Raw summary text

    Returns:
        Cleaned summary text
    """
    if not summary:
        return ""

    # Remove excessive whitespace
    summary = " ".join(summary.split())

    # Truncate if too long
    max_length = get_max_summary_length()
    if len(summary) > max_length:
        summary = summary[:max_length - 3] + "..."

    return summary.strip()
