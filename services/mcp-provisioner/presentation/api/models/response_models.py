"""Response models for API endpoints."""

from typing import Any, Optional, List, Dict
from datetime import datetime
from pydantic import BaseModel, Field


class MCPStatusResponse(BaseModel):
    """Response model for MCP instance status."""
    
    mcp_id: str = Field(..., description="MCP instance ID")
    client_id: str = Field(..., description="Client ID")
    name: str = Field(..., description="MCP instance name")
    state: str = Field(..., description="Current state (cold/warming/hot/cooling/error)")
    container_id: Optional[str] = Field(None, description="Docker container ID")
    ip_address: Optional[str] = Field(None, description="Container IP address")
    external_port: Optional[int] = Field(None, description="External port mapping")
    tier: int = Field(..., description="MCP tier")
    image_name: str = Field(..., description="Docker image name")
    created_at: Optional[str] = Field(None, description="Creation timestamp (ISO 8601)")
    updated_at: Optional[str] = Field(None, description="Last update timestamp (ISO 8601)")
    last_accessed_at: Optional[str] = Field(None, description="Last access timestamp (ISO 8601)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    health_status: Optional[str] = Field(None, description="Health status (healthy/unhealthy/unknown)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mcp_id": "550e8400-e29b-41d4-a716-446655440000",
                "client_id": "client-abc-123",
                "name": "mcp-client-abc-123-tier0",
                "state": "hot",
                "container_id": "a1b2c3d4e5f6",
                "ip_address": "172.20.0.50",
                "external_port": 9001,
                "tier": 0,
                "image_name": "client-mcp-tier0:latest",
                "created_at": "2025-10-06T10:00:00Z",
                "updated_at": "2025-10-06T10:05:00Z",
                "last_accessed_at": "2025-10-06T10:05:00Z",
                "metadata": {"owner": "team-a"},
                "health_status": "healthy"
            }
        }


class OperationResponse(BaseModel):
    """Standard response model for operations."""
    
    status: str = Field(..., description="Operation status (success/failure/partial/pending)")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Any] = Field(None, description="Response data (if any)")
    errors: List[str] = Field(default_factory=list, description="Error messages (if any)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "MCP instance started successfully",
                "data": None,
                "errors": [],
                "metadata": {}
            }
        }


class ListMCPsResponse(BaseModel):
    """Response model for listing MCP instances."""
    
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Human-readable message")
    data: List[MCPStatusResponse] = Field(..., description="List of MCP instances")
    count: int = Field(..., description="Total count")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Found 2 MCP instances",
                "data": [],
                "count": 2
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Current timestamp (ISO 8601)")
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependencies"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "mcp-provisioner",
                "version": "1.0.0",
                "timestamp": "2025-10-06T10:00:00Z",
                "dependencies": {
                    "redis": "healthy",
                    "docker": "healthy"
                }
            }
        }

