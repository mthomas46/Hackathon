"""LangGraph workflow engine for Orchestrator service.

This module provides the core LangGraph workflow execution engine
integrated with the existing orchestrator infrastructure.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.tools import BaseTool

from .state import WorkflowState, create_workflow_state
from .tools import create_service_tools
from .service_integrations import (
    SERVICE_INTEGRATIONS,
    get_service_integration_tools,
    initialize_all_service_integrations
)
from ..shared_utils import get_orchestrator_service_client
from ..startup_discovery import startup_discovery
from services.shared.utilities import utc_now
from services.shared.logging import fire_and_forget


class LangGraphWorkflowEngine:
    """LangGraph workflow execution engine integrated with orchestrator."""

    def __init__(self):
        self.workflows = {}  # Store compiled workflow graphs
        self.tools = {}  # Store available tools
        self.service_client = get_orchestrator_service_client()

    async def initialize_tools(self, service_names: List[str]) -> Dict[str, BaseTool]:
        """Initialize tools for specified services, using discovered tools when available."""
        tools = {}

        for service_name in service_names:
            try:
                # First, try to use discovered tools from startup discovery
                discovered_tools_data = await startup_discovery.get_discovered_tools(service_name)

                if discovered_tools_data and "tools" in discovered_tools_data:
                    # Use discovered tools
                    service_tools = await self._create_tools_from_discovery(service_name, discovered_tools_data)
                    print(f"🔍 Using discovered tools for {service_name}: {len(service_tools)} tools")
                # 2. Try comprehensive service integrations
                elif service_name in SERVICE_INTEGRATIONS:
                    integration_class = SERVICE_INTEGRATIONS[service_name]
                    integration = integration_class()
                    service_tools = await integration.initialize_tools()
                    print(f"🔧 Using service integration for {service_name}: {len(service_tools)} tools")

                # 3. Fallback to manual tool creation
                else:
                    service_tools = await create_service_tools(service_name, self.service_client)
                    print(f"⚙️ Created manual tools for {service_name}: {list(service_tools.keys())}")

                tools.update(service_tools)

            except Exception as e:
                print(f"✗ Failed to initialize tools for {service_name}: {e}")
                continue

        self.tools = tools
        return tools

    async def _create_tools_from_discovery(self, service_name: str, discovery_data: Dict[str, Any]) -> Dict[str, BaseTool]:
        """Create LangChain tools from discovered tool definitions."""
        tools = {}

        for tool_def in discovery_data.get("tools", []):
            try:
                # Create a LangChain tool from the discovered tool definition
                tool = await self._create_tool_from_definition(service_name, tool_def)
                if tool:
                    tools[tool.name] = tool
            except Exception as e:
                print(f"⚠️ Failed to create tool '{tool_def.get('name', 'unknown')}' from discovery: {e}")
                continue

        return tools

    async def _create_tool_from_definition(self, service_name: str, tool_def: Dict[str, Any]) -> Optional[BaseTool]:
        """Create a LangChain tool from a discovered tool definition."""
        from langchain_core.tools import tool
        from pydantic import BaseModel, Field
        import inspect

        tool_name = tool_def.get("name", "")
        tool_description = tool_def.get("description", "")
        parameters = tool_def.get("parameters", {})

        if not tool_name:
            return None

        # Create dynamic function for the tool
        async def dynamic_tool_func(**kwargs):
            """Dynamic tool function that calls the discovered service endpoint."""
            try:
                # Get service URL from discovery data
                service_url = tool_def.get("service_url", "")
                http_method = tool_def.get("http_method", "GET")
                path = tool_def.get("path", "")

                if not service_url or not path:
                    raise ValueError(f"Missing service_url or path for tool {tool_name}")

                # Construct full URL
                full_url = f"{service_url}{path}"

                # Prepare request data
                if http_method.upper() in ["POST", "PUT", "PATCH"]:
                    # For methods with body, pass kwargs as JSON
                    response = await self.service_client.post_json(full_url, kwargs)
                elif http_method.upper() == "GET":
                    # For GET, pass kwargs as query parameters
                    response = await self.service_client.get_json(full_url, params=kwargs)
                else:
                    # For other methods, pass kwargs as JSON
                    response = await self.service_client.post_json(full_url, kwargs)

                return response

            except Exception as e:
                error_msg = f"Tool {tool_name} execution failed: {str(e)}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)

        # Create the tool function with proper signature
        dynamic_tool_func.__name__ = tool_name
        dynamic_tool_func.__doc__ = tool_description

        # Create LangChain tool
        langchain_tool = tool(dynamic_tool_func)
        langchain_tool.name = tool_name
        langchain_tool.description = tool_description

        return langchain_tool

    def create_workflow_graph(
        self,
        workflow_type: str,
        nodes: Dict[str, Callable],
        edges: List[tuple],
        conditional_edges: Optional[List[tuple]] = None
    ):
        """Create and compile a LangGraph workflow."""

        # Create the state graph
        workflow = StateGraph(WorkflowState)

        # Add nodes
        for node_name, node_func in nodes.items():
            workflow.add_node(node_name, node_func)

        # Add edges
        for edge in edges:
            if len(edge) == 2:
                workflow.add_edge(edge[0], edge[1])
            elif len(edge) == 3:
                workflow.add_edge(edge[0], edge[1], edge[2])

        # Add conditional edges if provided
        if conditional_edges:
            for condition in conditional_edges:
                workflow.add_conditional_edges(*condition)

        # Compile the workflow
        compiled_workflow = workflow.compile()

        # Store the compiled workflow
        self.workflows[workflow_type] = compiled_workflow

        return compiled_workflow

    async def execute_workflow(
        self,
        workflow_type: str,
        input_data: Dict[str, Any],
        tools: Optional[Dict[str, BaseTool]] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute a LangGraph workflow."""

        # Get the compiled workflow
        if workflow_type not in self.workflows:
            raise ValueError(f"Workflow '{workflow_type}' not found. Available: {list(self.workflows.keys())}")

        workflow = self.workflows[workflow_type]

        # Create initial workflow state
        initial_state = create_workflow_state(
            workflow_type=workflow_type,
            input_data=input_data,
            user_id=user_id
        )

        # Log workflow start
        await self._log_workflow_event(initial_state.metadata.workflow_id, "started", {
            "workflow_type": workflow_type,
            "input_data": input_data,
            "user_id": user_id
        })

        try:
            # Execute the workflow
            start_time = utc_now()

            # For async workflows, we need to handle the execution differently
            # This is a simplified version - in practice, you'd handle async properly
            result = await workflow.ainvoke(initial_state)

            end_time = utc_now()
            execution_time = (end_time - start_time).total_seconds()

            # Update final state
            result.metadata.updated_at = end_time
            result.update_metrics({
                "execution_time": execution_time,
                "success": True,
                "end_time": end_time
            })

            # Log successful completion
            await self._log_workflow_event(
                result.metadata.workflow_id,
                "completed",
                {
                    "execution_time": execution_time,
                    "output_data": result.output_data,
                    "service_executions": len(result.service_executions),
                    "errors": len(result.errors)
                }
            )

            return {
                "workflow_id": result.metadata.workflow_id,
                "status": "completed",
                "execution_time": execution_time,
                "output": result.output_data,
                "metrics": result.metrics,
                "service_executions": len(result.service_executions),
                "errors": len(result.errors)
            }

        except Exception as e:
            # Log error
            await self._log_workflow_event(
                initial_state.metadata.workflow_id,
                "failed",
                {"error": str(e), "error_type": type(e).__name__}
            )

            # Re-raise the exception
            raise

    async def _log_workflow_event(self, workflow_id: str, event_type: str, data: Dict[str, Any]):
        """Log workflow events using the orchestrator's logging infrastructure."""
        try:
            # Use the existing logging infrastructure
            log_data = {
                "workflow_id": workflow_id,
                "event_type": event_type,
                "timestamp": utc_now(),
                "data": data
            }

            # This would integrate with your existing logging service
            # For now, we'll use a placeholder
            fire_and_forget(self._send_to_logging_service(log_data))

        except Exception as e:
            # Don't let logging failures break the workflow
            print(f"Logging failed: {e}")

    async def _send_to_logging_service(self, log_data: Dict[str, Any]):
        """Send log data to the logging service."""
        # Placeholder - would integrate with your logging service
        # await self.service_client.post_json("logging/log", log_data)
        print(f"[LOG] {log_data}")

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a running workflow."""
        # Placeholder - would query workflow state from storage
        return {
            "workflow_id": workflow_id,
            "status": "running",
            "current_step": "processing",
            "progress": 0.5
        }

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        # Placeholder - would implement workflow cancellation
        await self._log_workflow_event(workflow_id, "cancelled", {})
        return True

    def list_available_workflows(self) -> List[str]:
        """List all available compiled workflows."""
        return list(self.workflows.keys())

    def get_workflow_info(self, workflow_type: str) -> Dict[str, Any]:
        """Get information about a specific workflow."""
        if workflow_type not in self.workflows:
            return {"error": f"Workflow '{workflow_type}' not found"}

        workflow = self.workflows[workflow_type]

        return {
            "workflow_type": workflow_type,
            "nodes": list(workflow.nodes.keys()) if hasattr(workflow, 'nodes') else [],
            "compiled": True,
            "description": f"Compiled LangGraph workflow for {workflow_type}"
        }
