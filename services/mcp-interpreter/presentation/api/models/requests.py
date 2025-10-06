"""Request models for API endpoints."""

from typing import Dict, Any, Optional

from pydantic import BaseModel, Field


class ParseQueryRequestModel(BaseModel):
    """Request model for parsing a natural language query."""
    
    query: str = Field(..., description="Natural language query to parse", min_length=1, max_length=500)
    user_id: Optional[str] = Field(None, description="Optional user ID for context")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    use_cache: bool = Field(True, description="Whether to use cached results")
    force_reparse: bool = Field(False, description="Force reparsing even if cached")
    include_alternatives: bool = Field(False, description="Include alternative interpretations")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What coding patterns does Team Alpha use?",
                "user_id": "user-123",
                "session_id": "session-456",
                "context": {},
                "use_cache": True,
                "force_reparse": False,
                "include_alternatives": False
            }
        }

