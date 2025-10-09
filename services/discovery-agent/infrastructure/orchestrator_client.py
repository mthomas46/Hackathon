"""
Orchestrator Client - Integration with orchestrator service.

Handles communication with the orchestrator service for service
and tool registration.
"""

from typing import Dict, Any, List, Optional
import httpx


class OrchestratorClient:
    """
    Client for interacting with the orchestrator service.
    """
    
    def __init__(self, orchestrator_url: str = "http://orchestrator:5099"):
        """
        Initialize the orchestrator client.
        
        Args:
            orchestrator_url: Base URL of the orchestrator service
        """
        self.orchestrator_url = orchestrator_url.rstrip("/")
        self._http_client = None
    
    async def register_service(self, service) -> Dict[str, Any]:
        """
        Register a discovered service with the orchestrator.
        
        Args:
            service: Service entity to register
            
        Returns:
            Registration result
        """
        if self._http_client:
            # Use provided mock client
            return await self._http_client.register_service(service)
        
        # Real implementation
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.orchestrator_url}/api/v1/services/register",
                    json={
                        "name": service.name,
                        "base_url": service.base_url,
                        "version": service.version,
                        "description": service.description,
                        "status": service.status,
                        "endpoint_count": len(service.endpoints)
                    },
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    return {"success": True, "service_name": service.name}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            raise Exception(f"Failed to register service: {str(e)}")
    
    async def register_tools(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Register generated tools with the orchestrator.
        
        Args:
            tools: List of tool definitions
            
        Returns:
            Registration result
        """
        if self._http_client:
            # Use provided mock client
            return await self._http_client.register_tools(tools)
        
        # Real implementation
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.orchestrator_url}/api/v1/tools/register",
                    json={"tools": tools},
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    return {
                        "success": True,
                        "tools_registered": len(tools)
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            raise Exception(f"Failed to register tools: {str(e)}")
    
    async def get_service(self, service_name: str) -> Optional[Dict[str, Any]]:
        """
        Get service information from the orchestrator.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Service information or None if not found
        """
        if self._http_client:
            # Use provided mock client
            return await self._http_client.get_service(service_name)
        
        # Real implementation
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.orchestrator_url}/api/v1/services/{service_name}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    return None
        except Exception as e:
            return None

