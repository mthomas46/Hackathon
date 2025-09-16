"""Query Routes for Orchestrator Service"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional

router = APIRouter()

class QueryRequest(BaseModel):
    query: str

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v:
            raise ValueError('Query cannot be empty')
        if len(v) > 5000:
            raise ValueError('Query too long (max 5000 characters)')
        return v

@router.post("/query")
async def process_query(req: QueryRequest):
    """Process natural language query."""
    return {
        "query": req.query,
        "interpreted_intent": "search_documents",
        "confidence": 0.85,
        "results": []
    }

@router.post("/query/execute")
async def execute_query(req: QueryRequest):
    """Execute interpreted query."""
    return {
        "query": req.query,
        "status": "executed",
        "results": {
            "documents_found": 5,
            "services_used": ["doc_store", "analyzer"]
        }
    }
