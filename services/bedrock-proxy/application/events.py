"""Bedrock proxy domain events for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class BedrockRequestReceivedEvent(BaseModel):
    """Event fired when a Bedrock request is received."""
    request_id: str
    model: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class BedrockRequestProcessedEvent(BaseModel):
    """Event fired when a Bedrock request is successfully processed."""
    request_id: str
    processing_time_ms: int
    tokens_used: int
    cost: float
    timestamp: datetime


class BedrockRequestFailedEvent(BaseModel):
    """Event fired when a Bedrock request fails."""
    request_id: str
    error_code: str
    error_message: str
    timestamp: datetime
    retry_count: int = 0


class BedrockModelUsageEvent(BaseModel):
    """Event fired to track model usage."""
    model: str
    request_count: int
    total_tokens: int
    total_cost: float
    time_period: str
    timestamp: datetime
