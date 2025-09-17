"""Repository Models - Repository analysis request and response models."""

from typing import Optional, List, Dict, Any
from pydantic import Field

from .base import BaseModel


class CrossRepositoryAnalysisRequest(BaseModel):
    """Request for cross-repository analysis."""
    repository_ids: List[str] = Field(..., description="Repository IDs to analyze")
    analysis_type: Optional[str] = Field("consistency", description="Type of analysis")
    analysis_scope: Optional[str] = Field("all", description="Scope of analysis")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class CrossRepositoryAnalysisResponse(BaseModel):
    """Response for cross-repository analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    repository_ids: List[str] = Field(..., description="Repositories analyzed")
    repositories_analyzed: int = Field(..., description="Number of repositories analyzed")
    total_documents: int = Field(..., description="Total documents found")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="Consistency score")
    duplicate_content_found: int = Field(..., description="Duplicate content found")
    standardization_opportunities: int = Field(..., description="Standardization opportunities")
    recommendations: List[str] = Field(default_factory=list, description="Analysis recommendations")
    execution_time_seconds: float = Field(..., description="Time taken to complete analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class RepositoryConnectivityRequest(BaseModel):
    """Request for repository connectivity analysis."""
    repository_id: str = Field(..., description="Repository ID to check")
    connection_timeout_seconds: Optional[int] = Field(30, ge=1, le=300, description="Connection timeout")


class RepositoryConnectivityResponse(BaseModel):
    """Response for repository connectivity analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    repository_id: str = Field(..., description="Repository checked")
    connectivity_status: str = Field(..., description="Connectivity status")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    last_successful_access: str = Field(..., description="Last successful access time")
    error_count: int = Field(..., description="Number of connection errors")
    supported_operations: List[str] = Field(default_factory=list, description="Supported operations")
    error_message: Optional[str] = Field(None, description="Error message if connectivity check failed")


class RepositoryConnectorConfigRequest(BaseModel):
    """Request for repository connector configuration."""
    repository_type: str = Field(..., description="Type of repository")
    connection_details: Dict[str, Any] = Field(..., description="Connection details")
    authentication: Optional[Dict[str, Any]] = Field(None, description="Authentication details")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class RepositoryConnectorConfigResponse(BaseModel):
    """Response for repository connector configuration."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    connector_id: str = Field(..., description="Connector ID")
    repository_type: str = Field(..., description="Repository type")
    config_valid: bool = Field(..., description="Configuration validity")
    supported_features: List[str] = Field(default_factory=list, description="Supported features")
    status: str = Field(..., description="Configuration status")
    error_message: Optional[str] = Field(None, description="Error message if configuration failed")


class SupportedConnectorsResponse(BaseModel):
    """Response for supported connectors list."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    connectors: List[Dict[str, Any]] = Field(default_factory=list, description="Available connectors")
    total_count: int = Field(..., description="Total number of connectors")
    error_message: Optional[str] = Field(None, description="Error message if list failed")


class AnalysisFrameworksResponse(BaseModel):
    """Response for available analysis frameworks."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    frameworks: List[Dict[str, Any]] = Field(default_factory=list, description="Available frameworks")
    total_count: int = Field(..., description="Total number of frameworks")
    error_message: Optional[str] = Field(None, description="Error message if list failed")
