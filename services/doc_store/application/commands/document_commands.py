"""Document commands for Doc Store application layer.

Command objects that represent write operations on documents.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class CreateDocumentCommand:
    """Command to create a new document."""

    document_id: str
    content: str
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None

    def __post_init__(self):
        """Validate command data."""
        if not self.document_id or not self.document_id.strip():
            raise ValueError("Document ID cannot be empty")
        if not self.content or not self.content.strip():
            raise ValueError("Document content cannot be empty")


@dataclass
class UpdateDocumentCommand:
    """Command to update an existing document."""

    document_id: str
    content: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    tags: Optional[List[str]] = None

    def __post_init__(self):
        """Validate command data."""
        if not self.document_id or not self.document_id.strip():
            raise ValueError("Document ID cannot be empty")
        if not any([self.content, self.metadata, self.tags]):
            raise ValueError("At least one field must be updated")


@dataclass
class DeleteDocumentCommand:
    """Command to delete a document."""

    document_id: str

    def __post_init__(self):
        """Validate command data."""
        if not self.document_id or not self.document_id.strip():
            raise ValueError("Document ID cannot be empty")


@dataclass
class TagDocumentCommand:
    """Command to add tags to a document."""

    document_id: str
    tags: List[str]

    def __post_init__(self):
        """Validate command data."""
        if not self.document_id or not self.document_id.strip():
            raise ValueError("Document ID cannot be empty")
        if not self.tags:
            raise ValueError("At least one tag must be provided")
