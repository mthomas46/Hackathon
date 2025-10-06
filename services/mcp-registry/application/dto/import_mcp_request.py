"""Import MCP Request DTO."""

from dataclasses import dataclass
from typing import Optional

from services.mcp_registry.domain.value_objects.export_format import ExportFormat


@dataclass
class ImportMCPRequest:
    """Request to import an MCP."""
    
    package_data: bytes
    export_format: ExportFormat
    imported_by: str = "system"
    
    # Import options
    verify_integrity: bool = True
    run_security_scan: bool = True
    auto_register: bool = True
    make_public: bool = False
    
    # Override settings
    override_mcp_id: Optional[str] = None
    override_owner_id: Optional[str] = None
    override_organization: Optional[str] = None
    
    def __post_init__(self):
        """Validate request."""
        if not self.package_data:
            raise ValueError("Package data is required")

