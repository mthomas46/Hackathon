"""Documentation Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class Documentation:
    """
    Documentation entity.
    
    Represents a documentation file with lifecycle management,
    validation status, and synchronization metadata.
    """
    
    # Identity
    doc_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    file_path: str = ""
    
    # Content
    content: str = ""
    format: str = "markdown"  # markdown, restructuredtext, html, etc.
    
    # Source information
    source_type: str = ""  # git, api, manual, generated
    source_url: Optional[str] = None
    source_repo: Optional[str] = None
    source_branch: Optional[str] = None
    source_commit: Optional[str] = None
    
    # Validation
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    validation_timestamp: Optional[datetime] = None
    
    # Synchronization
    last_synced_at: Optional[datetime] = None
    sync_status: str = "pending"  # pending, synced, outdated, error
    needs_update: bool = False
    
    # Version control
    version: int = 1
    checksum: Optional[str] = None
    
    # Lifecycle
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    generated_at: Optional[datetime] = None
    
    # Relationships
    related_docs: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate documentation."""
        if not self.doc_id:
            self.doc_id = str(uuid4())
        if not self.title:
            raise ValueError("Documentation title is required")
        if not self.file_path:
            raise ValueError("File path is required")
    
    def mark_as_synced(self, commit: Optional[str] = None) -> None:
        """
        Mark documentation as synced.
        
        Args:
            commit: Optional commit hash
        """
        self.sync_status = "synced"
        self.last_synced_at = datetime.now(timezone.utc)
        self.needs_update = False
        if commit:
            self.source_commit = commit
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_as_outdated(self) -> None:
        """Mark documentation as outdated."""
        self.sync_status = "outdated"
        self.needs_update = True
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_sync_error(self, error: str) -> None:
        """
        Mark sync error.
        
        Args:
            error: Error message
        """
        self.sync_status = "error"
        self.validation_errors.append(f"Sync error: {error}")
        self.updated_at = datetime.now(timezone.utc)
    
    def validate(self) -> bool:
        """
        Validate documentation.
        
        Returns:
            True if valid, False otherwise
        """
        self.validation_errors = []
        self.validation_warnings = []
        
        # Check required content
        if not self.content:
            self.validation_errors.append("Documentation content is empty")
        
        # Check minimum content length
        if len(self.content) < 100:
            self.validation_warnings.append("Documentation content is very short (< 100 chars)")
        
        # Check format
        if self.format not in ("markdown", "restructuredtext", "html", "asciidoc"):
            self.validation_errors.append(f"Unsupported format: {self.format}")
        
        # Check source information
        if self.source_type == "git" and not self.source_repo:
            self.validation_errors.append("Git source requires source_repo")
        
        # Update validation status
        self.validated = len(self.validation_errors) == 0
        self.validation_timestamp = datetime.now(timezone.utc)
        
        return self.validated
    
    def add_related_doc(self, doc_id: str) -> None:
        """
        Add related documentation.
        
        Args:
            doc_id: Related document ID
        """
        if doc_id not in self.related_docs:
            self.related_docs.append(doc_id)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_dependency(self, doc_id: str) -> None:
        """
        Add documentation dependency.
        
        Args:
            doc_id: Dependency document ID
        """
        if doc_id not in self.dependencies:
            self.dependencies.append(doc_id)
        self.updated_at = datetime.now(timezone.utc)
    
    def increment_version(self) -> None:
        """Increment version number."""
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
    
    def calculate_checksum(self) -> str:
        """
        Calculate content checksum.
        
        Returns:
            MD5 checksum of content
        """
        import hashlib
        self.checksum = hashlib.md5(self.content.encode()).hexdigest()
        return self.checksum
    
    def has_changed(self, new_content: str) -> bool:
        """
        Check if content has changed.
        
        Args:
            new_content: New content to compare
            
        Returns:
            True if content changed
        """
        import hashlib
        new_checksum = hashlib.md5(new_content.encode()).hexdigest()
        return new_checksum != self.checksum
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "doc_id": self.doc_id,
            "title": self.title,
            "file_path": self.file_path,
            "content": self.content,
            "format": self.format,
            "source_type": self.source_type,
            "source_url": self.source_url,
            "source_repo": self.source_repo,
            "source_branch": self.source_branch,
            "source_commit": self.source_commit,
            "validated": self.validated,
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
            "validation_timestamp": self.validation_timestamp.isoformat() if self.validation_timestamp else None,
            "last_synced_at": self.last_synced_at.isoformat() if self.last_synced_at else None,
            "sync_status": self.sync_status,
            "needs_update": self.needs_update,
            "version": self.version,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "related_docs": self.related_docs,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "categories": self.categories,
            "metadata": self.metadata,
        }

