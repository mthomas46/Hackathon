"""Request and response models for Doc Store service.

Contains all Pydantic models used for API requests and responses.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class PutDocumentRequest(BaseModel):
    """Request model for storing documents."""
    id: Optional[str] = None
    content: str
    content_hash: Optional[str] = None
    # Accept any metadata input and coerce to dict inside handler
    metadata: Optional[Any] = None
    correlation_id: Optional[str] = None


class GetDocumentResponse(BaseModel):
    """Response model for document retrieval."""
    id: str
    content: str
    content_hash: str
    metadata: Dict[str, Any]
    created_at: str


class PutAnalysisRequest(BaseModel):
    """Request model for storing analysis results."""
    document_id: Optional[str] = None
    content: Optional[str] = None
    analyzer: Optional[str] = None
    model: Optional[str] = None
    prompt: Optional[str] = None
    result: Dict[str, Any]
    score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class ListAnalysesResponse(BaseModel):
    """Response model for analysis listing."""
    items: List[Dict[str, Any]]


class StyleExamplesResponse(BaseModel):
    """Response model for style examples listing."""
    items: List[Dict[str, Any]]


class ListDocumentsResponse(BaseModel):
    """Response model for document listing."""
    items: List[Dict[str, Any]]


class QualityItem(BaseModel):
    """Quality assessment item."""
    id: str
    created_at: str
    content_hash: str
    stale_days: int
    flags: List[str]
    metadata: Dict[str, Any]
    importance_score: Optional[float] = None


class QualityItemWithBadges(QualityItem):
    """Quality item with badges."""
    badges: List[str] = []


class QualityResponse(BaseModel):
    """Response model for quality assessment."""
    items: List[QualityItemWithBadges]


class SearchResponse(BaseModel):
    """Response model for search operations."""
    items: List[Dict[str, Any]]


class MetadataPatch(BaseModel):
    """Request model for metadata updates."""
    updates: Dict[str, Any]
