"""Source type value object."""

from enum import Enum
from typing import Optional, Dict, Any


class SourceType(Enum):
    """Enumeration of supported source system types."""

    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    JIRA = "jira"
    CONFLUENCE = "confluence"
    FILESYSTEM = "filesystem"
    WEB = "web"
    DATABASE = "database"

    @classmethod
    def from_string(cls, value: str) -> Optional['SourceType']:
        """Create source type from string value."""
        try:
            return cls(value.lower())
        except ValueError:
            return None

    def get_display_name(self) -> str:
        """Get human-readable display name."""
        display_names = {
            "github": "GitHub",
            "gitlab": "GitLab",
            "bitbucket": "Bitbucket",
            "jira": "Jira",
            "confluence": "Confluence",
            "filesystem": "File System",
            "web": "Web Source",
            "database": "Database",
        }
        return display_names.get(self.value, self.value.title())

    def supports_versioning(self) -> bool:
        """Check if this source type supports versioning."""
        return self in [self.GITHUB, self.GITLAB, self.BITBUCKET]

    def supports_real_time_sync(self) -> bool:
        """Check if this source type supports real-time synchronization."""
        return self in [self.GITHUB, self.GITLAB, self.JIRA, self.CONFLUENCE]

    def requires_authentication(self) -> bool:
        """Check if this source type requires authentication."""
        return self not in [self.FILESYSTEM, self.WEB]

    def get_default_sync_interval_minutes(self) -> int:
        """Get default synchronization interval in minutes."""
        intervals = {
            self.GITHUB: 15,
            self.GITLAB: 15,
            self.JIRA: 30,
            self.CONFLUENCE: 60,
            self.FILESYSTEM: 5,
            self.WEB: 60,
            self.DATABASE: 10,
        }
        return intervals.get(self, 30)

    def get_api_base_path(self) -> str:
        """Get the typical API base path for this source type."""
        base_paths = {
            self.GITHUB: "/api/v3",
            self.GITLAB: "/api/v4",
            self.JIRA: "/rest/api/3",
            self.CONFLUENCE: "/rest/api",
        }
        return base_paths.get(self, "")

    def validate_connection_params(self, params: Dict[str, Any]) -> bool:
        """Validate connection parameters for this source type."""
        required_params = {
            self.GITHUB: ["token"],
            self.GITLAB: ["token"],
            self.JIRA: ["username", "password"],
            self.CONFLUENCE: ["username", "password"],
            self.FILESYSTEM: ["path"],
            self.WEB: ["url"],
            self.DATABASE: ["connection_string"],
        }

        required = required_params.get(self, [])
        return all(param in params and params[param] for param in required)
