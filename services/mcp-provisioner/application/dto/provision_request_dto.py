"""Provision Request DTO - Application Layer.

This DTO carries all information needed to provision a new MCP instance.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ProvisionRequestDTO:
    """
    Data Transfer Object for MCP provisioning requests.
    
    This DTO is used to carry provisioning parameters from
    the presentation layer to the application layer use cases.
    """
    
    # Required fields
    client_id: str
    tier: int  # 0-4 (0 = Client-specific, 4 = Ecosystem)
    
    # Optional configuration
    image_name: Optional[str] = None
    network_name: Optional[str] = "hackathon_default"
    chromadb_path: Optional[str] = None
    neo4j_uri: Optional[str] = None
    api_port: Optional[int] = 3000
    
    # Resource limits
    memory_limit: Optional[str] = "512m"
    cpu_shares: Optional[int] = 1024
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the DTO after initialization."""
        if not self.client_id:
            raise ValueError("client_id is required")
        
        if not isinstance(self.tier, int) or self.tier < 0 or self.tier > 4:
            raise ValueError("tier must be an integer between 0 and 4")
        
        # Set defaults based on tier if not provided
        if not self.image_name:
            self.image_name = f"client-mcp-tier{self.tier}:latest"
        
        if not self.chromadb_path:
            self.chromadb_path = f"/data/chromadb/tier{self.tier}/{self.client_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DTO to dictionary."""
        return {
            "client_id": self.client_id,
            "tier": self.tier,
            "image_name": self.image_name,
            "network_name": self.network_name,
            "chromadb_path": self.chromadb_path,
            "neo4j_uri": self.neo4j_uri,
            "api_port": self.api_port,
            "memory_limit": self.memory_limit,
            "cpu_shares": self.cpu_shares,
            "metadata": self.metadata,
            "environment_vars": self.environment_vars,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProvisionRequestDTO":
        """Create DTO from dictionary."""
        return cls(
            client_id=data["client_id"],
            tier=data["tier"],
            image_name=data.get("image_name"),
            network_name=data.get("network_name", "hackathon_default"),
            chromadb_path=data.get("chromadb_path"),
            neo4j_uri=data.get("neo4j_uri"),
            api_port=data.get("api_port", 3000),
            memory_limit=data.get("memory_limit", "512m"),
            cpu_shares=data.get("cpu_shares", 1024),
            metadata=data.get("metadata", {}),
            environment_vars=data.get("environment_vars", {}),
        )

