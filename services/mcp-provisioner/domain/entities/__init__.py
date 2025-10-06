"""Domain Entities for MCP Provisioner.

Entities are objects with unique identity that persist over time.
They contain business logic and behavior.
"""

from .mcp_instance import MCPInstance

__all__ = [
    "MCPInstance",
]

