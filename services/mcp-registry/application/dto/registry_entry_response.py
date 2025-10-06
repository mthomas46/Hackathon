"""Registry Entry Response DTO."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class RegistryEntryResponse:
    """Response with registry entry details."""
    
    # Identity
    entry_id: str
    mcp_id: str
    name: str
    version: str
    description: str
    
    # Status
    status: str
    status_message: Optional[str]
    
    # Storage
    storage_backend: str
    storage_location: str
    export_format: str
    
    # Manifest summary
    tier: int
    scope: str
    total_size_bytes: int
    has_vector_db: bool
    has_graph_db: bool
    
    # Timestamps
    registered_at: str
    last_accessed_at: Optional[str]
    deprecated_at: Optional[str]
    archived_at: Optional[str]
    
    # Versioning
    is_latest: bool
    previous_version_id: Optional[str]
    next_version_id: Optional[str]
    
    # Usage
    download_count: int
    import_count: int
    access_count: int
    
    # Security
    security_scan_status: str
    security_scan_at: Optional[str]
    security_issues: List[str]
    
    # Integrity
    integrity_check_status: str
    integrity_check_at: Optional[str]
    
    # Ownership
    owner_id: str
    owner_organization: Optional[str]
    maintainers: List[str]
    
    # Visibility
    is_public: bool
    
    # Tags
    tags: List[str]
    
    # Metadata
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entry_id": self.entry_id,
            "mcp_id": self.mcp_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "status": self.status,
            "status_message": self.status_message,
            "storage_backend": self.storage_backend,
            "storage_location": self.storage_location,
            "export_format": self.export_format,
            "tier": self.tier,
            "scope": self.scope,
            "total_size_bytes": self.total_size_bytes,
            "has_vector_db": self.has_vector_db,
            "has_graph_db": self.has_graph_db,
            "registered_at": self.registered_at,
            "last_accessed_at": self.last_accessed_at,
            "deprecated_at": self.deprecated_at,
            "archived_at": self.archived_at,
            "is_latest": self.is_latest,
            "previous_version_id": self.previous_version_id,
            "next_version_id": self.next_version_id,
            "download_count": self.download_count,
            "import_count": self.import_count,
            "access_count": self.access_count,
            "security_scan_status": self.security_scan_status,
            "security_scan_at": self.security_scan_at,
            "security_issues": self.security_issues,
            "integrity_check_status": self.integrity_check_status,
            "integrity_check_at": self.integrity_check_at,
            "owner_id": self.owner_id,
            "owner_organization": self.owner_organization,
            "maintainers": self.maintainers,
            "is_public": self.is_public,
            "tags": self.tags,
            "metadata": self.metadata,
        }

