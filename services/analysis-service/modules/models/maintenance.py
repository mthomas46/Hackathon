"""Maintenance Models - Maintenance forecasting request and response models."""

from typing import Optional, List, Dict, Any
from pydantic import Field

from .base import BaseModel


class MaintenanceForecastRequest(BaseModel):
    """Request for maintenance forecast."""
    document_id: str = Field(..., description="Document ID to forecast")
    forecast_period_days: Optional[int] = Field(180, ge=1, le=365, description="Forecast period")
    factors: Optional[List[str]] = Field(None, description="Factors to consider")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class MaintenanceForecastResponse(BaseModel):
    """Response for maintenance forecast."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was forecasted")
    maintenance_forecast: Dict[str, Any] = Field(default_factory=dict, description="Maintenance forecast")
    recommended_actions: List[Dict[str, Any]] = Field(default_factory=list, description="Recommended actions")
    priority_level: str = Field(..., description="Priority level")
    execution_time_seconds: float = Field(..., description="Time taken to complete forecast")
    error_message: Optional[str] = Field(None, description="Error message if forecast failed")


class PortfolioMaintenanceForecastRequest(BaseModel):
    """Request for portfolio maintenance forecast."""
    document_ids: List[str] = Field(..., description="Document IDs to forecast")
    forecast_period_days: Optional[int] = Field(180, ge=1, le=365, description="Forecast period")
    factors: Optional[List[str]] = Field(None, description="Factors to consider")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class PortfolioMaintenanceForecastResponse(BaseModel):
    """Response for portfolio maintenance forecast."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_ids: List[str] = Field(..., description="Documents that were forecasted")
    portfolio_forecast: Dict[str, Any] = Field(default_factory=dict, description="Portfolio forecast")
    maintenance_schedule: Dict[str, Any] = Field(default_factory=dict, description="Maintenance schedule")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Resource requirements")
    execution_time_seconds: float = Field(..., description="Time taken to complete forecast")
    error_message: Optional[str] = Field(None, description="Error message if forecast failed")


class QualityDegradationDetectionRequest(BaseModel):
    """Request for quality degradation detection."""
    document_id: str = Field(..., description="Document ID to analyze")
    detection_period_days: Optional[int] = Field(60, ge=1, le=365, description="Detection period")
    degradation_threshold: Optional[float] = Field(0.1, ge=0.0, le=1.0, description="Degradation threshold")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class QualityDegradationDetectionResponse(BaseModel):
    """Response for quality degradation detection."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_id: str = Field(..., description="Document that was analyzed")
    degradation_detected: bool = Field(..., description="Whether degradation was detected")
    degradation_score: float = Field(..., ge=0.0, le=1.0, description="Degradation score")
    degradation_trend: Dict[str, Any] = Field(default_factory=dict, description="Degradation trend")
    quality_metrics: Dict[str, Any] = Field(default_factory=dict, description="Quality metrics")
    alerts: List[str] = Field(default_factory=list, description="Degradation alerts")
    execution_time_seconds: float = Field(..., description="Time taken to complete detection")
    error_message: Optional[str] = Field(None, description="Error message if detection failed")


class PortfolioQualityDegradationRequest(BaseModel):
    """Request for portfolio quality degradation detection."""
    document_ids: List[str] = Field(..., description="Document IDs to analyze")
    detection_period_days: Optional[int] = Field(60, ge=1, le=365, description="Detection period")
    degradation_threshold: Optional[float] = Field(0.1, ge=0.0, le=1.0, description="Degradation threshold")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options")


class PortfolioQualityDegradationResponse(BaseModel):
    """Response for portfolio quality degradation detection."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    document_ids: List[str] = Field(..., description="Documents that were analyzed")
    portfolio_degradation: Dict[str, Any] = Field(default_factory=dict, description="Portfolio degradation")
    degraded_documents: List[str] = Field(default_factory=list, description="Degraded documents")
    quality_trends: Dict[str, Any] = Field(default_factory=dict, description="Quality trends")
    alerts: List[str] = Field(default_factory=list, description="Degradation alerts")
    execution_time_seconds: float = Field(..., description="Time taken to complete detection")
    error_message: Optional[str] = Field(None, description="Error message if detection failed")
