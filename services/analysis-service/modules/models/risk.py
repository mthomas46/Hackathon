"""Risk Models - Risk assessment request and response models."""

from typing import Optional, List, Dict, Any
from pydantic import Field, field_validator

from .base import BaseModel


class RiskAssessmentRequest(BaseModel):
    """Request for risk assessment."""
    document_id: str = Field(..., description="Document ID to assess")
    risk_factors: Optional[List[str]] = Field(None, description="Risk factors to evaluate")
    assessment_period_days: Optional[int] = Field(90, ge=1, le=365, description="Assessment period")

    @field_validator('risk_factors')
    @classmethod
    def validate_risk_factors(cls, v):
        if v and len(v) > 20:
            raise ValueError('Too many risk factors (max 20)')
        return v


class RiskAssessmentResponse(BaseModel):
    """Response for risk assessment."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was assessed")
    risk_level: str = Field(..., description="Overall risk level")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Risk score")
    risk_factors: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Risk factor details")
    risk_indicators: List[Dict[str, Any]] = Field(default_factory=list, description="Risk indicators")
    mitigation_recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Mitigation recommendations")
    execution_time_seconds: float = Field(..., description="Time taken to complete assessment")
    error_message: Optional[str] = Field(None, description="Error message if assessment failed")


class PortfolioRiskAssessmentRequest(BaseModel):
    """Request for portfolio risk assessment."""
    document_ids: List[str] = Field(..., description="Document IDs to assess")
    risk_factors: Optional[List[str]] = Field(None, description="Risk factors to evaluate")
    assessment_period_days: Optional[int] = Field(90, ge=1, le=365, description="Assessment period")


class PortfolioRiskAssessmentResponse(BaseModel):
    """Response for portfolio risk assessment."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_ids: List[str] = Field(..., description="Documents that were assessed")
    portfolio_risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Portfolio risk assessment")
    high_risk_documents: List[str] = Field(default_factory=list, description="High risk documents")
    risk_mitigation_strategy: Dict[str, Any] = Field(default_factory=dict, description="Risk mitigation strategy")
    execution_time_seconds: float = Field(..., description="Time taken to complete assessment")
    error_message: Optional[str] = Field(None, description="Error message if assessment failed")
