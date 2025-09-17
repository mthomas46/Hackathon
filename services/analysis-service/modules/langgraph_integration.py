#!/usr/bin/env python3
"""
Enterprise-Grade LangGraph Integration for Analysis Service

This module provides comprehensive LangGraph awareness and integration capabilities
for the Analysis Service with enterprise-grade error handling, caching, and monitoring.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import BaseTool, tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import time

from services.shared.utilities import get_service_client
from services.shared.core.constants_new import ServiceNames
from services.shared.monitoring.logging import fire_and_forget
from services.shared.enterprise_error_handling import (
    enterprise_error_handler, ErrorContext, ErrorSeverity, ErrorCategory,
    with_error_handling, error_context
)
from services.shared.intelligent_caching import get_service_cache
from services.shared.enterprise_integration import (
    ServiceMeshClient, WorkflowContext, get_current_workflow_context,
    create_workflow_context, standardized_api_handler
)
from services.shared.operational_excellence import health_monitor


class AnalysisServiceLangGraphIntegration:
    """Enterprise-grade LangGraph integration for Analysis Service."""

    def __init__(self):
        self.service_name = ServiceNames.ANALYSIS_SERVICE
        self.service_client = get_service_client()
        self.workflow_context = {}
        self.cache = get_service_cache(self.service_name)
        self.service_mesh_client = ServiceMeshClient(self.service_name)
        self.performance_metrics = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_processing_time": 0.0,
            "cache_hit_rate": 0.0
        }

    async def initialize_langgraph_tools(self) -> Dict[str, BaseTool]:
        """Initialize LangGraph tools for analysis service."""

        @with_error_handling(self.service_name, "analyze_document_langgraph", ErrorSeverity.HIGH, ErrorCategory.INTERNAL)
        @tool
        async def analyze_document_langgraph(doc_id: str, analysis_types: List[str],
                                           workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Analyze a document within a LangGraph workflow context with enterprise-grade features."""
            start_time = time.time()

            try:
                # Get current workflow context
                current_workflow = get_current_workflow_context()
                if current_workflow:
                    workflow_id = current_workflow.workflow_id
                    user_id = current_workflow.user_id
                else:
                    workflow_id = workflow_context.get("workflow_id") if workflow_context else None
                    user_id = workflow_context.get("user_id") if workflow_context else None

                # Check cache first
                cache_key = f"analysis_{doc_id}_{'_'.join(analysis_types)}_{workflow_id or 'no_workflow'}"
                cached_result = await self.cache.get(cache_key, workflow_id)

                if cached_result:
                    self.performance_metrics["cache_hit_rate"] = (
                        (self.performance_metrics.get("cache_hits", 0) + 1) /
                        (self.performance_metrics.get("total_analyses", 0) + 1)
                    )
                    return {
                        "success": True,
                        "analysis_result": cached_result,
                        "source": "cache",
                        "workflow_integration": "completed"
                    }

                # Enhanced context with enterprise features
                enhanced_context = {
                    "source": "langgraph_workflow",
                    "workflow_context": workflow_context or {},
                    "timestamp": datetime.now().isoformat(),
                    "tool_integration": "langgraph",
                    "cache_enabled": True,
                    "error_handling": "enterprise",
                    "performance_monitoring": True
                }

                # Use service mesh client for resilient communication
                async with self.service_mesh_client as client:
                    result = await client.post(
                        f"/api/v1/analyze",
                        json={
                            "document_id": doc_id,
                            "analysis_types": analysis_types,
                            "context": enhanced_context
                        }
                    )

                # Update performance metrics
                processing_time = time.time() - start_time
                self._update_performance_metrics(success=True, processing_time=processing_time)

                # Cache the result
                await self.cache.set(cache_key, result, ttl_seconds=3600, workflow_id=workflow_id)  # 1 hour TTL

                # Store workflow context for future use
                if workflow_id:
                    self.workflow_context[doc_id] = {
                        "analysis_result": result,
                        "workflow_context": workflow_context,
                        "timestamp": datetime.now().isoformat(),
                        "cache_key": cache_key
                    }

                return {
                    "success": True,
                    "analysis_result": result,
                    "workflow_integration": "completed",
                    "processing_time_ms": processing_time * 1000,
                    "cached": False
                }

            except Exception as e:
                # Update failure metrics
                processing_time = time.time() - start_time
                self._update_performance_metrics(success=False, processing_time=processing_time)

                # Error will be handled by the decorator
                raise e

    def _update_performance_metrics(self, success: bool, processing_time: float):
        """Update performance metrics."""
        self.performance_metrics["total_analyses"] += 1

        if success:
            self.performance_metrics["successful_analyses"] += 1
        else:
            self.performance_metrics["failed_analyses"] += 1

        # Update average processing time
        current_avg = self.performance_metrics["average_processing_time"]
        total_count = self.performance_metrics["total_analyses"]
        self.performance_metrics["average_processing_time"] = (
            (current_avg * (total_count - 1)) + processing_time
        ) / total_count

        @with_error_handling(self.service_name, "get_confidence_score_langgraph", ErrorSeverity.MEDIUM, ErrorCategory.INTERNAL)
        @tool
        async def get_confidence_score_langgraph(analysis_id: str,
                                               workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Get confidence score within LangGraph workflow with enterprise-grade features."""
            start_time = time.time()

            try:
                # Get current workflow context
                current_workflow = get_current_workflow_context()
                workflow_id = current_workflow.workflow_id if current_workflow else None

                # Check cache first
                cache_key = f"confidence_{analysis_id}_{workflow_id or 'no_workflow'}"
                cached_result = await self.cache.get(cache_key, workflow_id)

                if cached_result:
                    return {
                        "success": True,
                        "confidence_score": cached_result,
                        "source": "cache",
                        "workflow_integration": "completed"
                    }

                # Use service mesh client for resilient communication
                async with self.service_mesh_client as client:
                    result = await client.get(f"/api/v1/analysis/{analysis_id}/confidence")

                # Enhance result with workflow context
                result["workflow_integration"] = {
                    "source": "langgraph_workflow",
                    "context": workflow_context,
                    "integration_timestamp": datetime.now().isoformat()
                }

                # Update performance metrics
                processing_time = time.time() - start_time
                self._update_performance_metrics(success=True, processing_time=processing_time)

                # Cache the result
                await self.cache.set(cache_key, result, ttl_seconds=1800, workflow_id=workflow_id)  # 30 minute TTL

                return {
                    "success": True,
                    "confidence_score": result,
                    "workflow_integration": "completed",
                    "processing_time_ms": processing_time * 1000
                }

            except Exception as e:
                # Update failure metrics
                processing_time = time.time() - start_time
                self._update_performance_metrics(success=False, processing_time=processing_time)
                raise e

        @tool
        async def cross_reference_analysis_langgraph(doc_ids: List[str], reference_docs: List[str],
                                                   workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Perform cross-reference analysis within LangGraph workflow."""
            try:
                enhanced_context = {
                    "source": "langgraph_workflow",
                    "workflow_context": workflow_context,
                    "cross_reference_metadata": {
                        "total_documents": len(doc_ids),
                        "reference_documents": len(reference_docs),
                        "analysis_timestamp": datetime.now().isoformat()
                    }
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/cross-reference",
                    {
                        "document_ids": doc_ids,
                        "reference_documents": reference_docs,
                        "context": enhanced_context
                    }
                )

                return {
                    "success": True,
                    "cross_reference_result": result,
                    "workflow_integration": "completed"
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph cross-reference failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def generate_workflow_report_langgraph(analysis_ids: List[str],
                                                   report_type: str = "comprehensive",
                                                   workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Generate analysis report optimized for LangGraph workflows."""
            try:
                # Create workflow-optimized report
                workflow_optimized_context = {
                    "source": "langgraph_workflow",
                    "report_type": report_type,
                    "workflow_context": workflow_context,
                    "optimization_flags": {
                        "include_workflow_metadata": True,
                        "format_for_ai_consumption": True,
                        "include_confidence_metrics": True,
                        "structured_output": True
                    },
                    "timestamp": datetime.now().isoformat()
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/reports/generate",
                    {
                        "analysis_ids": analysis_ids,
                        "report_type": report_type,
                        "context": workflow_optimized_context
                    }
                )

                return {
                    "success": True,
                    "workflow_report": result,
                    "report_metadata": {
                        "generated_for": "langgraph_workflow",
                        "optimization_applied": True,
                        "analysis_count": len(analysis_ids)
                    }
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph report generation failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        return {
            "analyze_document_langgraph": analyze_document_langgraph,
            "get_confidence_score_langgraph": get_confidence_score_langgraph,
            "cross_reference_analysis_langgraph": cross_reference_analysis_langgraph,
            "generate_workflow_report_langgraph": generate_workflow_report_langgraph
        }

    async def handle_langgraph_workflow_message(self, message: BaseMessage) -> Dict[str, Any]:
        """Handle incoming LangGraph workflow messages."""
        try:
            if isinstance(message, HumanMessage):
                # Process human workflow instructions
                return await self._process_workflow_instruction(message.content)
            elif isinstance(message, AIMessage):
                # Process AI workflow responses
                return await self._process_workflow_response(message.content)
            else:
                return {"status": "ignored", "message_type": type(message).__name__}

        except Exception as e:
            fire_and_forget("error", f"LangGraph message handling failed: {e}", self.service_name)
            return {"status": "error", "error": str(e)}

    async def _process_workflow_instruction(self, instruction: str) -> Dict[str, Any]:
        """Process workflow instructions from LangGraph."""
        # Analyze the instruction for analysis service operations
        instruction_lower = instruction.lower()

        if "analyze" in instruction_lower and "document" in instruction_lower:
            return {
                "action": "analyze_document",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["document_analysis", "confidence_scoring", "cross_reference"]
            }

        elif "confidence" in instruction_lower or "score" in instruction_lower:
            return {
                "action": "get_confidence",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["confidence_scoring", "quality_assessment"]
            }

        elif "cross" in instruction_lower and "reference" in instruction_lower:
            return {
                "action": "cross_reference",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["cross_reference_analysis", "consistency_checking"]
            }

        else:
            return {
                "action": "general_analysis",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["document_analysis", "quality_assessment", "consistency_checking"]
            }

    async def _process_workflow_response(self, response: str) -> Dict[str, Any]:
        """Process workflow responses from LangGraph."""
        # Store workflow context and prepare for next steps
        self.workflow_context["last_ai_response"] = {
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "processed_by": self.service_name
        }

        return {
            "status": "processed",
            "service": self.service_name,
            "response_stored": True,
            "next_actions": ["await_workflow_instructions", "prepare_analysis_tools"]
        }

    def get_langgraph_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive LangGraph capabilities for this service."""
        return {
            "service_name": self.service_name,
            "langgraph_enabled": True,
            "supported_workflows": [
                "document_analysis",
                "confidence_scoring",
                "cross_reference_analysis",
                "quality_assessment",
                "consistency_checking",
                "enterprise_workflow_integration"
            ],
            "tool_categories": [
                "analysis_tools",
                "confidence_tools",
                "reporting_tools",
                "enterprise_tools"
            ],
            "message_types": [
                "human_instructions",
                "ai_responses",
                "workflow_commands",
                "enterprise_messages"
            ],
            "integration_features": [
                "workflow_context_awareness",
                "enhanced_reporting",
                "real_time_analysis",
                "confidence_metrics",
                "enterprise_error_handling",
                "intelligent_caching",
                "service_mesh_compatibility",
                "performance_monitoring",
                "health_integration"
            ],
            "enterprise_features": {
                "error_handling": "comprehensive",
                "caching_strategy": "intelligent_multi_level",
                "monitoring_level": "detailed",
                "resilience_patterns": ["circuit_breaker", "retry", "fallback"],
                "performance_optimization": ["caching", "connection_pooling", "async_processing"]
            },
            "performance_metrics": self.get_performance_metrics()
        }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        total_analyses = self.performance_metrics["total_analyses"]
        successful_analyses = self.performance_metrics["successful_analyses"]

        return {
            "total_analyses": total_analyses,
            "successful_analyses": successful_analyses,
            "failed_analyses": self.performance_metrics["failed_analyses"],
            "success_rate": (successful_analyses / total_analyses) * 100 if total_analyses > 0 else 0,
            "average_processing_time": self.performance_metrics["average_processing_time"],
            "cache_hit_rate": self.performance_metrics.get("cache_hit_rate", 0),
            "cache_performance": self.cache.get_cache_stats() if self.cache else {},
            "error_statistics": enterprise_error_handler.get_error_statistics(self.service_name),
            "last_updated": datetime.now().isoformat()
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status for enterprise monitoring."""
        health_status = await health_monitor.get_health_status(self.service_name)

        if health_status.get('error'):
            # Service not registered, return basic health
            return {
                "service_name": self.service_name,
                "status": "unknown",
                "langgraph_integration": "active",
                "cache_status": self.cache.get_cache_stats() if self.cache else "no_cache",
                "performance_metrics": self.get_performance_metrics(),
                "last_check": datetime.now().isoformat()
            }

        # Enhance with LangGraph-specific metrics
        health_status.update({
            "langgraph_integration": {
                "status": "active",
                "tools_initialized": len(self.workflow_context) > 0,
                "active_workflows": len([k for k in self.workflow_context.keys() if k.startswith("workflow_")]),
                "performance_metrics": self.get_performance_metrics()
            },
            "cache_status": self.cache.get_cache_stats() if self.cache else "no_cache",
            "enterprise_features": {
                "error_handling": "active",
                "service_mesh": "active",
                "monitoring": "active"
            }
        })

        return health_status

    async def optimize_for_workflow(self, workflow_id: str, priority_keys: List[str]):
        """Optimize service for specific workflow execution."""
        # Optimize cache for workflow
        await self.cache.optimize_for_workflow(workflow_id, priority_keys)

        # Pre-warm cache with workflow-specific data
        workflow_cache_data = {}
        for key in priority_keys:
            if key in self.workflow_context:
                workflow_cache_data[key] = self.workflow_context[key]

        if workflow_cache_data:
            await self.cache.warmup_cache(workflow_cache_data)

        fire_and_forget("info", f"Optimized analysis service for workflow {workflow_id}", self.service_name)

    async def cleanup_workflow_resources(self, workflow_id: str):
        """Clean up resources for completed workflow."""
        # Invalidate workflow-specific cache entries
        await self.cache.invalidate_workflow(workflow_id)

        # Clean up workflow context
        workflow_keys = [k for k in self.workflow_context.keys()
                        if isinstance(self.workflow_context[k], dict) and
                        self.workflow_context[k].get("workflow_id") == workflow_id]

        for key in workflow_keys:
            del self.workflow_context[key]

        fire_and_forget("info", f"Cleaned up resources for workflow {workflow_id}", self.service_name)

    def get_workflow_integration_status(self) -> Dict[str, Any]:
        """Get current workflow integration status."""
        return {
            "service": self.service_name,
            "langgraph_integration": "active",
            "tools_initialized": len(self.workflow_context) > 0,
            "active_workflows": len([k for k in self.workflow_context.keys() if k.startswith("workflow_")]),
            "last_activity": datetime.now().isoformat(),
            "capabilities_ready": True
        }


# Global instance for easy access
analysis_service_langgraph = AnalysisServiceLangGraphIntegration()
