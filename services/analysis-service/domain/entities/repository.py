"""Repository domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass(frozen=True)
class RepositoryId:
    """Value object for repository identifier."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Repository ID must be a non-empty string")
        if len(self.value) > 200:
            raise ValueError("Repository ID too long (max 200 characters)")


@dataclass
class Repository:
    """Repository domain entity."""
    id: RepositoryId
    name: str
    url: str
    provider: str  # github, gitlab, bitbucket, etc.
    description: Optional[str] = None
    default_branch: str = "main"
    language: Optional[str] = None
    topics: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_synced_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Repository name must be a non-empty string")
        if len(self.name) > 100:
            raise ValueError("Repository name too long (max 100 characters)")

        if not self.url or not isinstance(self.url, str):
            raise ValueError("Repository URL must be a non-empty string")

        if not self.provider or not isinstance(self.provider, str):
            raise ValueError("Repository provider must be a non-empty string")

        valid_providers = ["github", "gitlab", "bitbucket", "azure_devops", "local"]
        if self.provider not in valid_providers:
            raise ValueError(f"Provider must be one of: {valid_providers}")

    def update_sync_time(self) -> None:
        """Update last synced timestamp."""
        self.last_synced_at = datetime.now()
        self.updated_at = datetime.now()

    def add_topic(self, topic: str) -> None:
        """Add a topic to the repository."""
        if topic not in self.topics:
            self.topics.append(topic)
            self.updated_at = datetime.now()

    def remove_topic(self, topic: str) -> None:
        """Remove a topic from the repository."""
        if topic in self.topics:
            self.topics.remove(topic)
            self.updated_at = datetime.now()

    @property
    def is_synced_recently(self) -> bool:
        """Check if repository was synced recently (within last 24 hours)."""
        if not self.last_synced_at:
            return False
        return (datetime.now() - self.last_synced_at).days < 1

    @property
    def sync_age_days(self) -> Optional[int]:
        """Get age of last sync in days."""
        if not self.last_synced_at:
            return None
        return (datetime.now() - self.last_synced_at).days

    def to_dict(self) -> Dict[str, Any]:
        """Convert repository to dictionary representation."""
        return {
            'id': self.id.value,
            'name': self.name,
            'url': self.url,
            'provider': self.provider,
            'description': self.description,
            'default_branch': self.default_branch,
            'language': self.language,
            'topics': self.topics,
            'metadata': self.metadata,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_synced_recently': self.is_synced_recently,
            'sync_age_days': self.sync_age_days
        }
