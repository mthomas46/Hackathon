"""Context API Routes."""

from fastapi import APIRouter
from typing import Optional

router = APIRouter(prefix="/api/v1/context", tags=["context"])


@router.post("/", response_model=dict)
async def create_session(
    model_id: str,
    user_id: Optional[str] = None,
):
    """Create context session."""
    return {
        "status": "created",
        "model_id": model_id,
        "user_id": user_id,
    }


@router.post("/{session_id}/message", response_model=dict)
async def add_message(
    session_id: str,
    role: str,
    content: str,
):
    """Add message to session."""
    return {
        "status": "added",
        "session_id": session_id,
        "role": role,
    }


@router.get("/{session_id}", response_model=dict)
async def get_session(session_id: str):
    """Get session."""
    return {"session_id": session_id}


@router.delete("/{session_id}/clear", response_model=dict)
async def clear_session(session_id: str):
    """Clear session history."""
    return {
        "status": "cleared",
        "session_id": session_id,
    }

