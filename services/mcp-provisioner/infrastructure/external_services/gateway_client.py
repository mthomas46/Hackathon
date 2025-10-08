"""
Gateway Client for registering MCPs with the mcp-gateway service.

This client enables automatic registration of provisioned MCPs with the gateway,
implementing the architectural pattern: provisioner → gateway integration.
"""

import httpx
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class GatewayClient:
    """
    Client for registering MCP instances with the mcp-gateway service.
    
    Enables the provisioner to automatically register newly deployed MCPs
    with the gateway for routing and load balancing.
    """
    
    def __init__(self, gateway_url: str = "http://mcp-gateway:8001"):
        """
        Initialize the GatewayClient.
        
        Args:
            gateway_url: Base URL of the mcp-gateway service
        """
        self.gateway_url = gateway_url
        self.client = httpx.AsyncClient(timeout=10.0)
        logger.info(f"GatewayClient initialized with URL: {gateway_url}")
    
    async def register_mcp(
        self,
        mcp_id: str,
        host: str,
        port: int,
        name: str,
        tier: int,
        health_check_url: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register an MCP instance with the gateway.
        
        Args:
            mcp_id: Unique identifier for the MCP
            host: Hostname or IP where MCP is accessible
            port: Port number for MCP service
            name: Human-readable name for the MCP
            tier: MCP tier (0=client, 1=project, 2=team, etc.)
            health_check_url: Full URL for health check endpoint
            tags: Optional list of tags for categorization
            metadata: Optional additional metadata
        
        Returns:
            bool: True if registration successful, False otherwise
        """
        try:
            logger.info(f"Registering MCP {mcp_id} with gateway at {self.gateway_url}")
            
            # Prepare registration payload
            payload = {
                "mcp_id": mcp_id,
                "name": name,
                "host": host,
                "port": port,
                "tier": tier,
                "priority": 100,  # Default priority
                "weight": 100,    # Default weight for load balancing
                "max_concurrent_requests": 50,  # Default concurrency limit
                "health_check_url": health_check_url,
                "tags": tags or [],
                "metadata": metadata or {}
            }
            
            # Make registration request
            response = await self.client.post(
                f"{self.gateway_url}/api/v1/gateway/register",
                json=payload
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Successfully registered MCP {mcp_id} with gateway")
                logger.debug(f"Gateway response: {response.json()}")
                return True
            else:
                logger.warning(
                    f"❌ Failed to register MCP {mcp_id} with gateway: "
                    f"status={response.status_code}, body={response.text[:200]}"
                )
                return False
        
        except httpx.ConnectError as e:
            logger.error(f"❌ Cannot connect to gateway at {self.gateway_url}: {e}")
            return False
        
        except httpx.TimeoutException as e:
            logger.error(f"❌ Gateway registration timeout for MCP {mcp_id}: {e}")
            return False
        
        except Exception as e:
            logger.error(
                f"❌ Unexpected error registering MCP {mcp_id} with gateway: {e}",
                exc_info=True
            )
            return False
    
    async def deregister_mcp(self, mcp_id: str) -> bool:
        """
        Deregister an MCP instance from the gateway.
        
        Args:
            mcp_id: Unique identifier for the MCP
        
        Returns:
            bool: True if deregistration successful, False otherwise
        """
        try:
            logger.info(f"Deregistering MCP {mcp_id} from gateway")
            
            response = await self.client.delete(
                f"{self.gateway_url}/api/v1/gateway/instances/{mcp_id}"
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"✅ Successfully deregistered MCP {mcp_id} from gateway")
                return True
            else:
                logger.warning(
                    f"❌ Failed to deregister MCP {mcp_id}: status={response.status_code}"
                )
                return False
        
        except Exception as e:
            logger.error(f"❌ Error deregistering MCP {mcp_id} from gateway: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client and cleanup resources."""
        try:
            await self.client.aclose()
            logger.debug("GatewayClient closed")
        except Exception as e:
            logger.warning(f"Error closing GatewayClient: {e}")

