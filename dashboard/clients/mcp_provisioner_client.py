"""Client for MCP Provisioner API."""

import logging
from typing import List, Dict, Any, Optional

from clients.base_client import BaseClient


logger = logging.getLogger(__name__)


class MCPProvisionerClient(BaseClient):
    """Client for interacting with MCP Provisioner."""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        """Initialize the MCP Provisioner client."""
        super().__init__(base_url)
    
    # ==================== MCP Lifecycle ====================
    
    async def provision_mcp(
        self,
        mcp_id: str,
        name: str,
        tier: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Provision a new MCP."""
        payload = {
            "mcp_id": mcp_id,
            "name": name,
            "tier": tier,
            "config": config or {}
        }
        return await self.post("/api/v1/mcps/provision", json=payload)
    
    async def start_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """Start an MCP."""
        return await self.post(f"/api/v1/mcps/{mcp_id}/start")
    
    async def stop_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """Stop an MCP."""
        return await self.post(f"/api/v1/mcps/{mcp_id}/stop")
    
    async def restart_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """Restart an MCP."""
        return await self.post(f"/api/v1/mcps/{mcp_id}/restart")
    
    async def delete_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """Delete an MCP."""
        return await self.delete(f"/api/v1/mcps/{mcp_id}")
    
    # ==================== MCP Queries ====================
    
    async def get_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """Get MCP details."""
        return await self.get(f"/api/v1/mcps/{mcp_id}")
    
    async def list_mcps(
        self,
        status: Optional[str] = None,
        tier: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all MCPs."""
        params = {}
        if status:
            params["status"] = status
        if tier:
            params["tier"] = tier
        return await self.get("/api/v1/mcps", params=params)
    
    async def get_mcp_status(self, mcp_id: str) -> Dict[str, Any]:
        """Get MCP status."""
        return await self.get(f"/api/v1/mcps/{mcp_id}/status")
    
    async def get_mcp_metrics(self, mcp_id: str) -> Dict[str, Any]:
        """Get MCP resource metrics."""
        return await self.get(f"/api/v1/mcps/{mcp_id}/metrics")
