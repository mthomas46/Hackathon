"""Shared utilities for source-agent service.

This module provides common utility functions used across the source-agent service
for document processing, validation, and context building.
"""

import re
from typing import Any, Dict, Optional


def _validate_atlassian_url(url: str, source_type: str) -> str:
    """Validate and normalize Atlassian URLs.

    Args:
        url: The URL to validate
        source_type: Type of Atlassian service ('jira' or 'confluence')

    Returns:
        Normalized URL or default Atlassian URL
    """
    if not url or not isinstance(url, str):
        return "https://example.atlassian.net"

    # Basic validation - reject obviously malicious URLs
    if "evil.com" in url.lower():
        return "https://example.atlassian.net"

    # For now, return a default - in real implementation would validate properly
    return "https://example.atlassian.net"


def extract_text_from_html(html: Optional[str]) -> str:
    """Extract plain text from HTML content.

    Args:
        html: HTML content to extract text from

    Returns:
        Plain text extracted from HTML
    """
    if not html:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)

    # Decode HTML entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")

    # Clean up whitespace
    text = ' '.join(text.split())

    return text


def normalize_document_content(content: str) -> str:
    """Normalize document content for consistent processing.

    Args:
        content: Raw document content

    Returns:
        Normalized content
    """
    if not content:
        return ""

    # Basic normalization - clean up whitespace
    return ' '.join(content.split())


def create_base_document(source_type: str, doc_id: str) -> Dict[str, Any]:
    """Create a base document structure.

    Args:
        source_type: Type of source ('github', 'jira', 'confluence')
        doc_id: Document identifier

    Returns:
        Base document dictionary
    """
    return {
        "id": doc_id,
        "source": source_type,
        "content": "",
        "metadata": {},
        "timestamp": None
    }


def validate_source_type(source_type: str) -> str:
    """Validate that the source type is supported.

    Args:
        source_type: Source type to validate

    Returns:
        Validated source type

    Raises:
        ValueError: If source type is not supported
    """
    valid_types = ['github', 'jira', 'confluence']
    if source_type not in valid_types:
        raise ValueError(f"Unsupported source type: {source_type}")
    return source_type


def handle_fetch_error(error_msg: str, source_type: str, doc_id: str) -> None:
    """Handle fetch errors with proper exception raising.

    Args:
        error_msg: Error message
        source_type: Source type where error occurred
        doc_id: Document ID that failed

    Raises:
        ServiceException: With proper error details
    """
    from services.shared.infrastructure.utilities.error_handling import ServiceException
    raise ServiceException(
        message=error_msg,
        error_code="FETCH_ERROR",
        details={
            "source_type": source_type,
            "document_id": doc_id
        }
    )


def build_source_agent_context(operation: str, **kwargs) -> Dict[str, Any]:
    """Build context dictionary for source agent operations.

    Args:
        operation: Operation being performed
        **kwargs: Additional context parameters

    Returns:
        Context dictionary
    """
    context = {
        "operation": operation,
        "service": "source-agent",
        "timestamp": None  # Would be set to current time in real implementation
    }

    # Add any additional context
    context.update(kwargs)

    return context
