"""Source domain entity."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class Source:
    """Domain entity representing a source system.

    Encapsulates configuration and metadata for external source systems
    like GitHub repositories, Jira projects, Confluence spaces, etc.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = ""  # github, jira, confluence, etc.
    base_url: str = ""
    credentials: Dict[str, Any] = field(default_factory=dict)  # Encrypted/safe storage
    configuration: Dict[str, Any] = field(default_factory=dict)
    last_sync_at: Optional[datetime] = None
    sync_status: str = "never_synced"  # never_synced, syncing, synced, failed
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

    def __post_init__(self):
        """Validate source after initialization."""
        if not self.name.strip():
            raise ValueError("Source name cannot be empty")
        if not self.type.strip():
            raise ValueError("Source type cannot be empty")
        if not self.base_url.strip():
            raise ValueError("Base URL cannot be empty")

        # Ensure valid source types
        valid_types = ["github", "jira", "confluence", "gitlab", "bitbucket", "filesystem"]
        if self.type.lower() not in valid_types:
            raise ValueError(f"Invalid source type: {self.type}")

        # Validate URL format (basic check)
        if not (self.base_url.startswith("http://") or self.base_url.startswith("https://")):
            if self.type != "filesystem":  # Filesystem can have local paths
                raise ValueError("Base URL must start with http:// or https://")

    @property
    def is_due_for_sync(self) -> bool:
        """Check if source is due for synchronization."""
        if not self.last_sync_at:
            return True

        # Sync every 15 minutes for active sources
        time_since_last_sync = datetime.now(timezone.utc) - self.last_sync_at
        return time_since_last_sync.total_seconds() > 900  # 15 minutes

    @property
    def has_credentials(self) -> bool:
        """Check if source has authentication credentials configured."""
        return bool(self.credentials)

    @property
    def sync_age_minutes(self) -> Optional[float]:
        """Get age of last sync in minutes."""
        if not self.last_sync_at:
            return None
        time_diff = datetime.now(timezone.utc) - self.last_sync_at
        return time_diff.total_seconds() / 60

    def update_sync_status(self, status: str, error_message: Optional[str] = None) -> None:
        """Update synchronization status."""
        valid_statuses = ["never_synced", "syncing", "synced", "failed"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid sync status: {status}")

        self.sync_status = status
        self.updated_at = datetime.now(timezone.utc)

        if status == "synced":
            self.last_sync_at = datetime.now(timezone.utc)
            self.error_message = None
        elif status == "failed":
            self.error_message = error_message
        elif status == "syncing":
            self.error_message = None

    def update_configuration(self, new_config: Dict[str, Any]) -> None:
        """Update source configuration."""
        self.configuration.update(new_config)
        self.updated_at = datetime.now(timezone.utc)

    def update_credentials(self, new_credentials: Dict[str, Any]) -> None:
        """Update source credentials."""
        self.credentials.update(new_credentials)
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        """Activate the source."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        """Deactivate the source."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def get_connection_string(self) -> str:
        """Get formatted connection string for the source."""
        if self.type == "filesystem":
            return f"file://{self.base_url}"
        else:
            return self.base_url

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "base_url": self.base_url,
            "configuration": self.configuration,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "sync_status": self.sync_status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Source':
        """Create Source from dictionary."""
        # Handle datetime conversion
        for date_field in ['last_sync_at', 'created_at', 'updated_at']:
            if isinstance(data.get(date_field), str):
                data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))

        # Remove credentials from dict for security (they should be loaded separately)
        data.pop('credentials', None)

        return cls(**data)
