"""SourceConfig Value Object."""

from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class SourceConfig:
    """
    Source configuration value object.
    
    Immutable configuration for documentation sources.
    """
    
    source_type: str  # git, github_api, confluence, jira, etc.
    url: str
    credentials: Optional[str] = None  # API key, token, etc.
    branch: Optional[str] = "main"
    path: Optional[str] = "/"
    file_patterns: tuple = ("*.md", "*.rst")
    exclude_patterns: tuple = ()
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.source_type:
            raise ValueError("Source type is required")
        if not self.url:
            raise ValueError("Source URL is required")
        
        # Validate source type
        valid_types = ("git", "github_api", "gitlab_api", "confluence", "jira", "local")
        if self.source_type not in valid_types:
            raise ValueError(f"Invalid source type. Must be one of: {valid_types}")
    
    def is_git_source(self) -> bool:
        """Check if source is Git-based."""
        return self.source_type in ("git", "github_api", "gitlab_api")
    
    def is_api_source(self) -> bool:
        """Check if source is API-based."""
        return self.source_type in ("github_api", "gitlab_api", "confluence", "jira")
    
    def requires_auth(self) -> bool:
        """Check if source requires authentication."""
        return self.credentials is not None

