"""Bedrock proxy queries for CQRS pattern compliance."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GetBedrockModelsQuery(BaseModel):
    """Query to get available Bedrock models."""
    region: Optional[str] = None
    model_family: Optional[str] = None


class GetBedrockRequestStatusQuery(BaseModel):
    """Query to get Bedrock request processing status."""
    request_id: str


class ListBedrockRequestsQuery(BaseModel):
    """Query to list Bedrock requests with filters."""
    status: Optional[str] = None
    model: Optional[str] = None
    limit: int = 50
    offset: int = 0


class GetBedrockMetricsQuery(BaseModel):
    """Query to get Bedrock processing metrics."""
    time_range: str = "24h"
    metric_types: List[str]
