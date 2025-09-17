"""Document Metadata Value Object"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class DocumentMetadata:
    """Value object representing metadata for ingested documents."""

    def __init__(
        self,
        document_id: str,
        source_url: str,
        title: Optional[str] = None,
        content_type: str = "document",
        file_size: Optional[int] = None,
        checksum: Optional[str] = None,
        last_modified: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        author: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_metadata: Optional[Dict[str, Any]] = None,
        ingestion_timestamp: Optional[datetime] = None
    ):
        self._document_id = document_id.strip()
        self._source_url = source_url.strip()
        self._title = title.strip() if title else None
        self._content_type = content_type.strip()
        self._file_size = file_size
        self._checksum = checksum.strip() if checksum else None
        self._last_modified = last_modified
        self._created_at = created_at
        self._author = author.strip() if author else None
        self._tags = tags or []
        self._custom_metadata = custom_metadata or {}
        self._ingestion_timestamp = ingestion_timestamp or datetime.utcnow()

        self._validate()

    def _validate(self):
        """Validate document metadata."""
        if not self._document_id:
            raise ValueError("Document ID cannot be empty")

        if not self._source_url:
            raise ValueError("Source URL cannot be empty")

        if len(self._document_id) > 255:
            raise ValueError("Document ID too long (max 255 characters)")

        if len(self._source_url) > 2000:
            raise ValueError("Source URL too long (max 2000 characters)")

    @property
    def document_id(self) -> str:
        """Get the unique document ID."""
        return self._document_id

    @property
    def source_url(self) -> str:
        """Get the source URL."""
        return self._source_url

    @property
    def title(self) -> Optional[str]:
        """Get the document title."""
        return self._title

    @property
    def content_type(self) -> str:
        """Get the content type."""
        return self._content_type

    @property
    def file_size(self) -> Optional[int]:
        """Get the file size in bytes."""
        return self._file_size

    @property
    def checksum(self) -> Optional[str]:
        """Get the content checksum."""
        return self._checksum

    @property
    def last_modified(self) -> Optional[datetime]:
        """Get the last modified timestamp."""
        return self._last_modified

    @property
    def created_at(self) -> Optional[datetime]:
        """Get the creation timestamp."""
        return self._created_at

    @property
    def author(self) -> Optional[str]:
        """Get the document author."""
        return self._author

    @property
    def tags(self) -> List[str]:
        """Get the document tags."""
        return self._tags.copy()

    @property
    def custom_metadata(self) -> Dict[str, Any]:
        """Get the custom metadata."""
        return self._custom_metadata.copy()

    @property
    def ingestion_timestamp(self) -> datetime:
        """Get the ingestion timestamp."""
        return self._ingestion_timestamp

    @property
    def has_tags(self) -> bool:
        """Check if document has tags."""
        return len(self._tags) > 0

    @property
    def has_custom_metadata(self) -> bool:
        """Check if document has custom metadata."""
        return len(self._custom_metadata) > 0

    @property
    def age_days(self) -> Optional[float]:
        """Get the document age in days since ingestion."""
        if self._created_at:
            return (datetime.utcnow() - self._created_at).total_seconds() / (24 * 3600)
        return None

    @property
    def file_size_mb(self) -> Optional[float]:
        """Get the file size in MB."""
        if self._file_size:
            return self._file_size / (1024 * 1024)
        return None

    def add_tag(self, tag: str):
        """Add a tag to the document."""
        if tag not in self._tags:
            self._tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove a tag from the document."""
        if tag in self._tags:
            self._tags.remove(tag)

    def set_custom_metadata(self, key: str, value: Any):
        """Set custom metadata."""
        self._custom_metadata[key] = value

    def get_custom_metadata(self, key: str, default: Any = None) -> Any:
        """Get custom metadata value."""
        return self._custom_metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "document_id": self._document_id,
            "source_url": self._source_url,
            "content_type": self._content_type,
            "tags": self._tags,
            "custom_metadata": self._custom_metadata,
            "ingestion_timestamp": self._ingestion_timestamp.isoformat(),
            "has_tags": self.has_tags,
            "has_custom_metadata": self.has_custom_metadata
        }

        if self._title:
            result["title"] = self._title

        if self._file_size is not None:
            result["file_size"] = self._file_size
            result["file_size_mb"] = self.file_size_mb

        if self._checksum:
            result["checksum"] = self._checksum

        if self._last_modified:
            result["last_modified"] = self._last_modified.isoformat()

        if self._created_at:
            result["created_at"] = self._created_at.isoformat()
            result["age_days"] = self.age_days

        if self._author:
            result["author"] = self._author

        return result

    def __repr__(self) -> str:
        return f"DocumentMetadata(document_id='{self._document_id}', title='{self._title or 'Untitled'}', type='{self._content_type}')"
