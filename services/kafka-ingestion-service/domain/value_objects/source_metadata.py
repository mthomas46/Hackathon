"""Source Metadata Value Object."""

from dataclasses import dataclass
from typing import Dict, Optional, Any


@dataclass(frozen=True)
class SourceMetadata:
    """
    Source metadata value object.
    
    Immutable metadata about the document source.
    """
    
    # Source identification
    source_type: str = ""  # "github", "confluence", "jira", "docs_directory", etc.
    source_id: str = ""
    source_name: str = ""
    
    # Location information
    repository: Optional[str] = None
    workspace: Optional[str] = None
    space: Optional[str] = None
    project: Optional[str] = None
    
    # Version control
    branch: Optional[str] = None
    commit: Optional[str] = None
    version: Optional[str] = None
    
    # Author information
    author: Optional[str] = None
    author_email: Optional[str] = None
    
    # Additional metadata
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize extra dict if None."""
        if self.extra is None:
            object.__setattr__(self, 'extra', {})
    
    @property
    def is_valid(self) -> bool:
        """Check if metadata has minimum required fields."""
        return bool(self.source_type and self.source_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_name": self.source_name,
            "repository": self.repository,
            "workspace": self.workspace,
            "space": self.space,
            "project": self.project,
            "branch": self.branch,
            "commit": self.commit,
            "version": self.version,
            "author": self.author,
            "author_email": self.author_email,
            "extra": self.extra or {},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceMetadata":
        """
        Create from dictionary.
        
        Args:
            data: Metadata dictionary
            
        Returns:
            SourceMetadata instance
        """
        return cls(
            source_type=data.get("source_type", ""),
            source_id=data.get("source_id", ""),
            source_name=data.get("source_name", ""),
            repository=data.get("repository"),
            workspace=data.get("workspace"),
            space=data.get("space"),
            project=data.get("project"),
            branch=data.get("branch"),
            commit=data.get("commit"),
            version=data.get("version"),
            author=data.get("author"),
            author_email=data.get("author_email"),
            extra=data.get("extra", {}),
        )
    
    @classmethod
    def for_docs_directory(
        cls,
        path: str,
        author: Optional[str] = None
    ) -> "SourceMetadata":
        """
        Create metadata for docs directory source.
        
        Args:
            path: Document path
            author: Optional author
            
        Returns:
            SourceMetadata instance
        """
        return cls(
            source_type="docs_directory",
            source_id=path,
            source_name="Documentation Directory",
            author=author,
            extra={"path": path}
        )
    
    @classmethod
    def for_github(
        cls,
        repository: str,
        path: str,
        branch: str = "main",
        commit: Optional[str] = None,
        author: Optional[str] = None
    ) -> "SourceMetadata":
        """
        Create metadata for GitHub source.
        
        Args:
            repository: Repository name
            path: File path
            branch: Branch name
            commit: Commit SHA
            author: Author name
            
        Returns:
            SourceMetadata instance
        """
        return cls(
            source_type="github",
            source_id=f"{repository}/{path}",
            source_name="GitHub",
            repository=repository,
            branch=branch,
            commit=commit,
            author=author,
            extra={"path": path}
        )
    
    @classmethod
    def for_confluence(
        cls,
        space: str,
        page_id: str,
        page_title: str,
        version: Optional[str] = None,
        author: Optional[str] = None
    ) -> "SourceMetadata":
        """
        Create metadata for Confluence source.
        
        Args:
            space: Confluence space key
            page_id: Page ID
            page_title: Page title
            version: Page version
            author: Author name
            
        Returns:
            SourceMetadata instance
        """
        return cls(
            source_type="confluence",
            source_id=page_id,
            source_name="Confluence",
            space=space,
            version=version,
            author=author,
            extra={"page_title": page_title}
        )

