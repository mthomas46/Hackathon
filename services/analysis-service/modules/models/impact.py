"""Impact Models - Change impact analysis request and response models."""

from typing import Optional, List, Dict, Any
from pydantic import Field

from .base import BaseModel


class ChangeImpactAnalysisRequest(BaseModel):
    """Request for change impact analysis."""
    document_id: str = Field(..., description="Document ID to analyze")
    change_description: str = Field(..., description="Description of the change")
    impact_scope: Optional[str] = Field("related", description="Scope of impact analysis")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class ChangeImpactAnalysisResponse(BaseModel):
    """Response for change impact analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was analyzed")
    affected_documents: List[str] = Field(default_factory=list, description="Affected documents")
    impact_level: str = Field(..., description="Impact level")
    impact_score: float = Field(..., ge=0.0, le=1.0, description="Impact score")
    stakeholders: List[str] = Field(default_factory=list, description="Affected stakeholders")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Risk assessment")
    recommendations: List[str] = Field(default_factory=list, description="Impact recommendations")
    execution_time_seconds: float = Field(..., description="Time taken to complete analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class PortfolioChangeImpactRequest(BaseModel):
    """Request for portfolio change impact analysis."""
    document_ids: List[str] = Field(..., description="Document IDs to analyze")
    change_description: str = Field(..., description="Description of the change")
    impact_scope: Optional[str] = Field("related", description="Scope of impact analysis")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class PortfolioChangeImpactResponse(BaseModel):
    """Response for portfolio change impact analysis."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_ids: List[str] = Field(..., description="Documents that were analyzed")
    portfolio_impact: Dict[str, Any] = Field(default_factory=dict, description="Portfolio impact")
    high_impact_documents: List[str] = Field(default_factory=list, description="High impact documents")
    impact_distribution: Dict[str, int] = Field(default_factory=dict, description="Impact distribution")
    stakeholders: List[str] = Field(default_factory=list, description="Affected stakeholders")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Risk assessment")
    recommendations: List[str] = Field(default_factory=list, description="Impact recommendations")
    execution_time_seconds: float = Field(..., description="Time taken to complete analysis")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
