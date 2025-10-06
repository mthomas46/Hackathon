"""Package Info Response DTO."""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class PackageInfoResponse:
    """Response with package details."""
    
    # Identity
    package_id: str
    mcp_id: str
    name: str
    version: str
    
    # Export info
    export_format: str
    exported_at: str
    exported_by: str
    
    # Storage
    storage_path: str
    storage_size_bytes: int
    storage_size_mb: float
    
    # Compression
    is_compressed: bool
    compression_ratio: float
    compression_savings_mb: float
    
    # Integrity
    checksum_sha256: str
    checksum_md5: str
    
    # Contents
    included_artifacts: List[str]
    artifact_count: int
    bundled_dependencies: List[str]
    external_dependencies: List[str]
    
    # Manifest summary
    tier: int
    scope: str
    description: str
    has_vector_db: bool
    has_graph_db: bool
    
    # Metadata
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "package_id": self.package_id,
            "mcp_id": self.mcp_id,
            "name": self.name,
            "version": self.version,
            "export_format": self.export_format,
            "exported_at": self.exported_at,
            "exported_by": self.exported_by,
            "storage_path": self.storage_path,
            "storage_size_bytes": self.storage_size_bytes,
            "storage_size_mb": self.storage_size_mb,
            "is_compressed": self.is_compressed,
            "compression_ratio": self.compression_ratio,
            "compression_savings_mb": self.compression_savings_mb,
            "checksum_sha256": self.checksum_sha256,
            "checksum_md5": self.checksum_md5,
            "included_artifacts": self.included_artifacts,
            "artifact_count": self.artifact_count,
            "bundled_dependencies": self.bundled_dependencies,
            "external_dependencies": self.external_dependencies,
            "tier": self.tier,
            "scope": self.scope,
            "description": self.description,
            "has_vector_db": self.has_vector_db,
            "has_graph_db": self.has_graph_db,
            "metadata": self.metadata,
        }

