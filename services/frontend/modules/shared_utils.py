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
_ORCHESTRATOR_URL_ENV = EnvVars.ORCHESTRATOR_URL_ENV
_SUMMARIZER_HUB_URL_ENV = EnvVars.SUMMARIZER_HUB_URL_ENV
_LOG_COLLECTOR_URL_ENV = EnvVars.LOG_COLLECTOR_URL_ENV
_PROMPT_STORE_URL_ENV = EnvVars.PROMPT_STORE_URL
_ANALYSIS_SERVICE_URL_ENV = EnvVars.ANALYSIS_SERVICE_URL
_BEDROCK_PROXY_URL_ENV = "BEDROCK_PROXY_URL"
_CODE_ANALYZER_URL_ENV = "CODE_ANALYZER_URL"
_DISCOVERY_AGENT_URL_ENV = "DISCOVERY_AGENT_URL"
_GITHUB_MCP_URL_ENV = EnvVars.GITHUB_AGENT_URL_ENV
_INTERPRETER_URL_ENV = EnvVars.INTERPRETER_URL
_MEMORY_AGENT_URL_ENV = "MEMORY_AGENT_URL"
_NOTIFICATION_SERVICE_URL_ENV = "NOTIFICATION_SERVICE_URL"
_SECURE_ANALYZER_URL_ENV = EnvVars.SECURE_ANALYZER_URL_ENV
_SOURCE_AGENT_URL_ENV = EnvVars.SOURCE_AGENT_URL
_CLI_URL_ENV = "CLI_URL"

def get_default_timeout() -> int:
    """Get default service client timeout."""
    return _DEFAULT_TIMEOUT

def get_reporting_url() -> str:
    """Get reporting service URL from config/env with fallback."""
    return get_config_value("REPORTING_URL", "http://reporting:5030", section="services", env_key=_REPORTING_URL_ENV)

def get_doc_store_url() -> str:
    """Get doc store service URL from config/env with fallback."""
    return get_config_value("DOC_STORE_URL", "http://doc_store:5010", section="services", env_key=_DOC_STORE_URL_ENV)

def get_consistency_engine_url() -> str:
    """Get consistency engine service URL from config/env with fallback."""
    return get_config_value("CONSISTENCY_ENGINE_URL", "http://consistency-engine:5020", section="services", env_key=_CONSISTENCY_ENGINE_URL_ENV)

def get_orchestrator_url() -> str:
    """Get orchestrator service URL from config/env with fallback."""
    return get_config_value("ORCHESTRATOR_URL", "http://orchestrator:5040", section="services", env_key=_ORCHESTRATOR_URL_ENV)

def get_summarizer_hub_url() -> str:
    """Get summarizer hub service URL from config/env with fallback."""
    return get_config_value("SUMMARIZER_HUB_URL", "http://summarizer-hub:5060", section="services", env_key=_SUMMARIZER_HUB_URL_ENV)

def get_log_collector_url() -> str:
    """Get log collector service URL from config/env with fallback."""
    return get_config_value("LOG_COLLECTOR_URL", "http://log-collector:5080", section="services", env_key=_LOG_COLLECTOR_URL_ENV)

def get_prompt_store_url() -> str:
    """Get prompt store service URL from config/env with fallback."""
    return get_config_value("PROMPT_STORE_URL", "http://prompt-store:5110", section="services", env_key=_PROMPT_STORE_URL_ENV)

def get_analysis_service_url() -> str:
    """Get analysis service URL from config/env with fallback."""
    return get_config_value("ANALYSIS_SERVICE_URL", "http://analysis-service:5020", section="services", env_key=_ANALYSIS_SERVICE_URL_ENV)

def get_bedrock_proxy_url() -> str:
    """Get bedrock proxy service URL from config/env with fallback."""
    return get_config_value("BEDROCK_PROXY_URL", "http://bedrock-proxy:5000", section="services", env_key=_BEDROCK_PROXY_URL_ENV)

def get_code_analyzer_url() -> str:
    """Get code analyzer service URL from config/env with fallback."""
    return get_config_value("CODE_ANALYZER_URL", "http://code-analyzer:5030", section="services", env_key=_CODE_ANALYZER_URL_ENV)

def get_discovery_agent_url() -> str:
    """Get discovery agent service URL from config/env with fallback."""
    return get_config_value("DISCOVERY_AGENT_URL", "http://discovery-agent:5070", section="services", env_key=_DISCOVERY_AGENT_URL_ENV)

def get_github_mcp_url() -> str:
    """Get GitHub MCP service URL from config/env with fallback."""
    return get_config_value("GITHUB_MCP_URL", "http://github-mcp:5090", section="services", env_key=_GITHUB_MCP_URL_ENV)

def get_interpreter_url() -> str:
    """Get interpreter service URL from config/env with fallback."""
    return get_config_value("INTERPRETER_URL", "http://interpreter:5100", section="services", env_key=_INTERPRETER_URL_ENV)

def get_memory_agent_url() -> str:
    """Get memory agent service URL from config/env with fallback."""
    return get_config_value("MEMORY_AGENT_URL", "http://memory-agent:5120", section="services", env_key=_MEMORY_AGENT_URL_ENV)

def get_notification_service_url() -> str:
    """Get notification service URL from config/env with fallback."""
    return get_config_value("NOTIFICATION_SERVICE_URL", "http://notification-service:5130", section="services", env_key=_NOTIFICATION_SERVICE_URL_ENV)

def get_secure_analyzer_url() -> str:
    """Get secure analyzer service URL from config/env with fallback."""
    return get_config_value("SECURE_ANALYZER_URL", "http://secure-analyzer:5140", section="services", env_key=_SECURE_ANALYZER_URL_ENV)

def get_source_agent_url() -> str:
    """Get source agent service URL from config/env with fallback."""
    return get_config_value("SOURCE_AGENT_URL", "http://source-agent:5150", section="services", env_key=_SOURCE_AGENT_URL_ENV)

def get_cli_url() -> str:
    """Get CLI service URL from config/env with fallback."""
    return get_config_value("CLI_URL", "http://localhost:8000", section="services", env_key=_CLI_URL_ENV)

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
        "doc_store": clients.doc_store_url(),
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
        "doc_store": get_doc_store_url(),
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
