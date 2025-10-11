"""
Document models for Ecosystem MCP Service.

Represents documents ingested from the codebase with metadata,
content, and versioning information.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class DocumentMetadata(BaseModel):
    """
    Metadata extracted from documents.
    
    Stored as JSONB in PostgreSQL for flexible querying.
    """
    
    service_name: Optional[str] = Field(
        default=None,
        description="Service this document belongs to"
    )
    
    phase: Optional[str] = Field(
        default=None,
        description="Refactoring phase (if applicable)"
    )
    
    topics: list[str] = Field(
        default_factory=list,
        description="Topics covered in document"
    )
    
    code_snippets: int = Field(
        default=0,
        ge=0,
        description="Number of code snippets"
    )
    
    has_diagrams: bool = Field(
        default=False,
        description="Whether document contains diagrams"
    )
    
    word_count: int = Field(
        default=0,
        ge=0,
        description="Word count"
    )
    
    language: Optional[str] = Field(
        default=None,
        description="Programming language (for code files)"
    )
    
    file_type: str = Field(
        description="File extension (md, py, yaml, etc.)"
    )
    
    tags: list[str] = Field(
        default_factory=list,
        description="User-defined tags"
    )
    
    references: list[str] = Field(
        default_factory=list,
        description="Referenced services or files"
    )
    
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class Document(BaseModel):
    """
    Core document model.
    
    Represents a single document in the ecosystem with full metadata,
    content, and linkage to git history.
    """
    
    id: UUID = Field(
        default_factory=uuid4,
        description="Unique document identifier"
    )
    
    service_name: str = Field(
        description="Service this document belongs to",
        min_length=1,
        max_length=255
    )
    
    file_path: str = Field(
        description="Path to file relative to repo root",
        min_length=1
    )
    
    original_format: str = Field(
        description="Original file format (md, py, yaml, etc.)",
        min_length=1,
        max_length=50
    )
    
    original_content: str = Field(
        description="Original file content (unchanged)"
    )
    
    normalized_content: str = Field(
        description="Normalized markdown content"
    )
    
    content_hash: str = Field(
        description="SHA256 hash of content for deduplication",
        min_length=64,
        max_length=64
    )
    
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When document was first ingested"
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When document was last updated"
    )
    
    git_commit_sha: Optional[str] = Field(
        default=None,
        description="Git commit SHA this version is from",
        min_length=40,
        max_length=40
    )
    
    is_latest: bool = Field(
        default=True,
        description="Whether this is the latest version"
    )
    
    embedding_id: Optional[UUID] = Field(
        default=None,
        description="Reference to embedding in ChromaDB"
    )
    
    metadata: DocumentMetadata = Field(
        default_factory=DocumentMetadata,
        description="Extracted metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "service_name": "expert-finder-service",
                "file_path": "services/expert-finder-service/README.md",
                "original_format": "md",
                "content_hash": "a" * 64,
                "git_commit_sha": "b" * 40,
                "is_latest": True,
                "metadata": {
                    "service_name": "expert-finder-service",
                    "phase": "Phase 7",
                    "topics": ["API", "endpoints", "demos"],
                    "file_type": "md",
                    "word_count": 1500
                }
            }
        }
    
    @field_validator('git_commit_sha')
    @classmethod
    def validate_git_sha(cls, v: Optional[str]) -> Optional[str]:
        """Validate git commit SHA format."""
        if v is not None and len(v) != 40:
            from ..utils.exceptions import ValidationError
            raise ValidationError("Git commit SHA must be exactly 40 characters")
        return v


class DocumentCreate(BaseModel):
    """
    Model for creating a new document.
    
    Excludes auto-generated fields like id, timestamps.
    """
    
    service_name: str = Field(min_length=1, max_length=255)
    file_path: str = Field(min_length=1)
    original_format: str = Field(min_length=1, max_length=50)
    original_content: str
    normalized_content: str
    content_hash: str = Field(min_length=64, max_length=64)
    git_commit_sha: Optional[str] = Field(default=None, min_length=40, max_length=40)
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)


class DocumentUpdate(BaseModel):
    """
    Model for updating an existing document.
    
    All fields optional for partial updates.
    """
    
    original_content: Optional[str] = None
    normalized_content: Optional[str] = None
    content_hash: Optional[str] = Field(default=None, min_length=64, max_length=64)
    git_commit_sha: Optional[str] = Field(default=None, min_length=40, max_length=40)
    is_latest: Optional[bool] = None
    embedding_id: Optional[UUID] = None
    metadata: Optional[DocumentMetadata] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

