"""Data Transfer Objects for Bedrock proxy operations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class BedrockRequestDto(BaseModel):
    """DTO for Bedrock request data."""
    id: str
    model: str
    prompt: str
    parameters: Optional[Dict[str, Any]] = None
    created_at: datetime
    status: str


class BedrockResponseDto(BaseModel):
    """DTO for Bedrock response data."""
    request_id: str
    response: Dict[str, Any]
    processing_time_ms: int
    tokens_used: Optional[int] = None
    cost: Optional[float] = None


class BedrockModelDto(BaseModel):
    """DTO for Bedrock model information."""
    id: str
    name: str
    provider: str
    capabilities: List[str]
    max_tokens: int
    cost_per_token: float
