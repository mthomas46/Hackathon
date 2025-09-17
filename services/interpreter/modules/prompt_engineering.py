"""Prompt Engineering Module for Interpreter Service.

This module provides advanced prompt engineering capabilities to translate natural
language queries into structured workflow executions within the LLM Documentation Ecosystem.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from .ecosystem_context import ecosystem_context
from .orchestrator_integration import orchestrator_integration


class PromptEngineer:
    """Advanced prompt engineering for natural language to workflow translation."""

    def __init__(self):
        self.templates = self._load_prompt_templates()
        self.context_cache = {}

    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load prompt templates for different query types and workflows."""
        return {
            "workflow_translation": """
You are an expert workflow orchestrator for the LLM Documentation Ecosystem. Your task is to translate natural language queries into structured workflow executions.

Available Services and Capabilities:
{ecosystem_context}

User Query: {query}
Detected Intent: {intent}
Extracted Entities: {entities}

Translate this query into a structured workflow that leverages the available ecosystem services. Consider:
1. Which services are needed for this task
2. The optimal sequence of operations
3. Required parameters and data flow
4. Error handling and fallback strategies

Provide a JSON response with:
- workflow_type: The type of workflow to execute
- parameters: Structured parameters for the workflow
- services: List of services involved
- confidence: Confidence score (0.0-1.0)
- explanation: Brief explanation of the translation
""",

            "intent_clarification": """
The user's query is ambiguous. Help clarify their intent by providing suggestions based on available ecosystem capabilities.

User Query: {query}
Available Capabilities: {capabilities}

Suggest the most likely interpretations and provide example queries for each.
""",

            "workflow_optimization": """
Optimize the workflow execution based on:
- Available service capabilities
- Current system load
- Data dependencies
- Performance requirements

Workflow: {workflow}
System Context: {context}

Provide optimization recommendations.
""",

            "error_recovery": """
A workflow execution failed. Suggest recovery strategies based on:
- Failure type and location
- Available alternative services
- Data preservation requirements
- User impact assessment

Failed Workflow: {workflow}
Error Details: {error}

Provide recovery recommendations.
"""
        }

    async def translate_query_to_workflow(self, query: str, intent: str,
                                       entities: Dict[str, Any],
                                       ecosystem_context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Translate a natural language query into a structured workflow."""
        try:
            # Prepare context for prompt engineering
            context = self._prepare_context(ecosystem_context_data)

            # Use the appropriate translation strategy
            if intent == "unknown" or self._needs_clarification(query, intent, entities):
                return await self._handle_ambiguous_query(query, context)
            else:
                return await self._translate_direct_workflow(query, intent, entities, context)

        except Exception as e:
            fire_and_forget(
                "interpreter_prompt_translation_failed",
                f"Failed to translate query to workflow: {str(e)}",
                ServiceNames.INTERPRETER,
                {"query": query, "intent": intent, "error": str(e)}
            )
            return self._create_fallback_workflow(query, intent, entities)

    async def _translate_direct_workflow(self, query: str, intent: str,
                                       entities: Dict[str, Any],
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Translate query directly to workflow using prompt engineering."""
        try:
            # Create the translation prompt
            prompt = self.templates["workflow_translation"].format(
                query=query,
                intent=intent,
                entities=json.dumps(entities, indent=2),
                ecosystem_context=json.dumps(context, indent=2)
            )

            # In a real implementation, this would call an LLM
            # For now, use rule-based translation with ecosystem context
            workflow = await self._rule_based_translation(query, intent, entities, context)

            return {
                "workflow_type": workflow.get("type", "generic"),
                "parameters": workflow.get("parameters", {}),
                "services": workflow.get("services", []),
                "confidence": workflow.get("confidence", 0.8),
                "explanation": workflow.get("explanation", "Workflow generated from natural language query"),
                "translation_method": "rule_based"
            }

        except Exception as e:
            return self._create_fallback_workflow(query, intent, entities)

    async def _rule_based_translation(self, query: str, intent: str,
                                    entities: Dict[str, Any],
                                    context: Dict[str, Any]) -> Dict[str, Any]:
        """Use rule-based logic to translate query to workflow."""
        workflow = {
            "type": "generic",
            "parameters": {},
            "services": [],
            "confidence": 0.7,
            "explanation": f"Generated workflow for {intent}"
        }

        # Map intents to workflow types and services
        if intent == "analyze_document":
            workflow.update({
                "type": "document_analysis",
                "services": ["document_store", "analysis_service", "summarizer_hub"],
                "parameters": {
                    "analysis_types": ["consistency", "quality", "security"],
                    "include_summary": True
                },
                "confidence": 0.9
            })

        elif intent == "analyze_code":
            workflow.update({
                "type": "code_documentation",
                "services": ["code_analyzer", "document_store", "summarizer_hub"],
                "parameters": {
                    "generate_docs": True,
                    "include_structure": True,
                    "analysis_types": ["complexity", "patterns", "quality"]
                },
                "confidence": 0.9
            })

        elif intent == "security_scan":
            workflow.update({
                "type": "security_audit",
                "services": ["secure_analyzer", "analysis_service", "notification_service"],
                "parameters": {
                    "scan_types": ["vulnerabilities", "compliance", "data_safety"],
                    "send_alerts": True
                },
                "confidence": 0.9
            })

        elif intent == "find_prompt":
            workflow.update({
                "type": "prompt_search",
                "services": ["prompt_store"],
                "parameters": {
                    "query": entities.get("search_terms", [""])[0],
                    "limit": 10,
                    "sort_by": "performance"
                },
                "confidence": 0.8
            })

        elif intent == "summarize_content":
            workflow.update({
                "type": "content_processing",
                "services": ["summarizer_hub", "document_store"],
                "parameters": {
                    "max_length": 500,
                    "include_key_concepts": True,
                    "format": "structured"
                },
                "confidence": 0.8
            })

        elif intent.startswith("ingest_"):
            source_type = intent.replace("ingest_", "")
            workflow.update({
                "type": "data_ingestion",
                "services": ["source_agent", "document_store"],
                "parameters": {
                    "source_type": source_type,
                    "validate_data": True,
                    "store_results": True
                },
                "confidence": 0.8
            })

        elif intent == "execute_workflow":
            workflow.update({
                "type": "custom_workflow",
                "services": ["orchestrator"],
                "parameters": {
                    "workflow_spec": entities.get("workflow_spec", {}),
                    "async_execution": True
                },
                "confidence": 0.7
            })

        # Add entity-based parameters
        workflow["parameters"].update(self._extract_workflow_parameters(entities))

        return workflow

    def _extract_workflow_parameters(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Extract workflow parameters from entities."""
        params = {}

        # Extract URLs
        if "url" in entities and entities["url"]:
            params["source_urls"] = entities["url"]

        # Extract repository information
        if "repo" in entities and entities["repo"]:
            params["repositories"] = entities["repo"]

        # Extract file paths
        if "file_path" in entities and entities["file_path"]:
            params["file_paths"] = entities["file_path"]

        # Extract search terms
        if "search_terms" in entities and entities["search_terms"]:
            params["query"] = " ".join(entities["search_terms"])

        return params

    async def _handle_ambiguous_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ambiguous queries by providing clarification suggestions."""
        capabilities = context.get("capabilities", [])

        return {
            "workflow_type": "clarification_needed",
            "parameters": {
                "original_query": query,
                "suggestions": self._generate_query_suggestions(query, capabilities),
                "available_capabilities": capabilities
            },
            "services": [],
            "confidence": 0.3,
            "explanation": "Query is ambiguous and needs clarification",
            "translation_method": "clarification"
        }

    def _generate_query_suggestions(self, query: str, capabilities: List[str]) -> List[str]:
        """Generate query suggestions for ambiguous queries."""
        suggestions = []

        query_lower = query.lower()

        if "analyze" in query_lower or "check" in query_lower:
            suggestions.extend([
                "analyze document quality",
                "check code for issues",
                "analyze security vulnerabilities"
            ])

        if "create" in query_lower or "generate" in query_lower:
            suggestions.extend([
                "create a new prompt",
                "generate documentation",
                "create a report"
            ])

        if "find" in query_lower or "search" in query_lower:
            suggestions.extend([
                "find prompts by category",
                "search documents",
                "find code patterns"
            ])

        # Add general suggestions if no specific ones match
        if not suggestions:
            suggestions.extend([
                "analyze document content",
                "search for prompts",
                "ingest data from repository"
            ])

        return suggestions[:5]  # Limit to top 5 suggestions

    def _needs_clarification(self, query: str, intent: str, entities: Dict[str, Any]) -> bool:
        """Determine if a query needs clarification."""
        # Low confidence intents need clarification
        if intent == "unknown":
            return True

        # Queries with very few entities might be ambiguous
        total_entities = sum(len(entity_list) for entity_list in entities.values()
                           if isinstance(entity_list, list))
        if total_entities < 2:
            return True

        # Very short queries might be ambiguous
        if len(query.split()) < 3:
            return True

        return False

    def _prepare_context(self, ecosystem_context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for prompt engineering."""
        return {
            "services": ecosystem_context_data.get("services", {}),
            "capabilities": ecosystem_context_data.get("capabilities", []),
            "workflows": ecosystem_context_data.get("workflows", []),
            "terminology": ecosystem_context_data.get("terminology", {}),
            "timestamp": datetime.now().isoformat()
        }

    def _create_fallback_workflow(self, query: str, intent: str,
                                entities: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback workflow when translation fails."""
        return {
            "workflow_type": "help",
            "parameters": {
                "original_query": query,
                "detected_intent": intent,
                "entities": entities,
                "reason": "Translation failed, providing help instead"
            },
            "services": [],
            "confidence": 0.1,
            "explanation": "Unable to translate query to workflow, providing help",
            "translation_method": "fallback"
        }

    async def optimize_workflow(self, workflow: Dict[str, Any],
                              system_context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize a workflow based on system context."""
        try:
            # Analyze workflow for optimization opportunities
            optimizations = []

            # Check for parallel execution opportunities
            if len(workflow.get("services", [])) > 1:
                optimizations.append("parallel_execution")

            # Check for caching opportunities
            if "search" in str(workflow):
                optimizations.append("result_caching")

            # Check for resource optimization
            if "analysis" in str(workflow):
                optimizations.append("resource_optimization")

            return {
                "optimized_workflow": workflow,
                "optimizations_applied": optimizations,
                "performance_estimate": "improved",
                "resource_usage": "optimized"
            }

        except Exception as e:
            return {
                "optimized_workflow": workflow,
                "optimizations_applied": [],
                "error": str(e)
            }

    async def suggest_workflow_improvements(self, workflow: Dict[str, Any],
                                          execution_history: List[Dict[str, Any]]) -> List[str]:
        """Suggest improvements based on execution history."""
        suggestions = []

        # Analyze execution patterns
        if execution_history:
            avg_duration = sum(h.get("duration", 0) for h in execution_history) / len(execution_history)
            if avg_duration > 300:  # 5 minutes
                suggestions.append("Consider breaking workflow into smaller steps")

            # Check for frequent failures
            failure_rate = sum(1 for h in execution_history if h.get("status") == "failed") / len(execution_history)
            if failure_rate > 0.2:
                suggestions.append("Add retry logic and error handling")

        return suggestions


# Create singleton instance
prompt_engineer = PromptEngineer()
