"""
Git commit models for Ecosystem MCP Service.

Represents git commits and their metadata for document versioning.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


class FileChange(BaseModel):
    """
    Represents a single file change in a commit.
    """
    
    path: str = Field(
        description="File path"
    )
    
    change_type: str = Field(
        description="Type of change (A=added, M=modified, D=deleted, R=renamed)"
    )
    
    insertions: int = Field(
        default=0,
        ge=0,
        description="Number of lines inserted"
    )
    
    deletions: int = Field(
        default=0,
        ge=0,
        description="Number of lines deleted"
    )
    
    old_path: Optional[str] = Field(
        default=None,
        description="Old path if file was renamed"
    )


class GitCommitMetadata(BaseModel):
    """
    Additional git commit metadata.
    """
    
    files_changed: int = Field(
        ge=0,
        description="Number of files changed"
    )
    
    insertions: int = Field(
        ge=0,
        description="Total insertions"
    )
    
    deletions: int = Field(
        ge=0,
        description="Total deletions"
    )
    
    file_changes: list[FileChange] = Field(
        default_factory=list,
        description="Detailed file changes"
    )
    
    branch: Optional[str] = Field(
        default=None,
        description="Branch name"
    )
    
    tags: list[str] = Field(
        default_factory=list,
        description="Git tags at this commit"
    )
    
    extra: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class GitCommit(BaseModel):
    """
    Git commit model.
    
    Represents a single git commit with full metadata.
    Cached to avoid repeated git operations.
    """
    
    sha: str = Field(
        description="Git commit SHA (40 character hex)",
        min_length=40,
        max_length=40
    )
    
    author: str = Field(
        description="Commit author name",
        min_length=1,
        max_length=255
    )
    
    author_email: str = Field(
        description="Commit author email",
        min_length=1,
        max_length=255
    )
    
    date: datetime = Field(
        description="Commit timestamp"
    )
    
    message: str = Field(
        description="Commit message"
    )
    
    metadata: Optional[GitCommitMetadata] = Field(
        default=None,
        description="Additional commit metadata"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "sha": "a" * 40,
                "author": "John Doe",
                "author_email": "john@example.com",
                "date": "2025-10-10T12:00:00Z",
                "message": "feat: Add new feature",
                "metadata": {
                    "files_changed": 3,
                    "insertions": 150,
                    "deletions": 20
                }
            }
        }
    
    @field_validator('sha')
    @classmethod
    def validate_sha(cls, v: str) -> str:
        """Validate git SHA format."""
        if len(v) != 40:
            from ..utils.exceptions import ValidationError
            raise ValidationError("Git SHA must be exactly 40 characters")
        if not all(c in '0123456789abcdef' for c in v.lower()):
            from ..utils.exceptions import ValidationError
            raise ValidationError("Git SHA must be hexadecimal")
        return v.lower()

