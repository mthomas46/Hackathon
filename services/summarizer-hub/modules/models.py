"""Models for Summarizer Hub service.

Pydantic models for API requests and responses in the Summarizer Hub service.
"""

from pydantic import BaseModel, field_validator
from typing import Dict, Any, List, Optional


class SummarizationRequest(BaseModel):
    """Request model for document summarization."""
    content: str
    summary_type: str = "comprehensive"
    max_length: Optional[int] = None
    include_metadata: bool = True

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) < 10:
            raise ValueError('Content too short for meaningful summarization')
        return v.strip()

    @field_validator('summary_type')
    @classmethod
    def validate_summary_type(cls, v):
        valid_types = ['brief', 'comprehensive', 'executive', 'technical']
        if v not in valid_types:
            raise ValueError(f'Summary type must be one of: {valid_types}')
        return v


class CategorizationRequest(BaseModel):
    """Request model for document categorization."""
    content: str
    confidence_threshold: float = 0.7
    max_categories: int = 5

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()

    @field_validator('confidence_threshold')
    @classmethod
    def validate_confidence_threshold(cls, v):
        if v < 0.0 or v > 1.0:
            raise ValueError('Confidence threshold must be between 0.0 and 1.0')
        return v

    @field_validator('max_categories')
    @classmethod
    def validate_max_categories(cls, v):
        if v < 1 or v > 20:
            raise ValueError('Max categories must be between 1 and 20')
        return v


class BatchCategorizationRequest(BaseModel):
    """Request model for batch document categorization."""
    documents: List[Dict[str, Any]]
    confidence_threshold: float = 0.7
    max_categories: int = 5

    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        if not v:
            raise ValueError('Documents list cannot be empty')
        if len(v) > 100:
            raise ValueError('Too many documents (max 100)')
        for i, doc in enumerate(v):
            if 'content' not in doc:
                raise ValueError(f'Document {i} missing content field')
        return v


class PeerReviewRequest(BaseModel):
    """Request model for documentation peer review."""
    content: str
    doc_type: str = "general"
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Content cannot be empty')
        if len(v) < 50:
            raise ValueError('Content too short for meaningful peer review')
        return v.strip()

    @field_validator('doc_type')
    @classmethod
    def validate_doc_type(cls, v):
        valid_types = ['general', 'api_reference', 'user_guide', 'tutorial',
                      'architecture', 'troubleshooting', 'security', 'technical_spec']
        if v not in valid_types:
            raise ValueError(f'Document type must be one of: {valid_types}')
        return v


class DocumentComparisonRequest(BaseModel):
    """Request model for document version comparison."""
    old_content: str
    new_content: str
    doc_type: str = "general"

    @field_validator('old_content')
    @classmethod
    def validate_old_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Old content cannot be empty')
        return v.strip()

    @field_validator('new_content')
    @classmethod
    def validate_new_content(cls, v):
        if not v or not v.strip():
            raise ValueError('New content cannot be empty')
        return v.strip()

    @field_validator('doc_type')
    @classmethod
    def validate_doc_type(cls, v):
        valid_types = ['general', 'api_reference', 'user_guide', 'tutorial',
                      'architecture', 'troubleshooting', 'security', 'technical_spec']
        if v not in valid_types:
            raise ValueError(f'Document type must be one of: {valid_types}')
        return v


class SummarizationResponse(BaseModel):
    """Response model for document summarization."""
    summary: str
    summary_type: str
    original_length: int
    summary_length: int
    compression_ratio: float
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None


class CategorizationResponse(BaseModel):
    """Response model for document categorization."""
    categories: List[Dict[str, Any]]
    primary_category: str
    confidence_score: float
    processing_time: float


class BatchCategorizationResponse(BaseModel):
    """Response model for batch document categorization."""
    results: List[Dict[str, Any]]
    total_documents: int
    successful_categorizations: int
    processing_time: float


class PeerReviewResponse(BaseModel):
    """Response model for documentation peer review."""
    document_title: str
    document_type: str
    overall_assessment: Dict[str, Any]
    criteria_analyses: Dict[str, Any]
    criteria_scores: Dict[str, float]
    feedback: List[Dict[str, Any]]
    review_summary: Dict[str, Any]
    processing_time: float
    review_timestamp: float


class DocumentComparisonResponse(BaseModel):
    """Response model for document version comparison."""
    comparison: Dict[str, Any]
    old_review: Dict[str, Any]
    new_review: Dict[str, Any]
    processing_time: float
    comparison_timestamp: float
