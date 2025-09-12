"""Shared utilities for orchestrator modules.

This module contains common patterns and utilities used across all orchestrator modules
to eliminate redundancy and ensure consistency.
"""

import os
from typing import Dict, Any, Optional
from services.shared.constants_new import ErrorCodes, EnvVars, ServiceNames
from services.shared.responses import create_success_response, create_error_response
from services.shared.logging import fire_and_forget


def get_orchestrator_service_client():
    """Get orchestrator service client with standardized error handling."""
    from . import get_orchestrator_client
    try:
        return get_orchestrator_client()
    except Exception as e:
        fire_and_forget("error", f"Failed to get orchestrator service client: {e}", ServiceNames.ORCHESTRATOR)
        raise


def get_service_url(service_name: str, default_url: str) -> str:
    """Get service URL with environment variable support."""
    url_env_map = {
        "reporting": EnvVars.REPORTING_URL_ENV,
        "secure_analyzer": EnvVars.SECURE_ANALYZER_URL_ENV,
        "prompt_store": EnvVars.PROMPT_STORE_URL_ENV,
        "interpreter": EnvVars.INTERPRETER_URL_ENV,
        "analysis_service": EnvVars.ANALYSIS_SERVICE_URL_ENV,
        "doc_store": EnvVars.DOC_STORE_URL_ENV,
        "source_agent": EnvVars.SOURCE_AGENT_URL_ENV,
        "memory_agent": EnvVars.MEMORY_AGENT_URL_ENV,
        "discovery_agent": EnvVars.DISCOVERY_AGENT_URL_ENV,
        "frontend": EnvVars.FRONTEND_URL_ENV,
    }
    env_var = url_env_map.get(service_name)
    return os.environ.get(env_var, default_url) if env_var else default_url


def prepare_correlation_headers(request) -> Dict[str, str]:
    """Standardized correlation header preparation."""
    if hasattr(request, 'headers'):
        correlation_id = request.headers.get(EnvVars.CORRELATION_ID_HEADER, "")
        return {EnvVars.CORRELATION_ID_HEADER: correlation_id} if correlation_id else {}
    return {}


def handle_service_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for service operations."""
    fire_and_forget("error", f"Service {operation} error: {error}", ServiceNames.ORCHESTRATOR, context)
    return create_error_response(
        f"Failed to {operation}",
        error_code=ErrorCodes.SERVICE_COMMUNICATION_FAILED,
        details={"error": str(error), **context}
    )


def create_service_success_response(operation: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response creation for service operations."""
    fire_and_forget("info", f"Service {operation} completed successfully", ServiceNames.ORCHESTRATOR, context)
    return create_success_response(
        f"Service {operation} completed successfully",
        data,
        **context
    )


def validate_request_data(data: Dict[str, Any], required_fields: list) -> Optional[str]:
    """Validate that required fields are present in request data."""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        return f"Missing required fields: {', '.join(missing_fields)}"
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


def build_orchestrator_context(operation: str, **kwargs) -> Dict[str, Any]:
    """Build standardized operation context for logging."""
    context = {"operation": operation}
    context.update(kwargs)
    return context


__all__ = [
    'get_orchestrator_service_client',
    'get_service_url',
    'prepare_correlation_headers',
    'handle_service_error',
    'create_service_success_response',
    'validate_request_data',
    'sanitize_string_input',
    'build_orchestrator_context'
]
