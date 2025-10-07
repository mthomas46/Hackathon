"""DTOs for performance-related responses."""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class PatternPerformanceResponse(BaseModel):
    """Response with pattern performance metrics."""
    
    pattern_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    timeout_executions: int
    success_rate: float
    failure_rate: float
    timeout_rate: float
    
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    
    avg_confidence: float
    avg_sources: float
    avg_response_length: float
    
    health_score: float
    is_degrading: bool
    is_improving: bool
    most_common_error: Optional[str]
    
    first_seen: datetime
    last_updated: datetime
    last_execution: Optional[datetime]
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class MetricsSummaryResponse(BaseModel):
    """Response with overall metrics summary."""
    
    total_executions: int
    successful_executions: int
    failed_executions: int
    timeout_executions: int
    success_rate: float
    failure_rate: float
    timeout_rate: float
    patterns_tracked: int
    degrading_patterns_count: int
    avg_duration_ms: float


class TrendsResponse(BaseModel):
    """Response with trend data."""
    
    hours: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    timeout_executions: int
    success_rate: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    patterns_used: int
