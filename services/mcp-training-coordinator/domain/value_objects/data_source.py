"""Data Source Value Object."""

from enum import Enum
from typing import Dict


class DataSource(str, Enum):
    """
    Data source for MCP training.
    
    Identifies where training data originates from.
    """
    
    GITHUB = "github"
    """GitHub repositories, issues, PRs, commits."""
    
    CONFLUENCE = "confluence"
    """Confluence documentation pages."""
    
    JIRA = "jira"
    """Jira tickets, epics, sprints."""
    
    FULLSTORY = "fullstory"
    """FullStory user session data."""
    
    SLACK = "slack"
    """Slack conversations and channels."""
    
    GOOGLE_DRIVE = "google_drive"
    """Google Drive documents."""
    
    LOCAL_FILES = "local_files"
    """Local filesystem files."""
    
    API_ENDPOINT = "api_endpoint"
    """Custom API endpoint."""
    
    DATABASE = "database"
    """Direct database access."""
    
    @property
    def requires_authentication(self) -> bool:
        """Check if source requires authentication."""
        return self in {
            DataSource.GITHUB,
            DataSource.CONFLUENCE,
            DataSource.JIRA,
            DataSource.FULLSTORY,
            DataSource.SLACK,
            DataSource.GOOGLE_DRIVE,
            DataSource.API_ENDPOINT,
            DataSource.DATABASE,
        }
    
    @property
    def supports_incremental(self) -> bool:
        """Check if source supports incremental updates."""
        return self in {
            DataSource.GITHUB,
            DataSource.CONFLUENCE,
            DataSource.JIRA,
            DataSource.SLACK,
        }
    
    @property
    def typical_rate_limit(self) -> str:
        """Get typical rate limit info."""
        rate_limits: Dict[DataSource, str] = {
            DataSource.GITHUB: "5000 req/hr (authenticated)",
            DataSource.CONFLUENCE: "Varies by plan",
            DataSource.JIRA: "Varies by plan",
            DataSource.FULLSTORY: "Custom limits",
            DataSource.SLACK: "Tier-based limits",
            DataSource.GOOGLE_DRIVE: "10000 req/100s",
            DataSource.LOCAL_FILES: "None",
            DataSource.API_ENDPOINT: "Custom",
            DataSource.DATABASE: "None",
        }
        return rate_limits.get(self, "Unknown")

