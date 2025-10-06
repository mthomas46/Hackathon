"""API Request Models - Pydantic models for incoming requests."""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, validator


class StoreContextRequest(BaseModel):
    """
    Request model for storing MCP context.
    
    Example:
        {
            "mcp_id": "mcp-123",
            "context_type": "instance",
            "data": {"status": "hot", "queries": 145},
            "metadata": {"tier": "0"},
            "ttl": 7200,
            "tags": ["tier-0", "production"]
        }
    """
    
    mcp_id: str = Field(
        ...,
        description="MCP instance ID",
        min_length=1,
        example="mcp-123"
    )
    
    context_type: str = Field(
        ...,
        description="Type of context (instance, training, knowledge, etc.)",
        example="instance"
    )
    
    data: Dict[str, Any] = Field(
        ...,
        description="Context data payload",
        example={"status": "hot", "queries": 145}
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the context"
    )
    
    ttl: Optional[int] = Field(
        None,
        description="Time-to-live in seconds (uses default if not provided)",
        ge=0,
        example=7200
    )
    
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization and search",
        example=["tier-0", "production"]
    )
    
    @validator('context_type')
    def validate_context_type(cls, v):
        """Validate context type is one of the allowed values."""
        valid_types = [
            "instance", "training", "knowledge", "performance",
            "coordination", "query", "relationship", "error"
        ]
        if v not in valid_types:
            raise ValueError(f"context_type must be one of {valid_types}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "mcp_id": "mcp-123",
                "context_type": "instance",
                "data": {
                    "status": "hot",
                    "queries_today": 145,
                    "avg_response_time_ms": 23
                },
                "metadata": {
                    "tier": "0",
                    "client_id": "acme-corp"
                },
                "ttl": 7200,
                "tags": ["tier-0", "production", "high-traffic"]
            }
        }


class ListContextsRequest(BaseModel):
    """
    Query parameters for listing contexts.
    
    At least one filter must be provided to prevent unfiltered queries.
    """
    
    mcp_id: Optional[str] = Field(
        None,
        description="Filter by MCP instance ID",
        example="mcp-123"
    )
    
    context_type: Optional[str] = Field(
        None,
        description="Filter by context type",
        example="training"
    )
    
    tags: Optional[List[str]] = Field(
        None,
        description="Filter by tags (OR logic)",
        example=["tier-0", "production"]
    )
    
    limit: Optional[int] = Field(
        None,
        description="Maximum number of results",
        ge=1,
        le=1000,
        example=50
    )
    
    @validator('tags', pre=True)
    def parse_tags(cls, v):
        """Parse comma-separated tags if provided as string."""
        if isinstance(v, str):
            return [tag.strip() for tag in v.split(',') if tag.strip()]
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "mcp_id": "mcp-123",
                "context_type": "training",
                "tags": ["tier-0"],
                "limit": 50
            }
        }


class DeleteContextRequest(BaseModel):
    """
    Request model for deleting contexts.
    
    Specify one of: context_id, mcp_id, or delete_expired.
    """
    
    context_id: Optional[str] = Field(
        None,
        description="Delete specific context by ID",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    
    mcp_id: Optional[str] = Field(
        None,
        description="Delete all contexts for an MCP",
        example="mcp-123"
    )
    
    delete_expired: bool = Field(
        False,
        description="Delete all expired contexts"
    )
    
    @validator('delete_expired')
    def validate_deletion_criteria(cls, v, values):
        """Ensure at least one deletion criteria is specified."""
        if not v and not values.get('context_id') and not values.get('mcp_id'):
            raise ValueError(
                "Must specify context_id, mcp_id, or set delete_expired=True"
            )
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "context_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

