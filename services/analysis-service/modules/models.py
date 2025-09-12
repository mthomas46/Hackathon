"""Request and response models for Analysis Service.

Contains all Pydantic models used for API requests and responses.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, field_validator

from services.shared.models import Finding


class AnalysisRequest(BaseModel):
    """Input for analysis operations."""
    targets: List[str]  # Document IDs or API IDs
    analysis_type: str = "consistency"  # consistency, reporting, combined
    options: Optional[Dict[str, Any]] = None

    @field_validator('targets')
    @classmethod
    def validate_targets(cls, v):
        if not v:
            raise ValueError('Targets cannot be empty')
        if len(v) > 1000:
            raise ValueError('Too many targets (max 1000)')
        for target in v:
            if len(target) > 500:
                raise ValueError('Target too long (max 500 characters)')
        return v

    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v):
        if v not in ["consistency", "reporting", "combined"]:
            raise ValueError('Analysis type must be one of: consistency, reporting, combined')
        return v


class ReportRequest(BaseModel):
    """Input for report generation."""
    kind: str  # summary, life_of_ticket, pr_confidence, trends
    format: str = "json"
    payload: Optional[Dict[str, Any]] = None

    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v):
        if not v:
            raise ValueError('Kind cannot be empty')
        if len(v) > 100:
            raise ValueError('Kind too long (max 100 characters)')
        return v

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if v not in ["json", "pdf", "html", "text"]:
            raise ValueError('Format must be one of: json, pdf, html, text')
        return v


class NotifyOwnersRequest(BaseModel):
    """Input for notification operations."""
    findings: List[Dict[str, Any]]
    channels: List[str] = ["email"]
    priority: str = "medium"

    @field_validator('findings')
    @classmethod
    def validate_findings(cls, v):
        if not v:
            raise ValueError('Findings cannot be empty')
        if len(v) > 1000:
            raise ValueError('Too many findings (max 1000)')
        return v

    @field_validator('channels')
    @classmethod
    def validate_channels(cls, v):
        if not v:
            raise ValueError('Channels cannot be empty')
        if len(v) > 10:
            raise ValueError('Too many channels (max 10)')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v not in ["low", "medium", "high", "urgent"]:
            raise ValueError('Priority must be one of: low, medium, high, urgent')
        return v


class FindingsResponse(BaseModel):
    """Response model for findings."""
    findings: List[Finding]
    count: int
    severity_counts: Dict[str, int]
    type_counts: Dict[str, int]
