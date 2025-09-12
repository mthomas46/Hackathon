"""Ingest Routes for Orchestrator Service"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional

router = APIRouter()

class IngestRequest(BaseModel):
    source: str
    correlation_id: Optional[str] = None
    scope: Optional[Dict[str, Any]] = None

    @field_validator('source')
    @classmethod
    def validate_source(cls, v):
        if not v:
            raise ValueError('Source cannot be empty')
        if len(v) > 100:
            raise ValueError('Source name too long (max 100 characters)')
        return v

    @field_validator('correlation_id')
    @classmethod
    def validate_correlation_id(cls, v):
        if v and len(v) > 255:
            raise ValueError('Correlation ID too long (max 255 characters)')
        return v

@router.post("/ingest")
async def ingest_data(req: IngestRequest):
    """Ingest data from various sources."""
    # Basic validation and acceptance
    return {
        "status": "accepted",
        "source": req.source,
        "correlation_id": req.correlation_id or "auto-generated",
        "timestamp": "2024-01-01T00:00:00Z"
    }
