"""Request and response models for Source Agent service.

Contains all Pydantic models used for API requests and responses.
"""

from typing import Optional, Dict, Any

from pydantic import BaseModel, field_validator


class DocumentRequest(BaseModel):
    """Request model for document fetching."""

    source: str  # github, jira, confluence
    identifier: str  # repo path, issue key, page ID
    scope: Optional[Dict[str, Any]] = None

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        supported = ["github", "jira", "confluence"]
        if v not in supported:
            from pydantic_core import PydanticCustomError

            raise PydanticCustomError(
                "source_not_supported",
                "Unsupported source: {source}. Must be one of {supported}",
                {"source": v, "supported": supported},
            )
        return v

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v, info):
        source = info.data.get("source")
        if source == "github" and ":" not in v:
            from pydantic_core import PydanticCustomError

            raise PydanticCustomError(
                "invalid_github_identifier",
                "GitHub identifier must be in format owner:repo",
            )
        return v


class NormalizationRequest(BaseModel):
    """Request model for data normalization."""

    source: str
    data: Dict[str, Any]
    correlation_id: Optional[str] = None


class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis."""

    source: str
    code: str
    language: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ArchitectureProcessRequest(BaseModel):
    """Request model for architecture processing."""

    diagram_data: str
    diagram_type: str
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Response model for document operations."""

    status: str
    document: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class NormalizationResponse(BaseModel):
    """Response model for normalization operations."""

    status: str
    normalized_data: Dict[str, Any]
    source: str
    processing_time: Optional[float] = None


class CodeAnalysisResponse(BaseModel):
    """Response model for code analysis operations."""

    status: str
    analysis: Dict[str, Any]
    endpoints: Optional[list] = None
    patterns: Optional[list] = None


class ArchitectureProcessResponse(BaseModel):
    """Response model for architecture processing."""

    status: str
    processed_diagram: Dict[str, Any]
    diagram_type: str
    processing_metadata: Optional[Dict[str, Any]] = None


class SourceCapabilities(BaseModel):
    """Model for source capabilities information."""

    source: str
    capabilities: list
    description: Optional[str] = None
