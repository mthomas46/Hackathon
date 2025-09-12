"""Jobs Routes for Orchestrator Service"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional

router = APIRouter()

class NotifyConsolidationRequest(BaseModel):
    min_confidence: Optional[float] = 0.8
    limit: Optional[int] = 100

    @field_validator('min_confidence')
    @classmethod
    def validate_confidence(cls, v):
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v

    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 2000):
            raise ValueError('Limit must be between 1 and 2000')
        return v

@router.post("/jobs/notify-consolidation")
async def notify_consolidation(req: NotifyConsolidationRequest):
    """Notify about consolidation jobs."""
    return {
        "status": "notified",
        "min_confidence": req.min_confidence,
        "limit": req.limit,
        "jobs_notified": 5
    }
