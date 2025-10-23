"""
Documentation models for API and business logic.

Pydantic models for documentation runs and artifacts.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class RunStatus(str, Enum):
    """Documentation run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GeneratedDocumentModel(BaseModel):
    """Generated document model (Pydantic)."""
    id: UUID
    run_id: UUID
    document_type: str
    file_path: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentationRunModel(BaseModel):
    """Documentation run model (Pydantic)."""
    id: UUID
    repo_path: str
    status: str  # Use string instead of enum for flexibility
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Optional relationships
    artifacts: List[GeneratedDocumentModel] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class DocumentationRunCreate(BaseModel):
    """Model for creating a documentation run."""
    repo_path: str
    config: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentationRunUpdate(BaseModel):
    """Model for updating a documentation run."""
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    completed_at: Optional[datetime] = None


class DocumentationArtifactCreate(BaseModel):
    """Model for creating a documentation artifact."""
    run_id: UUID
    document_type: str
    file_path: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

