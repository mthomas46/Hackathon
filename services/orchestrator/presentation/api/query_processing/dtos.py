"""DTOs for Query Processing API"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List
from datetime import datetime


class ProcessQueryRequest(BaseModel):
    """Request to process a natural language query."""

    query_text: str = Field(..., min_length=1, max_length=2000)
    context: Optional[Dict[str, Any]] = None
    max_results: Optional[int] = Field(50, ge=1, le=1000)
    include_explanation: bool = Field(True)

    @field_validator('query_text')
    @classmethod
    def validate_query_text(cls, v):
        if not v.strip():
            raise ValueError('Query text cannot be empty')
        return v.strip()


class QueryResultResponse(BaseModel):
    """Response containing query result."""

    query_id: str
    original_query: str
    interpreted_intent: str
    confidence_score: float
    results: List[Dict[str, Any]]
    total_results: int
    execution_time_ms: float
    explanation: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str

    class Config:
        from_attributes = True


class QueryHistoryResponse(BaseModel):
    """Response containing query history."""

    query_id: str
    query_text: str
    intent: str
    confidence_score: float
    result_count: int
    execution_time_ms: float
    created_at: str
    status: str

    class Config:
        from_attributes = True


class QueryListResponse(BaseModel):
    """Response containing list of queries."""

    queries: List[QueryHistoryResponse]
    total: int
    page: int
    page_size: int

    class Config:
        from_attributes = True


class StructuredQueryRequest(BaseModel):
    """Request to execute a structured query."""

    query_type: str = Field(..., min_length=1, max_length=100)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    filters: Optional[Dict[str, Any]] = None
    sorting: Optional[Dict[str, str]] = None
    pagination: Optional[Dict[str, int]] = None

    @field_validator('query_type')
    @classmethod
    def validate_query_type(cls, v):
        valid_types = ['search', 'analytics', 'aggregation', 'filter', 'count']
        if v not in valid_types:
            raise ValueError(f'Query type must be one of: {", ".join(valid_types)}')
        return v
