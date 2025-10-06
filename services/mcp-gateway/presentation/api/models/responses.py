"""Response models for API endpoints."""

from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field


class InstanceResponseModel(BaseModel):
    """Response model for MCP instance data."""
    
    id: str
    mcp_id: str
    name: str
    host: str
    port: int
    base_url: str
    status: str
    health_check_url: str
    last_health_check: Optional[str]
    consecutive_failures: int
    active_requests: int
    total_requests: int
    average_response_time_ms: float
    tier: int
    priority: int
    weight: int
    max_concurrent_requests: int
    registered_at: str
    last_seen_at: str
    version: int
    tags: List[str]
    metadata: Dict[str, Any]
    load_factor: float
    is_available: bool
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "inst-123",
                "mcp_id": "client-acme",
                "name": "ACME Corp Client MCP",
                "host": "mcp-client-acme",
                "port": 3000,
                "base_url": "http://mcp-client-acme:3000",
                "status": "available",
                "health_check_url": "http://mcp-client-acme:3000/health",
                "last_health_check": "2025-10-06T12:00:00Z",
                "consecutive_failures": 0,
                "active_requests": 5,
                "total_requests": 1000,
                "average_response_time_ms": 150.5,
                "tier": 0,
                "priority": 100,
                "weight": 100,
                "max_concurrent_requests": 50,
                "registered_at": "2025-10-06T10:00:00Z",
                "last_seen_at": "2025-10-06T12:00:00Z",
                "version": 5,
                "tags": ["client", "acme"],
                "metadata": {"version": "1.0.0"},
                "load_factor": 0.1,
                "is_available": True
            }
        }


class RoutingResponseModel(BaseModel):
    """Response model for routing result."""
    
    success: bool
    status_code: int
    body: Optional[Any] = None
    headers: Dict[str, str] = Field(default_factory=dict)
    instance_id: str = ""
    instance_url: str = ""
    response_time_ms: float = 0.0
    strategy_used: str = ""
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status_code": 200,
                "body": {"result": "ACME prefers agile methodology"},
                "headers": {"Content-Type": "application/json"},
                "instance_id": "inst-123",
                "instance_url": "http://mcp-client-acme:3000/api/query",
                "response_time_ms": 145.3,
                "strategy_used": "least_loaded",
                "error_message": None,
                "error_type": None
            }
        }


class HealthResponseModel(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Health status (healthy, degraded, unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Current timestamp")
    checks: Dict[str, Any] = Field(default_factory=dict, description="Individual health checks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "mcp-gateway",
                "version": "1.0.0",
                "timestamp": "2025-10-06T12:00:00Z",
                "checks": {
                    "redis": "healthy",
                    "instances": "3 available"
                }
            }
        }

