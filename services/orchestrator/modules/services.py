"""Service management functionality for the Orchestrator service.

This module contains all service discovery and information endpoints,
extracted from the main orchestrator service to improve maintainability.
"""

from typing import Dict, Any, List
from services.shared.core.constants_new import ServiceNames
from .shared_utils import (
    get_orchestrator_service_client,
    handle_service_error,
    create_service_success_response,
    build_orchestrator_context
)


# Helper functions removed - using shared utilities from shared_utils.py


def _get_service_definitions() -> Dict[str, Dict[str, Any]]:
    """Get comprehensive service definitions with metadata and capabilities."""
    return {
        ServiceNames.ORCHESTRATOR: {
            "name": "Orchestrator",
            "description": "Central control plane and service coordinator",
            "category": "orchestration",
            "capabilities": ["coordination", "health_monitoring", "query_processing"],
            "endpoints": [
                "GET /health - Health check",
                "GET /health/system - System-wide health monitoring",
                "POST /query - Natural language query processing",
                "POST /query/execute - Execute interpreted workflows",
                "GET /services - Service discovery and information",
                "GET /workflows - Available workflow templates"
            ]
        },
        ServiceNames.PROMPT_STORE: {
            "name": "Prompt Store",
            "description": "Advanced prompt management with versioning and analytics",
            "category": "ai_management",
            "capabilities": ["prompt_management", "versioning", "analytics", "ab_testing"],
            "endpoints": [
                "POST /prompts - Create new prompts",
                "GET /prompts - List prompts with filtering",
                "GET /prompts/{id} - Retrieve specific prompt",
                "PUT /prompts/{id} - Update existing prompt",
                "POST /ab-tests - Create A/B tests",
                "GET /analytics - Usage analytics and metrics"
            ]
        },
        ServiceNames.INTERPRETER: {
            "name": "Interpreter",
            "description": "Natural language processing for user queries",
            "category": "nlp",
            "capabilities": ["query_interpretation", "intent_recognition", "workflow_execution"],
            "endpoints": [
                "POST /interpret - Interpret natural language queries",
                "POST /execute - Execute interpreted workflows",
                "GET /intents - List supported intents",
                "GET /workflows - Available workflow templates"
            ]
        },
        ServiceNames.ANALYSIS_SERVICE: {
            "name": "Analysis Service",
            "description": "Document analysis and consistency checking",
            "category": "analysis",
            "capabilities": ["document_analysis", "consistency_checking", "quality_assessment"],
            "endpoints": [
                "POST /analyze - Analyze documents for consistency",
                "GET /findings - Retrieve analysis findings",
                "POST /reports/generate - Generate analysis reports",
                "GET /consistency/check - Validate document consistency"
            ]
        },
        ServiceNames.DOC_STORE: {
            "name": "Doc Store",
            "description": "Document storage and retrieval system",
            "category": "storage",
            "capabilities": ["document_storage", "retrieval", "search", "versioning"],
            "endpoints": [
                "POST /documents - Store new documents",
                "GET /documents/{id} - Retrieve specific document",
                "GET /documents/_list - List documents with filtering",
                "GET /search - Search documents by content",
                "GET /documents/quality - Quality metrics and flags"
            ]
        },
        ServiceNames.SOURCE_AGENT: {
            "name": "Source Agent",
            "description": "Data ingestion from various external sources",
            "category": "ingestion",
            "capabilities": ["data_ingestion", "source_integration", "document_processing"],
            "endpoints": [
                "POST /ingest - Ingest data from sources",
                "GET /sources - List available data sources",
                "GET /sources/{id}/status - Check source ingestion status"
            ]
        }
    }


def _build_service_info(service_name: str, service_config: Dict[str, Any], service_client) -> Dict[str, Any]:
    """Build comprehensive service information including URLs and status."""
    try:
        # Get service URL using the appropriate method
        url_method = f"{service_name.replace('-', '_')}_url"
        service_url = getattr(service_client, url_method, lambda: f"http://{service_name}:unknown")()

        return {
            **service_config,
            "service_name": service_name,
            "url": service_url,
            "status": "active",  # Could be enhanced with actual health checks
            "version": "1.0.0",  # Could be retrieved from service metadata
            "last_updated": None  # Could track service update timestamps
        }
    except Exception as e:
        # Use shared error handling for warnings
        from services.shared.monitoring.logging import fire_and_forget
        fire_and_forget("warning", f"Failed to get URL for service {service_name}: {e}", ServiceNames.ORCHESTRATOR)
        return {
            **service_config,
            "service_name": service_name,
            "url": f"http://{service_name}:unknown",
            "status": "configuration_error",
            "error": str(e)
        }


async def list_services() -> Dict[str, Any]:
    """Get comprehensive information about all integrated services with enhanced metadata."""
    try:
        service_client = get_orchestrator_service_client()
        service_definitions = _get_service_definitions()

        # Build detailed service information
        services_info = {}
        for service_name, service_config in service_definitions.items():
            services_info[service_name] = _build_service_info(service_name, service_config, service_client)

        # Categorize services by functionality
        categories = {}
        for service_name, service_info in services_info.items():
            category = service_info.get("category", "other")
            if category not in categories:
                categories[category] = []
            categories[category].append(service_name)

        # Create comprehensive response
        response_data = {
            "services": services_info,
            "total_services": len(services_info),
            "categories": categories,
            "integration_status": "fully_integrated",
            "orchestrator_version": "2.0.0",
            "last_service_discovery": None  # Could track discovery timestamps
        }

        context = build_orchestrator_context("service_discovery", total_services=len(services_info), categories=list(categories.keys()))
        return create_service_success_response("service discovery", response_data, **context)

    except Exception as e:
        context = build_orchestrator_context("service_discovery")
        return handle_service_error("retrieve service information", e, **context)
