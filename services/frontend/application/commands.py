"""Frontend commands for CQRS pattern compliance."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class UpdateUIViewCommand(BaseModel):
    """Command to update UI view."""
    user_id: str
    view: str
    data: Optional[Dict[str, Any]] = None


class CreateUISessionCommand(BaseModel):
    """Command to create UI session."""
    user_id: str
    session_id: str
    initial_view: str = "dashboard"


class RecordUserInteractionCommand(BaseModel):
    """Command to record user interaction."""
    user_id: str
    interaction_type: str
    element_id: str
    data: Optional[Dict[str, Any]] = None


class UpdateUIStateCommand(BaseModel):
    """Command to update UI state."""
    user_id: str
    state: str
    data: Optional[Dict[str, Any]] = None
