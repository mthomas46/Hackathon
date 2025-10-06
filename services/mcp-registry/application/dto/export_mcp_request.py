"""Export MCP Request DTO."""

from dataclasses import dataclass
from typing import Optional, List

from services.mcp_registry.domain.value_objects.export_format import ExportFormat
from services.mcp_registry.domain.value_objects.storage_backend import StorageBackend


@dataclass
class ExportMCPRequest:
    """Request to export an MCP."""
    
    mcp_id: str
    version: Optional[str] = None  # None = latest version
    export_format: ExportFormat = ExportFormat.MSGPACK
    storage_backend: StorageBackend = StorageBackend.LOCAL_FILESYSTEM
    compress: bool = True
    include_dependencies: bool = False
    exported_by: str = "system"
    
    # Optional filters for selective export
    include_vector_db: bool = True
    include_graph_db: bool = True
    include_artifacts: Optional[List[str]] = None  # None = all artifacts
    
    def __post_init__(self):
        """Validate request."""
        if not self.mcp_id:
            raise ValueError("MCP ID is required")

