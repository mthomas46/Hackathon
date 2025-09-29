"""DTOs for Health Monitoring API"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class HealthCheckRequest(BaseModel):
    """Request for health check."""

    service_name: Optional[str] = Field(None, max_length=255)
    include_details: bool = Field(True)


class SystemHealthResponse(BaseModel):
    """Response containing system health information."""

    overall_status: str
    timestamp: datetime
    services: Dict[str, Dict[str, Any]]
    uptime_seconds: Optional[int]
    version: Optional[str]

    class Config:
        from_attributes = True


class ServiceHealthResponse(BaseModel):
    """Response containing service health information."""

    service_name: str
    status: str
    timestamp: datetime
    response_time_ms: Optional[float]
    version: Optional[str]
    details: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class SystemMetricsResponse(BaseModel):
    """Response containing system metrics."""

    timestamp: datetime
    cpu_usage: Optional[float]
    memory_usage: Optional[float]
    disk_usage: Optional[float]
    active_connections: Optional[int]
    request_count: Optional[int]
    error_count: Optional[int]
    uptime_seconds: Optional[int]

    class Config:
        from_attributes = True


class SystemInfoResponse(BaseModel):
    """Response containing system information."""

    hostname: str
    platform: str
    python_version: str
    service_version: str
    environment: str
    startup_time: datetime
    config: Dict[str, Any]

    class Config:
        from_attributes = True


class ReadinessResponse(BaseModel):
    """Response containing system readiness information."""

    ready: bool
    timestamp: datetime
    checks: Dict[str, Dict[str, Any]]

    class Config:
        from_attributes = True
