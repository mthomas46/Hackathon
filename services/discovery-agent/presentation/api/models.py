"""API Request and Response Models for Discovery Agent

This module contains all Pydantic models for API requests and responses.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DiscoverRequest(BaseModel):
    """Request model for single service discovery"""

    name: str = Field(..., description="Service name")
    base_url: str = Field(..., description="Base URL of the service")
    openapi_url: Optional[str] = Field(None, description="OpenAPI spec URL")
    spec: Optional[Dict[str, Any]] = Field(None, description="Inline OpenAPI spec")
    dry_run: bool = Field(False, description="Dry run mode for testing")


class BulkDiscoverRequest(BaseModel):
    """Request model for bulk service discovery"""

    services: List[Dict[str, str]] = Field(
        ..., description="List of services to discover"
    )
    auto_detect: bool = Field(
        False, description="Auto-detect services in Docker network"
    )
    include_health_check: bool = Field(
        True, description="Check service health before discovery"
    )
    dry_run: bool = Field(False, description="Dry run mode for testing")
