"""LangGraph Workflow Discovery Integration for Interpreter Service.

This module integrates with the orchestrator's LangGraph workflow system to discover,
validate, and execute available workflows based on natural language queries.
"""

import json
from typing import Dict, Any, List, Optional
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from .orchestrator_integration import orchestrator_integration
from .ecosystem_context import ecosystem_context


class LangGraphWorkflowDiscovery:
    """Handles discovery and integration with LangGraph workflows."""

    def __init__(self):
        self.client = ServiceClients()
        self.orchestrator_url = "http://llm-orchestrator:5000"
        self.discovered_workflows = {}
        self.workflow_cache = {}

    async def discover_langgraph_workflows(self) -> Dict[str, Any]:
        """Discover available LangGraph workflows from the orchestrator."""
        try:
            # Get available workflows from orchestrator
            available_workflows = await orchestrator_integration.discover_available_workflows()

            # Get LangGraph-specific workflows
            langgraph_workflows = {}

            # Query orchestrator for LangGraph workflow endpoints
            try:
                response = await self.client.get_json(f"{self.orchestrator_url}/workflows")
                if response.get("success"):
                    workflows_data = response.get("data", {})
                    # Identify LangGraph workflows (those with /ai/ prefix)
                    for workflow_name, workflow_info in workflows_data.items():
                        if isinstance(workflow_info, dict) and workflow_info.get("type") == "langgraph":
                            langgraph_workflows[workflow_name] = workflow_info
            except Exception as e:
                fire_and_forget(
                    "interpreter_langgraph_discovery_partial",
                    f"Could not discover LangGraph workflows: {str(e)}",
                    ServiceNames.INTERPRETER
                )

            # Also check for known LangGraph workflow endpoints
            known_langgraph_workflows = {
                "document-analysis": {
                    "type": "langgraph",
                    "description": "Analyze documents using LangGraph orchestration",
                    "endpoint": "/workflows/ai/document-analysis",
                    "parameters": {
                        "doc_id": "string",
                        "analysis_types": ["array"],
                        "include_summary": "boolean"
                    }
                },
                "code-documentation": {
                    "type": "langgraph",
                    "description": "Generate code documentation using LangGraph",
                    "endpoint": "/workflows/ai/code-documentation",
                    "parameters": {
                        "repo_url": "string",
                        "doc_types": ["array"],
                        "include_examples": "boolean"
                    }
                },
                "quality-assurance": {
                    "type": "langgraph",
                    "description": "Comprehensive quality assurance workflow",
                    "endpoint": "/workflows/ai/quality-assurance",
                    "parameters": {
                        "target_type": "string",
                        "quality_checks": ["array"],
                        "generate_report": "boolean"
                    }
                }
            }

            # Merge discovered and known workflows
            all_workflows = {**langgraph_workflows, **known_langgraph_workflows}

            self.discovered_workflows = all_workflows

            fire_and_forget(
                "interpreter_langgraph_workflows_discovered",
                f"Discovered {len(all_workflows)} LangGraph workflows",
                ServiceNames.INTERPRETER,
                {"workflows": list(all_workflows.keys())}
            )

            return {
                "status": "success",
                "workflows": all_workflows,
                "count": len(all_workflows),
                "source": "orchestrator_discovery"
            }

        except Exception as e:
            error_msg = f"Failed to discover LangGraph workflows: {str(e)}"
            fire_and_forget(
                "interpreter_langgraph_discovery_failed",
                error_msg,
                ServiceNames.INTERPRETER,
                {"error": str(e)}
            )

            return {
                "status": "error",
                "error": str(e),
                "workflows": {},
                "count": 0
            }

    async def find_matching_langgraph_workflow(self, query: str, intent: str,
                                             entities: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the best matching LangGraph workflow for a query."""
        try:
            # Ensure we have discovered workflows
            if not self.discovered_workflows:
                await self.discover_langgraph_workflows()

            best_match = None
            best_score = 0.0

            query_lower = query.lower()

            for workflow_name, workflow_info in self.discovered_workflows.items():
                score = self._calculate_workflow_match_score(
                    query_lower, intent, entities, workflow_name, workflow_info
                )

                if score > best_score:
                    best_score = score
                    best_match = {
                        "workflow_name": workflow_name,
                        "workflow_info": workflow_info,
                        "match_score": score,
                        "match_reason": self._get_match_reason(query_lower, intent, workflow_name)
                    }

            return best_match if best_score > 0.5 else None

        except Exception as e:
            fire_and_forget(
                "interpreter_langgraph_matching_failed",
                f"Failed to find matching LangGraph workflow: {str(e)}",
                ServiceNames.INTERPRETER,
                {"query": query, "intent": intent}
            )
            return None

    def _calculate_workflow_match_score(self, query: str, intent: str,
                                      entities: Dict[str, Any],
                                      workflow_name: str, workflow_info: Dict[str, Any]) -> float:
        """Calculate how well a workflow matches the query."""
        score = 0.0

        # Intent-based matching
        if intent in workflow_name or workflow_name in intent:
            score += 0.4

        # Keyword matching in query
        workflow_keywords = workflow_name.lower().split('-')
        query_words = query.lower().split()

        keyword_matches = sum(1 for keyword in workflow_keywords if keyword in query_words)
        if keyword_matches > 0:
            score += min(0.3, keyword_matches * 0.1)

        # Description matching
        description = workflow_info.get("description", "").lower()
        description_matches = sum(1 for word in query_words if word in description)
        if description_matches > 0:
            score += min(0.2, description_matches * 0.05)

        # Entity-based matching
        if "repo" in entities and "code" in workflow_name:
            score += 0.2
        if "url" in entities and "document" in workflow_name:
            score += 0.2
        if "file_path" in entities and ("code" in workflow_name or "document" in workflow_name):
            score += 0.2

        return min(score, 1.0)

    def _get_match_reason(self, query: str, intent: str, workflow_name: str) -> str:
        """Get human-readable reason for workflow match."""
        reasons = []

        if intent in workflow_name:
            reasons.append(f"matches intent '{intent}'")
        if any(word in query for word in workflow_name.split('-')):
            reasons.append("keyword match in query")
        if "document" in query and "document" in workflow_name:
            reasons.append("document-related query")
        if "code" in query and "code" in workflow_name:
            reasons.append("code-related query")

        return "; ".join(reasons) if reasons else "general workflow match"

    async def execute_langgraph_workflow(self, workflow_name: str,
                                       parameters: Dict[str, Any],
                                       user_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a LangGraph workflow through the orchestrator."""
        try:
            # Validate workflow exists
            if workflow_name not in self.discovered_workflows:
                await self.discover_langgraph_workflows()  # Refresh discovery

            if workflow_name not in self.discovered_workflows:
                return {
                    "status": "error",
                    "error": f"Workflow '{workflow_name}' not found",
                    "available_workflows": list(self.discovered_workflows.keys())
                }

            # Execute through orchestrator
            result = await orchestrator_integration.execute_langgraph_workflow(
                workflow_name, parameters, user_id
            )

            if result["status"] == "success":
                fire_and_forget(
                    "interpreter_langgraph_workflow_executed",
                    f"LangGraph workflow '{workflow_name}' executed successfully",
                    ServiceNames.INTERPRETER,
                    {
                        "workflow_name": workflow_name,
                        "parameters": parameters,
                        "execution_result": result
                    }
                )

            return result

        except Exception as e:
            error_msg = f"Failed to execute LangGraph workflow '{workflow_name}': {str(e)}"
            fire_and_forget(
                "interpreter_langgraph_execution_failed",
                error_msg,
                ServiceNames.INTERPRETER,
                {"workflow_name": workflow_name, "error": str(e)}
            )

            return {
                "status": "error",
                "workflow_name": workflow_name,
                "error": str(e),
                "message": error_msg
            }

    async def validate_langgraph_workflow(self, workflow_name: str,
                                        parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that a LangGraph workflow can be executed with given parameters."""
        try:
            if workflow_name not in self.discovered_workflows:
                return {
                    "valid": False,
                    "error": f"Workflow '{workflow_name}' not found",
                    "available_workflows": list(self.discovered_workflows.keys())
                }

            workflow_info = self.discovered_workflows[workflow_name]
            expected_params = workflow_info.get("parameters", {})

            # Validate required parameters
            missing_params = []
            invalid_params = []

            for param_name, param_type in expected_params.items():
                if param_name not in parameters:
                    # Check if parameter is required (simplified check)
                    if param_type != "optional":
                        missing_params.append(param_name)
                else:
                    # Validate parameter type (basic validation)
                    actual_value = parameters[param_name]
                    if not self._validate_parameter_type(actual_value, param_type):
                        invalid_params.append(f"{param_name} (expected {param_type})")

            if missing_params or invalid_params:
                return {
                    "valid": False,
                    "missing_parameters": missing_params,
                    "invalid_parameters": invalid_params,
                    "expected_parameters": expected_params
                }

            return {
                "valid": True,
                "workflow_name": workflow_name,
                "parameters": parameters,
                "message": "Workflow parameters are valid"
            }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "message": f"Workflow validation failed: {str(e)}"
            }

    def _validate_parameter_type(self, value: Any, expected_type: str) -> bool:
        """Validate parameter type (simplified validation)."""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "boolean":
            return isinstance(value, bool)
        elif expected_type.startswith("array") or expected_type == "list":
            return isinstance(value, list)
        elif expected_type == "number" or expected_type == "integer":
            return isinstance(value, (int, float))
        else:
            # For unknown types, accept any value
            return True

    async def get_workflow_suggestions(self, query: str, intent: str) -> List[Dict[str, Any]]:
        """Get workflow suggestions based on query and intent."""
        try:
            suggestions = []

            # Ensure we have discovered workflows
            if not self.discovered_workflows:
                await self.discover_langgraph_workflows()

            for workflow_name, workflow_info in self.discovered_workflows.items():
                confidence = self._calculate_workflow_match_score(
                    query.lower(), intent, {}, workflow_name, workflow_info
                )

                if confidence > 0.3:  # Only suggest reasonably good matches
                    suggestions.append({
                        "workflow_name": workflow_name,
                        "description": workflow_info.get("description", ""),
                        "confidence": confidence,
                        "parameters": workflow_info.get("parameters", {}),
                        "endpoint": workflow_info.get("endpoint", "")
                    })

            # Sort by confidence
            suggestions.sort(key=lambda x: x["confidence"], reverse=True)

            return suggestions[:5]  # Return top 5 suggestions

        except Exception as e:
            fire_and_forget(
                "interpreter_workflow_suggestions_failed",
                f"Failed to get workflow suggestions: {str(e)}",
                ServiceNames.INTERPRETER,
                {"query": query, "intent": intent}
            )
            return []

    def get_available_langgraph_workflows(self) -> Dict[str, Any]:
        """Get all available LangGraph workflows."""
        return {
            "workflows": self.discovered_workflows,
            "count": len(self.discovered_workflows),
            "last_discovered": getattr(self, '_last_discovery', None)
        }


# Create singleton instance
langgraph_discovery = LangGraphWorkflowDiscovery()
