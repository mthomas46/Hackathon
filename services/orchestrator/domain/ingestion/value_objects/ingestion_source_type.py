"""Ingestion Source Type Value Object"""

from enum import Enum


class IngestionSourceType(Enum):
    """Enumeration of supported ingestion source types."""

    GITHUB = "github"              # GitHub repositories and issues
    GITLAB = "gitlab"             # GitLab repositories and issues
    JIRA = "jira"                 # JIRA issue tracking
    CONFLUENCE = "confluence"     # Confluence documentation
    FILESYSTEM = "filesystem"     # Local file system
    WEB = "web"                   # Web URLs and content
    DATABASE = "database"         # Database tables and queries
    API = "api"                   # REST API endpoints
    EMAIL = "email"               # Email messages and attachments
    SLACK = "slack"               # Slack channels and messages

    @property
    def requires_authentication(self) -> bool:
        """Check if this source type requires authentication."""
        authenticated_sources = {
            IngestionSourceType.GITHUB,
            IngestionSourceType.GITLAB,
            IngestionSourceType.JIRA,
            IngestionSourceType.CONFLUENCE,
            IngestionSourceType.DATABASE,
            IngestionSourceType.API,
            IngestionSourceType.SLACK
        }
        return self in authenticated_sources

    @property
    def supports_incremental_sync(self) -> bool:
        """Check if this source type supports incremental synchronization."""
        incremental_sources = {
            IngestionSourceType.GITHUB,
            IngestionSourceType.GITLAB,
            IngestionSourceType.JIRA,
            IngestionSourceType.CONFLUENCE,
            IngestionSourceType.DATABASE,
            IngestionSourceType.SLACK
        }
        return self in incremental_sources

    @property
    def is_version_controlled(self) -> bool:
        """Check if this source type is version-controlled."""
        return self in (IngestionSourceType.GITHUB, IngestionSourceType.GITLAB)

    @property
    def typical_content_types(self) -> list[str]:
        """Get typical content types for this source."""
        content_types = {
            IngestionSourceType.GITHUB: ["code", "documentation", "issues", "pull_requests"],
            IngestionSourceType.GITLAB: ["code", "documentation", "issues", "merge_requests"],
            IngestionSourceType.JIRA: ["issues", "epics", "tasks", "bugs"],
            IngestionSourceType.CONFLUENCE: ["documentation", "wiki", "knowledge_base"],
            IngestionSourceType.FILESYSTEM: ["documents", "reports", "data_files"],
            IngestionSourceType.WEB: ["web_pages", "articles", "documentation"],
            IngestionSourceType.DATABASE: ["tables", "queries", "reports"],
            IngestionSourceType.API: ["json", "xml", "data_feeds"],
            IngestionSourceType.EMAIL: ["messages", "attachments", "threads"],
            IngestionSourceType.SLACK: ["messages", "files", "threads"]
        }
        return content_types.get(self, [])

    def __str__(self) -> str:
        return self.value
