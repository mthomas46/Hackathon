"""MCP Version Entity - Domain Layer."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib


@dataclass
class MCPVersion:
    """
    Represents a specific version of an MCP package.
    
    Each version is immutable once published and includes:
    - Semantic version number
    - Storage reference (S3/MinIO path)
    - Checksum for integrity
    - Metadata (size, changelog, etc.)
    """
    
    # Identity
    version: str  # Semantic version (e.g., "1.0.0", "2.1.3-beta")
    package_id: str
    
    # Storage
    storage_path: str  # Path to .mcp file in S3/MinIO
    file_size_bytes: int
    checksum: str  # SHA-256 checksum
    
    # Metadata
    changelog: str = ""
    release_notes: str = ""
    is_prerelease: bool = False
    is_yanked: bool = False  # Removed from availability
    yank_reason: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    yanked_at: Optional[datetime] = None
    
    # Download statistics
    download_count: int = 0
    
    # Dependencies
    dependencies: Dict[str, str] = field(default_factory=dict)  # package_name -> version_constraint
    
    # Platform requirements
    min_python_version: Optional[str] = None
    max_python_version: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate version format."""
        self._validate_version()
    
    def _validate_version(self) -> None:
        """
        Validate semantic version format.
        
        Expected format: MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
        Examples: "1.0.0", "2.1.3-beta", "1.0.0-rc.1+build.123"
        """
        if not self.version:
            raise ValueError("Version cannot be empty")
        
        # Basic validation (simplified)
        parts = self.version.split("-")[0].split(".")
        if len(parts) < 3:
            raise ValueError(f"Invalid version format: {self.version}. Expected MAJOR.MINOR.PATCH")
        
        try:
            for part in parts:
                int(part.split("+")[0])  # Remove build metadata before parsing
        except ValueError:
            raise ValueError(f"Invalid version format: {self.version}. Version parts must be numeric")
    
    def calculate_checksum(self, file_content: bytes) -> str:
        """
        Calculate SHA-256 checksum of file content.
        
        Args:
            file_content: Raw bytes of the .mcp file
            
        Returns:
            Hex-encoded SHA-256 checksum
        """
        return hashlib.sha256(file_content).hexdigest()
    
    def verify_checksum(self, file_content: bytes) -> bool:
        """
        Verify file integrity against stored checksum.
        
        Args:
            file_content: Raw bytes of the .mcp file
            
        Returns:
            True if checksum matches, False otherwise
        """
        calculated = self.calculate_checksum(file_content)
        return calculated == self.checksum
    
    def increment_downloads(self) -> None:
        """Increment download counter."""
        self.download_count += 1
    
    def yank(self, reason: str) -> None:
        """
        Yank (remove) this version from availability.
        
        Yanked versions can no longer be downloaded but remain in storage
        for existing users who already downloaded them.
        
        Args:
            reason: Reason for yanking (e.g., "Security vulnerability")
        """
        self.is_yanked = True
        self.yank_reason = reason
        self.yanked_at = datetime.now()
    
    def unyank(self) -> None:
        """Restore yanked version to availability."""
        self.is_yanked = False
        self.yank_reason = None
        self.yanked_at = None
    
    def is_compatible_with_python(self, python_version: str) -> bool:
        """
        Check if this version is compatible with a Python version.
        
        Args:
            python_version: Python version string (e.g., "3.11")
            
        Returns:
            True if compatible, False otherwise
        """
        if not self.min_python_version and not self.max_python_version:
            return True  # No restrictions
        
        # Simplified comparison (would need proper semver in production)
        if self.min_python_version and python_version < self.min_python_version:
            return False
        if self.max_python_version and python_version > self.max_python_version:
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "package_id": self.package_id,
            "storage_path": self.storage_path,
            "file_size_bytes": self.file_size_bytes,
            "checksum": self.checksum,
            "changelog": self.changelog,
            "release_notes": self.release_notes,
            "is_prerelease": self.is_prerelease,
            "is_yanked": self.is_yanked,
            "yank_reason": self.yank_reason,
            "created_at": self.created_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "yanked_at": self.yanked_at.isoformat() if self.yanked_at else None,
            "download_count": self.download_count,
            "dependencies": self.dependencies,
            "min_python_version": self.min_python_version,
            "max_python_version": self.max_python_version,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPVersion":
        """Create from dictionary."""
        return cls(
            version=data["version"],
            package_id=data["package_id"],
            storage_path=data["storage_path"],
            file_size_bytes=data["file_size_bytes"],
            checksum=data["checksum"],
            changelog=data.get("changelog", ""),
            release_notes=data.get("release_notes", ""),
            is_prerelease=data.get("is_prerelease", False),
            is_yanked=data.get("is_yanked", False),
            yank_reason=data.get("yank_reason"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") and isinstance(data["published_at"], str) else None,
            yanked_at=datetime.fromisoformat(data["yanked_at"]) if data.get("yanked_at") and isinstance(data["yanked_at"], str) else None,
            download_count=data.get("download_count", 0),
            dependencies=data.get("dependencies", {}),
            min_python_version=data.get("min_python_version"),
            max_python_version=data.get("max_python_version"),
            metadata=data.get("metadata", {}),
        )
