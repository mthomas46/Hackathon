"""PackageVersion Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class PackageVersion:
    """
    Package version entity.
    
    Tracks version history and metadata for package versions.
    """
    
    # Identity
    package_id: str = ""
    version: str = "1.0.0"
    
    # Metadata
    changelog: str = ""
    breaking_changes: bool = False
    
    # Lifecycle
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    
    # Download stats
    download_count: int = 0
    last_downloaded_at: Optional[datetime] = None
    
    # Storage
    file_path: Optional[str] = None
    file_size_bytes: int = 0
    checksum: Optional[str] = None
    
    def __post_init__(self):
        """Validate version."""
        if not self.package_id:
            raise ValueError("Package ID is required")
        if not self.version:
            raise ValueError("Version is required")
        if not self._is_valid_semantic_version(self.version):
            raise ValueError(f"Invalid semantic version: {self.version}")
    
    def _is_valid_semantic_version(self, version: str) -> bool:
        """Check if version follows semantic versioning."""
        parts = version.split(".")
        if len(parts) != 3:
            return False
        return all(part.isdigit() for part in parts)
    
    def record_download(self) -> None:
        """Record a download of this version."""
        self.download_count += 1
        self.last_downloaded_at = datetime.now(timezone.utc)
    
    def get_major_version(self) -> int:
        """Get major version number."""
        return int(self.version.split(".")[0])
    
    def get_minor_version(self) -> int:
        """Get minor version number."""
        return int(self.version.split(".")[1])
    
    def get_patch_version(self) -> int:
        """Get patch version number."""
        return int(self.version.split(".")[2])
    
    def is_compatible_with(self, other_version: str) -> bool:
        """
        Check if this version is compatible with another version.
        
        Uses semantic versioning rules:
        - Same major version = compatible
        - Different major version = incompatible
        """
        other_parts = other_version.split(".")
        if len(other_parts) != 3:
            return False
        
        return self.get_major_version() == int(other_parts[0])
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "package_id": self.package_id,
            "version": self.version,
            "changelog": self.changelog,
            "breaking_changes": self.breaking_changes,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "download_count": self.download_count,
            "last_downloaded_at": self.last_downloaded_at.isoformat() if self.last_downloaded_at else None,
            "file_path": self.file_path,
            "file_size_bytes": self.file_size_bytes,
            "checksum": self.checksum,
        }
    
    @staticmethod
    def compare(version1: str, version2: str) -> int:
        """
        Compare two semantic versions.
        
        Args:
            version1: First version
            version2: Second version
            
        Returns:
            -1 if version1 < version2
            0 if version1 == version2
            1 if version1 > version2
        """
        v1_parts = [int(p) for p in version1.split(".")]
        v2_parts = [int(p) for p in version2.split(".")]
        
        for p1, p2 in zip(v1_parts, v2_parts):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
        
        return 0

