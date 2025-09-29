"""Document Domain Entities.

Core domain entities for document management and provenance tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from uuid import uuid4


class OutputFormat(Enum):
    """Enumeration of supported output formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    TEXT = "text"
    CSV = "csv"


@dataclass
class DocumentProvenance:
    """Domain entity representing document provenance information."""

    document_id: str
    workflow_execution_id: str
    workflow_name: str
    query_id: Optional[str] = None
    user_id: Optional[str] = None
    source_services: List[str] = field(default_factory=list)
    processing_steps: List[Dict[str, Any]] = field(default_factory=list)
    parameters_used: Dict[str, Any] = field(default_factory=dict)
    model_versions: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self):
        """Validate provenance entity."""
        if not self.document_id:
            raise ValueError("Document ID is required")
        if not self.workflow_execution_id:
            raise ValueError("Workflow execution ID is required")

    def add_processing_step(self, step_name: str, step_data: Dict[str, Any]):
        """Add a processing step to provenance."""
        step = {
            "step_name": step_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": step_data,
        }
        self.processing_steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "workflow_execution_id": self.workflow_execution_id,
            "workflow_name": self.workflow_name,
            "query_id": self.query_id,
            "user_id": self.user_id,
            "source_services": self.source_services,
            "processing_steps": self.processing_steps,
            "parameters_used": self.parameters_used,
            "model_versions": self.model_versions,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Document:
    """Domain entity representing a generated document."""

    content: str
    format: OutputFormat
    title: Optional[str] = None
    description: Optional[str] = None
    workflow_execution_id: Optional[str] = None
    query_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    size_bytes: int = field(init=False)

    def __post_init__(self):
        """Validate and initialize document entity."""
        if not self.content:
            raise ValueError("Document content cannot be empty")

        self.size_bytes = len(self.content.encode('utf-8'))

        if self.size_bytes > 50 * 1024 * 1024:  # 50MB limit
            raise ValueError("Document too large (max 50MB)")

        if not self.metadata:
            self.metadata = {}

    def get_content_preview(self, max_length: int = 200) -> str:
        """Get content preview with length limit."""
        if len(self.content) <= max_length:
            return self.content
        return self.content[:max_length] + "..."

    def has_tag(self, tag: str) -> bool:
        """Check if document has specific tag."""
        return tag in self.tags

    def add_tag(self, tag: str):
        """Add tag to document."""
        if tag not in self.tags:
            self.tags.append(tag)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "format": self.format.value,
            "content": self.content,
            "workflow_execution_id": self.workflow_execution_id,
            "query_id": self.query_id,
            "user_id": self.user_id,
            "metadata": self.metadata,
            "tags": self.tags,
            "size_bytes": self.size_bytes,
            "created_at": self.created_at.isoformat(),
        }
