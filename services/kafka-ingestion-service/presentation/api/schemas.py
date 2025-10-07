"""API Request/Response Schemas."""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any


class IngestDocumentRequest(BaseModel):
    """Request to ingest a document."""
    
    document_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    event_type: str = Field(..., description="Event type")
    source_metadata: Dict[str, Any] = Field(..., description="Source metadata")
    content_type: str = Field(default="text/markdown", description="Content type")
    source_url: Optional[str] = Field(None, description="Source URL")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    categories: Optional[List[str]] = Field(None, description="Document categories")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")


class CreateJobRequest(BaseModel):
    """Request to create an ingestion job."""
    
    name: str = Field(..., description="Job name")
    description: str = Field(..., description="Job description")
    source_type: str = Field(..., description="Source type")
    source_config: Dict[str, Any] = Field(..., description="Source configuration")
    created_by: Optional[str] = Field("system", description="Created by user")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Job metadata")

