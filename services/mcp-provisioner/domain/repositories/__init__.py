"""Repository interfaces for MCP Provisioner domain.

Repository interfaces define the contract for data persistence
without specifying implementation details (infrastructure concern).
"""

from .mcp_repository import MCPRepository

__all__ = [
    "MCPRepository",
]

