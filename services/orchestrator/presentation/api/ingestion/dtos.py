"""DTOs for Ingestion API"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List
from datetime import datetime


class IngestRequest(BaseModel):
    """Request to ingest documents."""
    source_url: str = Field(..., min_length=1, max_length=2000)
    source_type: str = Field("github", min_length=1, max_length=50)
    parameters: Optional[Dict[str, Any]] = None

    @field_validator('source_url')
    @classmethod
    def validate_source_url(cls, v):
        if not v.strip():
            raise ValueError('Source URL cannot be empty')
        return v.strip()

    @field_validator('source_type')
    @classmethod
    def validate_source_type(cls, v):
        valid_types = ['github', 'gitlab', 'jira', 'confluence', 'filesystem', 'web', 'database', 'api', 'email', 'slack']
        if v not in valid_types:
            raise ValueError(f'Source type must be one of: {", ".join(valid_types)}')
        return v


class IngestionStatusResponse(BaseModel):
    """Response containing ingestion status."""
    ingestion_id: str
    request_id: str
    status: str
    total_items: int
    successful_items: int
    failed_items: int
    skipped_items: int
    progress_percentage: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class IngestionListResponse(BaseModel):
    """Response containing list of ingestions."""
    ingestions: List[IngestionStatusResponse]
    total: int

    class Config:
        from_attributes = True


class DocumentMetadataResponse(BaseModel):
    """Response containing document metadata."""
    document_id: str
    source_url: str
    title: Optional[str]
    content_type: str
    file_size: Optional[int]
    checksum: Optional[str]
    last_modified: Optional[str]
    created_at: Optional[str]
    author: Optional[str]
    tags: List[str]
    ingestion_timestamp: str

    class Config:
        from_attributes = True
