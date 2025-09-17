"""Shared utilities for Source Agent service modules.

This module contains common utilities used across all source-agent modules
to eliminate code duplication and ensure consistency.
"""

import os
import re
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from services.shared.utilities import utc_now, generate_id, clean_string, stable_hash
from services.shared.monitoring.logging import fire_and_forget
from services.shared.core.responses.responses import create_success_response, create_error_response
from services.shared.utilities.error_handling import ServiceException
from services.shared.core.constants_new import ErrorCodes, ServiceNames
from services.shared.core.models.models import Document
from services.shared.auth.credentials import get_secret as get_secret
from services.shared.core.config.config import get_config_value


def sanitize_for_response(text: str) -> str:
    """Sanitize text to prevent XSS attacks in JSON responses."""
    if not text:
        return ""

    # Remove HTML tags
    import re
    text = re.sub(r'<[^>]+>', '', text)

    # Remove dangerous JavaScript event handlers and attributes
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'vbscript:', '', text, flags=re.IGNORECASE)

    # Remove quotes that could be used to break out of attributes
    text = text.replace('"', '').replace("'", '')

    return clean_string(text)


# Global configuration with secure URL validation
def _validate_atlassian_url(url: str, service_name: str) -> str:
    """Validate Atlassian URLs to prevent SSRF attacks."""
    from urllib.parse import urlparse

    try:
        parsed = urlparse(url)
        # Ensure it's HTTPS and a valid Atlassian domain
        if parsed.scheme != "https":
            return f"https://example.atlassian.net"
        if not parsed.netloc or ".." in parsed.netloc:
            return f"https://example.atlassian.net"
        # Allow only reasonable Atlassian domains
        if not any(domain in parsed.netloc.lower() for domain in ['atlassian.net', 'jira.com', 'confluence.com']):
            return f"https://example.atlassian.net"
        return url
    except Exception:
        return f"https://example.atlassian.net"

_GITHUB_BASE_URL = "https://api.github.com"  # GitHub is hardcoded for security
_JIRA_BASE_URL = _validate_atlassian_url(
    get_config_value("JIRA_BASE_URL", "https://example.atlassian.net", section="services", env_key="JIRA_BASE_URL"),
    "jira",
)
_CONFLUENCE_BASE_URL = _validate_atlassian_url(
    get_config_value("CONFLUENCE_BASE_URL", "https://example.atlassian.net", section="services", env_key="CONFLUENCE_BASE_URL"),
    "confluence",
)

def get_github_base_url() -> str:
    """Get GitHub API base URL."""
    return _GITHUB_BASE_URL

def get_jira_base_url() -> str:
    """Get Jira base URL."""
    return _JIRA_BASE_URL

def get_confluence_base_url() -> str:
    """Get Confluence base URL."""
    return _CONFLUENCE_BASE_URL

def handle_source_agent_error(operation: str, error: Exception, **context) -> Dict[str, Any]:
    """Standardized error handling for source-agent operations.

    Logs the error and returns a standardized error response.
    """
    fire_and_forget("error", f"Source-agent {operation} error: {error}", ServiceNames.SOURCE_AGENT, context)
    return create_error_response(
        f"Failed to {operation}",
        error_code=ErrorCodes.DOCUMENT_FETCH_FAILED,
        details={"error": str(error), **context}
    )

def create_source_agent_success_response(op: str, data: Any, **context) -> Dict[str, Any]:
    """Standardized success response for source-agent operations.

    Merge optional context into the response payload instead of passing
    as keyword args to the shared success response constructor.
    """
    payload: Dict[str, Any]
    if isinstance(data, dict):
        payload = {**data}
    else:
        payload = {"result": data}
    if context:
        payload["context"] = context
    return create_success_response(f"Source {op} successful", payload)

def build_source_agent_context(operation: str, source_type: Optional[str] = None, doc_id: Optional[str] = None, **additional) -> Dict[str, Any]:
    """Build context dictionary for source-agent operations.

    Provides consistent context for logging and responses.
    """
    context = {
        "operation": operation,
        "service": "source-agent"
    }

    if source_type:
        context["source_type"] = source_type
    if doc_id:
        context["doc_id"] = doc_id

    context.update(additional)
    return context

def create_base_document(source_type: str, id: str, title: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
    """Create a base document with standardized fields."""
    return Document(
        id=id,
        title=title,
        content=content,
        source_type=source_type,
        metadata=metadata or {},
        created_at=utc_now(),
        updated_at=utc_now()
    )

def extract_text_from_html(html_content: str) -> str:
    """Extract plain text from HTML content."""
    if not html_content:
        return ""

    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', html_content)
    # Clean up whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def normalize_document_content(content: str, source_type: str) -> str:
    """Normalize document content based on source type."""
    if source_type in ['confluence', 'jira']:
        content = extract_text_from_html(content)
    return clean_string(content)

def handle_fetch_error(error_msg: str, source_type: str, doc_id: str):
    """Handle document fetch errors with standardized error format."""
    raise ServiceException(
        message=f"{error_msg}: {doc_id}",
        error_code=ErrorCodes.DOCUMENT_FETCH_FAILED,
        details={
            "source_type": source_type,
            "document_id": doc_id,
            "error": error_msg
        }
    )

def validate_source_type(source: str) -> None:
    """Validate that the source type is supported."""
    supported_sources = ["github", "jira", "confluence"]
    if source not in supported_sources:
        # Raise HTTP 400 for invalid source type (tests expect 400)
        raise HTTPException(status_code=400, detail={
            "error": f"Unsupported source: {source}",
            "supported_sources": supported_sources,
            "provided_source": source
        })

def extract_endpoints_from_code(text: str) -> List[str]:
    """Extract API endpoints from code content."""
    endpoints: List[str] = []
    lines = text.splitlines()

    for line in lines:
        line = line.strip()

        # FastAPI patterns
        if line.startswith("@app.") and "(" in line:
            endpoints.append(line)
        elif "FastAPI(" in line and "/" in line:
            endpoints.append(line)
        elif ".route(" in line and "/" in line:
            endpoints.append(line)

        # Express.js patterns
        match = re.search(r"\b(?:app|router)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", line, flags=re.IGNORECASE)
        if match:
            endpoints.append(line)

    return endpoints[:100]  # Limit to prevent excessive results

def build_github_url(endpoint: str) -> str:
    """Build GitHub API URL."""
    return f"{_GITHUB_BASE_URL}{endpoint}"

def build_jira_url(endpoint: str) -> str:
    """Build Jira API URL."""
    return f"{_JIRA_BASE_URL}{endpoint}"

def build_confluence_url(endpoint: str) -> str:
    """Build Confluence API URL."""
    return f"{_CONFLUENCE_BASE_URL}{endpoint}"

def extract_adf_text(adf_content: Dict[str, Any]) -> str:
    """Extract plain text from Atlassian Document Format."""
    if not isinstance(adf_content, dict):
        return str(adf_content)

    content_parts = []

    def process_node(node):
        if isinstance(node, dict):
            node_type = node.get("type", "")
            if node_type == "text":
                content_parts.append(node.get("text", ""))
            elif node_type in ["paragraph", "heading", "listItem"]:
                if "content" in node:
                    for child in node["content"]:
                        process_node(child)
            elif "content" in node:
                for child in node["content"]:
                    process_node(child)
        elif isinstance(node, list):
            for item in node:
                process_node(item)

    process_node(adf_content)
    return " ".join(content_parts).strip()
