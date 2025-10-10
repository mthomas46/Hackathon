"""
Document version models for Ecosystem MCP Service.

Represents historical versions of documents linked to git commits.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentVersion(BaseModel):
    """
    Document version model.
    
    Represents a specific version of a document at a point in time,
    linked to a git commit.
    """
    
    id: int = Field(
        description="Version ID (auto-increment)"
    )
    
    document_id: UUID = Field(
        description="Reference to parent document"
    )
    
    version_number: int = Field(
        ge=1,
        description="Version number (1, 2, 3, ...)"
    )
    
    git_commit_sha: str = Field(
        description="Git commit SHA for this version",
        min_length=40,
        max_length=40
    )
    
    commit_message: str = Field(
        description="Git commit message"
    )
    
    commit_date: datetime = Field(
        description="When commit was made"
    )
    
    content: str = Field(
        description="Document content at this version"
    )
    
    content_hash: str = Field(
        description="SHA256 hash of content",
        min_length=64,
        max_length=64
    )
    
    embedding_id: Optional[UUID] = Field(
        default=None,
        description="Reference to embedding if generated"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "version_number": 3,
                "git_commit_sha": "a" * 40,
                "commit_message": "Update documentation",
                "commit_date": "2025-10-01T12:00:00Z",
                "content_hash": "b" * 64
            }
        }


class VersionDiff(BaseModel):
    """
    Represents a diff between two document versions.
    """
    
    document_id: UUID = Field(
        description="Document these versions belong to"
    )
    
    from_version: int = Field(
        ge=1,
        description="Starting version number"
    )
    
    to_version: int = Field(
        ge=1,
        description="Ending version number"
    )
    
    diff: str = Field(
        description="Unified diff format"
    )
    
    summary: str = Field(
        description="Human-readable summary of changes"
    )
    
    lines_added: int = Field(
        ge=0,
        description="Number of lines added"
    )
    
    lines_removed: int = Field(
        ge=0,
        description="Number of lines removed"
    )
    
    from_commit_sha: str = Field(
        min_length=40,
        max_length=40
    )
    
    to_commit_sha: str = Field(
        min_length=40,
        max_length=40
    )

