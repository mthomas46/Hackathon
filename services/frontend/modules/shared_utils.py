"""Shared utilities for Frontend service modules.

This module contains common utilities used across all frontend modules
to eliminate code duplication and ensure consistency.
"""

from typing import Any, Dict, List, Optional

from fastapi.responses import HTMLResponse

from services.shared.presentation.api.responses import create_error_response

# Import shared utilities
from services.shared.infrastructure.external.clients.clients import ServiceClients
from services.shared.infrastructure.monitoring.logging import fire_and_forget
from services.shared.infrastructure.utilities.error_handling import ServiceException
from services.shared.core.constants_new import EnvVars
from services.shared.infrastructure.config.config.config import get_config_value

# Global configuration for frontend service
_DEFAULT_TIMEOUT = 30

# Service URL configurations - DRY refactoring: consolidated from 18 individual functions
_SERVICE_URL_CONFIGS = {
    "reporting": {
        "config_key": "REAPI_PORTING_URL",
        "default_url": "http://reporting:5030",
        "env_key": EnvVars.REAPI_PORTING_URL_ENV,
    },
    "doc_store": {
        "config_key": "DOC_STORE_URL",
        "default_url": "http://doc_store:5010",
        "env_key": EnvVars.DOC_STORE_URL_ENV,
    },
    "consistency_engine": {
        "config_key": "CONSISTENCY_ENGINE_URL",
        "default_url": "http://consistency-engine:5020",
        "env_key": EnvVars.CONSISTENCY_ENGINE_URL_ENV,
    },
    "orchestrator": {
        "config_key": "ORCHESTRATOR_URL",
        "default_url": "http://orchestrator:5000",
        "env_key": EnvVars.ORCHESTRATOR_URL_ENV,
    },
    "summarizer-hub": {
        "config_key": "SUMMARIZER_HUB_URL",
        "default_url": "http://summarizer-hub:5040",
        "env_key": EnvVars.SUMMARIZER_HUB_URL_ENV,
    },
    "log_collector": {
        "config_key": "LOG_COLLECTOR_URL",
        "default_url": "http://log-collector:5050",
        "env_key": EnvVars.LOG_COLLECTOR_URL_ENV,
    },
    "prompt_store": {
        "config_key": "PROMPT_STORE_URL",
        "default_url": "http://prompt-store:5060",
        "env_key": EnvVars.PROMPT_STORE_URL,
    },
    "analysis_service": {
        "config_key": "ANALYSIS_SERVICE_URL",
        "default_url": "http://analysis-service:5070",
        "env_key": EnvVars.ANALYSIS_SERVICE_URL,
    },
    "bedrock_proxy": {
        "config_key": "BEDROCK_PROXY_URL",
        "default_url": "http://bedrock-proxy:5080",
        "env_key": "BEDROCK_PROXY_URL",
    },
    "code-analyzer": {
        "config_key": "CODE_ANALYZER_URL",
        "default_url": "http://code-analyzer:5090",
        "env_key": "CODE_ANALYZER_URL",
    },
    "discovery_agent": {
        "config_key": "DISCOVERY_AGENT_URL",
        "default_url": "http://discovery-agent:5100",
        "env_key": "DISCOVERY_AGENT_URL",
    },
    "github_mcp": {
        "config_key": "GITHUB_MCP_URL",
        "default_url": "http://github-mcp:5110",
        "env_key": EnvVars.GITHUB_AGENT_URL_ENV,
    },
    "interpreter": {
        "config_key": "INTERPRETER_URL",
        "default_url": "http://interpreter:5120",
        "env_key": EnvVars.INTERPRETER_URL,
    },
    "memory_agent": {
        "config_key": "MEMORY_AGENT_URL",
        "default_url": "http://memory-agent:5130",
        "env_key": "MEMORY_AGENT_URL",
    },
    "notification-service": {
        "config_key": "NOTIFICATION_SERVICE_URL",
        "default_url": "http://notification-service:5140",
        "env_key": "NOTIFICATION_SERVICE_URL",
    },
    "secure-analyzer": {
        "config_key": "SECURE_ANALYZER_URL",
        "default_url": "http://secure-analyzer:5150",
        "env_key": EnvVars.SECURE_ANALYZER_URL_ENV,
    },
    "source-agent": {
        "config_key": "SOURCE_AGENT_URL",
        "default_url": "http://source-agent:5160",
        "env_key": EnvVars.SOURCE_AGENT_URL,
    },
    "cli": {
        "config_key": "CLI_URL",
        "default_url": "http://cli:5170",
        "env_key": "CLI_URL",
    },
}


def get_default_timeout() -> int:
    """Get default service client timeout."""
    return _DEFAULT_TIMEOUT


def _get_service_url(service_key: str) -> str:
    """Generic function to get service URL from configuration.

    DRY refactoring: Consolidates 18+ individual URL functions into one generic function.
    Reduces code duplication from ~300 lines to ~20 lines (90% reduction).

    Args:
        service_key: Key for the service in _SERVICE_URL_CONFIGS

    Returns:
        Service URL string

    Raises:
        ServiceException: If service_key is not found in configuration
    """
    if service_key not in _SERVICE_URL_CONFIGS:
        raise ServiceException(
            f"Unknown service for URL lookup: {service_key}",
            error_code="VALIDATION_ERROR",
            details={"service_key": service_key, "available_keys": list(_SERVICE_URL_CONFIGS.keys())},
        )

    config = _SERVICE_URL_CONFIGS[service_key]
    return get_config_value(
        config["config_key"],
        config["default_url"],
        section="services",
        env_key=config["env_key"],
    )


