"""Infrastructure Utilities

Utility functions for infrastructure concerns in the orchestrator service.
These functions handle service communication, URL resolution, and request preparation.
"""

import os
from typing import Dict, Any, Optional

from services.shared.core.constants_new import EnvVars


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
        "bedrock_proxy": EnvVars.BEDROCK_PROXY_URL_ENV,
        "code_analyzer": EnvVars.CODE_ANALYZER_URL_ENV,
        "summarizer_hub": EnvVars.SUMMARIZER_HUB_URL_ENV,
        "notification_service": EnvVars.NOTIFICATION_SERVICE_URL_ENV,
        "github_mcp": EnvVars.GITHUB_MCP_URL_ENV,
        "llm_gateway": EnvVars.LLM_GATEWAY_URL_ENV,
    }
    env_var = url_env_map.get(service_name)
    return os.environ.get(env_var, default_url) if env_var else default_url


def prepare_correlation_headers(request) -> Dict[str, str]:
    """Standardized correlation header preparation."""
    if hasattr(request, 'headers'):
        correlation_id = request.headers.get(EnvVars.CORRELATION_ID_HEADER, "")
        return {EnvVars.CORRELATION_ID_HEADER: correlation_id} if correlation_id else {}
    return {}


def build_service_request_context(operation: str, **kwargs) -> Dict[str, Any]:
    """Build standardized service request context."""
    context = {"operation": operation, "service": "orchestrator"}
    context.update(kwargs)
    return context


__all__ = [
    'get_service_url',
    'prepare_correlation_headers',
    'build_service_request_context'
]
