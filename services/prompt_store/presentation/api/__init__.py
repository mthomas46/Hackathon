"""Prompt Store REST API."""

from fastapi import APIRouter

# Basic API router
api_router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])

@api_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "prompt-store"}

@api_router.get("/")
async def list_prompts():
    """List all prompts."""
    return {"prompts": [], "total": 0}

@api_router.post("/")
async def create_prompt(prompt: dict):
    """Create a new prompt."""
    return {"id": "new-prompt-id", "status": "created"}

@api_router.get("/{prompt_id}")
async def get_prompt(prompt_id: str):
    """Get a specific prompt."""
    return {"id": prompt_id, "content": "Sample prompt"}

@api_router.put("/{prompt_id}")
async def update_prompt(prompt_id: str, prompt: dict):
    """Update a prompt."""
    return {"id": prompt_id, "status": "updated"}

@api_router.delete("/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """Delete a prompt."""
    return {"id": prompt_id, "status": "deleted"}

