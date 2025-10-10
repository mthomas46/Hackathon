"""
Data models for data-services-dashboard.

Pydantic models for type-safe data validation and transformation.
"""

from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field, field_validator


class LogEntry(BaseModel):
    """
    Validated log entry from log-collector.
    
    Represents a single datastore operation with full metadata.
    """
    
    # Metadata
    timestamp: datetime = Field(..., description="When the operation occurred")
    service: str = Field(..., min_length=1, max_length=100, description="Service name")
    level: str = Field(default="INFO", description="Log level")
    message: str = Field(default="", max_length=1000, description="Log message")
    
    # Operation details
    operation_type: str = Field(default="unknown", description="Operation type")
    method: str = Field(default="", description="HTTP method")
    path: str = Field(default="", description="API endpoint path")
    
    # Metrics
    status_code: Optional[int] = Field(None, ge=100, le=599, description="HTTP status code")
    duration_ms: Optional[float] = Field(None, ge=0.0, description="Duration in milliseconds")
    success: Optional[bool] = Field(None, description="Whether operation succeeded")
    
    # Tracing
    phase: str = Field(default="", description="Operation phase")
    workflow_id: str = Field(default="", description="Workflow ID")
    
    @field_validator("duration_ms")
    @classmethod
    def validate_duration(cls, v: Optional[float]) -> Optional[float]:
        """Validate duration is reasonable."""
        if v is not None and v > 300000:  # > 5 minutes
            raise ValueError("Duration too large (> 5 minutes)")
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-09T12:00:00Z",
                "service": "doc_store",
                "level": "INFO",
                "message": "Document created",
                "operation_type": "CREATE",
                "method": "POST",
                "path": "/api/v1/documents",
                "status_code": 201,
                "duration_ms": 15.5,
                "success": True,
                "phase": "complete",
                "workflow_id": "wf_abc123"
            }
        }


class MetricsSummary(BaseModel):
    """
    Aggregate metrics calculated from log entries.
    
    Provides summary statistics for dashboard display.
    """
    
    total_operations: int = Field(default=0, ge=0, description="Total operations")
    successful_operations: int = Field(default=0, ge=0, description="Successful operations")
    failed_operations: int = Field(default=0, ge=0, description="Failed operations")
    avg_duration_ms: float = Field(default=0.0, ge=0.0, description="Average duration")
    error_rate: float = Field(default=0.0, ge=0.0, le=100.0, description="Error rate %")
    operations_per_service: Dict[str, int] = Field(
        default_factory=dict,
        description="Operation count per service"
    )
    
    @field_validator("error_rate")
    @classmethod
    def validate_error_rate(cls, v: float) -> float:
        """Ensure error rate is between 0 and 100."""
        return max(0.0, min(100.0, v))
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total_operations": 100,
                "successful_operations": 95,
                "failed_operations": 5,
                "avg_duration_ms": 12.5,
                "error_rate": 5.0,
                "operations_per_service": {
                    "doc_store": 50,
                    "prompt_store": 30,
                    "memory-agent": 20
                }
            }
        }


class DashboardFilter(BaseModel):
    """
    Validated dashboard filter input.
    
    Represents user-selected filters from the dashboard sidebar.
    """
    
    service: Optional[str] = Field(None, max_length=100, description="Service filter")
    time_range: str = Field(
        default="Last 100 operations",
        description="Time range"
    )
    operation_type: Optional[str] = Field(None, description="Operation type filter")
    
    @field_validator("time_range")
    @classmethod
    def validate_time_range(cls, v: str) -> str:
        """Validate time range is one of the allowed values."""
        allowed = ["Last 100 operations", "Last 500 operations", "Last 1000 operations"]
        if v not in allowed:
            return "Last 100 operations"
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "service": "doc_store",
                "time_range": "Last 500 operations",
                "operation_type": "CREATE"
            }
        }

