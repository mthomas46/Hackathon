"""API models for Architecture Digitizer presentation layer.

This module contains all Pydantic models used for API request/response
handling in the Architecture Digitizer service. These models ensure
consistent data validation and serialization across all endpoints.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class APIResponse(BaseModel):
    """Standard API response wrapper for consistent formatting.

    This model provides a standardized response format across all
    Architecture Digitizer endpoints, ensuring consistent API contracts
    and proper documentation generation.
    """

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable response message")
    data: Optional[Any] = Field(None, description="Response data payload")
    request_id: Optional[str] = Field(
        None, description="Unique request identifier for tracing"
    )
    timestamp: Optional[str] = Field(
        None, description="Response timestamp in ISO 8601 format"
    )
    processing_time_ms: Optional[float] = Field(
        None, description="Processing time in milliseconds"
    )


class ErrorResponse(BaseModel):
    """Standard error response for consistent error formatting.

    This model standardizes error responses across the service,
    providing structured error information for API consumers and
    proper error handling documentation.
    """

    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=False, description="Always false for error responses")
    error: Dict[str, Any] = Field(..., description="Error details")
    request_id: Optional[str] = Field(
        None, description="Unique request identifier for tracing"
    )
    timestamp: str = Field(..., description="Error timestamp in ISO 8601 format")


class HealthResponse(BaseModel):
    """Health check response model for architecture digitizer service.

    Provides comprehensive health information including service status,
    supported systems, and operational metrics for monitoring and
    observability purposes.
    """

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: Optional[float] = Field(
        None, description="Service uptime in seconds"
    )
    last_health_check: Optional[str] = Field(
        None, description="Last health check timestamp"
    )
    supported_systems_count: int = Field(
        ..., description="Number of supported diagram systems"
    )
    file_formats_supported: int = Field(
        ..., description="Number of supported file formats"
    )
    normalization_engine_active: bool = Field(
        ..., description="Whether normalization engine is active"
    )
