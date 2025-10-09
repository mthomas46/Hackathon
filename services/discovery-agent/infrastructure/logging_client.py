"""
Log Collector Client - Integration with log-collector service.

Handles sending logs and events to the centralized log-collector service.
"""

from typing import Dict, Any
from datetime import datetime, timezone
import httpx


class LogCollectorClient:
    """
    Client for interacting with the log-collector service.
    """
    
    def __init__(self, log_collector_url: str = "http://log-collector:5060"):
        """
        Initialize the log collector client.
        
        Args:
            log_collector_url: Base URL of the log-collector service
        """
        self.log_collector_url = log_collector_url.rstrip("/")
    
    async def send_log(self, log_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send a log entry to the log-collector.
        
        Args:
            log_entry: Log entry dictionary
            
        Returns:
            Response from log-collector or None on failure
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.log_collector_url}/api/v1/logs",
                    json=log_entry,
                    timeout=5.0
                )
                
                if response.status_code in [200, 201, 202]:
                    return {"success": True, "status": "logged"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            # Silently fail - logging should not break the main flow
            return None
    
    async def send_event(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Send an event to the log-collector.
        
        Args:
            event: Event dictionary
            
        Returns:
            Response from log-collector or None on failure
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.log_collector_url}/api/v1/events",
                    json=event,
                    timeout=5.0
                )
                
                if response.status_code in [200, 201, 202]:
                    return {"success": True, "status": "logged"}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            # Silently fail - logging should not break the main flow
            return None
    
    async def log_discovery_event(
        self,
        service_name: str,
        discovery_result: Dict[str, Any]
    ) -> None:
        """
        Log a service discovery event.
        
        Args:
            service_name: Name of the discovered service
            discovery_result: Discovery result details
        """
        event = {
            "service": "discovery-agent",
            "event_type": "service_discovered",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "service_name": service_name,
                **discovery_result
            }
        }
        
        await self.send_event(event)
    
    async def log_tool_generation_event(
        self,
        service_name: str,
        tools_count: int
    ) -> None:
        """
        Log a tool generation event.
        
        Args:
            service_name: Name of the service
            tools_count: Number of tools generated
        """
        event = {
            "service": "discovery-agent",
            "event_type": "tools_generated",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": {
                "service_name": service_name,
                "tools_count": tools_count
            }
        }
        
        await self.send_event(event)

