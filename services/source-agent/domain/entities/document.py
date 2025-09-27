"""Document domain entity."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class Document:
    """Domain entity representing a document from a source system.

    Encapsulates document data and metadata from various source systems
    like GitHub, Jira, Confluence, etc.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str = ""  # github, jira, confluence, etc.
    source_id: str = ""  # repository path, issue key, page ID, etc.
    title: str = ""
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: Optional[str] = None
    author: Optional[str] = None
    status: str = "active"  # active, archived, deleted

    def __post_init__(self):
        """Validate document after initialization."""
        if not self.source_type.strip():
            raise ValueError("Source type cannot be empty")
        if not self.source_id.strip():
            raise ValueError("Source ID cannot be empty")
        if not self.title.strip():
            raise ValueError("Title cannot be empty")

        # Ensure valid source types
        valid_sources = ["github", "jira", "confluence", "gitlab", "bitbucket", "filesystem"]
        if self.source_type.lower() not in valid_sources:
            raise ValueError(f"Invalid source type: {self.source_type}")

    @property
    def is_recent(self) -> bool:
        """Check if document was fetched recently (within last hour)."""
        time_diff = datetime.now(timezone.utc) - self.fetched_at
        return time_diff.total_seconds() < 3600  # 1 hour

    @property
    def content_length(self) -> int:
        """Get the length of document content."""
        return len(self.content)

    @property
    def has_metadata(self) -> bool:
        """Check if document has additional metadata."""
        return bool(self.metadata)

    def update_content(self, new_content: str, new_metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update document content and metadata."""
        if not new_content.strip():
            raise ValueError("Content cannot be empty")

        self.content = new_content
        self.updated_at = datetime.now(timezone.utc)

        if new_metadata:
            self.metadata.update(new_metadata)

    def add_tag(self, tag: str) -> None:
        """Add a tag to the document."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the document."""
        if tag in self.tags:
            self.tags.remove(tag)

    def mark_as_archived(self) -> None:
        """Mark document as archived."""
        self.status = "archived"
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_deleted(self) -> None:
        """Mark document as deleted."""
        self.status = "deleted"
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "fetched_at": self.fetched_at.isoformat(),
            "version": self.version,
            "author": self.author,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Document':
        """Create Document from dictionary."""
        # Handle datetime conversion
        for date_field in ['created_at', 'updated_at', 'fetched_at']:
            if isinstance(data.get(date_field), str):
                data[date_field] = datetime.fromisoformat(data[date_field].replace('Z', '+00:00'))

        return cls(**data)
