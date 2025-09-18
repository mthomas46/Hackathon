"""Request and response models for LLM Gateway Service.

Contains all Pydantic models used for API requests and responses in the LLM Gateway.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class LLMQuery(BaseModel):
    """Request model for LLM queries."""
    prompt: str = Field(..., description="The main prompt for the LLM")
    provider: Optional[str] = Field(None, description="Preferred LLM provider")
    model: Optional[str] = Field(None, description="Specific model to use")
    context: Optional[str] = Field(None, description="Additional context for the query")
    user_id: Optional[str] = Field(None, description="User identifier for tracking")
    temperature: Optional[float] = Field(0.7, description="Response creativity (0.0-1.0)")
    max_tokens: Optional[int] = Field(1024, description="Maximum response length")
    force_refresh: bool = Field(False, description="Skip cache and force fresh response")


class ChatMessage(BaseModel):
    """Model for chat messages."""
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")
    timestamp: Optional[float] = Field(None, description="Message timestamp")


class EmbeddingRequest(BaseModel):
    """Request model for text embeddings."""
    text: str = Field(..., description="Text to generate embeddings for")
    model: Optional[str] = Field(None, description="Embedding model to use")
    provider: Optional[str] = Field(None, description="Embedding provider")
    user_id: Optional[str] = Field(None, description="User identifier")


class ProviderInfo(BaseModel):
    """Information about an LLM provider."""
    name: str = Field(..., description="Provider name")
    type: str = Field(..., description="Provider type (local/cloud)")
    model: str = Field(..., description="Default model")
    security_level: str = Field(..., description="Security level (high/medium/low)")
    cost_per_token: float = Field(..., description="Cost per token in USD")
    status: str = Field(..., description="Current status")


class GatewayResponse(BaseModel):
    """Response model for LLM Gateway queries."""
    response: str = Field(..., description="LLM response text")
    provider: str = Field(..., description="Provider used for the response")
    tokens_used: int = Field(0, description="Number of tokens consumed")
    processing_time: float = Field(..., description="Time taken to process (seconds)")
    cost: Optional[float] = Field(None, description="Cost of the request in USD")
    cached: bool = Field(False, description="Whether response came from cache")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")


class MetricsResponse(BaseModel):
    """Response model for metrics endpoint."""
    total_requests: int = Field(..., description="Total number of requests")
    requests_by_provider: Dict[str, int] = Field(..., description="Requests grouped by provider")
    total_tokens_used: int = Field(..., description="Total tokens consumed")
    total_cost: float = Field(..., description="Total cost in USD")
    average_response_time: float = Field(..., description="Average response time in seconds")
    cache_hit_rate: float = Field(..., description="Cache hit rate (0.0-1.0)")
    error_rate: float = Field(..., description="Error rate (0.0-1.0)")
    uptime_percentage: float = Field(..., description="Service uptime percentage")


class CacheRequest(BaseModel):
    """Request model for cache operations."""
    pattern: Optional[str] = Field(None, description="Cache key pattern to clear (optional)")
    user_id: Optional[str] = Field(None, description="Clear cache for specific user")


class StreamChunk(BaseModel):
    """Model for streaming response chunks."""
    chunk: str = Field(..., description="Response chunk text")
    finished: bool = Field(False, description="Whether this is the final chunk")
    tokens_so_far: Optional[int] = Field(None, description="Tokens processed so far")


class HealthStatus(BaseModel):
    """Health status model."""
    service: str = Field(..., description="Service health status")
    providers: Dict[str, Dict[str, Any]] = Field(..., description="Provider health statuses")
    cache: Dict[str, Any] = Field(..., description="Cache health status")
    rate_limiter: Dict[str, Any] = Field(..., description="Rate limiter status")
    timestamp: float = Field(..., description="Health check timestamp")
