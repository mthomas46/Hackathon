"""Orchestrator Integration Module for Interpreter Service.

This module handles the integration between the interpreter service and the orchestrator,
enabling the execution of workflows based on natural language queries.
"""

import json
from typing import Dict, Any, List, Optional
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from .ecosystem_context import ecosystem_context


class OrchestratorIntegration:
    """Handles integration with the orchestrator for workflow execution."""

    def __init__(self):
        self.client = ServiceClients()
        self.orchestrator_url = "http://llm-orchestrator:5000"
        self.discovery_agent_url = "http://llm-discovery-agent:5045"

    async def execute_workflow(self, workflow_type: str, parameters: Dict[str, Any],
                              user_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a workflow through the orchestrator."""
        try:
            workflow_request = {
                "workflow_type": workflow_type,
                "parameters": parameters,
                "user_id": user_id,
                "correlation_id": f"interpreter_{workflow_type}_{parameters.get('id', 'auto')}"
            }

            # Execute through orchestrator's workflow endpoint
            response = await self.client.post_json(
                f"{self.orchestrator_url}/workflows/run",
                workflow_request
            )

            if response.get("success"):
                fire_and_forget(
                    "interpreter_workflow_executed",
                    f"Workflow '{workflow_type}' executed successfully",
                    ServiceNames.INTERPRETER,
                    {
                        "workflow_type": workflow_type,
                        "parameters": parameters,
                        "user_id": user_id,
                        "execution_result": response.get("data")
                    }
                )

                return {
                    "status": "success",
                    "workflow_type": workflow_type,
                    "execution_result": response.get("data"),
                    "message": f"Workflow '{workflow_type}' executed successfully"
                }
            else:
                return {
                    "status": "error",
                    "workflow_type": workflow_type,
                    "error": response.get("message", "Workflow execution failed"),
                    "message": f"Failed to execute workflow '{workflow_type}'"
                }

        except Exception as e:
            error_msg = f"Failed to execute workflow '{workflow_type}': {str(e)}"
            fire_and_forget(
                "interpreter_workflow_execution_failed",
                error_msg,
                ServiceNames.INTERPRETER,
                {
                    "workflow_type": workflow_type,
                    "parameters": parameters,
                    "error": str(e)
                }
            )
            return {
                "status": "error",
                "workflow_type": workflow_type,
                "error": str(e),
                "message": error_msg
            }

    async def execute_langgraph_workflow(self, workflow_type: str, parameters: Dict[str, Any],
                                       user_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a LangGraph workflow through the orchestrator."""
        try:
            langgraph_request = {
                "workflow_type": workflow_type,
                "parameters": parameters,
                "user_id": user_id,
                "tags": ["interpreter", "natural_language"]
            }

            # Execute through orchestrator's LangGraph endpoint
            response = await self.client.post_json(
                f"{self.orchestrator_url}/workflows/ai/{workflow_type}",
                langgraph_request
            )

            if response.get("success"):
                return {
                    "status": "success",
                    "workflow_type": workflow_type,
                    "execution_result": response.get("data"),
                    "message": f"LangGraph workflow '{workflow_type}' executed successfully"
                }
            else:
                return {
                    "status": "error",
                    "workflow_type": workflow_type,
                    "error": response.get("message", "LangGraph workflow execution failed"),
                    "message": f"Failed to execute LangGraph workflow '{workflow_type}'"
                }

        except Exception as e:
            error_msg = f"Failed to execute LangGraph workflow '{workflow_type}': {str(e)}"
            return {
                "status": "error",
                "workflow_type": workflow_type,
                "error": str(e),
                "message": error_msg
            }

    async def discover_available_workflows(self) -> Dict[str, Any]:
        """Discover available workflows from the orchestrator."""
        try:
            response = await self.client.get_json(f"{self.orchestrator_url}/workflows")
            return response.get("data", {})
        except Exception as e:
            fire_and_forget(
                "interpreter_workflow_discovery_failed",
                f"Failed to discover workflows: {str(e)}",
                ServiceNames.INTERPRETER
            )
            return {}

    async def get_orchestrator_tools(self) -> Dict[str, Any]:
        """Get available tools from the orchestrator."""
        try:
            # Try to discover tools through the orchestrator's tool discovery endpoint
            response = await self.client.post_json(
                f"{self.orchestrator_url}/tools/discover",
                {"dry_run": True}  # Dry run to just get available tools
            )

            if response.get("success"):
                return response.get("data", {})
            else:
                # Fallback: return ecosystem context tools
                return await ecosystem_context.get_orchestrator_tools()

        except Exception as e:
            # Fallback to ecosystem context
            return await ecosystem_context.get_orchestrator_tools()

    async def map_query_to_workflow(self, query: str, intent: str,
                                  entities: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map a natural language query to an appropriate workflow."""
        try:
            # Use ecosystem context to map query to workflow
            workflow_template = ecosystem_context.map_query_to_workflow(query, entities)

            if workflow_template:
                return workflow_template

            # Fallback: create custom workflow based on intent
            return await self._create_custom_workflow(intent, entities)

        except Exception as e:
            fire_and_forget(
                "interpreter_workflow_mapping_failed",
                f"Failed to map query to workflow: {str(e)}",
                ServiceNames.INTERPRETER,
                {"query": query, "intent": intent, "entities": entities}
            )
            return None

    async def _create_custom_workflow(self, intent: str, entities: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a custom workflow based on intent and entities."""
        workflow_config = {
            "description": f"Custom workflow for {intent}",
            "services": [],
            "steps": []
        }

        # Map intents to services and steps
        if intent == "analyze_document":
            workflow_config["services"] = ["document_store", "analysis_service"]
            workflow_config["steps"] = [
                {"service": "document_store", "action": "retrieve", "description": "Fetch documents"},
                {"service": "analysis_service", "action": "analyze", "description": "Analyze content"}
            ]

        elif intent == "find_prompt":
            workflow_config["services"] = ["prompt_store"]
            workflow_config["steps"] = [
                {"service": "prompt_store", "action": "search", "description": "Search prompts"}
            ]

        elif intent == "create_prompt":
            workflow_config["services"] = ["prompt_store"]
            workflow_config["steps"] = [
                {"service": "prompt_store", "action": "create", "description": "Create prompt"}
            ]

        elif intent.startswith("ingest_"):
            source_type = intent.replace("ingest_", "")
            workflow_config["services"] = ["source_agent", "document_store"]
            workflow_config["steps"] = [
                {"service": "source_agent", "action": "ingest", "description": f"Ingest from {source_type}"},
                {"service": "document_store", "action": "store", "description": "Store ingested content"}
            ]

        elif intent == "security_scan":
            workflow_config["services"] = ["secure_analyzer", "notification_service"]
            workflow_config["steps"] = [
                {"service": "secure_analyzer", "action": "scan", "description": "Security scan"},
                {"service": "notification_service", "action": "send", "description": "Send alerts"}
            ]

        # Return None if no workflow could be created
        if not workflow_config["services"]:
            return None

        return workflow_config

    async def validate_workflow_execution(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that a workflow can be executed."""
        try:
            # Check workflow compatibility with available services
            validation = await ecosystem_context.validate_workflow_compatibility(workflow)

            if not validation["valid"]:
                return {
                    "valid": False,
                    "issues": validation["missing_services"],
                    "available_services": validation["available_services"],
                    "message": f"Missing required services: {', '.join(validation['missing_services'])}"
                }

            return {
                "valid": True,
                "workflow": validation["workflow"],
                "message": "Workflow is valid and can be executed"
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "message": f"Workflow validation failed: {str(e)}"
            }

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a running workflow."""
        try:
            response = await self.client.get_json(f"{self.orchestrator_url}/workflows/status/{workflow_id}")
            return response.get("data", {})
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to get workflow status: {str(e)}"
            }

    async def cancel_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Cancel a running workflow."""
        try:
            response = await self.client.post_json(
                f"{self.orchestrator_url}/workflows/cancel/{workflow_id}",
                {}
            )
            return response.get("data", {})
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": f"Failed to cancel workflow: {str(e)}"
            }


# Create singleton instance
orchestrator_integration = OrchestratorIntegration()
