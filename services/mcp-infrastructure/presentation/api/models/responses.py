"""API Response Models - Pydantic models for outgoing responses."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ContextResponse(BaseModel):
    """
    Response model for a single MCP context.
    
    Represents the full context data returned by the API.
    """
    
    id: str = Field(..., description="Context ID")
    mcp_id: str = Field(..., description="MCP instance ID")
    context_type: str = Field(..., description="Context type")
    data: Dict[str, Any] = Field(..., description="Context data payload")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp (ISO 8601)")
    ttl: int = Field(..., description="Time-to-live in seconds")
    tags: List[str] = Field(default_factory=list, description="Context tags")
    version: int = Field(..., description="Context version")
    is_expired: bool = Field(..., description="Whether the context has expired")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "mcp_id": "mcp-123",
                "context_type": "instance",
                "data": {
                    "status": "hot",
                    "queries_today": 145
                },
                "metadata": {
                    "tier": "0"
                },
                "created_at": "2025-10-06T10:30:00Z",
                "updated_at": "2025-10-06T14:30:00Z",
                "expires_at": "2025-10-06T16:30:00Z",
                "ttl": 7200,
                "tags": ["tier-0", "production"],
                "version": 1,
                "is_expired": False
            }
        }


class ContextListResponse(BaseModel):
    """
    Response model for a list of contexts.
    
    Includes the contexts and metadata about the results.
    """
    
    contexts: List[ContextResponse] = Field(..., description="List of contexts")
    count: int = Field(..., description="Number of contexts returned")
    filters_applied: Dict[str, Any] = Field(
        default_factory=dict,
        description="Filters that were applied"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "contexts": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "mcp_id": "mcp-123",
                        "context_type": "instance",
                        "data": {"status": "hot"},
                        "created_at": "2025-10-06T10:30:00Z",
                        "updated_at": "2025-10-06T14:30:00Z",
                        "expires_at": "2025-10-06T16:30:00Z",
                        "ttl": 7200,
                        "tags": ["tier-0"],
                        "version": 1,
                        "is_expired": False
                    }
                ],
                "count": 1,
                "filters_applied": {
                    "mcp_id": "mcp-123"
                }
            }
        }


class OperationResponse(BaseModel):
    """
    Generic operation response.
    
    Used for operations that don't return specific data.
    """
    
    status: str = Field(..., description="Operation status (success, failure, partial)")
    message: str = Field(..., description="Human-readable message")
    data: Optional[Any] = Field(None, description="Optional data payload")
    errors: List[str] = Field(default_factory=list, description="Error messages if any")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Context stored successfully",
                "data": {
                    "context_id": "550e8400-e29b-41d4-a716-446655440000"
                },
                "errors": [],
                "metadata": {
                    "timestamp": "2025-10-06T14:30:00Z"
                }
            }
        }


class HealthResponse(BaseModel):
    """
    Health check response.
    
    Returns service health status and dependency information.
    """
    
    status: str = Field(..., description="Overall health status (healthy, degraded, unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Check timestamp (ISO 8601)")
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of dependencies"
    )
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "mcp-infrastructure",
                "version": "1.0.0",
                "timestamp": "2025-10-06T14:30:00Z",
                "dependencies": {
                    "redis": "healthy"
                },
                "uptime_seconds": 3600.5
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response model.
    
    Standardized error format for API errors.
    """
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(..., description="Error timestamp (ISO 8601)")
    path: Optional[str] = Field(None, description="Request path that caused the error")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid context type",
                "detail": "context_type must be one of [instance, training, knowledge, ...]",
                "status_code": 400,
                "timestamp": "2025-10-06T14:30:00Z",
                "path": "/api/v1/context"
            }
        }