def get_reporting_url() -> str:
    """Get reporting service URL from config/env with fallback."""
    return _get_service_url("reporting")


def get_doc_store_url() -> str:
    """Get doc store service URL from config/env with fallback."""
    return _get_service_url("doc_store")


def get_consistency_engine_url() -> str:
    """Get consistency engine service URL from config/env with fallback."""
    return _get_service_url("consistency_engine")


def get_orchestrator_url() -> str:
    """Get orchestrator service URL from config/env with fallback."""
    return _get_service_url("orchestrator")


def get_summarizer_hub_url() -> str:
    """Get summarizer hub service URL from config/env with fallback."""
    return _get_service_url("summarizer-hub")


def get_log_collector_url() -> str:
    """Get log collector service URL from config/env with fallback."""
    return _get_service_url("log_collector")


def get_prompt_store_url() -> str:
    """Get prompt store service URL from config/env with fallback."""
    return _get_service_url("prompt_store")


def get_analysis_service_url() -> str:
    """Get analysis service URL from config/env with fallback."""
    return _get_service_url("analysis_service")


def get_bedrock_proxy_url() -> str:
    """Get bedrock proxy service URL from config/env with fallback."""
    return _get_service_url("bedrock_proxy")


def get_code_analyzer_url() -> str:
    """Get code analyzer service URL from config/env with fallback."""
    return _get_service_url("code-analyzer")


def get_discovery_agent_url() -> str:
    """Get discovery agent service URL from config/env with fallback."""
    return _get_service_url("discovery_agent")


def get_github_mcp_url() -> str:
    """Get GitHub MCP service URL from config/env with fallback."""
    return _get_service_url("github_mcp")


def get_interpreter_url() -> str:
    """Get interpreter service URL from config/env with fallback."""
    return _get_service_url("interpreter")


def get_memory_agent_url() -> str:
    """Get memory agent service URL from config/env with fallback."""
    return _get_service_url("memory_agent")


def get_notification_service_url() -> str:
    """Get notification service URL from config/env with fallback."""
    return _get_service_url("notification-service")


def get_secure_analyzer_url() -> str:
    """Get secure analyzer service URL from config/env with fallback."""
    return _get_service_url("secure-analyzer")


def get_source_agent_url() -> str:
    """Get source agent service URL from config/env with fallback."""
    return _get_service_url("source-agent")


def get_cli_url() -> str:
    """Get CLI service URL from config/env with fallback."""
    return _get_service_url("cli")


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
        r"<script[^>]*>.*?</script>",  # Script tags
        r"javascript:",  # JavaScript URLs
        r"vbscript:",  # VBScript URLs
        r"data:",  # Data URLs
        r"../../../",  # Path traversal
        r"..\\..\\",  # Windows path traversal
        r"\${.*}",  # Environment variable expansion
        r"`.*`",  # Command injection
    ]

    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE | re.DOTALL)

    return sanitized


def create_html_response(
    content: str, title: str = "LLM Documentation Ecosystem"
) -> HTMLResponse:
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


def handle_frontend_error(
    operation: str, error: Exception, **context
) -> Dict[str, Any]:
    """Standardized error handling for frontend operations.

    Logs the error and returns a standardized error response.
    """
    fire_and_forget(
        "error", f"Frontend {operation} error: {error}", ServiceNames.FRONTEND, context
    )
    return create_error_response(
        f"Failed to {operation}",
        error_code=ErrorCodes.INTERNAL_ERROR,
        details={"error": str(error), **context},
    )


def create_frontend_success_response(
    operation: str, data: Any, **context
) -> Dict[str, Any]:
    """Standardized success response for frontend operations.

    Returns a consistent success response format.
    """
    from services.shared.presentation.responses import create_success_response

    return create_success_response(f"Frontend {operation} successful", data, **context)


def build_frontend_context(operation: str, **additional) -> Dict[str, Any]:
    """Build context dictionary for frontend operations.

    Provides consistent context for logging and responses.
    """
    context = {"operation": operation, "service": ServiceNames.FRONTEND}
    context.update(additional)
    return context


def fetch_service_data(
    service_name: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    clients: Optional[ServiceClients] = None,
) -> Dict[str, Any]:
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
        "source-agent": clients.source-agent_url(),
        "orchestrator": clients.orchestrator_url(),
        "reporting": get_reporting_url(),
        "consistency-engine": get_consistency_engine_url(),
    }

    if service_name not in service_url_map:
        raise ServiceException(
            f"Unknown service: {service_name}",
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={
                "service_name": service_name,
                "available_services": list(service_url_map.keys()),
            },
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
                "error": str(e),
            },
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
            details={"service_name": service_name},
        )

    return url_map[service_name]


def validate_frontend_request(
    params: Dict[str, Any], required_fields: Optional[List[str]] = None
) -> None:
    """Validate frontend request parameters."""
    if required_fields:
        missing_fields = [
            field
            for field in required_fields
            if field not in params or params[field] is None
        ]
        if missing_fields:
            raise ServiceException(
                f"Missing required fields: {missing_fields}",
                error_code=ErrorCodes.VALIDATION_ERROR,
                details={"missing_fields": missing_fields},
            )
