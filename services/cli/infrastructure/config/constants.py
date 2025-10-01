"""CLI Service Constants and Environment Variables.

This module provides centralized constants and environment variable names
for the CLI service to eliminate hardcoded values.
"""

from enum import Enum


class EnvVars:
    """Environment variable names for CLI service configuration."""

    # Service URLs
    ANALYSIS_SERVICE_URL = "ANALYSIS_SERVICE_URL"
    PROMPT_STORE_URL = "PROMPT_STORE_URL"
    MEMORY_AGENT_URL = "MEMORY_AGENT_URL"
    SOURCE_AGENT_URL = "SOURCE_AGENT_URL"
    DOC_STORE_URL = "DOC_STORE_URL"
    GITHUB_MCP_URL = "GITHUB_MCP_URL"
    INTERPRETER_URL = "INTERPRETER_URL"
    SECURE_ANALYZER_URL = "SECURE_ANALYZER_URL"
    LOG_COLLECTOR_URL = "LOG_COLLECTOR_URL"
    NOTIFICATION_SERVICE_URL = "NOTIFICATION_SERVICE_URL"
    ORCHESTRATOR_URL = "ORCHESTRATOR_URL"
    SUMMARIZER_HUB_URL = "SUMMARIZER_HUB_URL"
    CODE_ANALYZER_URL = "CODE_ANALYZER_URL"
    BEDROCK_PROXY_URL = "BEDROCK_PROXY_URL"
    ARCHITECTURE_DIGITIZER_URL = "ARCHITECTURE_DIGITIZER_URL"
    LLM_GATEWAY_URL = "LLM_GATEWAY_URL"

    # External Service URLs
    OLLAMA_ENDPOINT = "OLLAMA_ENDPOINT"
    REDIS_URL = "REDIS_URL"
    DATABASE_URL = "DATABASE_URL"

    # Service Configuration
    CLI_SERVICE_API_HOST = "CLI_SERVICE_API_HOST"
    CLI_SERVICE_API_PORT = "CLI_SERVICE_API_PORT"
    CLI_DEBUG_MODE = "CLI_DEBUG_MODE"
    CLI_LOG_LEVEL = "CLI_LOG_LEVEL"

    # Default Values
    DEFAULT_ANALYSIS_SERVICE_URL = "http://localhost:5020"
    DEFAULT_PROMPT_STORE_URL = "http://localhost:5110"
    DEFAULT_MEMORY_AGENT_URL = "http://localhost:5040"
    DEFAULT_SOURCE_AGENT_URL = "http://localhost:5000"
    DEFAULT_DOC_STORE_URL = "http://localhost:5087"
    DEFAULT_GITHUB_MCP_URL = "http://localhost:5072"
    DEFAULT_INTERPRETER_URL = "http://localhost:5120"
    DEFAULT_SECURE_ANALYZER_URL = "http://localhost:5070"
    DEFAULT_LOG_COLLECTOR_URL = "http://localhost:5050"
    DEFAULT_NOTIFICATION_SERVICE_URL = "http://localhost:5060"
    DEFAULT_ORCHESTRATOR_URL = "http://localhost:5000"
    DEFAULT_SUMMARIZER_HUB_URL = "http://localhost:5030"
    DEFAULT_CODE_ANALYZER_URL = "http://localhost:5090"
    DEFAULT_BEDROCK_PROXY_URL = "http://localhost:5055"
    DEFAULT_ARCHITECTURE_DIGITIZER_URL = "http://localhost:5100"
    DEFAULT_LLM_GATEWAY_URL = "http://localhost:5055"
    DEFAULT_OLLAMA_ENDPOINT = "http://localhost:11434"
    DEFAULT_CLI_API_HOST = "127.0.0.1"
    DEFAULT_CLI_API_PORT = "8000"


class ServicePorts:
    """Default service ports."""

    ANALYSIS_SERVICE = 5020
    PROMPT_STORE = 5110
    MEMORY_AGENT = 5040
    SOURCE_AGENT = 5000
    DOC_STORE = 5087
    GITHUB_MCP = 5072
    INTERPRETER = 5120
    SECURE_ANALYZER = 5070
    LOG_COLLECTOR = 5050
    NOTIFICATION_SERVICE = 5060
    ORCHESTRATOR = 5000
    SUMMARIZER_HUB = 5030
    CODE_ANALYZER = 5090
    BEDROCK_PROXY = 5055
    ARCHITECTURE_DIGITIZER = 5100
    LLM_GATEWAY = 5055
    CLI = 8000
    OLLAMA = 11434


def get_service_url(service_name: str, default_url: str) -> str:
    """Get service URL from environment variable with fallback to default.

    Args:
        service_name: Name of the service (used to construct env var name)
        default_url: Default URL to use if env var not set

    Returns:
        Service URL from environment or default
    """
    import os
    env_var = f"{service_name.upper().replace('-', '_')}_URL"
    return os.getenv(env_var, default_url)


def get_service_urls() -> dict:
    """Get all service URLs from environment variables with defaults.

    Returns:
        Dictionary of service names to URLs
    """
    return {
        "analysis-service": get_service_url("ANALYSIS_SERVICE", EnvVars.DEFAULT_ANALYSIS_SERVICE_URL),
        "prompt_store": get_service_url("PROMPT_STORE", EnvVars.DEFAULT_PROMPT_STORE_URL),
        "memory-agent": get_service_url("MEMORY_AGENT", EnvVars.DEFAULT_MEMORY_AGENT_URL),
        "source-agent": get_service_url("SOURCE_AGENT", EnvVars.DEFAULT_SOURCE_AGENT_URL),
        "doc_store": get_service_url("DOC_STORE", EnvVars.DEFAULT_DOC_STORE_URL),
        "github-mcp": get_service_url("GITHUB_MCP", EnvVars.DEFAULT_GITHUB_MCP_URL),
        "interpreter": get_service_url("INTERPRETER", EnvVars.DEFAULT_INTERPRETER_URL),
        "secure-analyzer": get_service_url("SECURE_ANALYZER", EnvVars.DEFAULT_SECURE_ANALYZER_URL),
        "log-collector": get_service_url("LOG_COLLECTOR", EnvVars.DEFAULT_LOG_COLLECTOR_URL),
        "notification-service": get_service_url("NOTIFICATION_SERVICE", EnvVars.DEFAULT_NOTIFICATION_SERVICE_URL),
        "orchestrator": get_service_url("ORCHESTRATOR", EnvVars.DEFAULT_ORCHESTRATOR_URL),
        "summarizer-hub": get_service_url("SUMMARIZER_HUB", EnvVars.DEFAULT_SUMMARIZER_HUB_URL),
        "code-analyzer": get_service_url("CODE_ANALYZER", EnvVars.DEFAULT_CODE_ANALYZER_URL),
        "bedrock-proxy": get_service_url("BEDROCK_PROXY", EnvVars.DEFAULT_BEDROCK_PROXY_URL),
        "architecture-digitizer": get_service_url("ARCHITECTURE_DIGITIZER", EnvVars.DEFAULT_ARCHITECTURE_DIGITIZER_URL),
        "llm-gateway": get_service_url("LLM_GATEWAY", EnvVars.DEFAULT_LLM_GATEWAY_URL),
    }
