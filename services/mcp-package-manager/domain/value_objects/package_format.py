"""PackageFormat Value Object."""

from enum import Enum


class PackageFormat(Enum):
    """Package format types."""
    
    MCP_V1 = "mcp_v1"
    MCP_V2 = "mcp_v2"
    COMPRESSED_TAR = "compressed_tar"
    JSON = "json"
    
    def get_file_extension(self) -> str:
        """Get file extension for format."""
        extensions = {
            PackageFormat.MCP_V1: ".mcp",
            PackageFormat.MCP_V2: ".mcp",
            PackageFormat.COMPRESSED_TAR: ".tar.gz",
            PackageFormat.JSON: ".json",
        }
        return extensions.get(self, ".mcp")

