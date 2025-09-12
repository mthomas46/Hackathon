"""Shared utilities for Frontend service modules.

This module contains common utilities used across all frontend modules
to eliminate code duplication and ensure consistency.
"""

import os
from typing import Dict, Any, Optional, List
from fastapi.responses import HTMLResponse

# Import shared utilities
from services.shared.clients import ServiceClients
from services.shared.constants_new import EnvVars, ErrorCodes, ServiceNames
from services.shared.error_handling import ServiceException
from services.shared.responses import create_error_response
from services.shared.logging import fire_and_forget
from services.shared.utilities import utc_now
from services.shared.config import get_config_value

# Global configuration for frontend service
_DEFAULT_TIMEOUT = 30
_REPORTING_URL_ENV = EnvVars.REPORTING_URL_ENV
_DOC_STORE_URL_ENV = EnvVars.DOC_STORE_URL_ENV
_CONSISTENCY_ENGINE_URL_ENV = EnvVars.CONSISTENCY_ENGINE_URL_ENV

def get_default_timeout() -> int:
    """Get default service client timeout."""
    return _DEFAULT_TIMEOUT

def get_reporting_url() -> str:
    """Get reporting service URL from config/env with fallback."""
    return get_config_value("REPORTING_URL", "http://reporting:5030", section="services", env_key=_REPORTING_URL_ENV)

def get_doc_store_url() -> str:
    """Get doc store service URL from config/env with fallback."""
    return get_config_value("DOC_STORE_URL", "http://doc-store:5010", section="services", env_key=_DOC_STORE_URL_ENV)

def get_consistency_engine_url() -> str:
    """Get consistency engine service URL from config/env with fallback."""
    return get_config_value("CONSISTENCY_ENGINE_URL", "http://consistency-engine:5020", section="services", env_key=_CONSISTENCY_ENGINE_URL_ENV)

def get_frontend_clients(timeout: int = _DEFAULT_TIMEOUT) -> ServiceClients:
    """Create and return a ServiceClients instance with proper timeout."""
    return ServiceClients(timeout=timeout)

def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent XSS and injection attacks."""
    import html
    import re

    if not input_str:
        return input_str

    # Escape HTML characters
    sanitized = html.escape(input_str)

    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',                # JavaScript URLs
        r'vbscript:',                  # VBScript URLs
        r'data:',                      # Data URLs
        r'../../../',                  # Path traversal
        r'..\\..\\',                   # Windows path traversal
        r'\${.*}',                     # Environment variable expansion
        r'`.*`',                       # Command injection
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)

    return sanitized


def create_html_response(content: str, title: str = "LLM Documentation Ecosystem") -> HTMLResponse:
    """Create a standardized HTML response with consistent styling and XSS protection."""
    import html

    # Escape user input to prevent XSS attacks
    safe_title = html.escape(title)
    safe_content = html.escape(content)

    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{safe_title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .header {{ background-color: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
            .content {{ background-color: white; padding: 20px; margin: 20px 0; border-radius: 5px; }}
            .metric {{ background-color: #ecf0f1; padding: 10px; margin: 10px 0; border-radius: 3px; }}
            .error {{ color: #e74c3c; }}
            .success {{ color: #27ae60; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {safe_content}
    </body>
    </html>
    """
    return HTMLResponse(content=html_template, status_code=200)

def handle_frontend_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for frontend operations.

    Logs the error and returns a standardized error response.
    """
    fire_and_forget("error", f"Frontend {operation} error: {error}", ServiceNames.FRONTEND, context)
    return create_error_response(
        f"Failed to {operation}",
        error_code=ErrorCodes.INTERNAL_ERROR,
        details={"error": str(error), **context}
    )

def create_frontend_success_response(operation: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response for frontend operations.

    Returns a consistent success response format.
    """
    from services.shared.responses import create_success_response
    return create_success_response(f"Frontend {operation} successful", data, **context)

def build_frontend_context(operation: str, **additional) -> Dict[str, Any]:
    """Build context dictionary for frontend operations.

    Provides consistent context for logging and responses.
    """
    context = {
        "operation": operation,
        "service": ServiceNames.FRONTEND
    }
    context.update(additional)
    return context

def fetch_service_data(service_name: str, endpoint: str, params: Optional[Dict[str, Any]] = None, clients: Optional[ServiceClients] = None) -> Dict[str, Any]:
    """Fetch data from a service with consistent error handling and client management.

    Args:
        service_name: Name of the service to call
        endpoint: API endpoint to call
        params: Optional query parameters
        clients: Optional ServiceClients instance (will create if not provided)

    Returns:
        Dict containing the service response

    Raises:
        ServiceException: If service call fails
    """
    if not clients:
        clients = get_frontend_clients()

    service_url_map = {
        "doc-store": clients.doc_store_url(),
        "analysis-service": clients.analysis_service_url(),
        "source-agent": clients.source_agent_url(),
        "orchestrator": clients.orchestrator_url(),
        "reporting": get_reporting_url(),
        "consistency-engine": get_consistency_engine_url(),
    }

    if service_name not in service_url_map:
        raise ServiceException(
            f"Unknown service: {service_name}",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={"service_name": service_name, "available_services": list(service_url_map.keys())}
        )

    try:
        full_url = f"{service_url_map[service_name]}{endpoint}"
        return clients.get_json(full_url, params=params)
    except Exception as e:
        raise ServiceException(
            f"Failed to fetch from {service_name}",
            error_code=ErrorCodes.SERVICE_UNAVAILABLE,
            details={
                "service": service_name,
                "endpoint": endpoint,
                "full_url": full_url,
                "error": str(e)
            }
        )

def get_service_url(service_name: str) -> str:
    """Get the URL for a specific service."""
    url_map = {
        "doc-store": get_doc_store_url(),
        "reporting": get_reporting_url(),
        "consistency-engine": get_consistency_engine_url(),
    }

    if service_name not in url_map:
        raise ServiceException(
            f"Unknown service for URL lookup: {service_name}",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={"service_name": service_name}
        )

    return url_map[service_name]

def validate_frontend_request(params: Dict[str, Any], required_fields: Optional[List[str]] = None) -> None:
    """Validate frontend request parameters."""
    if required_fields:
        missing_fields = [field for field in required_fields if field not in params or params[field] is None]
        if missing_fields:
            raise ServiceException(
                f"Missing required fields: {missing_fields}",
                error_code=ErrorCodes.VALIDATION_ERROR,
                details={"missing_fields": missing_fields}
            )
