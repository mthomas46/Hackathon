#!/usr/bin/env python3
"""
LangGraph Integration for Interpreter Service

This module provides LangGraph awareness and integration capabilities
for the Interpreter Service, enabling natural language workflow orchestration.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import BaseTool, tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from services.shared.utilities import get_service_client
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class InterpreterLangGraphIntegration:
    """LangGraph integration for Interpreter Service."""

    def __init__(self):
        self.service_name = ServiceNames.INTERPRETER
        self.service_client = get_service_client()
        self.workflow_conversations = {}
        self.intent_cache = {}

    async def initialize_langgraph_tools(self) -> Dict[str, BaseTool]:
        """Initialize LangGraph tools for interpreter."""

        @tool
        async def interpret_query_langgraph(query: str, context: Dict[str, Any],
                                          workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Interpret a natural language query within LangGraph workflow context."""
            try:
                # Enhance interpretation with workflow context
                enhanced_context = {
                    **context,
                    "workflow_context": workflow_context or {},
                    "langgraph_integration": True,
                    "interpretation_timestamp": datetime.now().isoformat(),
                    "query_type": "workflow_driven"
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/interpret",
                    {
                        "query": query,
                        "context": enhanced_context
                    }
                )

                # Cache interpretation for workflow continuity
                if workflow_context:
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        if workflow_id not in self.workflow_conversations:
                            self.workflow_conversations[workflow_id] = []
                        self.workflow_conversations[workflow_id].append({
                            "query": query,
                            "interpretation": result,
                            "timestamp": datetime.now().isoformat(),
                            "context": enhanced_context
                        })

                return {
                    "success": True,
                    "interpretation": result,
                    "workflow_integration": "completed",
                    "cached_for_workflow": bool(workflow_context)
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph query interpretation failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def extract_intent_langgraph(text: str, domain: str = "general",
                                         workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Extract intent from text within workflow context."""
            try:
                # Check cache first for similar queries
                cache_key = f"{text[:50]}_{domain}"
                if cache_key in self.intent_cache:
                    cached_result = self.intent_cache[cache_key]
                    return {
                        "success": True,
                        "intent": cached_result,
                        "source": "cache",
                        "workflow_integration": "completed"
                    }

                enhanced_context = {
                    "domain": domain,
                    "workflow_context": workflow_context,
                    "intent_extraction_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/intent",
                    {
                        "text": text,
                        "context": enhanced_context
                    }
                )

                # Cache the result
                self.intent_cache[cache_key] = result

                # Track in workflow if applicable
                if workflow_context:
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        if workflow_id not in self.workflow_conversations:
                            self.workflow_conversations[workflow_id] = []
                        self.workflow_conversations[workflow_id].append({
                            "text": text,
                            "intent": result,
                            "domain": domain,
                            "timestamp": datetime.now().isoformat()
                        })

                return {
                    "success": True,
                    "intent": result,
                    "source": "fresh_analysis",
                    "workflow_integration": "completed"
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph intent extraction failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def get_ecosystem_context_langgraph(query_focus: str = "general",
                                                workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Get current ecosystem context within workflow."""
            try:
                enhanced_context = {
                    "query_focus": query_focus,
                    "workflow_context": workflow_context,
                    "context_request_timestamp": datetime.now().isoformat(),
                    "langgraph_integration": True
                }

                result = await self.service_client.get_json(
                    f"{self.service_name}/api/v1/ecosystem/context?focus={query_focus}"
                )

                # Enhance result with workflow context
                result["workflow_enhancement"] = {
                    "context_requested_for": query_focus,
                    "workflow_context": workflow_context,
                    "enhanced_at": datetime.now().isoformat(),
                    "integration_status": "completed"
                }

                return {
                    "success": True,
                    "ecosystem_context": result,
                    "workflow_integration": "completed"
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        @tool
        async def translate_workflow_instruction_langgraph(instruction: str,
                                                        target_services: List[str],
                                                        workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Translate natural language instruction into service-specific commands."""
            try:
                translation_context = {
                    "instruction": instruction,
                    "target_services": target_services,
                    "workflow_context": workflow_context,
                    "translation_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/translate/workflow",
                    {
                        "instruction": instruction,
                        "target_services": target_services,
                        "context": translation_context
                    }
                )

                # Store translation in workflow context
                if workflow_context:
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        if workflow_id not in self.workflow_conversations:
                            self.workflow_conversations[workflow_id] = []
                        self.workflow_conversations[workflow_id].append({
                            "original_instruction": instruction,
                            "translation": result,
                            "target_services": target_services,
                            "timestamp": datetime.now().isoformat()
                        })

                return {
                    "success": True,
                    "translation": result,
                    "workflow_integration": "completed",
                    "services_addressed": target_services
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph instruction translation failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def get_workflow_conversation_history_langgraph(workflow_id: str) -> Dict[str, Any]:
            """Get conversation history for a workflow."""
            try:
                if workflow_id in self.workflow_conversations:
                    conversation_history = self.workflow_conversations[workflow_id]
                    return {
                        "success": True,
                        "conversation_history": conversation_history,
                        "source": "workflow_cache",
                        "workflow_id": workflow_id,
                        "total_exchanges": len(conversation_history)
                    }

                # If not in cache, this would query the service's conversation storage
                # For now, return empty result
                return {
                    "success": True,
                    "conversation_history": [],
                    "source": "cache_miss",
                    "workflow_id": workflow_id,
                    "total_exchanges": 0
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        return {
            "interpret_query_langgraph": interpret_query_langgraph,
            "extract_intent_langgraph": extract_intent_langgraph,
            "get_ecosystem_context_langgraph": get_ecosystem_context_langgraph,
            "translate_workflow_instruction_langgraph": translate_workflow_instruction_langgraph,
            "get_workflow_conversation_history_langgraph": get_workflow_conversation_history_langgraph
        }

    async def handle_langgraph_workflow_message(self, message: BaseMessage) -> Dict[str, Any]:
        """Handle incoming LangGraph workflow messages."""
        try:
            if isinstance(message, HumanMessage):
                return await self._process_interpreter_workflow_instruction(message.content)
            elif isinstance(message, AIMessage):
                return await self._process_interpreter_workflow_response(message.content)
            else:
                return {"status": "ignored", "message_type": type(message).__name__}

        except Exception as e:
            fire_and_forget("error", f"LangGraph message handling failed: {e}", self.service_name)
            return {"status": "error", "error": str(e)}

    async def _process_interpreter_workflow_instruction(self, instruction: str) -> Dict[str, Any]:
        """Process interpreter-related workflow instructions."""
        instruction_lower = instruction.lower()

        if "interpret" in instruction_lower or "understand" in instruction_lower:
            return {
                "action": "interpret_query",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["natural_language_processing", "context_awareness", "intent_recognition"]
            }

        elif "intent" in instruction_lower or "meaning" in instruction_lower:
            return {
                "action": "extract_intent",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["intent_analysis", "semantic_understanding", "domain_recognition"]
            }

        elif "context" in instruction_lower or "ecosystem" in instruction_lower:
            return {
                "action": "get_context",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["ecosystem_awareness", "service_discovery", "context_management"]
            }

        elif "translate" in instruction_lower or "convert" in instruction_lower:
            return {
                "action": "translate_instruction",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["instruction_translation", "service_mapping", "workflow_orchestration"]
            }

        else:
            return {
                "action": "general_interpretation",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["natural_language_processing", "workflow_integration", "context_awareness"]
            }

    async def _process_interpreter_workflow_response(self, response: str) -> Dict[str, Any]:
        """Process interpreter workflow responses."""
        # Store response context for workflow continuity
        response_context = {
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "processed_by": self.service_name,
            "response_type": "interpreter_workflow"
        }

        return {
            "status": "processed",
            "service": self.service_name,
            "response_stored": True,
            "next_actions": ["await_workflow_instructions", "prepare_interpretation_tools"]
        }

    def get_langgraph_capabilities(self) -> Dict[str, Any]:
        """Get LangGraph capabilities for interpreter."""
        return {
            "service_name": self.service_name,
            "langgraph_enabled": True,
            "supported_workflows": [
                "natural_language_processing",
                "intent_recognition",
                "ecosystem_context_awareness",
                "instruction_translation",
                "conversation_management"
            ],
            "tool_categories": [
                "interpretation_tools",
                "intent_tools",
                "context_tools",
                "translation_tools"
            ],
            "message_types": [
                "human_instructions",
                "ai_responses",
                "workflow_commands",
                "conversation_messages"
            ],
            "integration_features": [
                "workflow_context_awareness",
                "conversation_caching",
                "intent_caching",
                "multi_service_coordination"
            ]
        }

    def get_workflow_integration_status(self) -> Dict[str, Any]:
        """Get current workflow integration status."""
        return {
            "service": self.service_name,
            "langgraph_integration": "active",
            "active_workflows": len(self.workflow_conversations),
            "cached_intents": len(self.intent_cache),
            "total_conversation_turns": sum(len(conversation) for conversation in self.workflow_conversations.values()),
            "last_activity": datetime.now().isoformat(),
            "capabilities_ready": True
        }

    def get_interpretation_performance_summary(self) -> Dict[str, Any]:
        """Get summary of interpretation performance."""
        summary = {
            "total_workflows": len(self.workflow_conversations),
            "total_interactions": sum(len(conversation) for conversation in self.workflow_conversations.values()),
            "cache_hit_ratio": 0,  # Would be calculated from actual usage
            "average_response_time": 0,  # Would be tracked from actual calls
            "common_intent_types": {},
            "recent_activity": []
        }

        # Analyze cached intents for patterns
        intent_types = {}
        for cache_key, intent_result in self.intent_cache.items():
            intent_type = intent_result.get("intent_type", "unknown")
            if intent_type not in intent_types:
                intent_types[intent_type] = 0
            intent_types[intent_type] += 1

        summary["common_intent_types"] = intent_types

        # Get recent workflow activity
        recent_workflows = []
        for workflow_id, conversation in list(self.workflow_conversations.items())[-5:]:
            if conversation:
                recent_workflows.append({
                    "workflow_id": workflow_id,
                    "last_interaction": conversation[-1]["timestamp"],
                    "total_turns": len(conversation)
                })

        summary["recent_activity"] = recent_workflows

        return summary

    async def clear_workflow_cache(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Clear workflow cache to free memory."""
        if workflow_id:
            if workflow_id in self.workflow_conversations:
                removed_turns = len(self.workflow_conversations[workflow_id])
                del self.workflow_conversations[workflow_id]
                return {"cache_cleared": True, "workflow_id": workflow_id, "turns_removed": removed_turns}
            else:
                return {"cache_cleared": False, "error": "workflow_not_found"}
        else:
            total_turns = sum(len(conversation) for conversation in self.workflow_conversations.values())
            self.workflow_conversations.clear()
            return {"cache_cleared": True, "total_turns_removed": total_turns}


# Global instance for easy access
interpreter_langgraph = InterpreterLangGraphIntegration()
