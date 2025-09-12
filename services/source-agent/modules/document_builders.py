"""Document builder functions for the Source Agent service.

This module contains all document construction and processing functions,
extracted from the main source-agent service to improve maintainability.
"""

from typing import List, Optional
from services.shared.models import Document
from services.shared.utilities import utc_now

# Import shared utilities from main service module
from .shared_utils import (
    create_base_document,
    extract_text_from_html,
    normalize_document_content,
    extract_adf_text,
    get_jira_base_url,
    get_confluence_base_url
)


def build_readme_doc(owner: str, repo: str, content: str) -> Document:
    """Build document from GitHub README using shared utilities."""
    doc = create_base_document(
        source_type="github",
        id=f"github:{owner}/{repo}:readme",
        title="README.md",
        content=normalize_document_content(content, "github"),
        metadata={
            "owner": owner,
            "repo": repo,
            "type": "readme",
            "url": f"https://github.com/{owner}/{repo}"
        }
    )
    return doc


def extract_endpoints_from_patch(patch: str) -> List[str]:
    """Extract API endpoints from GitHub patch content."""
    import re
    # Look for common API patterns in patch files
    patterns = [
        r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
        r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
        r'url_for\(["\']([^"\']+)["\']',
        r'path=["\']([^"\']+)["\']',
    ]

    endpoints = []
    for pattern in patterns:
        matches = re.findall(pattern, patch)
        if isinstance(matches[0], tuple) if matches else False:
            endpoints.extend([match[1] for match in matches])
        else:
            endpoints.extend(matches)

    return list(set(endpoints))  # Remove duplicates


def build_jira_doc(key: str, data: dict) -> Document:
    """Build document from Jira issue data using shared utilities."""
    title = data.get("fields", {}).get("summary", f"Jira Issue {key}")
    description = data.get("fields", {}).get("description", "")

    # Handle Atlassian Document Format
    if isinstance(description, dict) and "content" in description:
        # Convert ADF to plain text
        content = extract_adf_text(description)
    else:
        content = str(description)

    # Normalize content
    content = normalize_document_content(content, "jira")

    doc = create_base_document(
        source_type="jira",
        id=f"jira:{key}",
        title=title,
        content=content,
        metadata={
            "issue_key": key,
            "project": key.split("-")[0] if "-" in key else "",
            "status": data.get("fields", {}).get("status", {}).get("name", ""),
            "assignee": data.get("fields", {}).get("assignee", {}).get("displayName", ""),
            "reporter": data.get("fields", {}).get("reporter", {}).get("displayName", ""),
            "type": data.get("fields", {}).get("issuetype", {}).get("name", ""),
            "url": f"{get_jira_base_url()}/browse/{key}"
        }
    )
    return doc


def storage_html_to_text(storage: str) -> str:
    """Convert Jira storage format HTML to plain text using shared utilities."""
    return extract_text_from_html(storage)


def build_confluence_doc(page_id: str, data: dict) -> Document:
    """Build document from Confluence page data using shared utilities."""
    title = data.get("title", f"Confluence Page {page_id}")
    body = data.get("body", {}).get("storage", {}).get("value", "")

    # Convert storage format to plain text
    content = storage_html_to_text(body) if body else ""
    content = normalize_document_content(content, "confluence")

    doc = create_base_document(
        source_type="confluence",
        id=f"confluence:{page_id}",
        title=title,
        content=content,
        metadata={
            "page_id": page_id,
            "space": data.get("space", {}).get("key", ""),
            "version": data.get("version", {}).get("number", 0),
            "creator": data.get("creator", {}).get("displayName", ""),
            "last_modifier": data.get("lastModifier", {}).get("displayName", ""),
            "url": f"{get_confluence_base_url()}/pages/viewpage.action?pageId={page_id}"
        }
    )
    return doc


# Note: ADF text extraction is now handled by shared_utils.extract_adf_text
# This function is kept for backward compatibility but delegates to shared utility
