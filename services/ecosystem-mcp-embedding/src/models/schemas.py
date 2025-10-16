"""
Pydantic models for API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class EmbedRequest(BaseModel):
    """Request to embed a single text."""
    text: str = Field(..., description="Text to embed", max_length=8000)
    model: Optional[str] = Field(None, description="Model to use (optional)")


class EmbedResponse(BaseModel):
    """Response with single embedding."""
    embedding: List[float] = Field(..., description="Embedding vector")
    dimensions: int = Field(..., description="Embedding dimensions")
    tokens: int = Field(..., description="Estimated token count")
    model: str = Field(..., description="Model used")
    cached: bool = Field(..., description="Whether result was cached")
    duration_ms: float = Field(..., description="Generation time in milliseconds")


class BatchEmbedRequest(BaseModel):
    """Request to embed multiple texts."""
    texts: List[str] = Field(..., description="Texts to embed", max_length=1000)
    model: Optional[str] = Field(None, description="Model to use (optional)")


class BatchEmbedResponse(BaseModel):
    """Response with batch embeddings."""
    embeddings: List[List[float]] = Field(..., description="Embedding vectors")
    dimensions: int = Field(..., description="Embedding dimensions")
    tokens: List[int] = Field(..., description="Estimated token counts")
    model: str = Field(..., description="Model used")
    cache_hits: int = Field(..., description="Number of cache hits")
    cache_misses: int = Field(..., description="Number of cache misses")
    duration_ms: float = Field(..., description="Total processing time in milliseconds")


class NormalizeRequest(BaseModel):
    """Request to normalize document content."""
    content: str = Field(..., description="Raw content to normalize")
    file_path: str = Field(..., description="File path (for extension detection)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class NormalizeResponse(BaseModel):
    """Response with normalized content."""
    content: str = Field(..., description="Normalized markdown content")
    metadata: dict = Field(..., description="Enhanced metadata")
    tokens: int = Field(..., description="Estimated token count")
    cached: bool = Field(..., description="Whether result was cached")
    duration_ms: float = Field(..., description="Processing time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    model: str = Field(..., description="Model loaded")
    redis_connected: bool = Field(..., description="Redis connection status")
    cache_enabled: bool = Field(..., description="Whether caching is enabled")

