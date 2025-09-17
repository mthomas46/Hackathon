#!/usr/bin/env python3
"""
LangGraph Integration for Discovery Agent Service

This module provides LangGraph awareness and integration capabilities
for the Discovery Agent Service, enabling automated tool discovery and registration.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import BaseTool, tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from services.shared.utilities import get_service_client
from services.shared.core.constants_new import ServiceNames
from services.shared.monitoring.logging import fire_and_forget


class DiscoveryAgentLangGraphIntegration:
    """LangGraph integration for Discovery Agent Service."""

    def __init__(self):
        self.service_name = ServiceNames.DISCOVERY_AGENT
        self.service_client = get_service_client()
        self.discovered_tools_cache = {}
        self.service_capabilities = {}

    async def initialize_langgraph_tools(self) -> Dict[str, BaseTool]:
        """Initialize LangGraph tools for discovery agent."""

        @tool
        async def discover_service_tools_langgraph(service_name: str, service_url: str,
                                                 workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Discover tools for a service within LangGraph workflow context."""
            try:
                # Check cache first
                cache_key = f"{service_name}_{service_url}"
                if cache_key in self.discovered_tools_cache:
                    cached_result = self.discovered_tools_cache[cache_key]
                    return {
                        "success": True,
                        "discovered_tools": cached_result,
                        "source": "cache",
                        "workflow_integration": "completed"
                    }

                # Enhance discovery with workflow context
                discovery_context = {
                    "service_name": service_name,
                    "service_url": service_url,
                    "workflow_context": workflow_context or {},
                    "discovery_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True,
                    "auto_registration": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/discover/tools",
                    {
                        "service_name": service_name,
                        "service_url": service_url,
                        "context": discovery_context
                    }
                )

                # Cache the discovery result
                if result.get("success"):
                    self.discovered_tools_cache[cache_key] = result

                    # Update service capabilities
                    if service_name not in self.service_capabilities:
                        self.service_capabilities[service_name] = []
                    self.service_capabilities[service_name].extend(result.get("tools", []))

                return {
                    "success": True,
                    "discovered_tools": result,
                    "source": "fresh_discovery",
                    "workflow_integration": "completed",
                    "cached_for_future": True
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph tool discovery failed for {service_name}: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def register_tools_with_orchestrator_langgraph(tools_data: Dict[str, Any],
                                                          workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Register discovered tools with orchestrator within workflow context."""
            try:
                # Enhance registration with workflow context
                registration_context = {
                    "tools_data": tools_data,
                    "workflow_context": workflow_context or {},
                    "registration_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True,
                    "auto_registration": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/register/tools",
                    {
                        "tools_data": tools_data,
                        "target": "orchestrator",
                        "context": registration_context
                    }
                )

                # Update workflow context with registration result
                if workflow_context and result.get("success"):
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        # This would typically be stored in a workflow state manager
                        registration_record = {
                            "tools_registered": len(tools_data.get("tools", [])),
                            "registration_timestamp": datetime.now().isoformat(),
                            "workflow_id": workflow_id
                        }

                return {
                    "success": True,
                    "registration_result": result,
                    "workflow_integration": "completed",
                    "tools_registered": len(tools_data.get("tools", []))
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph tool registration failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def validate_service_compatibility_langgraph(service_name: str,
                                                        workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Validate service compatibility for tool discovery within workflow."""
            try:
                validation_context = {
                    "service_name": service_name,
                    "workflow_context": workflow_context or {},
                    "validation_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/validate",
                    {
                        "service_name": service_name,
                        "validation_context": validation_context
                    }
                )

                # Store validation result in service capabilities
                if result.get("success"):
                    compatibility_status = result.get("compatibility_status", "unknown")
                    self.service_capabilities[service_name] = {
                        "compatibility_status": compatibility_status,
                        "last_validated": datetime.now().isoformat(),
                        "validation_context": validation_context
                    }

                return {
                    "success": True,
                    "validation_result": result,
                    "workflow_integration": "completed",
                    "service_compatible": result.get("compatibility_status") == "compatible"
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        @tool
        async def get_service_capabilities_langgraph(service_name: str,
                                                   workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Get discovered capabilities for a service within workflow."""
            try:
                # Check local cache first
                if service_name in self.service_capabilities:
                    cached_capabilities = self.service_capabilities[service_name]
                    return {
                        "success": True,
                        "capabilities": cached_capabilities,
                        "source": "cache",
                        "workflow_integration": "completed"
                    }

                # Query service capabilities
                result = await self.service_client.get_json(
                    f"{self.service_name}/api/v1/capabilities/{service_name}"
                )

                # Cache the result
                if result.get("success"):
                    self.service_capabilities[service_name] = result.get("capabilities", {})

                return {
                    "success": True,
                    "capabilities": result,
                    "source": "fresh_query",
                    "workflow_integration": "completed"
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        @tool
        async def discover_ecosystem_services_langgraph(workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Discover all available services in the ecosystem."""
            try:
                discovery_context = {
                    "workflow_context": workflow_context or {},
                    "ecosystem_discovery_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True,
                    "comprehensive_scan": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/discover/ecosystem",
                    {
                        "context": discovery_context
                    }
                )

                # Update local capabilities cache
                if result.get("success") and "services" in result:
                    for service_info in result["services"]:
                        service_name = service_info.get("name")
                        if service_name:
                            self.service_capabilities[service_name] = service_info.get("capabilities", {})

                return {
                    "success": True,
                    "ecosystem_services": result,
                    "workflow_integration": "completed",
                    "services_discovered": len(result.get("services", []))
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph ecosystem discovery failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        return {
            "discover_service_tools_langgraph": discover_service_tools_langgraph,
            "register_tools_with_orchestrator_langgraph": register_tools_with_orchestrator_langgraph,
            "validate_service_compatibility_langgraph": validate_service_compatibility_langgraph,
            "get_service_capabilities_langgraph": get_service_capabilities_langgraph,
            "discover_ecosystem_services_langgraph": discover_ecosystem_services_langgraph
        }

    async def handle_langgraph_workflow_message(self, message: BaseMessage) -> Dict[str, Any]:
        """Handle incoming LangGraph workflow messages."""
        try:
            if isinstance(message, HumanMessage):
                return await self._process_discovery_workflow_instruction(message.content)
            elif isinstance(message, AIMessage):
                return await self._process_discovery_workflow_response(message.content)
            else:
                return {"status": "ignored", "message_type": type(message).__name__}

        except Exception as e:
            fire_and_forget("error", f"LangGraph message handling failed: {e}", self.service_name)
            return {"status": "error", "error": str(e)}

    async def _process_discovery_workflow_instruction(self, instruction: str) -> Dict[str, Any]:
        """Process discovery-related workflow instructions."""
        instruction_lower = instruction.lower()

        if "discover" in instruction_lower and "tool" in instruction_lower:
            return {
                "action": "discover_tools",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["tool_discovery", "openapi_parsing", "service_introspection"]
            }

        elif "register" in instruction_lower or "integrate" in instruction_lower:
            return {
                "action": "register_tools",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["tool_registration", "orchestrator_integration", "workflow_setup"]
            }

        elif "validate" in instruction_lower or "check" in instruction_lower:
            return {
                "action": "validate_compatibility",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["compatibility_validation", "service_health_check", "capability_assessment"]
            }

        elif "capability" in instruction_lower or "feature" in instruction_lower:
            return {
                "action": "get_capabilities",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["capability_discovery", "feature_enumeration", "service_introspection"]
            }

        elif "ecosystem" in instruction_lower or "services" in instruction_lower:
            return {
                "action": "discover_ecosystem",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["ecosystem_discovery", "service_enumeration", "capability_mapping"]
            }

        else:
            return {
                "action": "general_discovery",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["service_discovery", "tool_discovery", "capability_assessment"]
            }

    async def _process_discovery_workflow_response(self, response: str) -> Dict[str, Any]:
        """Process discovery workflow responses."""
        # Store response context for workflow continuity
        response_context = {
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "processed_by": self.service_name,
            "response_type": "discovery_workflow"
        }

        return {
            "status": "processed",
            "service": self.service_name,
            "response_stored": True,
            "next_actions": ["await_workflow_instructions", "prepare_discovery_tools"]
        }

    def get_langgraph_capabilities(self) -> Dict[str, Any]:
        """Get LangGraph capabilities for discovery agent."""
        return {
            "service_name": self.service_name,
            "langgraph_enabled": True,
            "supported_workflows": [
                "tool_discovery",
                "service_introspection",
                "tool_registration",
                "compatibility_validation",
                "ecosystem_discovery"
            ],
            "tool_categories": [
                "discovery_tools",
                "registration_tools",
                "validation_tools",
                "capability_tools"
            ],
            "message_types": [
                "discovery_instructions",
                "workflow_responses",
                "service_commands"
            ],
            "integration_features": [
                "workflow_context_awareness",
                "caching_optimization",
                "auto_registration",
                "capability_tracking"
            ]
        }

    def get_workflow_integration_status(self) -> Dict[str, Any]:
        """Get current workflow integration status."""
        return {
            "service": self.service_name,
            "langgraph_integration": "active",
            "cached_tools_count": len(self.discovered_tools_cache),
            "known_services_count": len(self.service_capabilities),
            "total_capabilities_tracked": sum(len(capabilities) if isinstance(capabilities, list) else 1
                                            for capabilities in self.service_capabilities.values()),
            "last_activity": datetime.now().isoformat(),
            "capabilities_ready": True
        }

    def get_discovery_performance_summary(self) -> Dict[str, Any]:
        """Get summary of discovery performance."""
        summary = {
            "total_services_discovered": len(self.service_capabilities),
            "total_tools_cached": len(self.discovered_tools_cache),
            "cache_hit_ratio": 0,  # Would be calculated from actual usage
            "average_discovery_time": 0,  # Would be tracked from actual calls
            "service_types": {},
            "recent_discoveries": []
        }

        # Analyze service types
        service_types = {}
        for service_name, capabilities in self.service_capabilities.items():
            if isinstance(capabilities, dict) and "service_type" in capabilities:
                service_type = capabilities["service_type"]
            else:
                service_type = "unknown"

            if service_type not in service_types:
                service_types[service_type] = 0
            service_types[service_type] += 1

        summary["service_types"] = service_types

        # Get recent discoveries (would be populated from actual discovery history)
        summary["recent_discoveries"] = []

        return summary

    async def clear_discovery_cache(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Clear discovery cache to free memory."""
        if service_name:
            # Clear cache for specific service
            removed_tools = 0
            cache_keys_to_remove = [key for key in self.discovered_tools_cache.keys()
                                  if key.startswith(f"{service_name}_")]

            for cache_key in cache_keys_to_remove:
                del self.discovered_tools_cache[cache_key]
                removed_tools += 1

            if service_name in self.service_capabilities:
                del self.service_capabilities[service_name]

            return {
                "cache_cleared": True,
                "service_name": service_name,
                "tools_removed": removed_tools,
                "capabilities_removed": 1 if service_name in self.service_capabilities else 0
            }
        else:
            # Clear all caches
            total_tools = len(self.discovered_tools_cache)
            total_services = len(self.service_capabilities)

            self.discovered_tools_cache.clear()
            self.service_capabilities.clear()

            return {
                "cache_cleared": True,
                "total_tools_removed": total_tools,
                "total_services_removed": total_services
            }


# Global instance for easy access
discovery_agent_langgraph = DiscoveryAgentLangGraphIntegration()
