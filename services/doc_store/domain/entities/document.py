"""Document domain entity for DDD compliance."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class Document:
    """Domain entity representing a document."""

    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1

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
