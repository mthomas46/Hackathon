"""MCPPackage Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class MCPPackage:
    """
    MCP Package entity.
    
    Represents a versioned package of MCP knowledge that can be
    exported, imported, and deployed across systems.
    """
    
    # Identity
    package_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    version: str = "1.0.0"
    
    # Metadata
    description: str = ""
    author: str = ""
    license: str = "MIT"
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    
    # Content
    knowledge_items: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # package_id or name@version
    
    # Storage
    size_bytes: int = 0
    checksum: Optional[str] = None
    compressed_size_bytes: int = 0
    
    # Status
    status: str = "draft"  # draft, published, deprecated
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    # Lifecycle
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # Versioning
    previous_version: Optional[str] = None
    changelog: List[Dict[str, Any]] = field(default_factory=list)
    
    # Deployment
    deployed_count: int = 0
    last_deployed_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate package."""
        if not self.package_id:
            self.package_id = str(uuid4())
        if not self.name:
            raise ValueError("Package name is required")
        if not self.version:
            raise ValueError("Package version is required")
    
    def add_knowledge_item(
        self,
        content: str,
        item_type: str = "text",
        relevance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add knowledge item to package.
        
        Args:
            content: Knowledge content
            item_type: Type of knowledge (text, code, config, etc.)
            relevance: Relevance score (0.0-1.0)
            metadata: Additional metadata
        """
        if not 0.0 <= relevance <= 1.0:
            raise ValueError("Relevance must be between 0.0 and 1.0")
        
        item = {
            "id": str(uuid4()),
            "content": content,
            "type": item_type,
            "relevance": relevance,
            "metadata": metadata or {},
            "added_at": datetime.now(timezone.utc).isoformat(),
        }
        
        self.knowledge_items.append(item)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_dependency(self, dependency: str) -> None:
        """
        Add package dependency.
        
        Args:
            dependency: Dependency string (package_id or name@version)
        """
        if dependency not in self.dependencies:
            self.dependencies.append(dependency)
        self.updated_at = datetime.now(timezone.utc)
    
    def validate(self) -> bool:
        """
        Validate package.
        
        Returns:
            True if valid, False otherwise
        """
        self.validation_errors = []
        
        # Check name
        if not self.name:
            self.validation_errors.append("Package name is required")
        
        # Check version format (semantic versioning)
        if not self._is_valid_version(self.version):
            self.validation_errors.append(f"Invalid version format: {self.version}")
        
        # Check knowledge items
        if not self.knowledge_items:
            self.validation_errors.append("Package must contain at least one knowledge item")
        
        # Check size
        if self.size_bytes > 1_000_000_000:  # 1GB limit
            self.validation_errors.append("Package size exceeds 1GB limit")
        
        self.validated = len(self.validation_errors) == 0
        return self.validated
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid semantic version."""
        parts = version.split(".")
        if len(parts) != 3:
            return False
        return all(part.isdigit() for part in parts)
    
    def publish(self) -> None:
        """Mark package as published."""
        if not self.validated:
            raise ValueError("Package must be validated before publishing")
        
        self.status = "published"
        self.published_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def deprecate(self) -> None:
        """Mark package as deprecated."""
        self.status = "deprecated"
        self.updated_at = datetime.now(timezone.utc)
    
    def record_deployment(self) -> None:
        """Record package deployment."""
        self.deployed_count += 1
        self.last_deployed_at = datetime.now(timezone.utc)
    
    def calculate_checksum(self) -> str:
        """
        Calculate package checksum.
        
        Returns:
            MD5 checksum
        """
        import hashlib
        import json
        
        # Create deterministic representation
        data = {
            "name": self.name,
            "version": self.version,
            "knowledge_items": self.knowledge_items,
            "dependencies": sorted(self.dependencies),
        }
        
        content = json.dumps(data, sort_keys=True)
        self.checksum = hashlib.md5(content.encode()).hexdigest()
        return self.checksum
    
    def create_changelog_entry(self, changes: str) -> None:
        """
        Add changelog entry.
        
        Args:
            changes: Description of changes
        """
        entry = {
            "version": self.version,
            "changes": changes,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.changelog.append(entry)
        self.updated_at = datetime.now(timezone.utc)
    
    def get_knowledge_count(self) -> int:
        """Get count of knowledge items."""
        return len(self.knowledge_items)
    
    def get_total_relevance(self) -> float:
        """Get sum of all relevance scores."""
        return sum(item.get("relevance", 0.0) for item in self.knowledge_items)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "package_id": self.package_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "license": self.license,
            "tags": self.tags,
            "categories": self.categories,
            "knowledge_items": self.knowledge_items,
            "dependencies": self.dependencies,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "compressed_size_bytes": self.compressed_size_bytes,
            "status": self.status,
            "validated": self.validated,
            "validation_errors": self.validation_errors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "previous_version": self.previous_version,
            "changelog": self.changelog,
            "deployed_count": self.deployed_count,
            "last_deployed_at": self.last_deployed_at.isoformat() if self.last_deployed_at else None,
            "metadata": self.metadata,
        }

