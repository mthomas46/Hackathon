"""Response models for API endpoints."""

from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field


class ParsedQueryResponseModel(BaseModel):
    """Response model for parsed query."""
    
    query_id: str = Field(..., description="Unique query ID")
    original_query: str = Field(..., description="Original query text")
    normalized_query: str = Field(..., description="Normalized query text")
    intent: str = Field(..., description="Classified intent")
    intent_confidence: float = Field(..., description="Intent confidence (0.0-1.0)")
    entities: List[Dict[str, Any]] = Field(..., description="Extracted entities")
    required_tiers: List[int] = Field(..., description="Required MCP tiers")
    primary_tier: Optional[int] = Field(None, description="Primary MCP tier")
    requires_multiple_mcps: bool = Field(..., description="Whether multiple MCPs are needed")
    overall_confidence: float = Field(..., description="Overall confidence (0.0-1.0)")
    confidence_level: str = Field(..., description="Confidence level category")
    estimated_complexity: int = Field(..., description="Estimated complexity (1-10)")
    keywords: List[str] = Field(..., description="Extracted keywords")
    topics: List[str] = Field(..., description="Identified topics")
    temporal_scope: Optional[str] = Field(None, description="Temporal scope")
    parsed_at: str = Field(..., description="Parse timestamp (ISO 8601)")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    cached: bool = Field(..., description="Whether result was cached")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "query-123",
                "original_query": "What coding patterns does Team Alpha use?",
                "normalized_query": "what coding patterns does team alpha use?",
                "intent": "search",
                "intent_confidence": 0.85,
                "entities": [
                    {
                        "text": "Team Alpha",
                        "entity_type": "team",
                        "normalized_value": "team alpha",
                        "confidence": 0.9
                    },
                    {
                        "text": "coding patterns",
                        "entity_type": "code_pattern",
                        "normalized_value": "coding patterns",
                        "confidence": 0.85
                    }
                ],
                "required_tiers": [2, 3],
                "primary_tier": 2,
                "requires_multiple_mcps": False,
                "overall_confidence": 0.82,
                "confidence_level": "high",
                "estimated_complexity": 5,
                "keywords": ["coding", "patterns", "team", "alpha"],
                "topics": ["development", "team"],
                "temporal_scope": None,
                "parsed_at": "2025-10-06T12:00:00Z",
                "processing_time_ms": 145.3,
                "cached": False
            }
        }


class HealthResponseModel(BaseModel):
    """Response model for health check."""
    
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Current timestamp")
    checks: Dict[str, Any] = Field(..., description="Individual health checks")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "mcp-interpreter",
                "version": "1.0.0",
                "timestamp": "2025-10-06T12:00:00Z",
                "checks": {
                    "redis": "healthy",
                    "cache": "enabled"
                }
            }
        }

