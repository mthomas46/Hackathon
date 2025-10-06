"""MCP Package Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, List, Any
import hashlib

from services.mcp_registry.domain.entities.mcp_manifest import MCPManifest
from services.mcp_registry.domain.value_objects.export_format import ExportFormat


@dataclass
class MCPPackage:
    """
    Complete MCP package ready for export/import.
    
    Aggregate root for MCP packaging operations.
    Contains manifest, checksums, and references to artifacts.
    """
    
    # Identity
    package_id: str
    manifest: MCPManifest
    
    # Export metadata
    export_format: ExportFormat
    exported_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    exported_by: str = "system"
    
    # Storage
    storage_path: Optional[str] = None  # Path where package is stored
    storage_size_bytes: int = 0
    
    # Checksums for integrity
    checksum_sha256: Optional[str] = None
    checksum_md5: Optional[str] = None
    
    # Compression
    is_compressed: bool = False
    compression_ratio: float = 1.0  # Ratio of compressed to uncompressed size
    
    # Artifacts included
    included_artifacts: List[str] = field(default_factory=list)
    artifact_checksums: Dict[str, str] = field(default_factory=dict)  # artifact_path -> checksum
    
    # Dependencies
    bundled_dependencies: List[str] = field(default_factory=list)  # Dependencies included
    external_dependencies: List[str] = field(default_factory=list)  # Dependencies not included
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate package."""
        if not self.package_id:
            raise ValueError("Package ID is required")
        if not self.manifest:
            raise ValueError("Manifest is required")
    
    @property
    def mcp_id(self) -> str:
        """Get MCP ID from manifest."""
        return self.manifest.mcp_id
    
    @property
    def name(self) -> str:
        """Get MCP name from manifest."""
        return self.manifest.name
    
    @property
    def version(self):
        """Get MCP version from manifest."""
        return self.manifest.version
    
    def get_storage_size_mb(self) -> float:
        """Get storage size in megabytes."""
        return self.storage_size_bytes / (1024 * 1024)
    
    def get_uncompressed_size_mb(self) -> float:
        """Get estimated uncompressed size in megabytes."""
        if self.is_compressed and self.compression_ratio > 0:
            return self.get_storage_size_mb() / self.compression_ratio
        return self.get_storage_size_mb()
    
    def calculate_checksum(self, data: bytes, algorithm: str = "sha256") -> str:
        """
        Calculate checksum for data.
        
        Args:
            data: Data to checksum
            algorithm: Hash algorithm (sha256 or md5)
        
        Returns:
            Hex digest of checksum
        """
        if algorithm == "sha256":
            return hashlib.sha256(data).hexdigest()
        elif algorithm == "md5":
            return hashlib.md5(data).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    def verify_checksum(self, data: bytes, algorithm: str = "sha256") -> bool:
        """
        Verify checksum of data.
        
        Args:
            data: Data to verify
            algorithm: Hash algorithm
        
        Returns:
            True if checksum matches
        """
        expected = self.checksum_sha256 if algorithm == "sha256" else self.checksum_md5
        if not expected:
            return False
        
        actual = self.calculate_checksum(data, algorithm)
        return actual == expected
    
    def set_checksum(self, data: bytes) -> None:
        """
        Calculate and set checksums for package data.
        
        Args:
            data: Package data
        """
        self.checksum_sha256 = self.calculate_checksum(data, "sha256")
        self.checksum_md5 = self.calculate_checksum(data, "md5")
    
    def add_artifact(self, artifact_path: str, checksum: str) -> None:
        """
        Add artifact to package.
        
        Args:
            artifact_path: Path to artifact
            checksum: Checksum of artifact
        """
        if artifact_path not in self.included_artifacts:
            self.included_artifacts.append(artifact_path)
        self.artifact_checksums[artifact_path] = checksum
    
    def verify_artifact(self, artifact_path: str, data: bytes) -> bool:
        """
        Verify an artifact's integrity.
        
        Args:
            artifact_path: Path to artifact
            data: Artifact data
        
        Returns:
            True if checksum matches
        """
        expected = self.artifact_checksums.get(artifact_path)
        if not expected:
            return False
        
        actual = self.calculate_checksum(data, "sha256")
        return actual == expected
    
    def get_compression_savings_mb(self) -> float:
        """Get storage savings from compression in MB."""
        if not self.is_compressed:
            return 0.0
        
        uncompressed = self.get_uncompressed_size_mb()
        compressed = self.get_storage_size_mb()
        return uncompressed - compressed
    
    def is_complete(self) -> bool:
        """Check if package is complete (has all required data)."""
        return (
            self.storage_path is not None
            and self.storage_size_bytes > 0
            and self.checksum_sha256 is not None
            and len(self.included_artifacts) > 0
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert package to dictionary."""
        return {
            "package_id": self.package_id,
            "manifest": self.manifest.to_dict(),
            "export_format": self.export_format.value,
            "exported_at": self.exported_at.isoformat(),
            "exported_by": self.exported_by,
            "storage_path": self.storage_path,
            "storage_size_bytes": self.storage_size_bytes,
            "checksum_sha256": self.checksum_sha256,
            "checksum_md5": self.checksum_md5,
            "is_compressed": self.is_compressed,
            "compression_ratio": self.compression_ratio,
            "included_artifacts": self.included_artifacts,
            "artifact_checksums": self.artifact_checksums,
            "bundled_dependencies": self.bundled_dependencies,
            "external_dependencies": self.external_dependencies,
            "metadata": self.metadata,
        }

