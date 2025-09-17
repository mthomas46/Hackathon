"""Document fetch handler for Source Agent service.

Handles the complex logic for fetching documents from different sources.
"""
import os
import base64
from typing import Any, Dict
from fastapi import HTTPException

from services.shared.integrations.clients.clients import ServiceClients
from services.shared.utilities import cached_get

from .document_builders import build_readme_doc
from .shared_utils import (
    sanitize_for_response,
    build_github_url,
    handle_source_agent_error,
    create_source_agent_success_response,
    build_source_agent_context
)


class FetchHandler:
    """Handles document fetching from various sources."""

    @staticmethod
    async def fetch_github_document(owner: str, repo: str, req) -> Dict[str, Any]:
        """Fetch document from GitHub."""
        # Optionally delegate to local GitHub MCP when enabled
        if os.environ.get("USE_GITHUB_MCP", "0") in ("1", "true", "TRUE"):
            try:
                clients = ServiceClients(timeout=20)
                mcp_resp = await clients.post_json(
                    "github-mcp/tools/github.get_repo/invoke",
                    {"arguments": {"owner": owner, "repo": repo}}
                )
                result = (mcp_resp or {}).get("result", {})
                title = f"{result.get('full_name', f'{owner}/{repo}')}"
                content = f"Repository: {result.get('full_name', f'{owner}/{repo}')}\nStars: {result.get('stars', 0)}\nTopics: {', '.join(result.get('topics', []))}"
                doc = build_readme_doc(owner, repo, content)
                context = build_source_agent_context("fetch", req.source, doc.id)
                return create_source_agent_success_response("retrieved", {
                    "document": doc.model_dump(),
                    "source": req.source,
                    "via": "github-mcp"
                }, **context)
            except Exception as e:
                # Fallback to direct GitHub fetch below
                pass

        # Direct GitHub README fetch or offline-friendly fallback
        url = build_github_url(f"/repos/{owner}/{repo}/readme")
        status, body, _ = await cached_get(url)

        if status == 200:
            content = base64.b64decode(body.get("content", "")).decode("utf-8")
        else:
            # Offline-friendly fallback content
            content = f"# {owner}/{repo}\n\nREADME unavailable in test environment."

        # Sanitize all content for security (prevent XSS in responses)
        safe_owner = sanitize_for_response(owner)
        safe_repo = sanitize_for_response(repo)
        safe_content = sanitize_for_response(content)
        doc = build_readme_doc(safe_owner, safe_repo, safe_content)

        context = build_source_agent_context("fetch", req.source, doc.id)
        return create_source_agent_success_response("retrieved", {
            "document": doc.model_dump(),
            "source": req.source
        }, **context)

    @staticmethod
    async def fetch_jira_document(req) -> Dict[str, Any]:
        """Fetch document from Jira (placeholder)."""
        return handle_source_agent_error(
            "fetch from Jira",
            Exception("Jira fetch not implemented"),
            error_code="FEATURE_NOT_IMPLEMENTED",
            source=req.source, status="placeholder"
        )

    @staticmethod
    async def fetch_confluence_document(req) -> Dict[str, Any]:
        """Fetch document from Confluence (placeholder)."""
        return handle_source_agent_error(
            "fetch from Confluence",
            Exception("Confluence fetch not implemented"),
            error_code="FEATURE_NOT_IMPLEMENTED",
            source=req.source, status="placeholder"
        )


# Create singleton instance
fetch_handler = FetchHandler()
