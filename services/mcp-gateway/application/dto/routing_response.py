"""Routing Response DTO."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class RoutingResponse:
    """
    DTO for routing response.
    
    Contains the routed request result and metadata.
    """
    
    # Status
    success: bool
    status_code: int
    
    # Response data
    body: Optional[Any] = None
    headers: Dict[str, str] = None
    
    # Routing metadata
    instance_id: str = ""
    instance_url: str = ""
    response_time_ms: float = 0.0
    strategy_used: str = ""
    
    # Error information
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.headers is None:
            self.headers = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "status_code": self.status_code,
            "body": self.body,
            "headers": self.headers,
            "instance_id": self.instance_id,
            "instance_url": self.instance_url,
            "response_time_ms": self.response_time_ms,
            "strategy_used": self.strategy_used,
            "error_message": self.error_message,
            "error_type": self.error_type,
        }

