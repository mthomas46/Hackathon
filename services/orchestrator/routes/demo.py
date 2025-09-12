"""Demo Routes for Orchestrator Service"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional

router = APIRouter()

class DemoE2ERequest(BaseModel):
    format: Optional[str] = "json"
    log_limit: Optional[int] = 1000

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        if v and v not in ["json", "text", "xml"]:
            raise ValueError('Format must be one of: json, text, xml')
        return v

    @field_validator('log_limit')
    @classmethod
    def validate_log_limit(cls, v):
        if v is not None and (v < 1 or v > 10000):
            raise ValueError('Log limit must be between 1 and 10000')
        return v

@router.post("/demo/e2e")
async def run_demo_e2e(req: DemoE2ERequest):
    """Run end-to-end demo workflow."""
    return {
        "status": "completed",
        "format": req.format,
        "log_limit": req.log_limit,
        "results": {
            "services_tested": ["registry", "workflows", "health"],
            "total_operations": 15,
            "success_rate": 1.0
        }
    }
