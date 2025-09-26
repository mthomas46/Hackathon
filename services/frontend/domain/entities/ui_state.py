"""UI State domain entity for DDD compliance."""

from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class UIState(Enum):
    """UI state enumeration."""
    LOADING = "loading"
    READY = "ready"
    ERROR = "error"
    PROCESSING = "processing"


@dataclass
class UIStateEntity:
    """Domain entity representing UI state."""

    id: str
    user_id: str
    current_view: str
    state: UIState = UIState.READY
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None

    def update_view(self, new_view: str) -> None:
        """Update current view."""
        self.current_view = new_view
        self.updated_at = datetime.utcnow()

    def set_state(self, state: UIState) -> None:
        """Set UI state."""
        self.state = state
        self.updated_at = datetime.utcnow()

    def update_data(self, key: str, value: Any) -> None:
        """Update state data."""
        self.data[key] = value
        self.updated_at = datetime.utcnow()

    @property
    def is_ready(self) -> bool:
        """Check if UI is ready."""
        return self.state == UIState.READY
