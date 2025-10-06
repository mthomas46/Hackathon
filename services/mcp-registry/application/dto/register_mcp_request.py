"""Register MCP Request DTO."""

from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class RegisterMCPRequest:
    """Request to register an MCP in the registry."""
    
    mcp_id: str
    package_id: str
    storage_location: str
    owner_id: str
    
    # Visibility
    is_public: bool = False
    allowed_users: List[str] = field(default_factory=list)
    allowed_organizations: List[str] = field(default_factory=list)
    
    # Metadata
    owner_organization: Optional[str] = None
    maintainers: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate request."""
        if not self.mcp_id:
            raise ValueError("MCP ID is required")
        if not self.package_id:
            raise ValueError("Package ID is required")
        if not self.storage_location:
            raise ValueError("Storage location is required")
        if not self.owner_id:
            raise ValueError("Owner ID is required")

