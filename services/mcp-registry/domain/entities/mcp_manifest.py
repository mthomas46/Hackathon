"""MCP Manifest Entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from services.mcp_registry.domain.value_objects.mcp_version import MCPVersion


@dataclass
class MCPManifest:
    """
    Manifest describing an MCP package.
    
    Contains metadata about the MCP, its contents, dependencies, and requirements.
    Similar to a package.json or requirements.txt but for MCPs.
    """
    
    # Identity
    mcp_id: str
    name: str
    version: MCPVersion
    description: str
    
    # Classification
    tier: int  # MCP tier (0=Client, 1=Project, 2=Team, 3=Company, 4=Ecosystem)
    scope: str  # Scope of knowledge (e.g., "team-alpha", "client-acme")
    
    # Authorship
    created_by: str
    created_at: datetime
    organization: Optional[str] = None
    
    # Content metadata
    total_size_bytes: int = 0
    artifact_count: int = 0
    document_count: int = 0
    
    # Data stores
    has_vector_db: bool = False
    has_graph_db: bool = False
    vector_db_size_bytes: int = 0
    graph_db_size_bytes: int = 0
    
    # Knowledge metadata
    total_embeddings: int = 0
    total_entities: int = 0
    total_relationships: int = 0
    knowledge_sources: List[str] = field(default_factory=list)  # e.g., ["github", "confluence"]
    
    # Dependencies
    required_services: List[str] = field(default_factory=list)  # Services this MCP needs
    compatible_with: List[str] = field(default_factory=list)  # Compatible MCP versions
    
    # Requirements
    min_memory_mb: int = 512
    min_cpu_cores: int = 1
    requires_gpu: bool = False
    
    # Tags and labels
    tags: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    
    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate manifest."""
        if not self.mcp_id:
            raise ValueError("MCP ID is required")
        if not self.name:
            raise ValueError("Name is required")
        if self.tier < 0 or self.tier > 4:
            raise ValueError("Tier must be 0-4")
        if self.total_size_bytes < 0:
            raise ValueError("Size cannot be negative")
    
    def get_size_mb(self) -> float:
        """Get total size in megabytes."""
        return self.total_size_bytes / (1024 * 1024)
    
    def get_storage_breakdown(self) -> Dict[str, int]:
        """Get storage breakdown by component."""
        return {
            "vector_db_bytes": self.vector_db_size_bytes,
            "graph_db_bytes": self.graph_db_size_bytes,
            "other_bytes": self.total_size_bytes - self.vector_db_size_bytes - self.graph_db_size_bytes,
            "total_bytes": self.total_size_bytes,
        }
    
    def has_tag(self, tag: str) -> bool:
        """Check if manifest has a specific tag."""
        return tag in self.tags
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the manifest."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the manifest."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manifest to dictionary."""
        return {
            "mcp_id": self.mcp_id,
            "name": self.name,
            "version": str(self.version),
            "description": self.description,
            "tier": self.tier,
            "scope": self.scope,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "organization": self.organization,
            "total_size_bytes": self.total_size_bytes,
            "artifact_count": self.artifact_count,
            "document_count": self.document_count,
            "has_vector_db": self.has_vector_db,
            "has_graph_db": self.has_graph_db,
            "vector_db_size_bytes": self.vector_db_size_bytes,
            "graph_db_size_bytes": self.graph_db_size_bytes,
            "total_embeddings": self.total_embeddings,
            "total_entities": self.total_entities,
            "total_relationships": self.total_relationships,
            "knowledge_sources": self.knowledge_sources,
            "required_services": self.required_services,
            "compatible_with": self.compatible_with,
            "min_memory_mb": self.min_memory_mb,
            "min_cpu_cores": self.min_cpu_cores,
            "requires_gpu": self.requires_gpu,
            "tags": self.tags,
            "labels": self.labels,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPManifest":
        """Create manifest from dictionary."""
        version_str = data.pop("version")
        version = MCPVersion.from_string(version_str) if isinstance(version_str, str) else version_str
        
        created_at_str = data.pop("created_at")
        created_at = datetime.fromisoformat(created_at_str) if isinstance(created_at_str, str) else created_at_str
        
        return cls(
            version=version,
            created_at=created_at,
            **data
        )

