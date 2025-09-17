"""Request and response models for Discovery Agent service.

Contains all Pydantic models used for API requests and responses.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class DiscoverRequest(BaseModel):
    """Input for discovery.

    - `spec`: Optional inline OpenAPI for offline/testing flows
    - `openapi_url`: Fetch spec from URL when provided
    - `orchestrator_url`: Override orchestrator base for tests
    """
    name: str
    base_url: str
    openapi_url: Optional[str] = None  # e.g., http://service:port/openapi.json
    spec: Optional[dict] = None  # inline OpenAPI for testing/offline
    dry_run: bool = False
    orchestrator_url: Optional[str] = None


class ToolDiscoveryRequest(BaseModel):
    """Input for LangGraph tool discovery.

    - `service_name`: Name of the service to discover tools for
    - `service_url`: Base URL of the service
    - `openapi_url`: OpenAPI spec URL for the service
    - `tool_categories`: Categories of tools to discover (optional filter)
    - `dry_run`: Test mode without actual registration
    """
    service_name: str
    service_url: str
    openapi_url: Optional[str] = None
    tool_categories: Optional[List[str]] = None  # Filter by tool categories
    dry_run: bool = False
    orchestrator_url: Optional[str] = None
