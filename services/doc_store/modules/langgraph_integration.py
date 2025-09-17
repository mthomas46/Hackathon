#!/usr/bin/env python3
"""
LangGraph Integration for Document Store Service

This module provides LangGraph awareness and integration capabilities
for the Document Store Service, enabling it to participate in AI-powered workflows.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from langchain_core.tools import BaseTool, tool
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from services.shared.utilities import get_service_client
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class DocStoreLangGraphIntegration:
    """LangGraph integration for Document Store Service."""

    def __init__(self):
        self.service_name = ServiceNames.DOCUMENT_STORE
        self.service_client = get_service_client()
        self.workflow_cache = {}
        self.active_workflows = {}

    async def initialize_langgraph_tools(self) -> Dict[str, BaseTool]:
        """Initialize LangGraph tools for document store."""

        @tool
        async def store_document_langgraph(content: str, metadata: Dict[str, Any],
                                         source: str, workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Store a document within a LangGraph workflow context."""
            try:
                # Enhance metadata with workflow context
                enhanced_metadata = {
                    **metadata,
                    "source": source,
                    "workflow_context": workflow_context or {},
                    "langgraph_integration": True,
                    "stored_at": datetime.now().isoformat(),
                    "workflow_id": workflow_context.get("workflow_id") if workflow_context else None
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/documents",
                    {
                        "content": content,
                        "metadata": enhanced_metadata,
                        "source": f"{source}_langgraph"
                    }
                )

                # Cache for workflow continuity
                doc_id = result.get("id")
                if doc_id and workflow_context:
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        if workflow_id not in self.workflow_cache:
                            self.workflow_cache[workflow_id] = []
                        self.workflow_cache[workflow_id].append({
                            "doc_id": doc_id,
                            "action": "stored",
                            "timestamp": datetime.now().isoformat(),
                            "metadata": enhanced_metadata
                        })

                return {
                    "success": True,
                    "document_id": doc_id,
                    "workflow_integration": "completed",
                    "cache_updated": bool(workflow_context)
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph document storage failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def retrieve_document_langgraph(doc_id: str,
                                            workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Retrieve a document within LangGraph workflow context."""
            try:
                result = await self.service_client.get_json(
                    f"{self.service_name}/api/v1/documents/{doc_id}"
                )

                # Add workflow context to retrieval
                if workflow_context:
                    result["workflow_context"] = workflow_context
                    result["retrieved_for_workflow"] = True
                    result["retrieval_timestamp"] = datetime.now().isoformat()

                    # Update workflow cache
                    workflow_id = workflow_context.get("workflow_id")
                    if workflow_id:
                        if workflow_id not in self.workflow_cache:
                            self.workflow_cache[workflow_id] = []
                        self.workflow_cache[workflow_id].append({
                            "doc_id": doc_id,
                            "action": "retrieved",
                            "timestamp": datetime.now().isoformat(),
                            "workflow_context": workflow_context
                        })

                return {
                    "success": True,
                    "document": result,
                    "workflow_integration": "completed"
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        @tool
        async def search_documents_langgraph(query: str, filters: Dict[str, Any],
                                           workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Search documents within LangGraph workflow context."""
            try:
                # Enhance filters with workflow context
                enhanced_filters = {
                    **filters,
                    "workflow_context": workflow_context,
                    "search_timestamp": datetime.now().isoformat(),
                    "langgraph_search": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/search",
                    {
                        "query": query,
                        "filters": enhanced_filters
                    }
                )

                # Add workflow metadata to results
                result["workflow_integration"] = {
                    "search_performed_in_workflow": bool(workflow_context),
                    "query": query,
                    "filters_applied": list(enhanced_filters.keys()),
                    "results_count": len(result.get("results", []))
                }

                return {
                    "success": True,
                    "search_results": result,
                    "workflow_integration": "completed"
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph document search failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def get_workflow_documents_langgraph(workflow_id: str) -> Dict[str, Any]:
            """Get all documents associated with a specific workflow."""
            try:
                # Check cache first
                if workflow_id in self.workflow_cache:
                    cached_docs = self.workflow_cache[workflow_id]
                    return {
                        "success": True,
                        "documents": cached_docs,
                        "source": "workflow_cache",
                        "workflow_id": workflow_id
                    }

                # Query by workflow metadata
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
                    "documents": result.get("results", []),
                    "source": "database_query",
                    "workflow_id": workflow_id,
                    "total_found": len(result.get("results", []))
                }

            except Exception as e:
                fire_and_forget("error", f"LangGraph workflow documents query failed: {e}", self.service_name)
                return {"success": False, "error": str(e)}

        @tool
        async def create_document_relationship_langgraph(doc_id_1: str, doc_id_2: str,
                                                       relationship_type: str,
                                                       workflow_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            """Create a relationship between documents within a workflow."""
            try:
                relationship_data = {
                    "document_id_1": doc_id_1,
                    "document_id_2": doc_id_2,
                    "relationship_type": relationship_type,
                    "workflow_context": workflow_context,
                    "created_at": datetime.now().isoformat(),
                    "langgraph_created": True
                }

                result = await self.service_client.post_json(
                    f"{self.service_name}/api/v1/relationships",
                    relationship_data
                )

                return {
                    "success": True,
                    "relationship": result,
                    "workflow_integration": "completed"
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        return {
            "store_document_langgraph": store_document_langgraph,
            "retrieve_document_langgraph": retrieve_document_langgraph,
            "search_documents_langgraph": search_documents_langgraph,
            "get_workflow_documents_langgraph": get_workflow_documents_langgraph,
            "create_document_relationship_langgraph": create_document_relationship_langgraph
        }

    async def handle_langgraph_workflow_message(self, message: BaseMessage) -> Dict[str, Any]:
        """Handle incoming LangGraph workflow messages."""
        try:
            if isinstance(message, HumanMessage):
                return await self._process_document_workflow_instruction(message.content)
            elif isinstance(message, AIMessage):
                return await self._process_document_workflow_response(message.content)
            else:
                return {"status": "ignored", "message_type": type(message).__name__}

        except Exception as e:
            fire_and_forget("error", f"LangGraph message handling failed: {e}", self.service_name)
            return {"status": "error", "error": str(e)}

    async def _process_document_workflow_instruction(self, instruction: str) -> Dict[str, Any]:
        """Process document-related workflow instructions."""
        instruction_lower = instruction.lower()

        if "store" in instruction_lower and "document" in instruction_lower:
            return {
                "action": "store_document",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["document_storage", "metadata_enhancement", "workflow_tracking"]
            }

        elif "retrieve" in instruction_lower or "get" in instruction_lower:
            return {
                "action": "retrieve_document",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["document_retrieval", "workflow_context", "cache_optimization"]
            }

        elif "search" in instruction_lower or "find" in instruction_lower:
            return {
                "action": "search_documents",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["document_search", "advanced_filtering", "workflow_aware_search"]
            }

        elif "relationship" in instruction_lower or "link" in instruction_lower:
            return {
                "action": "manage_relationships",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["relationship_creation", "document_linking", "workflow_relationships"]
            }

        else:
            return {
                "action": "general_document_operation",
                "service": self.service_name,
                "instruction": instruction,
                "capabilities": ["document_operations", "workflow_integration", "metadata_management"]
            }

    async def _process_document_workflow_response(self, response: str) -> Dict[str, Any]:
        """Process document workflow responses."""
        # Store response context for workflow continuity
        response_context = {
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "processed_by": self.service_name,
            "response_type": "document_workflow"
        }

        # Update active workflow if exists
        for workflow_id in self.active_workflows:
            self.active_workflows[workflow_id]["last_response"] = response_context

        return {
            "status": "processed",
            "service": self.service_name,
            "response_stored": True,
            "active_workflows_updated": len(self.active_workflows)
        }

    def get_langgraph_capabilities(self) -> Dict[str, Any]:
        """Get LangGraph capabilities for document store."""
        return {
            "service_name": self.service_name,
            "langgraph_enabled": True,
            "supported_workflows": [
                "document_storage",
                "document_retrieval",
                "document_search",
                "relationship_management",
                "workflow_document_tracking"
            ],
            "tool_categories": [
                "storage_tools",
                "retrieval_tools",
                "search_tools",
                "relationship_tools"
            ],
            "message_types": [
                "document_instructions",
                "workflow_responses",
                "storage_commands"
            ],
            "integration_features": [
                "workflow_context_awareness",
                "cache_optimization",
                "relationship_tracking",
                "metadata_enhancement"
            ]
        }

    def get_workflow_integration_status(self) -> Dict[str, Any]:
        """Get current workflow integration status."""
        return {
            "service": self.service_name,
            "langgraph_integration": "active",
            "cache_size": len(self.workflow_cache),
            "active_workflows": len(self.active_workflows),
            "total_cached_documents": sum(len(docs) for docs in self.workflow_cache.values()),
            "last_activity": datetime.now().isoformat(),
            "capabilities_ready": True
        }

    async def cleanup_workflow_cache(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """Clean up workflow cache to free memory."""
        if workflow_id:
            removed = len(self.workflow_cache.pop(workflow_id, []))
            return {"cache_cleaned": True, "workflow_id": workflow_id, "documents_removed": removed}
        else:
            total_removed = sum(len(docs) for docs in self.workflow_cache.values())
            self.workflow_cache.clear()
            return {"cache_cleaned": True, "total_documents_removed": total_removed}


# Global instance for easy access
doc_store_langgraph = DocStoreLangGraphIntegration()
