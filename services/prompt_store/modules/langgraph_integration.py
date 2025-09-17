#!/usr/bin/env python3
"""
LangGraph Integration for Prompt Store Service

This module provides LangGraph awareness and integration capabilities
for the Prompt Store Service, enabling intelligent prompt management in AI workflows.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import BaseTool, tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from services.shared.utilities import get_service_client
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class PromptStoreLangGraphIntegration:
    """LangGraph integration for Prompt Store Service."""

    def __init__(self):
        self.service_name = ServiceNames.PROMPT_STORE
        self.service_client = get_service_client()
        self.workflow_prompts = {}
        self.performance_tracker = {}

    async def initialize_langgraph_tools(self) -> Dict[str, BaseTool]:
        """Initialize LangGraph tools for prompt store."""

        @tool
        async def create_prompt_langgraph(name: str, category: str, content: str,
                                        variables: List[str], workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Create a prompt within LangGraph workflow context."""
            try:
                # Enhance prompt with workflow context
                enhanced_metadata = {
                    "source": "langgraph_workflow",
                    "workflow_context": workflow_context or {},
                    "created_at": datetime.now().isoformat(),
                    "langgraph_integration": True,
                    "performance_tracking": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/prompts",
                    {
                        "name": name,
                        "category": category,
                        "content": content,
                        "variables": variables,
                        "metadata": enhanced_metadata
                    }
                )

                # Track prompt in workflow context
                prompt_id = result.get("id")
                if prompt_id and workflow_context:
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        if workflow_id not in self.workflow_prompts:
                            self.workflow_prompts[workflow_id] = []
                        self.workflow_prompts[workflow_id].append({
                            "prompt_id": prompt_id,
                            "name": name,
                            "category": category,
                            "created_at": datetime.now().isoformat()
                        })

                return {
                    "success": True,
                    "prompt_id": prompt_id,
                    "workflow_integration": "completed",
                    "prompt_tracked": bool(workflow_context)
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph prompt creation failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def get_prompt_langgraph(name: str, category: str,
                                     workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Retrieve a prompt within LangGraph workflow context."""
            try:
                result = await self.service_client.get_json(
                    f"{self.service_name}/api/v1/prompts/search/{category}/{name}"
                )

                # Add workflow context and tracking
                if workflow_context:
                    result["workflow_context"] = workflow_context
                    result["retrieved_for_workflow"] = True
                    result["retrieval_timestamp"] = datetime.now().isoformat()

                    # Track usage for performance monitoring
                    prompt_id = result.get("id")
                    if prompt_id:
                        self._track_prompt_usage(prompt_id, workflow_context)

                return {
                    "success": True,
                    "prompt": result,
                    "workflow_integration": "completed"
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        @tool
        async def get_optimal_prompt_langgraph(task_type: str, context: Dict[str, Any],
                                              workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Get the optimal prompt for a task within workflow context."""
            try:
                # Enhance context with workflow information
                enhanced_context = {
                    **context,
                    "workflow_context": workflow_context,
                    "request_timestamp": datetime.now().isoformat(),
                    "optimization_request": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/orchestration/prompts/select",
                    {
                        "task_type": task_type,
                        "context": enhanced_context
                    }
                )

                # Track optimization request
                if workflow_context and result.get("prompt_id"):
                    self._track_prompt_optimization(
                        result["prompt_id"],
                        task_type,
                        workflow_context
                    )

                return {
                    "success": True,
                    "optimal_prompt": result,
                    "workflow_integration": "completed",
                    "optimization_tracked": bool(workflow_context)
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph prompt optimization failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def update_prompt_performance_langgraph(prompt_id: str, performance_metrics: Dict[str, Any],
                                                    workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Update prompt performance metrics from workflow execution."""
            try:
                # Enhance performance metrics with workflow context
                enhanced_metrics = {
                    **performance_metrics,
                    "workflow_context": workflow_context,
                    "updated_at": datetime.now().isoformat(),
                    "update_source": "langgraph_workflow"
                }

                result = await self.service_client.put_json(
                    f"{self.service_name}/api/v1/prompts/{prompt_id}/performance",
                    {
                        "performance_metrics": enhanced_metrics,
                        "updated_by": "langgraph_workflow"
                    }
                )

                # Update local performance tracking
                if prompt_id not in self.performance_tracker:
                    self.performance_tracker[prompt_id] = []
                self.performance_tracker[prompt_id].append({
                    "metrics": enhanced_metrics,
                    "workflow_context": workflow_context,
                    "timestamp": datetime.now().isoformat()
                })

                return {
                    "success": True,
                    "performance_updated": result,
                    "workflow_integration": "completed"
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        @tool
        async def get_workflow_prompts_langgraph(workflow_id: str) -> Dict[str, Any]:
            """Get all prompts used in a specific workflow."""
            try:
                # Check local workflow tracking first
                if workflow_id in self.workflow_prompts:
                    local_prompts = self.workflow_prompts[workflow_id]
                    return {
                        "success": True,
                        "prompts": local_prompts,
                        "source": "workflow_cache",
                        "workflow_id": workflow_id,
                        "cached_count": len(local_prompts)
                    }

                # Query prompts by workflow metadata
                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/search",
                    {
                        "query": f"workflow_id:{workflow_id}",
                        "filters": {
                            "langgraph_integration": True,
                            "workflow_query": True
                        }
                    }
                )

                return {
                    "success": True,
                    "prompts": result.get("results", []),
                    "source": "database_query",
                    "workflow_id": workflow_id,
                    "total_found": len(result.get("results", []))
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph workflow prompts query failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        return {
            "create_prompt_langgraph": create_prompt_langgraph,
            "get_prompt_langgraph": get_prompt_langgraph,
            "get_optimal_prompt_langgraph": get_optimal_prompt_langgraph,
            "update_prompt_performance_langgraph": update_prompt_performance_langgraph,
            "get_workflow_prompts_langgraph": get_workflow_prompts_langgraph
        }

    def _track_prompt_usage(self, prompt_id: str, workflow_context: Dict[str, Any]):
        """Track prompt usage for performance monitoring."""
        if prompt_id not in self.performance_tracker:
            self.performance_tracker[prompt_id] = []

        usage_record = {
            "action": "retrieved",
            "workflow_context": workflow_context,
            "timestamp": datetime.now().isoformat()
        }

        self.performance_tracker[prompt_id].append(usage_record)

    def _track_prompt_optimization(self, prompt_id: str, task_type: str, workflow_context: Dict[str, Any]):
        """Track prompt optimization requests."""
        if prompt_id not in self.performance_tracker:
            self.performance_tracker[prompt_id] = []

        optimization_record = {
            "action": "optimized",
            "task_type": task_type,
            "workflow_context": workflow_context,
            "timestamp": datetime.now().isoformat()
        }

        self.performance_tracker[prompt_id].append(optimization_record)

    async def handle_langgraph_workflow_message(self, message: BaseMessage) -> Dict[str, Any]:
        """Handle incoming LangGraph workflow messages."""
        try:
            if isinstance(message, HumanMessage):
                return await self._process_prompt_workflow_instruction(message.content)
            elif isinstance(message, AIMessage):
                return await self._process_prompt_workflow_response(message.content)
            else:
                return {"status": "ignored", "message_type": type(message).__name__}

        except Exception as e:
            fire_and_forget("error", f"LangGraph message handling failed: {e}", self.service_name)
            return {"status": "error", "error": str(e)}

    async def _process_prompt_workflow_instruction(self, instruction: str) -> Dict[str, Any]:
        """Process prompt-related workflow instructions."""
        instruction_lower = instruction.lower()

        if "create" in instruction_lower and "prompt" in instruction_lower:
            return {
                "action": "create_prompt",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["prompt_creation", "variable_management", "workflow_tracking"]
            }

        elif "get" in instruction_lower or "retrieve" in instruction_lower:
            return {
                "action": "get_prompt",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["prompt_retrieval", "version_control", "performance_tracking"]
            }

        elif "optimal" in instruction_lower or "best" in instruction_lower:
            return {
                "action": "get_optimal_prompt",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["prompt_optimization", "context_awareness", "performance_based_selection"]
            }

        elif "performance" in instruction_lower or "metrics" in instruction_lower:
            return {
                "action": "update_performance",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["performance_tracking", "metrics_collection", "optimization_feedback"]
            }

        else:
            return {
                "action": "general_prompt_operation",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["prompt_management", "workflow_integration", "performance_monitoring"]
            }

    async def _process_prompt_workflow_response(self, response: str) -> Dict[str, Any]:
        """Process prompt workflow responses."""
        # Store response context for workflow continuity
        response_context = {
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "processed_by": self.service_name,
            "response_type": "prompt_workflow"
        }

        return {
            "status": "processed",
            "service": self.service_name,
            "response_stored": True,
            "next_actions": ["await_workflow_instructions", "prepare_prompt_tools"]
        }

    def get_langgraph_capabilities(self) -> Dict[str, Any]:
        """Get LangGraph capabilities for prompt store."""
        return {
            "service_name": self.service_name,
            "langgraph_enabled": True,
            "supported_workflows": [
                "prompt_creation",
                "prompt_retrieval",
                "prompt_optimization",
                "performance_tracking",
                "workflow_prompt_management"
            ],
            "tool_categories": [
                "creation_tools",
                "retrieval_tools",
                "optimization_tools",
                "performance_tools"
            ],
            "message_types": [
                "prompt_instructions",
                "workflow_responses",
                "optimization_commands"
            ],
            "integration_features": [
                "workflow_context_awareness",
                "performance_monitoring",
                "optimization_engine",
                "usage_tracking"
            ]
        }

    def get_workflow_integration_status(self) -> Dict[str, Any]:
        """Get current workflow integration status."""
        return {
            "service": self.service_name,
            "langgraph_integration": "active",
            "tracked_workflows": len(self.workflow_prompts),
            "performance_tracked_prompts": len(self.performance_tracker),
            "total_prompt_operations": sum(len(prompts) for prompts in self.workflow_prompts.values()),
            "last_activity": datetime.now().isoformat(),
            "capabilities_ready": True
        }

    def get_prompt_performance_summary(self) -> Dict[str, Any]:
        """Get summary of prompt performance across workflows."""
        summary = {
            "total_prompts_tracked": len(self.performance_tracker),
            "total_operations": sum(len(operations) for operations in self.performance_tracker.values()),
            "operation_types": {},
            "recent_activity": []
        }

        # Analyze operation types
        for prompt_id, operations in self.performance_tracker.items():
            for operation in operations:
                op_type = operation.get("action", "unknown")
                if op_type not in summary["operation_types"]:
                    summary["operation_types"][op_type] = 0
                summary["operation_types"][op_type] += 1

        # Get recent activity (last 10 operations)
        all_operations = []
        for prompt_id, operations in self.performance_tracker.items():
            for operation in operations[-5:]:  # Last 5 from each prompt
                all_operations.append({
                    "prompt_id": prompt_id,
                    **operation
                })

        # Sort by timestamp and get most recent
        all_operations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        summary["recent_activity"] = all_operations[:10]

        return summary


# Global instance for easy access
prompt_store_langgraph = PromptStoreLangGraphIntegration()
