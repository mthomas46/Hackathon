"""
DTO for querying orchestration executions.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ExecutionQueryRequest(BaseModel):
    """Request to query orchestration executions with filters."""
    
    mcp_id: Optional[str] = Field(None, description="Filter by MCP ID")
    pattern_used: Optional[str] = Field(None, description="Filter by pattern")
    success: Optional[bool] = Field(None, description="Filter by success status")
    start_time: Optional[datetime] = Field(None, description="Filter by start time")
    end_time: Optional[datetime] = Field(None, description="Filter by end time")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    
    class Config:
        json_schema_extra = {
            "example": {
                "mcp_id": "mcp-weather-001",
                "pattern_used": "chain-of-thought",
                "success": True,
                "limit": 50,
                "offset": 0
            }
        }
