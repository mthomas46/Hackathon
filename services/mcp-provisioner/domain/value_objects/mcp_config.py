"""MCP Configuration Value Object."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)  # Immutable value object
class MCPConfig:
    """
    Value object representing MCP configuration.
    
    Immutable configuration for an MCP instance.
    """
    
    tier: int  # 0=Client, 1=Project, 2=Team, 3=Company, 4=Ecosystem
    docker_image: str  # Docker image to use
    port: int  # Internal port for MCP service
    chromadb_path: str  # Path to ChromaDB data
    neo4j_uri: str  # Neo4j connection URI
    environment_vars: Dict[str, str]  # Additional environment variables
    
    def __post_init__(self):
        """Validate configuration."""
        if self.tier < 0 or self.tier > 4:
            raise ValueError(f"Invalid tier: {self.tier}. Must be 0-4.")
        
        if self.port < 1024 or self.port > 65535:
            raise ValueError(f"Invalid port: {self.port}. Must be 1024-65535.")
        
        if not self.docker_image:
            raise ValueError("Docker image cannot be empty")
        
        if not self.chromadb_path:
            raise ValueError("ChromaDB path cannot be empty")
        
        if not self.neo4j_uri:
            raise ValueError("Neo4j URI cannot be empty")
    
    def tier_name(self) -> str:
        """Get human-readable tier name."""
        tier_names = {
            0: "Client",
            1: "Project",
            2: "Team",
            3: "Company",
            4: "Ecosystem"
        }
        return tier_names.get(self.tier, "Unknown")
    
    def with_port(self, new_port: int) -> "MCPConfig":
        """Create new config with different port (immutable pattern)."""
        return MCPConfig(
            tier=self.tier,
            docker_image=self.docker_image,
            port=new_port,
            chromadb_path=self.chromadb_path,
            neo4j_uri=self.neo4j_uri,
            environment_vars=self.environment_vars
        )
    
    def with_env_var(self, key: str, value: str) -> "MCPConfig":
        """Create new config with additional environment variable."""
        new_env_vars = {**self.environment_vars, key: value}
        return MCPConfig(
            tier=self.tier,
            docker_image=self.docker_image,
            port=self.port,
            chromadb_path=self.chromadb_path,
            neo4j_uri=self.neo4j_uri,
            environment_vars=new_env_vars
        )


def default_config_for_tier(tier: int, mcp_id: str) -> MCPConfig:
    """Create default configuration for a tier."""
    return MCPConfig(
        tier=tier,
        docker_image=f"mcp-server:tier-{tier}",
        port=3000 + tier,  # 3000, 3001, 3002, 3003, 3004
        chromadb_path=f"/data/{mcp_id}/chromadb",
        neo4j_uri=f"bolt://neo4j-{mcp_id}:7687",
        environment_vars={
            "MCP_ID": mcp_id,
            "TIER": str(tier),
            "LOG_LEVEL": "INFO"
        }
    )

