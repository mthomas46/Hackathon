"""LLM Gateway queries for CQRS pattern compliance."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class GetLLMRequestQuery(BaseModel):
    """Query to get LLM request by ID."""
    request_id: str


class ListLLMRequestsQuery(BaseModel):
    """Query to list LLM requests."""
    status: Optional[str] = None
    model: Optional[str] = None
    limit: int = 50
    offset: int = 0


class GetProviderQuery(BaseModel):
    """Query to get provider by ID."""
    provider_id: str


class ListProvidersQuery(BaseModel):
    """Query to list providers."""
    status: Optional[str] = None
    model: Optional[str] = None


class GetAvailableModelsQuery(BaseModel):
    """Query to get available models."""
    pass


class GetGatewayStatsQuery(BaseModel):
    """Query to get gateway statistics."""
    time_range: str = "24h"
