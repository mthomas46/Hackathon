"""Data normalization handler for Source Agent service.

Handles the complex logic for normalizing data from different sources.
"""

from typing import Any, Dict, Optional

from services.shared.envelopes import DocumentEnvelope
from services.shared.utilities import stable_hash

from .document_builders import build_confluence_doc, build_jira_doc
from .shared_utils import (
    build_source_agent_context,
    create_base_document,
    create_source_agent_success_response,
)


class NormalizeHandler:
    """Handles data normalization from various sources.

    This class provides methods to normalize data from different source systems
    into a consistent DocumentEnvelope format. It handles the transformation
    of platform-specific data structures into standardized document representations.

    Supported sources include GitHub (PRs, issues, repos), Jira (issues, projects),
    and Confluence (pages, blogs, spaces).
    """

    @staticmethod
    def normalize_github_data(
        data: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Optional[DocumentEnvelope]:
        """Normalize GitHub data into standardized document format.

        Transforms GitHub-specific data structures (pull requests, issues, repositories)
        into consistent DocumentEnvelope objects with normalized metadata and content.

        Args:
            data: Raw GitHub API response data
            correlation_id: Optional correlation ID for tracking

        Returns:
            DocumentEnvelope with normalized GitHub data, or None if normalization fails

        Raises:
            Various exceptions during data transformation that are handled gracefully
        """
        if data.get("type") == "pr":
            # GitHub PR normalization
            pr_data = data
            content = f"PR #{pr_data.get('number')}: {pr_data.get('title')}\n\n{pr_data.get('body', '')}"
            doc = create_base_document(
                source_type="github",
                id=f"github:pr:{pr_data.get('number')}",
                title=f"PR #{pr_data.get('number')}: {pr_data.get('title')}",
                content=content,
                metadata={
                    "type": "pull_request",
                    "state": pr_data.get("state"),
                    "merged": pr_data.get("merged"),
                    "owner": pr_data.get("user", {}).get("login"),
                },
            )
            doc.source_id = str(pr_data.get("number"))
            doc.content_hash = stable_hash(content)
            doc.url = pr_data.get("html_url", "")
            doc.project = pr_data.get("base", {}).get("repo", {}).get("full_name", "")

            envelope = DocumentEnvelope(
                id=f"env:{doc.id}",
                correlation_id=correlation_id,
                document=doc.model_dump(),
            )
            return envelope

        elif data.get("type") == "readme":
            # Normalize README-like content
            readme = data
            title = readme.get("name") or "README"
            content = readme.get("content") or ""
            doc = create_base_document(
                source_type="github",
                id=f"github:readme:{stable_hash(content)[:8]}",
                title=title,
                content=content,
                metadata={"type": "readme", "url": readme.get("html_url")},
            )
            return DocumentEnvelope(
                id=f"env:{doc.id}",
                correlation_id=correlation_id,
                document=doc.model_dump(),
            )

        else:
            # Generic normalization for arbitrary GitHub-derived content
            title = data.get("title") or "GitHub Document"
            content = data.get("content") or ""
            doc = create_base_document(
                source_type="github",
                id=f"github:doc:{stable_hash(title + content)[:8]}",
                title=title,
                content=content,
                metadata=data.get("metadata") or {},
            )
            return DocumentEnvelope(
                id=f"env:{doc.id}",
                correlation_id=correlation_id,
                document=doc.model_dump(),
            )

    @staticmethod
    def normalize_jira_data(
        data: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Optional[DocumentEnvelope]:
        """Normalize Jira data into standardized document format.

        Transforms Jira-specific data structures (issues, projects, epics)
        into consistent DocumentEnvelope objects with normalized metadata.

        Args:
            data: Raw Jira API response data containing issue/project information
            correlation_id: Optional correlation ID for request tracking

        Returns:
            DocumentEnvelope with normalized Jira data, or None if data is invalid

        Raises:
            Various exceptions during data transformation that are handled gracefully
        """
        if data.get("key"):
            # Jira issue normalization
            doc = build_jira_doc(data["key"], data)
            return DocumentEnvelope(
                id=f"env:{doc.id}",
                correlation_id=correlation_id,
                document=doc.model_dump(),
            )
        return None

    @staticmethod
    def normalize_confluence_data(
        data: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Optional[DocumentEnvelope]:
        """Normalize Confluence data into standardized document format.

        Transforms Confluence-specific data structures (pages, blogs, spaces)
        into consistent DocumentEnvelope objects with normalized metadata and content.

        Args:
            data: Raw Confluence API response data containing page/blog information
            correlation_id: Optional correlation ID for request tracking

        Returns:
            DocumentEnvelope with normalized Confluence data, or None if data is invalid

        Raises:
            Various exceptions during content extraction and transformation
        """
        if data.get("id"):
            # Confluence page normalization
            doc = build_confluence_doc(data["id"], data)
            return DocumentEnvelope(
                id=f"env:{doc.id}",
                correlation_id=correlation_id,
                document=doc.model_dump(),
            )
        return None

    @staticmethod
    def normalize_data(
        source: str, data: Dict[str, Any], correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Normalize data from specified source into standardized format.

        Main entry point for data normalization that routes to source-specific
        normalization methods. Transforms platform-specific data structures
        into consistent DocumentEnvelope objects.

        Args:
            source: Source system identifier (github, jira, confluence)
            data: Raw data from the source system
            correlation_id: Optional correlation ID for request tracking

        Returns:
            Dictionary containing success status and normalized DocumentEnvelope,
            or error response if normalization fails

        Raises:
            Handles all normalization errors gracefully and returns error responses
        """
        envelope = None

        if source == "github":
            envelope = NormalizeHandler.normalize_github_data(data, correlation_id)
        elif source == "jira":
            envelope = NormalizeHandler.normalize_jira_data(data, correlation_id)
        elif source == "confluence":
            envelope = NormalizeHandler.normalize_confluence_data(data, correlation_id)

        if envelope:
            context = build_source_agent_context("normalize", source)
            context = {k: v for k, v in context.items() if k != "operation"}
            envelope_dict = envelope.model_dump()
            # Ensure correlation_id is included
            if correlation_id is not None:
                envelope_dict["correlation_id"] = correlation_id
            return create_source_agent_success_response(
                "normalized", {"envelope": envelope_dict}, **context
            )
        else:
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail="Unable to normalize data")


# Create singleton instance
normalize_handler = NormalizeHandler()
