"""Model API Routes."""

from fastapi import APIRouter
from typing import List

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.post("/load", response_model=dict)
async def load_model(
    model_id: str,
    name: str,
):
    """Load model."""
    return {
        "status": "loaded",
        "model_id": model_id,
        "name": name,
    }


@router.post("/{model_id}/unload", response_model=dict)
async def unload_model(model_id: str):
    """Unload model."""
    return {
        "status": "unloaded",
        "model_id": model_id,
    }


@router.get("/{model_id}", response_model=dict)
async def get_model(model_id: str):
    """Get model by ID."""
    return {"model_id": model_id}


@router.get("/", response_model=List[dict])
async def list_models():
    """List all models."""
    return []


@router.get("/loaded/list", response_model=List[dict])
async def list_loaded_models():
    """List loaded models."""
    return []

