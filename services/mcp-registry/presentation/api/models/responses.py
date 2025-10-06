"""Response models for API endpoints."""

from typing import Dict, Any

from pydantic import BaseModel


class HealthResponseModel(BaseModel):
    """Health check response."""
    
    status: str
    service: str
    version: str
    timestamp: str
    checks: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "mcp-registry",
                "version": "1.0.0",
                "checks": {
                    "redis": "healthy",
                    "storage": "healthy"
                }
            }
        }

