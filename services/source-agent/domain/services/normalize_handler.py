"""Data normalization handler for Source Agent service.

Handles the normalization of data from various sources.
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class NormalizeHandler:
    """Handles data normalization from various sources."""

    @staticmethod
    def normalize_data(source: str, data: Dict[str, Any], correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Normalize data from specified source.

        Args:
            source: The source system (github, jira, confluence)
            data: Raw data to normalize
            correlation_id: Optional correlation ID for tracking

        Returns:
            Normalized data dictionary
        """
        try:
            if source == "github":
                return NormalizeHandler._normalize_github_data(data)
            elif source == "jira":
                return NormalizeHandler._normalize_jira_data(data)
            elif source == "confluence":
                return NormalizeHandler._normalize_confluence_data(data)
            else:
                logger.warning(f"Unknown source: {source}")
                return data

        except Exception as e:
            logger.error(f"Error normalizing data from {source}: {e}")
            return {
                "error": f"Normalization failed: {str(e)}",
                "original_data": data
            }

    @staticmethod
    def _normalize_github_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize GitHub-specific data."""
        normalized = {
            "source": "github",
            "type": "repository",
            "normalized_at": "2024-01-01T00:00:00Z"
        }

        # Extract common GitHub fields
        if "full_name" in data:
            normalized["name"] = data["full_name"]
        if "description" in data:
            normalized["description"] = data["description"]
        if "html_url" in data:
            normalized["url"] = data["html_url"]
        if "topics" in data:
            normalized["tags"] = data["topics"]

        return normalized

    @staticmethod
    def _normalize_jira_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Jira-specific data."""
        normalized = {
            "source": "jira",
            "type": "issue",
            "normalized_at": "2024-01-01T00:00:00Z"
        }

        # Extract common Jira fields
        if "key" in data:
            normalized["id"] = data["key"]
        if "fields" in data:
            fields = data["fields"]
            if "summary" in fields:
                normalized["title"] = fields["summary"]
            if "description" in fields:
                normalized["description"] = fields["description"]
            if "issuetype" in fields:
                normalized["type"] = fields["issuetype"]["name"]

        return normalized

    @staticmethod
    def _normalize_confluence_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Confluence-specific data."""
        normalized = {
            "source": "confluence",
            "type": "page",
            "normalized_at": "2024-01-01T00:00:00Z"
        }

        # Extract common Confluence fields
        if "id" in data:
            normalized["id"] = data["id"]
        if "title" in data:
            normalized["title"] = data["title"]
        if "body" in data and "storage" in data["body"]:
            normalized["content"] = data["body"]["storage"]["value"]

        return normalized
