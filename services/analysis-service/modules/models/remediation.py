"""Remediation Models - Automated remediation request and response models."""

from typing import Optional, List, Dict, Any
from pydantic import Field

from .base import BaseModel


class AutomatedRemediationRequest(BaseModel):
    """Request for automated remediation."""
    document_id: str = Field(..., description="Document ID to remediate")
    issues: List[Dict[str, Any]] = Field(..., description="Issues to remediate")
    remediation_type: Optional[str] = Field("auto", description="Type of remediation")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class AutomatedRemediationResponse(BaseModel):
    """Response for automated remediation."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was remediated")
    success: bool = Field(..., description="Whether remediation was successful")
    changes_applied: int = Field(..., description="Number of changes applied")
    issues_resolved: int = Field(..., description="Number of issues resolved")
    remediation_report: Dict[str, Any] = Field(default_factory=dict, description="Remediation report")
    execution_time_seconds: float = Field(..., description="Time taken to complete remediation")
    error_message: Optional[str] = Field(None, description="Error message if remediation failed")


class RemediationPreviewRequest(BaseModel):
    """Request for remediation preview."""
    document_id: str = Field(..., description="Document ID to preview")
    issues: List[Dict[str, Any]] = Field(..., description="Issues to preview remediation for")
    remediation_type: Optional[str] = Field("auto", description="Type of remediation")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class RemediationPreviewResponse(BaseModel):
    """Response for remediation preview."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was previewed")
    preview_available: bool = Field(..., description="Whether preview is available")
    proposed_changes: List[Dict[str, Any]] = Field(default_factory=list, description="Proposed changes")
    impact_assessment: Dict[str, Any] = Field(default_factory=dict, description="Impact assessment")
    risk_level: str = Field(..., description="Risk level of changes")
    recommendations: List[str] = Field(default_factory=list, description="Remediation recommendations")
    execution_time_seconds: float = Field(..., description="Time taken to generate preview")
    error_message: Optional[str] = Field(None, description="Error message if preview failed")
