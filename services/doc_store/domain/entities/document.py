"""Document domain entity for DDD compliance."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field
import hashlib


@dataclass
class Document:
    """Domain entity representing a document."""

    id: str
    content: str
    content_hash: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    correlation_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    version: int = 1
    
    def __post_init__(self):
        """Generate content_hash if not provided."""
        if not self.content_hash and self.content:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()

    def update_content(self, new_content: str) -> None:
        """Update document content."""
        self.content = new_content
        self.updated_at = datetime.utcnow()
        self.version += 1

    def add_tags(self, tags: List[str]) -> None:
        """Add tags to document."""
        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)
        self.updated_at = datetime.utcnow()

    def remove_tags(self, tags: List[str]) -> None:
        """Remove tags from document."""
        for tag in tags:
            if tag in self.tags:
                self.tags.remove(tag)
        self.updated_at = datetime.utcnow()

    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update document metadata."""
        self.metadata.update(metadata)
        self.updated_at = datetime.utcnow()

    @property
    def is_empty(self) -> bool:
        """Check if document is empty."""
        return not self.content.strip()

    @property
    def word_count(self) -> int:
        """Get word count of document."""
        return len(self.content.split())
    
    @classmethod
    def generate_id(cls) -> str:
        """Generate a unique identifier for new entities."""
        from uuid import uuid4
        return str(uuid4())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary representation."""
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            content_hash=data.get("content_hash", ""),
            metadata=data.get("metadata", {}) if isinstance(data.get("metadata"), dict) else {},
            tags=data.get("tags", []) if isinstance(data.get("tags"), list) else [],
            correlation_id=data.get("correlation_id"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now(timezone.utc)),
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) and data.get("updated_at") else None,
            version=data.get("version", 1),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        import json
        return {
            "id": self.id,
            "content": self.content,
            "content_hash": self.content_hash,
            "metadata": json.dumps(self.metadata) if isinstance(self.metadata, dict) else self.metadata,
            "tags": json.dumps(self.tags) if isinstance(self.tags, list) else self.tags,
            "correlation_id": self.correlation_id,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) and self.updated_at else None,
            "version": self.version,
        }
