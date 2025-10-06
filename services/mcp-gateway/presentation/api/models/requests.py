"""Request models for API endpoints."""

from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field


class RegisterInstanceRequestModel(BaseModel):
    """Request model for registering an MCP instance."""
    
    mcp_id: str = Field(..., description="MCP identifier")
    host: str = Field(..., description="Hostname or IP address")
    port: int = Field(..., description="Port number", gt=0)
    name: str = Field("", description="Human-readable name")
    tier: int = Field(0, description="MCP tier (0=client, 1=project, etc.)")
    priority: int = Field(100, description="Routing priority (higher = preferred)")
    weight: int = Field(100, description="Load balancing weight")
    max_concurrent_requests: int = Field(100, description="Maximum concurrent requests")
    health_check_url: str = Field("", description="Health check endpoint URL")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mcp_id": "client-acme",
                "host": "mcp-client-acme",
                "port": 3000,
                "name": "ACME Corp Client MCP",
                "tier": 0,
                "priority": 100,
                "weight": 100,
                "max_concurrent_requests": 50,
                "health_check_url": "http://mcp-client-acme:3000/health",
                "tags": ["client", "acme", "production"],
                "metadata": {"version": "1.0.0"}
            }
        }


class RouteRequestModel(BaseModel):
    """Request model for routing a request to an MCP."""
    
    mcp_id: str = Field(..., description="Target MCP type")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    path: str = Field(..., description="Request path")
    headers: Dict[str, str] = Field(default_factory=dict, description="Request headers")
    body: Optional[Any] = Field(None, description="Request body")
    query_params: Dict[str, str] = Field(default_factory=dict, description="Query parameters")
    tier: Optional[int] = Field(None, description="Preferred tier")
    session_id: Optional[str] = Field(None, description="Session ID for sticky sessions")
    timeout_seconds: int = Field(30, description="Request timeout in seconds")
    request_id: str = Field("", description="Request tracking ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mcp_id": "client-acme",
                "method": "POST",
                "path": "/api/query",
                "headers": {"Content-Type": "application/json"},
                "body": {"query": "What are ACME's project preferences?"},
                "query_params": {},
                "tier": 0,
                "session_id": "session-123",
                "timeout_seconds": 30,
                "request_id": "req-456"
            }
        }


class UpdateHealthRequestModel(BaseModel):
    """Request model for updating instance health."""
    
    is_healthy: bool = Field(..., description="Whether the instance is healthy")
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_healthy": True
            }
        }

