"""Prompts Routes for Orchestrator Service"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional

router = APIRouter()

class PromptUsageRequest(BaseModel):
    prompt_id: str
    input_tokens: Optional[int] = 0
    output_tokens: Optional[int] = 0

    @field_validator('prompt_id')
    @classmethod
    def validate_prompt_id(cls, v):
        if not v:
            raise ValueError('Prompt ID cannot be empty')
        return v

@router.post("/prompts/usage")
async def log_prompt_usage(req: PromptUsageRequest):
    """Log prompt usage."""
    return {
        "status": "logged",
        "prompt_id": req.prompt_id,
        "input_tokens": req.input_tokens,
        "output_tokens": req.output_tokens
    }

@router.get("/prompts/search/{category}/{name}")
async def search_prompts(category: str, name: str):
    """Search for prompts."""
    if len(category) > 100 or len(name) > 100:
        raise HTTPException(status_code=400, detail="Category or name too long")

    return {
        "prompts": [
            {
                "id": f"{category}-{name}",
                "category": category,
                "name": name,
                "content": f"Sample prompt for {category}/{name}"
            }
        ],
        "total": 1
    }
