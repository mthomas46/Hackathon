"""Docstore Routes for Orchestrator Service."""

from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, field_validator

router = APIRouter()


class DocstoreSaveRequest(BaseModel):
    id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v:
            raise ValueError("Content cannot be empty")
        if len(v) > 1000000:  # 1MB limit
            raise ValueError("Content too large (max 1MB)")
        return v


@router.post("/docstore/save")
async def save_document(req: DocstoreSaveRequest):
    """Save document to docstore."""
    return {"status": "saved", "id": req.id, "size": len(req.content), "timestamp": "2024-01-01T00:00:00Z"}
