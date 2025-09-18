"""
Orchestrator Service Adapter

Comprehensive adapter for the Orchestrator service providing unified CLI interface
for workflow management, service registry, peer synchronization, and orchestration features.
"""

from typing import List, Tuple, Any, Dict
import time
from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult


class OrchestratorAdapter(BaseServiceAdapter):
    """
    Unified adapter for Orchestrator Service
    
    Provides standardized access to:
    - Service registry management
    - Peer synchronization
    - Workflow orchestration
    - OpenAPI polling
    - E2E demonstrations
    - Registry operations
    """
    
    def get_service_info(self) -> ServiceInfo:
        """Get Orchestrator Service information"""
        return ServiceInfo(
            name="orchestrator",
            port=5099,
            version="0.1.0",
            status=ServiceStatus.HEALTHY,
            description="Central orchestration service for workflow and service management",
            features=[
                "Service Registry Management",
                "Peer Synchronization",
                "Workflow Orchestration",
                "OpenAPI Polling",
                "E2E Demonstrations",
                "Service Discovery",
                "Health Monitoring",
                "Registry Operations"
            ],
            dependencies=["redis"],
            endpoints={
                "health": "/health",
                "peers": "/peers",
                "sync_peers": "/registry/sync-peers",
                "poll_openapi": "/registry/poll-openapi",
                "demo_e2e": "/demo/e2e",
                "registry_status": "/registry/status",
                "services": "/services",
                "workflow_status": "/workflows/status"
            }
        )
    
    async def health_check(self) -> CommandResult:
        """Perform comprehensive health check"""
        try:
            start_time = time.time()
            
            # Test health endpoint
            health_url = f"{self.base_url}/health"
            health_response = await self.clients.get_json(health_url)
            
            # Test peers endpoint
            peers_url = f"{self.base_url}/peers"
            peers_response = await self.clients.get_json(peers_url)
            
            execution_time = time.time() - start_time
            
            if health_response and health_response.get('status') == 'healthy':
                return CommandResult(
                    success=True,
                    data={
                        "health": health_response,
                        "peers_accessible": peers_response is not None,
                        "peer_count": len(peers_response) if isinstance(peers_response, list) else 0
                    },
                    message="Orchestrator is fully operational",
                    execution_time=execution_time
                )
            else:
                return CommandResult(
                    success=False,
                    error="Orchestrator health check failed",
                    execution_time=execution_time
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Health check error: {str(e)}"
            )
    
    async def get_available_commands(self) -> List[Tuple[str, str, str]]:
        """Get available Orchestrator commands"""
        return [
            ("peers", "List all registered peers", "peers"),
            ("sync_peers", "Synchronize peer registry", "sync_peers"),
            ("poll_openapi", "Poll OpenAPI specifications", "poll_openapi"),
            ("demo_e2e", "Run end-to-end demonstration", "demo_e2e [format]"),
            ("registry_status", "Get registry status", "registry_status"),
            ("services", "List registered services", "services"),
            ("workflow_status", "Get workflow status", "workflow_status"),
            ("register_service", "Register a new service", "register_service [service_data]"),
            ("health_detailed", "Get detailed health information", "health_detailed")
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute Orchestrator commands"""
        try:
            start_time = time.time()
            
            if command == "peers":
                return await self._get_peers()
            elif command == "sync_peers":
                return await self._sync_peers()
            elif command == "poll_openapi":
                return await self._poll_openapi()
            elif command == "demo_e2e":
                return await self._demo_e2e(kwargs)
            elif command == "registry_status":
                return await self._get_registry_status()
            elif command == "services":
                return await self._get_services()
            elif command == "workflow_status":
                return await self._get_workflow_status()
            elif command == "register_service":
                return await self._register_service(kwargs)
            elif command == "health_detailed":
                return await self.health_check()
            else:
                return CommandResult(
                    success=False,
                    error=f"Unknown command: {command}"
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Command execution failed: {str(e)}"
            )
    
    # Private command implementations
    async def _get_peers(self) -> CommandResult:
        """Get all registered peers - fallback to workflows since peers endpoint not available"""
        try:
            start_time = time.time()
            # Try peers endpoint first, fallback to workflows
            try:
                url = f"{self.base_url}/peers"
                response = await self.clients.get_json(url)
            except:
                # Fallback to available endpoint
                url = f"{self.base_url}/workflows"
                response = await self.clients.get_json(url)
                
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved orchestrator data (fallback to workflows endpoint)",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get orchestrator data: {str(e)}"
            )
    
    async def _sync_peers(self) -> CommandResult:
        """Synchronize peer registry"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/registry/sync-peers"
            response = await self.clients.post_json(url, {})
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Peer synchronization completed",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Peer synchronization failed: {str(e)}"
            )
    
    async def _poll_openapi(self) -> CommandResult:
        """Poll OpenAPI specifications"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/registry/poll-openapi"
            response = await self.clients.post_json(url, {})
            execution_time = time.time() - start_time
            
            results = response.get("results", []) if response else []
            return CommandResult(
                success=True,
                data=response,
                message=f"OpenAPI polling completed, found {len(results)} candidates",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"OpenAPI polling failed: {str(e)}"
            )
    
    async def _demo_e2e(self, params: Dict) -> CommandResult:
        """Run end-to-end demonstration"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/demo/e2e"
            
            payload = {
                "format": params.get("format", "json")
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="E2E demonstration completed successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"E2E demonstration failed: {str(e)}"
            )
    
    async def _get_registry_status(self) -> CommandResult:
        """Get registry status"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/registry/status"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Registry status retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get registry status: {str(e)}"
            )
    
    async def _get_services(self) -> CommandResult:
        """Get registered services"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/services"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            services_count = len(response) if isinstance(response, list) else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {services_count} registered services",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get services: {str(e)}"
            )
    
    async def _get_workflow_status(self) -> CommandResult:
        """Get workflow status"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/workflows/status"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Workflow status retrieved successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get workflow status: {str(e)}"
            )
    
    async def _register_service(self, params: Dict) -> CommandResult:
        """Register a new service"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/registry/services"
            
            # Default service registration payload
            payload = {
                "name": params.get("name", "new-service"),
                "url": params.get("url", "http://new-service:8080"),
                "health_endpoint": params.get("health_endpoint", "/health"),
                "version": params.get("version", "1.0.0")
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Service '{payload['name']}' registered successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Service registration failed: {str(e)}"
            )
