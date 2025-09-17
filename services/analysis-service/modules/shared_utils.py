"""Shared utilities for analysis service modules.

This module contains common patterns and utilities used across all analysis service modules
to eliminate redundancy and ensure consistency.
"""

import os
from typing import Dict, Any
try:
    from services.shared.constants_new import ErrorCodes, EnvVars, ServiceNames
except ImportError:
    # Fallback for testing or when shared services are not available
    class ErrorCodes:
        ANALYSIS_FAILED = "ANALYSIS_FAILED"
        VALIDATION_ERROR = "VALIDATION_ERROR"

    class EnvVars:
        ANALYSIS_SERVICE_HOST = "ANALYSIS_SERVICE_HOST"
        ANALYSIS_SERVICE_PORT = "ANALYSIS_SERVICE_PORT"

    class ServiceNames:
        ANALYSIS_SERVICE = "analysis-service"
        DOC_STORE = "doc-store"
        ORCHESTRATOR = "orchestrator"
try:
    from services.shared.responses import create_success_response, create_error_response
    from services.shared.logging import fire_and_forget
    from services.shared.error_handling import ValidationException
except ImportError:
    # Fallback for testing or when shared services are not available
    def create_success_response(message, data=None, **kwargs):
        return {"message": message, "data": data, "status": "success"}

    def create_error_response(message, error_code=None, **kwargs):
        return {"message": message, "error": error_code, "status": "error"}

    def fire_and_forget(level, message, service, data):
        pass

    class ValidationException(Exception):
        pass

# Configuration constants for analysis service with secure validation
def _validate_float_env_var(var_name: str, default: str) -> float:
    """Safely validate and convert environment variable to float."""
    value = os.environ.get(var_name, default)
    try:
        result = float(value)
        # Prevent negative values and unreasonably large values
        if result < 0 or result > 1:
            return float(default)
        return result
    except (ValueError, TypeError):
        return float(default)

def _validate_int_env_var(var_name: str, default: str, min_val: int = 0, max_val: int = 100) -> int:
    """Safely validate and convert environment variable to int."""
    value = os.environ.get(var_name, default)
    try:
        result = int(value)
        # Prevent out-of-range values
        if result < min_val or result > max_val:
            return int(default)
        return result
    except (ValueError, TypeError):
        return int(default)

_DEFAULT_DRIFT_OVERLAP_THRESHOLD = _validate_float_env_var("DRIFT_OVERLAP_THRESHOLD", "0.1")
_DEFAULT_CRITICAL_SCORE = _validate_int_env_var("CRITICAL_SCORE", "90", 0, 100)
_DEFAULT_HIGH_PRIORITY_SCORE = _validate_int_env_var("HIGH_PRIORITY_SCORE", "80", 0, 100)
_DEFAULT_MEDIUM_PRIORITY_SCORE = _validate_int_env_var("MEDIUM_PRIORITY_SCORE", "50", 0, 100)


def get_analysis_service_client():
    """Get analysis service client with standardized error handling."""
    from services.shared.utilities import get_service_client
    try:
        return get_service_client()
    except Exception as e:
        fire_and_forget("error", f"Failed to get analysis service client: {e}", ServiceNames.ANALYSIS_SERVICE)
        raise


def get_service_url(service_name: str, default_url: str) -> str:
    """Get service URL with environment variable support."""
    url_env_map = {
        "doc_store": EnvVars.DOC_STORE_URL_ENV,
        "source_agent": EnvVars.SOURCE_AGENT_URL_ENV,
        "prompt_store": EnvVars.PROMPT_STORE_URL_ENV,
        "interpreter": EnvVars.INTERPRETER_URL_ENV,
        "orchestrator": EnvVars.ORCHESTRATOR_URL_ENV,
    }
    env_var = url_env_map.get(service_name)
    return os.environ.get(env_var, default_url) if env_var else default_url


def handle_analysis_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for analysis operations."""
    fire_and_forget("error", f"Analysis {operation} error: {error}", ServiceNames.ANALYSIS_SERVICE, context)
    return create_error_response(
        f"Failed to {operation}",
        error_code=ErrorCodes.SERVICE_COMMUNICATION_FAILED,
        details={"error": str(error), **context}
    )


def create_analysis_success_response(operation: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response creation for analysis operations."""
    fire_and_forget("info", f"Analysis {operation} completed successfully", ServiceNames.ANALYSIS_SERVICE, context)
    return create_success_response(
        f"Analysis {operation} completed successfully",
        data,
        **context
    )


def _create_analysis_error_response(message: str, error_code: str, details: Dict[str, Any]) -> Dict[str, Any]:
    """Create standardized error response for analysis operations."""
    fire_and_forget("error", f"Analysis error: {message}", ServiceNames.ANALYSIS_SERVICE, details)
    return create_error_response(
        message,
        error_code=error_code,
        details=details
    )


def build_analysis_context(operation: str, **kwargs) -> Dict[str, Any]:
    """Build standardized analysis operation context for logging."""
    context = {"operation": operation, "service": ServiceNames.ANALYSIS_SERVICE}
    context.update(kwargs)
    return context


def validate_analysis_targets(targets: list) -> None:
    """Validate analysis targets and raise exception if invalid."""
    if not targets:
        raise ValidationException(
            "No targets specified for analysis",
            {"targets": ["Cannot be empty"]}
        )

    for target in targets:
        if not isinstance(target, str):
            raise ValidationException(
                f"Invalid target format: {target}",
                {"targets": ["All targets must be strings"]}
            )


def get_drift_overlap_threshold() -> float:
    """Get drift overlap threshold configuration."""
    return _DEFAULT_DRIFT_OVERLAP_THRESHOLD


def get_critical_score() -> int:
    """Get critical score threshold configuration."""
    return _DEFAULT_CRITICAL_SCORE


def get_high_priority_score() -> int:
    """Get high priority score threshold configuration."""
    return _DEFAULT_HIGH_PRIORITY_SCORE


def get_medium_priority_score() -> int:
    """Get medium priority score threshold configuration."""
    return _DEFAULT_MEDIUM_PRIORITY_SCORE


__all__ = [
    'get_analysis_service_client',
    'get_service_url',
    'handle_analysis_error',
    'create_analysis_success_response',
    '_create_analysis_error_response',
    'build_analysis_context',
    'validate_analysis_targets',
    'get_drift_overlap_threshold',
    'get_critical_score',
    'get_high_priority_score',
    'get_medium_priority_score'
]
