"""Document domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass(frozen=True)
class DocumentId:
    """Value object for document identifier."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Document ID must be a non-empty string")
        if len(self.value) > 500:
            raise ValueError("Document ID too long (max 500 characters)")


@dataclass(frozen=True)
class Content:
    """Value object for document content."""
    text: str
    format: str = "markdown"

    def __post_init__(self):
        if not self.text or not isinstance(self.text, str):
            raise ValueError("Content text must be a non-empty string")
        if self.format not in ["markdown", "html", "plaintext", "json"]:
            raise ValueError("Unsupported content format")


@dataclass(frozen=True)
class Metadata:
    """Value object for document metadata."""
    created_at: datetime
    updated_at: datetime
    author: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at > self.updated_at:
            raise ValueError("Created date cannot be after updated date")


@dataclass
class Document:
    """Document domain entity."""
    id: DocumentId
    title: str
    content: Content
    metadata: Metadata
    repository_id: Optional[str] = None
    version: str = "1.0"

    def __post_init__(self):
        if not self.title or not isinstance(self.title, str):
            raise ValueError("Document title must be a non-empty string")
        if len(self.title) > 200:
            raise ValueError("Document title too long (max 200 characters)")

    def update_content(self, new_content: Content) -> None:
        """Update document content."""
        self.content = new_content
        # In a real implementation, this would trigger domain events

    def update_metadata(self, new_metadata: Metadata) -> None:
        """Update document metadata."""
        self.metadata = new_metadata

    def add_tag(self, tag: str) -> None:
        """Add a tag to the document."""
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the document."""
        if tag in self.metadata.tags:
            self.metadata.tags.remove(tag)

    @property
    def is_recently_updated(self) -> bool:
        """Check if document was updated recently (within last 24 hours)."""
        return (datetime.now() - self.metadata.updated_at).days < 1

    @property
    def word_count(self) -> int:
        """Get word count of document content."""
        return len(self.content.text.split())

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary representation."""
        return {
            'id': self.id.value,
            'title': self.title,
            'content': {
                'text': self.content.text,
                'format': self.content.format
            },
            'metadata': {
                'created_at': self.metadata.created_at.isoformat(),
                'updated_at': self.metadata.updated_at.isoformat(),
                'author': self.metadata.author,
                'tags': self.metadata.tags,
                'properties': self.metadata.properties
            },
            'repository_id': self.repository_id,
            'version': self.version
        }
