"""User Interaction domain entity for DDD compliance."""

from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class InteractionType(Enum):
    """User interaction type enumeration."""
    CLICK = "click"
    SUBMIT = "submit"
    NAVIGATION = "navigation"
    SEARCH = "search"
    FILTER = "filter"
    EXAPI_PORT = "export"


@dataclass
class UserInteraction:
    """Domain entity representing user interaction."""

    id: str
    user_id: str
    interaction_type: InteractionType
    element_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    page_url: Optional[str] = None
    user_agent: Optional[str] = None

    @property
    def interaction_category(self) -> str:
        """Get interaction category."""
        return self.interaction_type.value

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to interaction."""
        self.data[key] = value
