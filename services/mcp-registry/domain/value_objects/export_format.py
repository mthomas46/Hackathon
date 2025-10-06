"""Export Format Value Object."""

from enum import Enum
from typing import Dict


class ExportFormat(str, Enum):
    """
    Export/import formats for MCP packages.
    
    Different formats optimize for different use cases.
    """
    
    MSGPACK = "msgpack"
    """MessagePack format - compact, fast binary serialization."""
    
    JSON = "json"
    """JSON format - human-readable, widely compatible."""
    
    COMPRESSED_TAR = "compressed_tar"
    """Compressed tarball - includes all artifacts."""
    
    ZIP = "zip"
    """ZIP archive - cross-platform compatibility."""
    
    DOCKER_IMAGE = "docker_image"
    """Docker image - complete containerized MCP."""
    
    @property
    def is_binary(self) -> bool:
        """Check if format is binary."""
        return self in {
            ExportFormat.MSGPACK,
            ExportFormat.COMPRESSED_TAR,
            ExportFormat.ZIP,
            ExportFormat.DOCKER_IMAGE,
        }
    
    @property
    def is_human_readable(self) -> bool:
        """Check if format is human-readable."""
        return self == ExportFormat.JSON
    
    @property
    def supports_compression(self) -> bool:
        """Check if format supports/includes compression."""
        return self in {
            ExportFormat.MSGPACK,  # Often compressed
            ExportFormat.COMPRESSED_TAR,
            ExportFormat.ZIP,
        }
    
    @property
    def file_extension(self) -> str:
        """Get typical file extension for format."""
        extensions: Dict[ExportFormat, str] = {
            ExportFormat.MSGPACK: ".msgpack",
            ExportFormat.JSON: ".json",
            ExportFormat.COMPRESSED_TAR: ".tar.gz",
            ExportFormat.ZIP: ".zip",
            ExportFormat.DOCKER_IMAGE: ".tar",  # Docker save format
        }
        return extensions[self]
    
    @property
    def mime_type(self) -> str:
        """Get MIME type for format."""
        mime_types: Dict[ExportFormat, str] = {
            ExportFormat.MSGPACK: "application/msgpack",
            ExportFormat.JSON: "application/json",
            ExportFormat.COMPRESSED_TAR: "application/gzip",
            ExportFormat.ZIP: "application/zip",
            ExportFormat.DOCKER_IMAGE: "application/x-tar",
        }
        return mime_types[self]
    
    @classmethod
    def get_recommended(cls, size_mb: float, requires_portability: bool = False) -> "ExportFormat":
        """
        Recommend format based on MCP size and requirements.
        
        Args:
            size_mb: MCP size in megabytes
            requires_portability: Whether cross-platform portability is critical
        
        Returns:
            Recommended ExportFormat
        """
        # Small MCPs (< 10MB) - use MessagePack for speed
        if size_mb < 10:
            return cls.MSGPACK
        
        # Medium MCPs (10-100MB)
        if size_mb < 100:
            if requires_portability:
                return cls.ZIP
            else:
                return cls.COMPRESSED_TAR
        
        # Large MCPs (100MB+) - use Docker image for containerization
        return cls.DOCKER_IMAGE

