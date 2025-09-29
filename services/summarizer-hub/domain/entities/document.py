"""Document domain entity.

This module contains the Document aggregate root and related value objects
for the summarizer-hub domain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass(frozen=True)
class DocumentId:
    """Value object for Document ID."""
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Document ID cannot be empty")

    @classmethod
    def generate(cls) -> 'DocumentId':
        """Generate a new DocumentId."""
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass
class DocumentMetadata:
    """Value object for document metadata."""
    source: Optional[str] = None
    author: Optional[str] = None
    created_at: Optional[datetime] = None
    language: str = "en"
    word_count: int = 0
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Document aggregate root.

    Represents a document that can be summarized, categorized, and analyzed.
    This is the central aggregate in the summarizer-hub domain.
    """

    id: DocumentId
    content: str
    title: Optional[str] = None
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1

    def __post_init__(self):
        if not self.content or not self.content.strip():
            raise ValueError("Document content cannot be empty")

        if len(self.content.strip()) < 10:
            raise ValueError("Document content too short for meaningful processing")

        # Ensure updated_at is current
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def update_content(self, new_content: str, new_title: Optional[str] = None) -> None:
        """Update the document content and increment version."""
        if not new_content or not new_content.strip():
            raise ValueError("New content cannot be empty")

        if len(new_content.strip()) < 10:
            raise ValueError("New content too short for meaningful processing")

        self.content = new_content.strip()
        if new_title:
            self.title = new_title
        self.version += 1
        self.updated_at = datetime.now()

    def update_metadata(self, **kwargs) -> None:
        """Update document metadata."""
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
        self.updated_at = datetime.now()

    def add_tag(self, tag: str) -> None:
        """Add a tag to the document."""
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the document."""
        if tag in self.metadata.tags:
            self.metadata.tags.remove(tag)
            self.updated_at = datetime.now()

    def get_word_count(self) -> int:
        """Get the word count of the document content."""
        return len(self.content.split())

    def is_recent(self, days: int = 7) -> bool:
        """Check if the document was created within the last N days."""
        from datetime import timedelta
        return (datetime.now() - self.created_at) < timedelta(days=days)

    @classmethod
    def create(
        cls,
        content: str,
        title: Optional[str] = None,
        source: Optional[str] = None,
        author: Optional[str] = None,
        language: str = "en",
        tags: Optional[List[str]] = None,
    ) -> 'Document':
        """Factory method to create a new document."""
        doc_id = DocumentId.generate()
        metadata = DocumentMetadata(
            source=source,
            author=author,
            language=language,
            tags=tags or [],
        )

        return cls(
            id=doc_id,
            content=content,
            title=title,
            metadata=metadata,
        )
