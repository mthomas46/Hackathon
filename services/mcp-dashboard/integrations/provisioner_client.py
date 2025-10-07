"""MCP Provisioner integration client - TIGHT COUPLING."""

import httpx
from typing import Dict, List, Optional, Any


class ProvisionerClient:
    """
    Tightly integrated client for MCP Provisioner service.
    
    Provides seamless dashboard integration for:
    - MCP instance creation
    - Lifecycle management
    - Health monitoring
    - Configuration management
    """
    
    def __init__(self, base_url: str = "http://mcp-provisioner:8003"):
        """
        Initialize Provisioner client.
        
        Args:
            base_url: Provisioner service URL
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def create_mcp(
        self,
        name: str,
        tier: str,
        parent_tier: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new MCP instance from the dashboard.
        
        Args:
            name: MCP name
            tier: Tier level (Client, Project, Team, Company, Ecosystem)
            parent_tier: Parent tier ID
            config: MCP configuration
        
        Returns:
            MCP details with mcp_id
        """
        payload = {
            "name": name,
            "tier": tier,
            "parent_tier": parent_tier,
            "config": config or {}
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/mcps",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """
        Get MCP details.
        
        Args:
            mcp_id: MCP instance ID
        
        Returns:
            MCP details
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/mcps/{mcp_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def list_mcps(
        self,
        tier: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List MCP instances with filtering.
        
        Args:
            tier: Filter by tier
            status: Filter by status (CREATED, TRAINING, READY, ERROR)
            limit: Max results
        
        Returns:
            List of MCPs
        """
        params = {"limit": limit}
        if tier:
            params["tier"] = tier
        if status:
            params["status"] = status
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/mcps",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def update_mcp(
        self,
        mcp_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update MCP configuration.
        
        Args:
            mcp_id: MCP instance ID
            config: New configuration
        
        Returns:
            Updated MCP details
        """
        response = await self.client.put(
            f"{self.base_url}/api/v1/mcps/{mcp_id}",
            json=config
        )
        response.raise_for_status()
        return response.json()
    
    async def delete_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """
        Delete an MCP instance.
        
        Args:
            mcp_id: MCP instance ID
        
        Returns:
            Deletion status
        """
        response = await self.client.delete(
            f"{self.base_url}/api/v1/mcps/{mcp_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_mcp_health(self, mcp_id: str) -> Dict[str, Any]:
        """
        Get MCP health status (for status indicators).
        
        Args:
            mcp_id: MCP instance ID
        
        Returns:
            Health status
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/mcps/{mcp_id}/health"
        )
        response.raise_for_status()
        return response.json()
    
    async def start_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """
        Start an MCP instance.
        
        Args:
            mcp_id: MCP instance ID
        
        Returns:
            Start status
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/mcps/{mcp_id}/start"
        )
        response.raise_for_status()
        return response.json()
    
    async def stop_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """
        Stop an MCP instance.
        
        Args:
            mcp_id: MCP instance ID
        
        Returns:
            Stop status
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/mcps/{mcp_id}/stop"
        )
        response.raise_for_status()
        return response.json()
    
    async def restart_mcp(self, mcp_id: str) -> Dict[str, Any]:
        """
        Restart an MCP instance.
        
        Args:
            mcp_id: MCP instance ID
        
        Returns:
            Restart status
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/mcps/{mcp_id}/restart"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_mcp_stats(self, mcp_id: str) -> Dict[str, Any]:
        """
        Get MCP statistics (for cards and charts).
        
        Args:
            mcp_id: MCP instance ID
        
        Returns:
            Statistics (documents, queries, etc.)
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/mcps/{mcp_id}/stats"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_tier_options(self) -> List[Dict[str, str]]:
        """
        Get available tier options for dropdown.
        
        Returns:
            List of tiers with names and IDs
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/tiers"
        )
        response.raise_for_status()
        return response.json()
    
    async def validate_mcp_name(self, name: str) -> Dict[str, bool]:
        """
        Validate MCP name before creation.
        
        Args:
            name: Proposed MCP name
        
        Returns:
            Validation result
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/mcps/validate",
            params={"name": name}
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

