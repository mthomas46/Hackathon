"""
DTO for pattern performance response.
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime


class TimeWindowMetricsResponse(BaseModel):
    """Metrics for a specific time window."""
    total_executions: int = Field(default=0)
    success_rate: float = Field(default=0.0)
    avg_latency_ms: float = Field(default=0.0)
    avg_cost_cents: float = Field(default=0.0)
    avg_accuracy: float = Field(default=0.0)
    avg_confidence: float = Field(default=0.0)


class PatternPerformanceResponse(BaseModel):
    """Response containing pattern performance metrics."""
    
    pattern_id: str = Field(..., description="Pattern ID")
    pattern_name: str = Field(..., description="Pattern name")
    version: str = Field(..., description="Pattern version")
    
    # Overall Metrics
    total_executions: int = Field(..., description="Total executions")
    success_rate: float = Field(..., description="Overall success rate")
    avg_latency_ms: float = Field(..., description="Average latency")
    p50_latency_ms: float = Field(..., description="P50 latency")
    p95_latency_ms: float = Field(..., description="P95 latency")
    p99_latency_ms: float = Field(..., description="P99 latency")
    avg_cost_cents: float = Field(..., description="Average cost")
    avg_accuracy: float = Field(..., description="Average accuracy")
    avg_confidence: float = Field(..., description="Average confidence")
    
    # Time Windows
    last_hour: TimeWindowMetricsResponse
    last_day: TimeWindowMetricsResponse
    last_week: TimeWindowMetricsResponse
    last_month: TimeWindowMetricsResponse
    
    # Trends
    trend_direction: str = Field(..., description="Trend direction")
    anomalies_detected: List[Dict[str, Any]] = Field(default_factory=list)
    health_status: str = Field(..., description="Health status (healthy/warning/critical)")
    overall_score: float = Field(..., description="Overall performance score (0-1)")
    
    # Timestamps
    last_updated: datetime
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "pattern_id": "pattern-cot-v1",
                "pattern_name": "chain-of-thought",
                "version": "1.0.0",
                "total_executions": 15420,
                "success_rate": 0.96,
                "avg_latency_ms": 1250.5,
                "p50_latency_ms": 1100.0,
                "p95_latency_ms": 2300.0,
                "p99_latency_ms": 3500.0,
                "avg_cost_cents": 0.018,
                "avg_accuracy": 0.89,
                "avg_confidence": 0.85,
                "trend_direction": "stable",
                "health_status": "healthy",
                "overall_score": 0.87,
                "last_updated": "2025-10-07T00:00:00Z",
                "created_at": "2025-10-01T00:00:00Z"
            }
        }
