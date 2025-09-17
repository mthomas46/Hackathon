"""Ecosystem Context Awareness Module for Interpreter Service.

This module provides comprehensive knowledge about the LLM Documentation Ecosystem,
enabling the interpreter to understand available services, their capabilities, and
how to translate natural language queries into appropriate workflow executions.
"""

import json
from typing import Dict, Any, List, Optional, Set
from services.shared.clients import ServiceClients
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class EcosystemContext:
    """Provides comprehensive context about the LLM Documentation Ecosystem."""

    def __init__(self):
        self.client = ServiceClients()
        self.orchestrator_url = "http://llm-orchestrator:5000"

        # Core ecosystem services and their capabilities
        self.service_capabilities = {
            "document_store": {
                "description": "Document storage and retrieval system",
                "capabilities": [
                    "store_documents", "retrieve_documents", "search_documents",
                    "tag_documents", "version_documents", "lifecycle_management",
                    "bulk_operations", "semantic_search"
                ],
                "endpoints": {
                    "store": "/documents",
                    "retrieve": "/documents/{id}",
                    "search": "/documents/search",
                    "bulk": "/bulk/documents"
                },
                "aliases": ["doc_store", "documents", "document storage"]
            },
            "prompt_store": {
                "description": "AI prompt management and optimization system",
                "capabilities": [
                    "create_prompts", "store_prompts", "search_prompts",
                    "optimize_prompts", "version_prompts", "categorize_prompts",
                    "a_b_testing", "performance_analytics", "bulk_operations"
                ],
                "endpoints": {
                    "create": "/prompts",
                    "search": "/prompts/search",
                    "optimize": "/prompts/{id}/optimize",
                    "analytics": "/analytics/prompts"
                },
                "aliases": ["prompts", "prompt management", "ai prompts"]
            },
            "code_analyzer": {
                "description": "Code analysis and documentation generation",
                "capabilities": [
                    "analyze_code", "extract_functions", "generate_docs",
                    "detect_patterns", "code_quality", "dependency_analysis",
                    "security_scanning", "performance_analysis"
                ],
                "endpoints": {
                    "analyze": "/analyze",
                    "structure": "/structure",
                    "docs": "/generate-docs"
                },
                "aliases": ["code", "code analysis", "code docs"]
            },
            "summarizer_hub": {
                "description": "Advanced text summarization and content processing",
                "capabilities": [
                    "summarize_text", "extract_key_concepts", "content_analysis",
                    "generate_abstracts", "multi_language_support", "bulk_summarization"
                ],
                "endpoints": {
                    "summarize": "/summarize",
                    "concepts": "/concepts",
                    "bulk": "/bulk/summarize"
                },
                "aliases": ["summarizer", "text summary", "content processing"]
            },
            "analysis_service": {
                "description": "Comprehensive document and content analysis",
                "capabilities": [
                    "consistency_analysis", "quality_analysis", "security_analysis",
                    "bias_detection", "sentiment_analysis", "topic_modeling",
                    "duplicate_detection", "completeness_check"
                ],
                "endpoints": {
                    "analyze": "/analyze",
                    "consistency": "/consistency",
                    "quality": "/quality",
                    "security": "/security"
                },
                "aliases": ["analysis", "content analysis", "document analysis"]
            },
            "notification_service": {
                "description": "Multi-channel notification and alert system",
                "capabilities": [
                    "send_notifications", "manage_templates", "webhook_delivery",
                    "email_notifications", "schedule_notifications", "notification_history"
                ],
                "endpoints": {
                    "send": "/notify",
                    "templates": "/templates",
                    "history": "/history"
                },
                "aliases": ["notifications", "alerts", "messaging"]
            },
            "source_agent": {
                "description": "Multi-source data ingestion and processing",
                "capabilities": [
                    "github_ingestion", "jira_ingestion", "confluence_ingestion",
                    "swagger_ingestion", "web_scraping", "api_ingestion",
                    "batch_processing", "data_validation"
                ],
                "endpoints": {
                    "ingest": "/ingest",
                    "sources": "/sources",
                    "batch": "/batch"
                },
                "aliases": ["ingestion", "data sources", "source ingestion"]
            },
            "secure_analyzer": {
                "description": "Security analysis and compliance checking",
                "capabilities": [
                    "security_scanning", "vulnerability_detection", "compliance_checking",
                    "data_sanitization", "access_control", "audit_trails",
                    "privacy_analysis", "risk_assessment"
                ],
                "endpoints": {
                    "scan": "/scan",
                    "compliance": "/compliance",
                    "audit": "/audit"
                },
                "aliases": ["security", "compliance", "secure analysis"]
            },
            "orchestrator": {
                "description": "Central workflow orchestration and coordination",
                "capabilities": [
                    "workflow_execution", "service_coordination", "langgraph_workflows",
                    "event_processing", "saga_orchestration", "distributed_tracing",
                    "health_monitoring", "service_discovery"
                ],
                "endpoints": {
                    "workflows": "/workflows",
                    "execute": "/workflows/run",
                    "ai_workflows": "/workflows/ai",
                    "services": "/services"
                },
                "aliases": ["orchestrator", "workflows", "coordination"]
            }
        }

        # Project-specific context and terminology
        self.project_context = {
            "domains": [
                "documentation", "code analysis", "content processing",
                "ai prompts", "security", "compliance", "notifications",
                "data ingestion", "workflow orchestration"
            ],
            "technologies": [
                "fastapi", "pydantic", "docker", "kubernetes", "redis",
                "postgresql", "elasticsearch", "langchain", "langgraph",
                "openai", "anthropic", "huggingface"
            ],
            "terminology": {
                "doc_store": "document_store",
                "docs": "document_store",
                "documents": "document_store",
                "prompts": "prompt_store",
                "ai": "prompt_store",
                "code": "code_analyzer",
                "analysis": "analysis_service",
                "security": "secure_analyzer",
                "notifications": "notification_service",
                "ingestion": "source_agent",
                "sources": "source_agent",
                "orchestrator": "orchestrator",
                "workflows": "orchestrator"
            }
        }

        # Workflow templates for common operations
        self.workflow_templates = {
            "document_analysis": {
                "description": "Analyze documents for quality, consistency, and security",
                "services": ["document_store", "analysis_service", "summarizer_hub"],
                "steps": [
                    {"service": "document_store", "action": "retrieve", "description": "Fetch documents"},
                    {"service": "analysis_service", "action": "analyze", "description": "Analyze content"},
                    {"service": "summarizer_hub", "action": "summarize", "description": "Generate summary"}
                ]
            },
            "code_documentation": {
                "description": "Generate documentation from code repositories",
                "services": ["source_agent", "code_analyzer", "document_store"],
                "steps": [
                    {"service": "source_agent", "action": "ingest", "description": "Ingest code"},
                    {"service": "code_analyzer", "action": "analyze", "description": "Analyze code"},
                    {"service": "document_store", "action": "store", "description": "Store documentation"}
                ]
            },
            "security_audit": {
                "description": "Comprehensive security analysis and reporting",
                "services": ["secure_analyzer", "analysis_service", "notification_service"],
                "steps": [
                    {"service": "secure_analyzer", "action": "scan", "description": "Security scan"},
                    {"service": "analysis_service", "action": "analyze", "description": "Risk analysis"},
                    {"service": "notification_service", "action": "send", "description": "Send alerts"}
                ]
            },
            "content_processing": {
                "description": "Process and optimize content for AI consumption",
                "services": ["document_store", "summarizer_hub", "prompt_store"],
                "steps": [
                    {"service": "document_store", "action": "retrieve", "description": "Get content"},
                    {"service": "summarizer_hub", "action": "summarize", "description": "Summarize content"},
                    {"service": "prompt_store", "action": "optimize", "description": "Optimize for AI"}
                ]
            }
        }

    async def get_service_capabilities(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get capabilities for a specific service or all services."""
        if service_name:
            return self.service_capabilities.get(service_name, {})
        return self.service_capabilities

    def get_service_by_alias(self, alias: str) -> Optional[str]:
        """Find service name by alias."""
        alias_lower = alias.lower()
        for service_name, info in self.service_capabilities.items():
            if alias_lower in [a.lower() for a in info.get("aliases", [])]:
                return service_name
            if alias_lower in service_name.lower():
                return service_name
        return None

    def get_capability_service(self, capability: str) -> List[str]:
        """Find services that provide a specific capability."""
        capability_lower = capability.lower().replace(" ", "_")
        matching_services = []

        for service_name, info in self.service_capabilities.items():
            capabilities = [cap.lower().replace(" ", "_") for cap in info.get("capabilities", [])]
            if capability_lower in capabilities:
                matching_services.append(service_name)

        return matching_services

    async def discover_available_workflows(self) -> Dict[str, Any]:
        """Discover available LangGraph workflows from the orchestrator."""
        try:
            # Try to get available workflows from orchestrator
            response = await self.client.get_json(f"{self.orchestrator_url}/workflows")
            if response.get("success"):
                return response.get("data", {})
        except Exception as e:
            fire_and_forget(
                "error",
                f"Failed to discover workflows from orchestrator: {str(e)}",
                ServiceNames.INTERPRETER
            )

        # Fallback to predefined workflow templates
        return {
            "available_workflows": list(self.workflow_templates.keys()),
            "templates": self.workflow_templates
        }

    async def get_orchestrator_tools(self) -> Dict[str, Any]:
        """Get discovered tools from the orchestrator."""
        try:
            # This would integrate with the tool discovery system
            # For now, return service capabilities as tools
            tools = {}
            for service_name, service_info in self.service_capabilities.items():
                for capability in service_info.get("capabilities", []):
                    tool_name = f"{service_name}_{capability}"
                    tools[tool_name] = {
                        "name": tool_name,
                        "description": f"{capability.replace('_', ' ')} using {service_name}",
                        "service": service_name,
                        "capability": capability,
                        "endpoint": service_info.get("endpoints", {}).get(capability.split("_")[0], "/")
                    }
            return tools
        except Exception as e:
            fire_and_forget(
                "error",
                f"Failed to get orchestrator tools: {str(e)}",
                ServiceNames.INTERPRETER
            )
            return {}

    def map_query_to_workflow(self, query: str, entities: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Map a natural language query to an appropriate workflow."""
        query_lower = query.lower()

        # Document analysis workflows
        if any(word in query_lower for word in ["analyze", "check", "review", "examine"]):
            if any(word in query_lower for word in ["document", "docs", "content", "file"]):
                return self.workflow_templates.get("document_analysis")

        # Code analysis workflows
        if any(word in query_lower for word in ["code", "repository", "repo", "programming"]):
            if any(word in query_lower for word in ["analyze", "document", "generate docs"]):
                return self.workflow_templates.get("code_documentation")

        # Security workflows
        if any(word in query_lower for word in ["security", "secure", "vulnerability", "scan"]):
            return self.workflow_templates.get("security_audit")

        # Content processing workflows
        if any(word in query_lower for word in ["summarize", "process", "optimize", "content"]):
            return self.workflow_templates.get("content_processing")

        return None

    def get_contextual_help(self, query: str) -> Dict[str, Any]:
        """Provide contextual help based on query analysis."""
        query_lower = query.lower()

        help_info = {
            "available_services": list(self.service_capabilities.keys()),
            "common_workflows": list(self.workflow_templates.keys()),
            "suggestions": []
        }

        # Provide suggestions based on query content
        if "analyze" in query_lower or "check" in query_lower:
            help_info["suggestions"].append("Try: 'analyze document quality'")
            help_info["suggestions"].append("Try: 'check consistency across docs'")

        if "code" in query_lower or "repo" in query_lower:
            help_info["suggestions"].append("Try: 'analyze code repository'")
            help_info["suggestions"].append("Try: 'generate documentation from code'")

        if "security" in query_lower or "secure" in query_lower:
            help_info["suggestions"].append("Try: 'scan for security vulnerabilities'")
            help_info["suggestions"].append("Try: 'check compliance'")

        return help_info

    async def validate_workflow_compatibility(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that a workflow can be executed with available services."""
        required_services = workflow.get("services", [])
        missing_services = []

        for service in required_services:
            if service not in self.service_capabilities:
                # Try to find by alias
                actual_service = self.get_service_by_alias(service)
                if not actual_service:
                    missing_services.append(service)
                else:
                    # Replace with actual service name
                    workflow["services"] = [
                        actual_service if s == service else s
                        for s in workflow["services"]
                    ]

        return {
            "valid": len(missing_services) == 0,
            "missing_services": missing_services,
            "available_services": list(self.service_capabilities.keys()),
            "workflow": workflow
        }


# Create singleton instance
ecosystem_context = EcosystemContext()
