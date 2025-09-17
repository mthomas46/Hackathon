"""Orchestrator Integration Module for Discovery Agent service.

This module provides Phase 3 integration between the Discovery Agent and Orchestrator
to enable dynamic tool loading and AI-powered workflow generation.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
try:
    from services.shared.clients import ServiceClients
except ImportError:
    # Fallback for when running in Docker or different environment
    ServiceClients = None


class OrchestratorIntegration:
    """Integration layer between Discovery Agent and Orchestrator for dynamic tool loading"""

    def __init__(self, orchestrator_url: str = "http://localhost:5099"):
        self.orchestrator_url = orchestrator_url
        self.service_client = ServiceClients()
        self.workflow_cache = {}

    async def register_discovered_tools(self, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Register discovered tools with the orchestrator for workflow use

        Args:
            tools: List of discovered tools to register

        Returns:
            Registration results with success/failure status
        """
        results = {
            "total_tools": len(tools),
            "registered_tools": 0,
            "failed_registrations": 0,
            "details": []
        }

        print(f"🔗 Registering {len(tools)} discovered tools with orchestrator...")

        for tool in tools:
            try:
                # Check if tool is LangGraph-ready
                if not tool.get("langraph_ready", {}).get("ready", False):
                    results["details"].append({
                        "tool": tool["name"],
                        "status": "skipped",
                        "reason": "Not LangGraph-ready"
                    })
                    continue

                # Register tool with orchestrator
                registration_result = await self._register_tool_with_orchestrator(tool)

                if registration_result["success"]:
                    results["registered_tools"] += 1
                    results["details"].append({
                        "tool": tool["name"],
                        "status": "registered",
                        "workflow_id": registration_result.get("workflow_id")
                    })
                else:
                    results["failed_registrations"] += 1
                    results["details"].append({
                        "tool": tool["name"],
                        "status": "failed",
                        "error": registration_result.get("error")
                    })

            except Exception as e:
                results["failed_registrations"] += 1
                results["details"].append({
                    "tool": tool["name"],
                    "status": "error",
                    "error": str(e)
                })

        print(f"✅ Registration complete: {results['registered_tools']} registered, {results['failed_registrations']} failed")

        return results

    async def _register_tool_with_orchestrator(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Register a single tool with the orchestrator"""
        try:
            # Prepare tool registration payload
            tool_payload = {
                "tool_name": tool["name"],
                "service": tool["service"],
                "category": tool["category"],
                "description": tool["description"],
                "parameters": tool.get("parameters", []),
                "method": tool["method"],
                "path": tool["path"],
                "langraph_ready": tool.get("langraph_ready", {}),
                "registered_by": "discovery-agent"
            }

            async with self.service_client.session() as session:
                url = f"{self.orchestrator_url}/api/workflows/register-tool"

                async with session.post(url, json=tool_payload, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "workflow_id": result.get("workflow_id"),
                            "tool_id": result.get("tool_id")
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Registration failed: {response.status} - {error_text}"
                        }

        except Exception as e:
            return {
                "success": False,
                "error": f"Connection error: {str(e)}"
            }

    async def create_dynamic_workflow(self, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """Create a dynamic workflow using discovered tools

        Args:
            workflow_request: Workflow specification with required tools and steps

        Returns:
            Workflow creation results
        """
        try:
            print(f"🔄 Creating dynamic workflow: {workflow_request.get('name', 'unnamed')}")

            # Validate required tools are available
            required_tools = workflow_request.get("required_tools", [])
            available_tools = await self._check_tool_availability(required_tools)

            if not available_tools["all_available"]:
                return {
                    "success": False,
                    "error": "Required tools not available",
                    "missing_tools": available_tools["missing_tools"],
                    "available_tools": available_tools["available_tools"]
                }

            # Create workflow specification
            workflow_spec = {
                "name": workflow_request["name"],
                "description": workflow_request.get("description", ""),
                "steps": workflow_request["steps"],
                "required_tools": required_tools,
                "created_by": "discovery-agent-dynamic",
                "tool_sources": available_tools["tool_sources"]
            }

            # Register workflow with orchestrator
            result = await self._register_workflow(workflow_spec)

            if result["success"]:
                self.workflow_cache[workflow_request["name"]] = {
                    "spec": workflow_spec,
                    "created_at": "2025-01-17T21:30:00Z",
                    "status": "active"
                }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow creation failed: {str(e)}"
            }

    async def _check_tool_availability(self, required_tools: List[str]) -> Dict[str, Any]:
        """Check if required tools are available in the orchestrator"""
        try:
            async with self.service_client.session() as session:
                url = f"{self.orchestrator_url}/api/workflows/available-tools"

                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        available_data = await response.json()
                        available_tools = available_data.get("tools", [])

                        missing_tools = []
                        tool_sources = {}

                        for required_tool in required_tools:
                            tool_found = False
                            for available_tool in available_tools:
                                if available_tool["name"] == required_tool:
                                    tool_found = True
                                    tool_sources[required_tool] = available_tool.get("service", "unknown")
                                    break

                            if not tool_found:
                                missing_tools.append(required_tool)

                        return {
                            "all_available": len(missing_tools) == 0,
                            "available_tools": [t["name"] for t in available_tools],
                            "missing_tools": missing_tools,
                            "tool_sources": tool_sources
                        }
                    else:
                        return {
                            "all_available": False,
                            "available_tools": [],
                            "missing_tools": required_tools,
                            "tool_sources": {},
                            "error": f"Failed to check tool availability: {response.status}"
                        }

        except Exception as e:
            return {
                "all_available": False,
                "available_tools": [],
                "missing_tools": required_tools,
                "tool_sources": {},
                "error": str(e)
            }

    async def _register_workflow(self, workflow_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Register a workflow with the orchestrator"""
        try:
            async with self.service_client.session() as session:
                url = f"{self.orchestrator_url}/api/workflows/create-dynamic"

                async with session.post(url, json=workflow_spec, timeout=15) as response:
                    if response.status == 201:
                        result = await response.json()
                        return {
                            "success": True,
                            "workflow_id": result.get("workflow_id"),
                            "execution_url": result.get("execution_url"),
                            "status": "created"
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Workflow creation failed: {response.status} - {error_text}"
                        }

        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow registration error: {str(e)}"
            }

    async def execute_dynamic_workflow(self, workflow_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a previously created dynamic workflow"""
        try:
            # Get workflow spec from cache or orchestrator
            workflow_spec = self.workflow_cache.get(workflow_name)

            if not workflow_spec:
                # Try to retrieve from orchestrator
                workflow_spec = await self._get_workflow_from_orchestrator(workflow_name)
                if not workflow_spec:
                    return {
                        "success": False,
                        "error": f"Workflow '{workflow_name}' not found"
                    }

            # Execute workflow
            execution_payload = {
                "workflow_name": workflow_name,
                "parameters": parameters,
                "execution_source": "discovery-agent"
            }

            async with self.service_client.session() as session:
                url = f"{self.orchestrator_url}/api/workflows/execute-dynamic"

                async with session.post(url, json=execution_payload, timeout=30) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        return {
                            "success": True,
                            "execution_id": result.get("execution_id"),
                            "status": result.get("status", "running"),
                            "results": result.get("results", {})
                        }
                    else:
                        error_text = await response.text()
                        return {
                            "success": False,
                            "error": f"Workflow execution failed: {response.status} - {error_text}"
                        }

        except Exception as e:
            return {
                "success": False,
                "error": f"Workflow execution error: {str(e)}"
            }

    async def _get_workflow_from_orchestrator(self, workflow_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve workflow specification from orchestrator"""
        try:
            async with self.service_client.session() as session:
                url = f"{self.orchestrator_url}/api/workflows/{workflow_name}"

                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        workflow_data = await response.json()
                        return workflow_data.get("workflow")
                    else:
                        return None

        except Exception:
            return None

    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get orchestrator status and available capabilities"""
        try:
            async with self.service_client.session() as session:
                async with session.get(f"{self.orchestrator_url}/health", timeout=5) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        return {
                            "status": "healthy",
                            "version": health_data.get("version", "unknown"),
                            "services": health_data.get("services", []),
                            "workflows": health_data.get("active_workflows", 0)
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"Orchestrator returned {response.status}"
                        }

        except Exception as e:
            return {
                "status": "unreachable",
                "error": str(e)
            }

    async def list_registered_workflows(self) -> Dict[str, Any]:
        """List all workflows registered with the orchestrator"""
        try:
            async with self.service_client.session() as session:
                url = f"{self.orchestrator_url}/api/workflows/list"

                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        workflows_data = await response.json()
                        return {
                            "success": True,
                            "workflows": workflows_data.get("workflows", []),
                            "total_count": workflows_data.get("total_count", 0)
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to list workflows: {response.status}"
                        }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Create singleton instance
orchestrator_integration = OrchestratorIntegration()
