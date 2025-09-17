#!/usr/bin/env python3
"""
LangGraph Integration for Summarizer Hub Service

This module provides LangGraph awareness and integration capabilities
for the Summarizer Hub Service, enabling intelligent summarization in workflows.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import BaseTool, tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from services.shared.utilities import get_service_client
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class SummarizerHubLangGraphIntegration:
    """LangGraph integration for Summarizer Hub Service."""

    def __init__(self):
        self.service_name = ServiceNames.SUMMARIZER_HUB
        self.service_client = get_service_client()
        self.summary_cache = {}
        self.workflow_summaries = {}

    async def initialize_langgraph_tools(self) -> Dict[str, BaseTool]:
        """Initialize LangGraph tools for summarizer hub."""

        @tool
        async def summarize_content_langgraph(content: str, summary_type: str = "concise",
                                           max_length: int = 500,
                                           workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Summarize content within LangGraph workflow context."""
            try:
                # Check cache first for similar content
                content_hash = hash(content[:1000])  # Simple hash for caching
                cache_key = f"{content_hash}_{summary_type}_{max_length}"

                if cache_key in self.summary_cache:
                    cached_summary = self.summary_cache[cache_key]
                    return {
                        "success": True,
                        "summary": cached_summary,
                        "source": "cache",
                        "workflow_integration": "completed"
                    }

                # Enhance summarization with workflow context
                summary_context = {
                    "content": content,
                    "summary_type": summary_type,
                    "max_length": max_length,
                    "workflow_context": workflow_context or {},
                    "summarization_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/summarize",
                    {
                        "content": content,
                        "summary_type": summary_type,
                        "max_length": max_length,
                        "context": summary_context
                    }
                )

                # Cache the summary
                if result.get("success") and "summary" in result:
                    self.summary_cache[cache_key] = result

                    # Track in workflow if applicable
                    if workflow_context:
                        workflow_id = workflow_context.get("workflow_id")
                        if workflow_id:
                            if workflow_id not in self.workflow_summaries:
                                self.workflow_summaries[workflow_id] = []
                            self.workflow_summaries[workflow_id].append({
                                "content_hash": content_hash,
                                "summary_type": summary_type,
                                "created_at": datetime.now().isoformat(),
                                "summary_length": len(result["summary"])
                            })

                return {
                    "success": True,
                    "summary": result,
                    "source": "fresh_summary",
                    "workflow_integration": "completed",
                    "cached_for_future": True
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph summarization failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def compare_summaries_langgraph(summaries: List[str], comparison_criteria: List[str],
                                           workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Compare multiple summaries within workflow context."""
            try:
                comparison_context = {
                    "summaries": summaries,
                    "comparison_criteria": comparison_criteria,
                    "workflow_context": workflow_context or {},
                    "comparison_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/compare",
                    {
                        "summaries": summaries,
                        "comparison_criteria": comparison_criteria,
                        "context": comparison_context
                    }
                )

                return {
                    "success": True,
                    "comparison_result": result,
                    "workflow_integration": "completed",
                    "summaries_compared": len(summaries)
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph summary comparison failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def get_summary_quality_metrics_langgraph(summary_id: str,
                                                      workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Get quality metrics for a summary within workflow."""
            try:
                result = await self.service_client.get_json(
                    f"{self.service_name}/api/v1/summaries/{summary_id}/quality"
                )

                # Enhance with workflow context
                if workflow_context:
                    result["workflow_context"] = workflow_context
                    result["metrics_retrieved_for_workflow"] = True
                    result["retrieval_timestamp"] = datetime.now().isoformat()

                return {
                    "success": True,
                    "quality_metrics": result,
                    "workflow_integration": "completed"
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        @tool
        async def generate_workflow_summary_langgraph(content_list: List[str],
                                                   workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Generate a comprehensive workflow summary from multiple content pieces."""
            try:
                workflow_summary_context = {
                    "content_list": content_list,
                    "workflow_context": workflow_context or {},
                    "summary_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True,
                    "workflow_summary": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/summarize/workflow",
                    {
                        "content_list": content_list,
                        "context": workflow_summary_context
                    }
                )

                # Store workflow summary tracking
                if workflow_context and result.get("success"):
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        if workflow_id not in self.workflow_summaries:
                            self.workflow_summaries[workflow_id] = []
                        self.workflow_summaries[workflow_id].append({
                            "summary_type": "workflow_summary",
                            "content_pieces": len(content_list),
                            "created_at": datetime.now().isoformat(),
                            "summary_id": result.get("summary_id")
                        })

                return {
                    "success": True,
                    "workflow_summary": result,
                    "workflow_integration": "completed",
                    "content_pieces_summarized": len(content_list)
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph workflow summary failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def get_workflow_summaries_langgraph(workflow_id: str) -> Dict[str, Any]:
            """Get all summaries generated for a workflow."""
            try:
                if workflow_id in self.workflow_summaries:
                    summaries = self.workflow_summaries[workflow_id]
                    return {
                        "success": True,
                        "summaries": summaries,
                        "source": "workflow_cache",
                        "workflow_id": workflow_id,
                        "total_summaries": len(summaries)
                    }

                # If not in cache, return empty result
                return {
                    "success": True,
                    "summaries": [],
                    "source": "cache_miss",
                    "workflow_id": workflow_id,
                    "total_summaries": 0
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        return {
            "summarize_content_langgraph": summarize_content_langgraph,
            "compare_summaries_langgraph": compare_summaries_langgraph,
            "get_summary_quality_metrics_langgraph": get_summary_quality_metrics_langgraph,
            "generate_workflow_summary_langgraph": generate_workflow_summary_langgraph,
            "get_workflow_summaries_langgraph": get_workflow_summaries_langgraph
        }

    async def handle_langgraph_workflow_message(self, message: BaseMessage) -> Dict[str, Any]:
        """Handle incoming LangGraph workflow messages."""
        try:
            if isinstance(message, HumanMessage):
                return await self._process_summarizer_workflow_instruction(message.content)
            elif isinstance(message, AIMessage):
                return await self._process_summarizer_workflow_response(message.content)
            else:
                return {"status": "ignored", "message_type": type(message).__name__}

        except Exception as e:
            fire_and_forget("error", f"LangGraph message handling failed: {e}", self.service_name)
            return {"status": "error", "error": str(e)}

    async def _process_summarizer_workflow_instruction(self, instruction: str) -> Dict[str, Any]:
        """Process summarizer-related workflow instructions."""
        instruction_lower = instruction.lower()

        if "summarize" in instruction_lower or "summary" in instruction_lower:
            return {
                "action": "summarize_content",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["content_summarization", "multi_model_summaries", "quality_assessment"]
            }

        elif "compare" in instruction_lower or "comparison" in instruction_lower:
            return {
                "action": "compare_summaries",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["summary_comparison", "quality_assessment", "difference_analysis"]
            }

        elif "quality" in instruction_lower or "metrics" in instruction_lower:
            return {
                "action": "get_quality_metrics",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["quality_assessment", "metrics_calculation", "performance_evaluation"]
            }

        elif "workflow" in instruction_lower and "summary" in instruction_lower:
            return {
                "action": "generate_workflow_summary",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["workflow_summarization", "multi_content_synthesis", "comprehensive_overview"]
            }

        else:
            return {
                "action": "general_summarization",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["content_summarization", "text_processing", "information_extraction"]
            }

    async def _process_summarizer_workflow_response(self, response: str) -> Dict[str, Any]:
        """Process summarizer workflow responses."""
        # Store response context for workflow continuity
        response_context = {
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "processed_by": self.service_name,
            "response_type": "summarizer_workflow"
        }

        return {
            "status": "processed",
            "service": self.service_name,
            "response_stored": True,
            "next_actions": ["await_workflow_instructions", "prepare_summarization_tools"]
        }

    def get_langgraph_capabilities(self) -> Dict[str, Any]:
        """Get LangGraph capabilities for summarizer hub."""
        return {
            "service_name": self.service_name,
            "langgraph_enabled": True,
            "supported_workflows": [
                "content_summarization",
                "multi_model_summaries",
                "summary_comparison",
                "quality_assessment",
                "workflow_summarization"
            ],
            "tool_categories": [
                "summarization_tools",
                "comparison_tools",
                "quality_tools",
                "workflow_tools"
            ],
            "message_types": [
                "summarization_instructions",
                "workflow_responses",
                "content_commands"
            ],
            "integration_features": [
                "workflow_context_awareness",
                "caching_optimization",
                "multi_model_support",
                "quality_tracking"
            ]
        }

    def get_workflow_integration_status(self) -> Dict[str, Any]:
        """Get current workflow integration status."""
        return {
            "service": self.service_name,
            "langgraph_integration": "active",
            "cached_summaries": len(self.summary_cache),
            "active_workflows": len(self.workflow_summaries),
            "total_summaries_generated": sum(len(summaries) for summaries in self.workflow_summaries.values()),
            "last_activity": datetime.now().isoformat(),
            "capabilities_ready": True
        }

    def get_summarization_performance_summary(self) -> Dict[str, Any]:
        """Get summary of summarization performance."""
        summary = {
            "total_summaries_cached": len(self.summary_cache),
            "total_workflows": len(self.workflow_summaries),
            "total_summaries_generated": sum(len(summaries) for summaries in self.workflow_summaries.values()),
            "cache_hit_ratio": 0,  # Would be calculated from actual usage
            "average_summary_time": 0,  # Would be tracked from actual calls
            "summary_types": {},
            "recent_activity": []
        }

        # Analyze summary types
        summary_types = {}
        for workflow_id, summaries in self.workflow_summaries.items():
            for summary_info in summaries:
                summary_type = summary_info.get("summary_type", "content_summary")
                if summary_type not in summary_types:
                    summary_types[summary_type] = 0
                summary_types[summary_type] += 1

        summary["summary_types"] = summary_types

        # Get recent workflow activity
        recent_workflows = []
        for workflow_id, summaries in list(self.workflow_summaries.items())[-5:]:
            if summaries:
                recent_workflows.append({
                    "workflow_id": workflow_id,
                    "last_summary": max(summary["created_at"] for summary in summaries),
                    "total_summaries": len(summaries)
                })

        summary["recent_activity"] = recent_workflows

        return summary

    async def clear_summary_cache(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Clear summary cache to free memory."""
        if workflow_id:
            if workflow_id in self.workflow_summaries:
                removed_summaries = len(self.workflow_summaries[workflow_id])
                del self.workflow_summaries[workflow_id]
                return {"cache_cleared": True, "workflow_id": workflow_id, "summaries_removed": removed_summaries}
            else:
                return {"cache_cleared": False, "error": "workflow_not_found"}
        else:
            # Clear all caches
            total_summaries = sum(len(summaries) for summaries in self.workflow_summaries.values())
            total_cached = len(self.summary_cache)

            self.workflow_summaries.clear()
            self.summary_cache.clear()

            return {
                "cache_cleared": True,
                "total_summaries_removed": total_summaries,
                "total_cached_removed": total_cached
            }


# Global instance for easy access
summarizer_hub_langgraph = SummarizerHubLangGraphIntegration()
