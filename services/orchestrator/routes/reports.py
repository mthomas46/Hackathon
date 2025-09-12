"""Reports Routes for Orchestrator Service"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional

router = APIRouter()

class ReportRequest(BaseModel):
    format: Optional[str] = "json"
    type: Optional[str] = "summary"

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if v and v not in ["json", "pdf", "html", "text"]:
            raise ValueError('Format must be one of: json, pdf, html, text')
        return v

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v and v not in ["summary", "detailed", "metrics", "audit"]:
            raise ValueError('Type must be one of: summary, detailed, metrics, audit')
        return v

@router.post("/report/request")
async def request_report(req: ReportRequest):
    """Request a report generation."""
    return {
        "status": "requested",
        "report_id": "report-001",
        "format": req.format,
        "type": req.type,
        "estimated_completion": "2024-01-01T01:00:00Z"
    }
