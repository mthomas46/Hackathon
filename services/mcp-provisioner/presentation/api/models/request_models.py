"""Request models for API endpoints."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class ProvisionRequest(BaseModel):
    """Request model for provisioning an MCP instance."""
    
    client_id: str = Field(
        ..., 
        description="Unique client identifier",
        min_length=1,
        max_length=100,
        examples=["client-abc-123"]
    )
    
    tier: int = Field(
        ...,
        description="MCP tier (0=Client-specific, 1=Project, 2=Company, 3=Team, 4=Ecosystem)",
        ge=0,
        le=4,
        examples=[0]
    )
    
    image_name: Optional[str] = Field(
        None,
        description="Docker image name for the MCP instance",
        examples=["client-mcp-tier0:latest"]
    )
    
    memory_limit: Optional[str] = Field(
        "512m",
        description="Memory limit for container",
        examples=["512m", "1g", "2g"]
    )
    
    cpu_shares: Optional[int] = Field(
        1024,
        description="CPU shares (relative weight)",
        ge=1,
        le=10000,
        examples=[1024]
    )
    
    environment_vars: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional environment variables",
        examples=[{"LOG_LEVEL": "DEBUG"}]
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata",
        examples=[{"owner": "team-a", "project": "proj-x"}]
    )
    
    @field_validator("client_id")
    @classmethod
    def validate_client_id(cls, v: str) -> str:
        """Validate client_id format."""
        if not v or v.strip() == "":
            raise ValueError("client_id cannot be empty")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "client-abc-123",
                "tier": 0,
                "memory_limit": "512m",
                "cpu_shares": 1024,
                "metadata": {"owner": "team-a"}
            }
        }


class StartRequest(BaseModel):
    """Request model for starting an MCP instance."""
    pass  # No body needed, mcp_id comes from path


class StopRequest(BaseModel):
    """Request model for stopping an MCP instance."""
    pass  # No body needed, mcp_id comes from path


class DeleteRequest(BaseModel):
    """Request model for deleting an MCP instance."""
    
    force: bool = Field(
        default=False,
        description="Force deletion even if running",
        examples=[False]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "force": False
            }
        }

