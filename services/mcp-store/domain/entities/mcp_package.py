"""MCP Package Entity - Domain Layer."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from services.mcp_store.domain.entities.mcp_version import MCPVersion
from services.mcp_store.domain.value_objects.package_status import PackageStatus


@dataclass
class MCPPackage:
    """
    Represents an MCP package in the store.
    
    An MCP package is a versioned collection of knowledge graph data
    that can be exported, imported, and shared across systems.
    
    Think "Docker for Knowledge Graphs" - portable, versioned, shareable.
    """
    
    # Identity
    package_id: str
    name: str  # Unique name (e.g., "openai-api-mcp", "postgres-schemas")
    display_name: str  # Human-readable name
    
    # Metadata
    description: str
    author: str
    author_email: Optional[str] = None
    homepage_url: Optional[str] = None
    repository_url: Optional[str] = None
    documentation_url: Optional[str] = None
    license: str = "MIT"
    
    # Status
    status: PackageStatus = PackageStatus.DRAFT
    
    # Versions
    versions: List[MCPVersion] = field(default_factory=list)
    latest_version: Optional[str] = None
    
    # Classification
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)  # e.g., ["api", "database", "documentation"]
    
    # Statistics
    total_downloads: int = 0
    download_count_30d: int = 0
    star_count: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None
    
    # Owner/Permissions
    owner_id: str = ""
    is_public: bool = True
    allowed_users: List[str] = field(default_factory=list)  # For private packages
    
    # Content metadata
    embedding_count: int = 0  # Number of embeddings in the package
    document_count: int = 0  # Number of documents
    entity_count: int = 0  # Number of entities
    relationship_count: int = 0  # Number of relationships
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_version(self, version: MCPVersion) -> None:
        """
        Add a new version to the package.
        
        Args:
            version: The version to add
            
        Raises:
            ValueError: If version already exists
        """
        # Check for duplicate
        if any(v.version == version.version for v in self.versions):
            raise ValueError(f"Version {version.version} already exists")
        
        self.versions.append(version)
        self.updated_at = datetime.now()
        
        # Update latest version (simplified - would need proper semver comparison)
        if not self.latest_version or self._is_newer_version(version.version, self.latest_version):
            self.latest_version = version.version
    
    def get_version(self, version_str: str) -> Optional[MCPVersion]:
        """
        Get a specific version.
        
        Args:
            version_str: Version string (e.g., "1.0.0")
            
        Returns:
            The version if found, None otherwise
        """
        for version in self.versions:
            if version.version == version_str:
                return version
        return None
    
    def get_latest_version(self) -> Optional[MCPVersion]:
        """Get the latest version."""
        if not self.latest_version:
            return None
        return self.get_version(self.latest_version)
    
    def get_all_versions(self, include_yanked: bool = False, include_prerelease: bool = True) -> List[MCPVersion]:
        """
        Get all versions with optional filtering.
        
        Args:
            include_yanked: Whether to include yanked versions
            include_prerelease: Whether to include prerelease versions
            
        Returns:
            Filtered list of versions
        """
        versions = self.versions
        
        if not include_yanked:
            versions = [v for v in versions if not v.is_yanked]
        
        if not include_prerelease:
            versions = [v for v in versions if not v.is_prerelease]
        
        return versions
    
    def _is_newer_version(self, v1: str, v2: str) -> bool:
        """
        Compare two semantic versions.
        
        Args:
            v1: First version string
            v2: Second version string
            
        Returns:
            True if v1 is newer than v2
            
        Note: This is a simplified comparison. Production would use proper semver library.
        """
        def parse_version(v: str) -> tuple:
            # Extract main version (before - or +)
            main = v.split("-")[0].split("+")[0]
            parts = main.split(".")
            return tuple(int(p) for p in parts)
        
        try:
            return parse_version(v1) > parse_version(v2)
        except (ValueError, IndexError):
            return False
    
    def publish(self) -> None:
        """Publish the package (make it available)."""
        if self.status == PackageStatus.DRAFT:
            self.status = PackageStatus.PUBLISHED
            self.published_at = datetime.now()
            self.updated_at = datetime.now()
    
    def deprecate(self, reason: Optional[str] = None) -> None:
        """Mark package as deprecated."""
        self.status = PackageStatus.DEPRECATED
        self.updated_at = datetime.now()
        if reason:
            self.metadata["deprecation_reason"] = reason
    
    def archive(self) -> None:
        """Archive the package (remove from active use)."""
        self.status = PackageStatus.ARCHIVED
        self.updated_at = datetime.now()
    
    def make_private(self, allowed_users: Optional[List[str]] = None) -> None:
        """Make package private."""
        self.is_public = False
        self.status = PackageStatus.PRIVATE
        if allowed_users:
            self.allowed_users = allowed_users
        self.updated_at = datetime.now()
    
    def make_public(self) -> None:
        """Make package public."""
        self.is_public = True
        if self.status == PackageStatus.PRIVATE:
            self.status = PackageStatus.PUBLISHED
        self.updated_at = datetime.now()
    
    def can_access(self, user_id: str) -> bool:
        """
        Check if a user can access this package.
        
        Args:
            user_id: The user ID to check
            
        Returns:
            True if user can access, False otherwise
        """
        if self.is_public:
            return True
        
        if user_id == self.owner_id:
            return True
        
        return user_id in self.allowed_users
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the package."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.now()
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the package."""
        if tag in self.tags:
            self.tags.remove(tag)
            self.updated_at = datetime.now()
    
    def add_category(self, category: str) -> None:
        """Add a category to the package."""
        if category not in self.categories:
            self.categories.append(category)
            self.updated_at = datetime.now()
    
    def increment_downloads(self, version: Optional[str] = None) -> None:
        """
        Increment download counter.
        
        Args:
            version: Specific version that was downloaded (optional)
        """
        self.total_downloads += 1
        self.download_count_30d += 1  # Would need periodic reset in production
        
        if version:
            ver = self.get_version(version)
            if ver:
                ver.increment_downloads()
    
    def add_star(self) -> None:
        """Increment star count."""
        self.star_count += 1
    
    def remove_star(self) -> None:
        """Decrement star count."""
        if self.star_count > 0:
            self.star_count -= 1
    
    def get_popularity_score(self) -> float:
        """
        Calculate popularity score (0-100).
        
        Based on:
        - Total downloads (40%)
        - Recent downloads (30%)
        - Stars (30%)
        """
        # Normalize values (simplified scoring)
        download_score = min(self.total_downloads / 1000.0, 1.0) * 40
        recent_score = min(self.download_count_30d / 100.0, 1.0) * 30
        star_score = min(self.star_count / 50.0, 1.0) * 30
        
        return download_score + recent_score + star_score
    
    def to_dict(self, include_versions: bool = True) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            "package_id": self.package_id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "author": self.author,
            "author_email": self.author_email,
            "homepage_url": self.homepage_url,
            "repository_url": self.repository_url,
            "documentation_url": self.documentation_url,
            "license": self.license,
            "status": self.status.value,
            "latest_version": self.latest_version,
            "tags": self.tags,
            "categories": self.categories,
            "total_downloads": self.total_downloads,
            "download_count_30d": self.download_count_30d,
            "star_count": self.star_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "owner_id": self.owner_id,
            "is_public": self.is_public,
            "allowed_users": self.allowed_users,
            "embedding_count": self.embedding_count,
            "document_count": self.document_count,
            "entity_count": self.entity_count,
            "relationship_count": self.relationship_count,
            "metadata": self.metadata,
            "popularity_score": self.get_popularity_score(),
        }
        
        if include_versions:
            data["versions"] = [v.to_dict() for v in self.versions]
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPPackage":
        """Create from dictionary."""
        # Parse versions if present
        versions = []
        if "versions" in data:
            versions = [MCPVersion.from_dict(v) for v in data["versions"]]
        
        return cls(
            package_id=data["package_id"],
            name=data["name"],
            display_name=data["display_name"],
            description=data["description"],
            author=data["author"],
            author_email=data.get("author_email"),
            homepage_url=data.get("homepage_url"),
            repository_url=data.get("repository_url"),
            documentation_url=data.get("documentation_url"),
            license=data.get("license", "MIT"),
            status=PackageStatus(data.get("status", "draft")),
            versions=versions,
            latest_version=data.get("latest_version"),
            tags=data.get("tags", []),
            categories=data.get("categories", []),
            total_downloads=data.get("total_downloads", 0),
            download_count_30d=data.get("download_count_30d", 0),
            star_count=data.get("star_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else data.get("updated_at", datetime.now()),
            published_at=datetime.fromisoformat(data["published_at"]) if data.get("published_at") and isinstance(data["published_at"], str) else None,
            owner_id=data.get("owner_id", ""),
            is_public=data.get("is_public", True),
            allowed_users=data.get("allowed_users", []),
            embedding_count=data.get("embedding_count", 0),
            document_count=data.get("document_count", 0),
            entity_count=data.get("entity_count", 0),
            relationship_count=data.get("relationship_count", 0),
            metadata=data.get("metadata", {}),
        )
