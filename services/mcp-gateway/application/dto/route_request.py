"""Route Request DTO."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class RouteRequest:
    """
    DTO for routing a request to an MCP instance.
    """
    
    # Required fields
    mcp_id: str  # Target MCP type
    method: str  # HTTP method (GET, POST, etc.)
    path: str  # Request path
    
    # Optional fields
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    query_params: Dict[str, str] = field(default_factory=dict)
    
    # Routing preferences
    tier: Optional[int] = None
    session_id: Optional[str] = None  # For sticky sessions
    timeout_seconds: int = 30
    
    # Metadata
    request_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the request."""
        if not self.mcp_id:
            raise ValueError("mcp_id is required")
        if not self.method:
            raise ValueError("method is required")
        if not self.path:
            raise ValueError("path is required")

