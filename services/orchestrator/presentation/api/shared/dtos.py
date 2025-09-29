"""Shared DTOs for cross-cutting concerns"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List
from datetime import datetime


class DemoE2ERequest(BaseModel):
    """Request for E2E demo operations."""
    scenario: str = Field("basic_ingestion", min_length=1, max_length=100)
    parameters: Optional[Dict[str, Any]] = None


class JobRecalcQualityRequest(BaseModel):
    """Request for quality recalculation jobs."""
    target_services: List[str] = Field(default_factory=list)
    force_recalc: bool = False

    @field_validator('target_services')
    @classmethod
    def validate_target_services(cls, v):
        if len(v) > 50:
            raise ValueError('Too many target services (max 50)')
        return v


class NotifyConsolidationRequest(BaseModel):
    """Request for consolidation notifications."""
    consolidation_id: str = Field(..., min_length=1, max_length=255)
    notification_channels: List[str] = Field(default_factory=lambda: ["email"])
    recipients: Optional[List[str]] = None

    @field_validator('consolidation_id')
    @classmethod
    def validate_consolidation_id(cls, v):
        if not v.strip():
            raise ValueError('Consolidation ID cannot be empty')
        return v.strip()

    @field_validator('notification_channels')
    @classmethod
    def validate_notification_channels(cls, v):
        valid_channels = ['email', 'slack', 'webhook', 'sms']
        for channel in v:
            if channel not in valid_channels:
                raise ValueError(f'Invalid notification channel: {channel}. Must be one of: {", ".join(valid_channels)}')
        return v


class DocStoreSaveRequest(BaseModel):
    """Request for docstore save operations."""
    documents: List[Dict[str, Any]] = Field(..., min_items=1)
    collection: str = Field("default", min_length=1, max_length=100)
    metadata: Optional[Dict[str, Any]] = None

    @field_validator('documents')
    @classmethod
    def validate_documents(cls, v):
        if len(v) > 1000:
            raise ValueError('Too many documents (max 1000)')
        return v


class QualityRecalcResultResponse(BaseModel):
    """Response containing quality recalculation results."""
    service_name: str
    documents_processed: int
    quality_improvements: int
    errors: List[str]

    class Config:
        from_attributes = True


class ConsolidationNotificationResponse(BaseModel):
    """Response containing consolidation notification details."""
    consolidation_id: str
    status: str
    recipients_notified: int
    channels_used: List[str]
    sent_at: str

    class Config:
        from_attributes = True
