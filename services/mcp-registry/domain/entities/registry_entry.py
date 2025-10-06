"""Registry Entry Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from services.mcp_registry.domain.entities.mcp_manifest import MCPManifest
from services.mcp_registry.domain.value_objects.registry_status import RegistryStatus
from services.mcp_registry.domain.value_objects.storage_backend import StorageBackend
from services.mcp_registry.domain.value_objects.export_format import ExportFormat
from services.mcp_registry.domain.value_objects.mcp_version import MCPVersion


@dataclass
class RegistryEntry:
    """
    Registry entry for an MCP.
    
    Aggregate root for registry operations.
    Tracks an MCP's presence in the registry with full metadata.
    """
    
    # Identity
    entry_id: str
    mcp_id: str
    manifest: MCPManifest
    
    # Status
    status: RegistryStatus = RegistryStatus.PENDING
    status_message: Optional[str] = None
    
    # Storage
    storage_backend: StorageBackend = StorageBackend.LOCAL_FILESYSTEM
    storage_location: str = ""  # Path or URL
    export_format: ExportFormat = ExportFormat.MSGPACK
    
    # Lifecycle timestamps
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: Optional[datetime] = None
    deprecated_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    
    # Versioning
    is_latest: bool = True  # Is this the latest version?
    previous_version_id: Optional[str] = None
    next_version_id: Optional[str] = None
    
    # Usage tracking
    download_count: int = 0
    import_count: int = 0
    access_count: int = 0
    
    # Security
    security_scan_status: str = "pending"  # pending, passed, failed
    security_scan_at: Optional[datetime] = None
    security_issues: List[str] = field(default_factory=list)
    
    # Integrity
    integrity_check_status: str = "pending"  # pending, passed, failed
    integrity_check_at: Optional[datetime] = None
    
    # Ownership
    owner_id: str = ""
    owner_organization: Optional[str] = None
    maintainers: List[str] = field(default_factory=list)
    
    # Visibility
    is_public: bool = False
    allowed_users: List[str] = field(default_factory=list)
    allowed_organizations: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate entry."""
        if not self.entry_id:
            raise ValueError("Entry ID is required")
        if not self.mcp_id:
            raise ValueError("MCP ID is required")
        if not self.manifest:
            raise ValueError("Manifest is required")
    
    @property
    def name(self) -> str:
        """Get MCP name from manifest."""
        return self.manifest.name
    
    @property
    def version(self) -> MCPVersion:
        """Get MCP version from manifest."""
        return self.manifest.version
    
    @property
    def description(self) -> str:
        """Get MCP description from manifest."""
        return self.manifest.description
    
    def update_status(self, new_status: RegistryStatus, message: Optional[str] = None) -> None:
        """
        Update registry status.
        
        Args:
            new_status: New status
            message: Optional status message
        
        Raises:
            ValueError: If transition is invalid
        """
        if not self.status.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {self.status} to {new_status}")
        
        self.status = new_status
        self.status_message = message
        
        # Update timestamps
        now = datetime.now(timezone.utc)
        if new_status == RegistryStatus.DEPRECATED:
            self.deprecated_at = now
        elif new_status == RegistryStatus.ARCHIVED:
            self.archived_at = now
    
    def record_access(self) -> None:
        """Record an access to this MCP."""
        self.access_count += 1
        self.last_accessed_at = datetime.now(timezone.utc)
    
    def record_download(self) -> None:
        """Record a download of this MCP."""
        self.download_count += 1
        self.record_access()
    
    def record_import(self) -> None:
        """Record an import of this MCP."""
        self.import_count += 1
        self.record_access()
    
    def update_security_scan(self, passed: bool, issues: Optional[List[str]] = None) -> None:
        """
        Update security scan results.
        
        Args:
            passed: Whether scan passed
            issues: List of security issues found
        """
        self.security_scan_status = "passed" if passed else "failed"
        self.security_scan_at = datetime.now(timezone.utc)
        self.security_issues = issues or []
        
        # Quarantine if security failed
        if not passed:
            self.update_status(RegistryStatus.QUARANTINED, "Failed security scan")
    
    def update_integrity_check(self, passed: bool) -> None:
        """
        Update integrity check results.
        
        Args:
            passed: Whether integrity check passed
        """
        self.integrity_check_status = "passed" if passed else "failed"
        self.integrity_check_at = datetime.now(timezone.utc)
        
        # Mark as corrupted if integrity failed
        if not passed:
            self.update_status(RegistryStatus.CORRUPTED, "Failed integrity check")
    
    def can_access(self, user_id: str, organization: Optional[str] = None) -> bool:
        """
        Check if user can access this MCP.
        
        Args:
            user_id: User ID
            organization: User's organization
        
        Returns:
            True if user has access
        """
        # Public MCPs are accessible to all
        if self.is_public:
            return True
        
        # Owner always has access
        if user_id == self.owner_id:
            return True
        
        # Maintainers have access
        if user_id in self.maintainers:
            return True
        
        # Check explicit user permissions
        if user_id in self.allowed_users:
            return True
        
        # Check organization permissions
        if organization and organization in self.allowed_organizations:
            return True
        
        return False
    
    def add_maintainer(self, user_id: str) -> None:
        """Add a maintainer."""
        if user_id not in self.maintainers:
            self.maintainers.append(user_id)
    
    def remove_maintainer(self, user_id: str) -> None:
        """Remove a maintainer."""
        if user_id in self.maintainers:
            self.maintainers.remove(user_id)
    
    def mark_as_latest(self) -> None:
        """Mark this version as the latest."""
        self.is_latest = True
    
    def mark_as_outdated(self, next_version_id: str) -> None:
        """
        Mark this version as outdated.
        
        Args:
            next_version_id: ID of the newer version
        """
        self.is_latest = False
        self.next_version_id = next_version_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary."""
        return {
            "entry_id": self.entry_id,
            "mcp_id": self.mcp_id,
            "manifest": self.manifest.to_dict(),
            "status": self.status.value,
            "status_message": self.status_message,
            "storage_backend": self.storage_backend.value,
            "storage_location": self.storage_location,
            "export_format": self.export_format.value,
            "registered_at": self.registered_at.isoformat(),
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
            "is_latest": self.is_latest,
            "previous_version_id": self.previous_version_id,
            "next_version_id": self.next_version_id,
            "download_count": self.download_count,
            "import_count": self.import_count,
            "access_count": self.access_count,
            "security_scan_status": self.security_scan_status,
            "security_scan_at": self.security_scan_at.isoformat() if self.security_scan_at else None,
            "security_issues": self.security_issues,
            "integrity_check_status": self.integrity_check_status,
            "integrity_check_at": self.integrity_check_at.isoformat() if self.integrity_check_at else None,
            "owner_id": self.owner_id,
            "owner_organization": self.owner_organization,
            "maintainers": self.maintainers,
            "is_public": self.is_public,
            "allowed_users": self.allowed_users,
            "allowed_organizations": self.allowed_organizations,
            "metadata": self.metadata,
        }

