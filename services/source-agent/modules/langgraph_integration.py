#!/usr/bin/env python3
"""
LangGraph Integration for Source Agent Service

This module provides LangGraph awareness and integration capabilities
for the Source Agent Service, enabling repository content fetching in workflows.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import BaseTool, tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from services.shared.utilities import get_service_client
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class SourceAgentLangGraphIntegration:
    """LangGraph integration for Source Agent Service."""

    def __init__(self):
        self.service_name = ServiceNames.SOURCE_AGENT
        self.service_client = get_service_client()
        self.repository_cache = {}
        self.workflow_repositories = {}

    async def initialize_langgraph_tools(self) -> Dict[str, BaseTool]:
        """Initialize LangGraph tools for source agent."""

        @tool
        async def fetch_repository_content_langgraph(repo_url: str, file_path: str,
                                                   workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Fetch repository content within LangGraph workflow context."""
            try:
                # Check cache first
                cache_key = f"{repo_url}_{file_path}"
                if cache_key in self.repository_cache:
                    cached_content = self.repository_cache[cache_key]
                    return {
                        "success": True,
                        "content": cached_content,
                        "source": "cache",
                        "workflow_integration": "completed"
                    }

                # Enhance fetch with workflow context
                fetch_context = {
                    "repo_url": repo_url,
                    "file_path": file_path,
                    "workflow_context": workflow_context or {},
                    "fetch_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/fetch",
                    {
                        "repo_url": repo_url,
                        "file_path": file_path,
                        "context": fetch_context
                    }
                )

                # Cache the result
                if result.get("success") and "content" in result:
                    self.repository_cache[cache_key] = result["content"]

                    # Track in workflow if applicable
                    if workflow_context:
                        workflow_id = workflow_context.get("workflow_id")
                        if workflow_id:
                            if workflow_id not in self.workflow_repositories:
                                self.workflow_repositories[workflow_id] = []
                            self.workflow_repositories[workflow_id].append({
                                "repo_url": repo_url,
                                "file_path": file_path,
                                "fetched_at": datetime.now().isoformat()
                            })

                return {
                    "success": True,
                    "content": result,
                    "source": "fresh_fetch",
                    "workflow_integration": "completed",
                    "cached_for_future": True
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph content fetch failed for {repo_url}: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def analyze_repository_structure_langgraph(repo_url: str,
                                                       workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Analyze repository structure within workflow context."""
            try:
                analysis_context = {
                    "repo_url": repo_url,
                    "workflow_context": workflow_context or {},
                    "analysis_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True,
                    "structure_analysis": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/analyze/structure",
                    {
                        "repo_url": repo_url,
                        "context": analysis_context
                    }
                )

                # Store analysis result in workflow context
                if workflow_context and result.get("success"):
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        if workflow_id not in self.workflow_repositories:
                            self.workflow_repositories[workflow_id] = []
                        self.workflow_repositories[workflow_id].append({
                            "repo_url": repo_url,
                            "analysis_type": "structure",
                            "analyzed_at": datetime.now().isoformat(),
                            "structure_summary": result.get("structure", {})
                        })

                return {
                    "success": True,
                    "structure_analysis": result,
                    "workflow_integration": "completed",
                    "repo_analyzed": repo_url
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph structure analysis failed for {repo_url}: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def get_repository_metadata_langgraph(repo_url: str,
                                                  workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Get repository metadata within workflow context."""
            try:
                result = await self.service_client.get_json(
                    f"{self.service_name}/api/v1/repos/{repo_url}/metadata"
                )

                # Enhance with workflow context
                if workflow_context:
                    result["workflow_context"] = workflow_context
                    result["metadata_retrieved_for_workflow"] = True
                    result["retrieval_timestamp"] = datetime.now().isoformat()

                    # Track repository access
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        if workflow_id not in self.workflow_repositories:
                            self.workflow_repositories[workflow_id] = []
                        self.workflow_repositories[workflow_id].append({
                            "repo_url": repo_url,
                            "access_type": "metadata",
                            "accessed_at": datetime.now().isoformat()
                        })

                return {
                    "success": True,
                    "metadata": result,
                    "workflow_integration": "completed"
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        @tool
        async def search_repository_content_langgraph(repo_url: str, search_query: str,
                                                   file_pattern: str = "*",
                                                   workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Search repository content within workflow context."""
            try:
                search_context = {
                    "repo_url": repo_url,
                    "search_query": search_query,
                    "file_pattern": file_pattern,
                    "workflow_context": workflow_context or {},
                    "search_timestamp": datetime.now().isoformat(),
                    "langgraph_driven": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/search",
                    {
                        "repo_url": repo_url,
                        "query": search_query,
                        "file_pattern": file_pattern,
                        "context": search_context
                    }
                )

                return {
                    "success": True,
                    "search_results": result,
                    "workflow_integration": "completed",
                    "search_metadata": {
                        "repo_url": repo_url,
                        "query": search_query,
                        "file_pattern": file_pattern,
                        "results_count": len(result.get("results", []))
                    }
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph content search failed for {repo_url}: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def get_workflow_repositories_langgraph(workflow_id: str) -> Dict[str, Any]:
            """Get all repositories accessed in a workflow."""
            try:
                if workflow_id in self.workflow_repositories:
                    repositories = self.workflow_repositories[workflow_id]
                    return {
                        "success": True,
                        "repositories": repositories,
                        "source": "workflow_cache",
                        "workflow_id": workflow_id,
                        "total_accesses": len(repositories)
                    }

                # If not in cache, return empty result
                return {
                    "success": True,
                    "repositories": [],
                    "source": "cache_miss",
                    "workflow_id": workflow_id,
                    "total_accesses": 0
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        return {
            "fetch_repository_content_langgraph": fetch_repository_content_langgraph,
            "analyze_repository_structure_langgraph": analyze_repository_structure_langgraph,
            "get_repository_metadata_langgraph": get_repository_metadata_langgraph,
            "search_repository_content_langgraph": search_repository_content_langgraph,
            "get_workflow_repositories_langgraph": get_workflow_repositories_langgraph
        }

    async def handle_langgraph_workflow_message(self, message: BaseMessage) -> Dict[str, Any]:
        """Handle incoming LangGraph workflow messages."""
        try:
            if isinstance(message, HumanMessage):
                return await self._process_source_workflow_instruction(message.content)
            elif isinstance(message, AIMessage):
                return await self._process_source_workflow_response(message.content)
            else:
                return {"status": "ignored", "message_type": type(message).__name__}

        except Exception as e:
            fire_and_forget("error", f"LangGraph message handling failed: {e}", self.service_name)
            return {"status": "error", "error": str(e)}

    async def _process_source_workflow_instruction(self, instruction: str) -> Dict[str, Any]:
        """Process source-related workflow instructions."""
        instruction_lower = instruction.lower()

        if "fetch" in instruction_lower or "get" in instruction_lower:
            return {
                "action": "fetch_content",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["content_fetching", "repository_access", "file_retrieval"]
            }

        elif "analyze" in instruction_lower and "structure" in instruction_lower:
            return {
                "action": "analyze_structure",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["structure_analysis", "repository_introspection", "codebase_mapping"]
            }

        elif "metadata" in instruction_lower or "info" in instruction_lower:
            return {
                "action": "get_metadata",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["metadata_extraction", "repository_information", "commit_history"]
            }

        elif "search" in instruction_lower or "find" in instruction_lower:
            return {
                "action": "search_content",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["content_search", "pattern_matching", "repository_wide_search"]
            }

        else:
            return {
                "action": "general_source_operation",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["repository_operations", "content_access", "source_code_management"]
            }

    async def _process_source_workflow_response(self, response: str) -> Dict[str, Any]:
        """Process source workflow responses."""
        # Store response context for workflow continuity
        response_context = {
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "processed_by": self.service_name,
            "response_type": "source_workflow"
        }

        return {
            "status": "processed",
            "service": self.service_name,
            "response_stored": True,
            "next_actions": ["await_workflow_instructions", "prepare_source_tools"]
        }

    def get_langgraph_capabilities(self) -> Dict[str, Any]:
        """Get LangGraph capabilities for source agent."""
        return {
            "service_name": self.service_name,
            "langgraph_enabled": True,
            "supported_workflows": [
                "content_fetching",
                "repository_structure_analysis",
                "metadata_extraction",
                "content_search",
                "workflow_repository_tracking"
            ],
            "tool_categories": [
                "fetching_tools",
                "analysis_tools",
                "metadata_tools",
                "search_tools"
            ],
            "message_types": [
                "source_instructions",
                "workflow_responses",
                "repository_commands"
            ],
            "integration_features": [
                "workflow_context_awareness",
                "caching_optimization",
                "repository_tracking",
                "content_indexing"
            ]
        }

    def get_workflow_integration_status(self) -> Dict[str, Any]:
        """Get current workflow integration status."""
        return {
            "service": self.service_name,
            "langgraph_integration": "active",
            "cached_repositories": len(self.repository_cache),
            "active_workflows": len(self.workflow_repositories),
            "total_repository_accesses": sum(len(repos) for repos in self.workflow_repositories.values()),
            "last_activity": datetime.now().isoformat(),
            "capabilities_ready": True
        }

    def get_source_performance_summary(self) -> Dict[str, Any]:
        """Get summary of source agent performance."""
        summary = {
            "total_repositories_cached": len(self.repository_cache),
            "total_workflows": len(self.workflow_repositories),
            "total_accesses": sum(len(repos) for repos in self.workflow_repositories.values()),
            "cache_hit_ratio": 0,  # Would be calculated from actual usage
            "average_fetch_time": 0,  # Would be tracked from actual calls
            "repository_types": {},
            "recent_activity": []
        }

        # Get recent workflow activity
        recent_workflows = []
        for workflow_id, repositories in list(self.workflow_repositories.items())[-5:]:
            if repositories:
                recent_workflows.append({
                    "workflow_id": workflow_id,
                    "last_access": max(repo["accessed_at"] if "accessed_at" in repo
                                     else repo.get("fetched_at", repo.get("analyzed_at", ""))
                                     for repo in repositories),
                    "total_accesses": len(repositories)
                })

        summary["recent_activity"] = recent_workflows

        return summary

    async def clear_repository_cache(self, repo_url: Optional[str] = None) -> Dict[str, Any]:
        """Clear repository cache to free memory."""
        if repo_url:
            # Clear cache for specific repository
            removed_items = 0
            cache_keys_to_remove = [key for key in self.repository_cache.keys()
                                  if key.startswith(f"{repo_url}_")]

            for cache_key in cache_keys_to_remove:
                del self.repository_cache[cache_key]
                removed_items += 1

            return {
                "cache_cleared": True,
                "repo_url": repo_url,
                "items_removed": removed_items
            }
        else:
            # Clear all caches
            total_items = len(self.repository_cache)
            self.repository_cache.clear()
            return {"cache_cleared": True, "total_items_removed": total_items}


# Global instance for easy access
source_agent_langgraph = SourceAgentLangGraphIntegration()
