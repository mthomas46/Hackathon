"""Service: Interpreter

Endpoints:
- POST /interpret: Interpret user queries and extract intents with entities and workflows
- POST /execute: Interpret queries and execute the resulting workflows end-to-end
- GET /intents: List all supported intents and their examples

Responsibilities:
- Process natural language user queries for intent recognition and entity extraction
- Generate structured workflows from interpreted intents for service orchestration
- Support multiple query types including documentation search, analysis, and reporting
- Provide confidence scoring and fallback handling for ambiguous queries
- Integrate with multiple backend services to execute complex multi-step operations

Dependencies: Intent recognizer, workflow builder, shared utilities for NLP processing.
"""

import re
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.responses.responses import create_success_response
from services.shared.core.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import setup_common_middleware, attach_self_register


# ============================================================================
# HANDLER MODULES - Extracted business logic
# ============================================================================
try:
    from .modules.models import UserQuery, InterpretedIntent, InterpretedWorkflow, WorkflowStep
    from .modules.query_handlers import query_handlers
    from .modules.list_handlers import list_handlers
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from modules.models import UserQuery, InterpretedIntent, InterpretedWorkflow, WorkflowStep
    from modules.query_handlers import query_handlers
    from modules.list_handlers import list_handlers

# ============================================================================
# ENHANCED CAPABILITIES - New ecosystem-aware modules
# ============================================================================
from .modules.ecosystem_context import ecosystem_context
from .modules.orchestrator_integration import orchestrator_integration
from .modules.prompt_engineering import prompt_engineer
from .modules.langgraph_discovery import langgraph_discovery

# Service configuration constants
SERVICE_NAME = "interpreter"
SERVICE_TITLE = "Interpreter"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5120

# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware and error handlers
app = FastAPI(
    title=SERVICE_TITLE,
    description="Natural language processing service for user query interpretation and workflow generation",
    version=SERVICE_VERSION
)

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.INTERPRETER)

# Auto-register with orchestrator
attach_self_register(app, ServiceNames.INTERPRETER)

# Register standardized health endpoints
register_health_endpoints(app, ServiceNames.INTERPRETER, SERVICE_VERSION)

# Core components are now initialized in handlers

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/interpret", response_model=InterpretedIntent)
async def interpret_query(query: UserQuery):
    """Interpret user query and return intent with workflow.

    Processes natural language queries to extract intent, entities, and generate
    structured workflows. Includes confidence scoring and fallback handling for
    ambiguous queries with optional session and user context.
    """
    return await query_handlers.handle_interpret_query(query)

@app.post("/execute")
async def execute_workflow(query: UserQuery):
    """Interpret query and execute the resulting workflow.

    Interprets the user query and immediately executes the generated workflow
    across multiple services. Provides end-to-end processing from natural language
    to completed operations with detailed execution results.
    """
    return await query_handlers.handle_execute_workflow(query)



@app.get("/intents")
async def list_supported_intents():
    """List all supported intents and examples.

    Returns comprehensive information about all supported query intents,
    including example queries, entity extraction patterns, and workflow
    generation capabilities for each intent type.
    """
    return await list_handlers.handle_list_supported_intents()


# ============================================================================
# ENHANCED NATURAL LANGUAGE ENDPOINTS - New ecosystem-aware capabilities
# ============================================================================

@app.post("/natural-query")
async def process_natural_query(query: UserQuery):
    """Process natural language query with full ecosystem context.

    This enhanced endpoint provides:
    - Ecosystem-aware intent recognition
    - Context-aware entity extraction
    - Intelligent workflow mapping
    - LangGraph workflow discovery and execution
    - Prompt engineering for query translation

    The interpreter now understands the full LLM Documentation Ecosystem
    and can translate natural language into complex multi-service workflows.
    """
    try:
        # Enhanced interpretation with ecosystem context
        interpretation = await query_handlers.handle_interpret_query(query)

        # Get ecosystem context for the query
        detected_services = interpretation.entities.get("ecosystem_context", {}).get("detected_services", [])
        detected_capabilities = interpretation.entities.get("ecosystem_context", {}).get("detected_capabilities", [])

        # Find matching LangGraph workflows
        langgraph_match = await langgraph_discovery.find_matching_langgraph_workflow(
            query.query, interpretation.intent, interpretation.entities
        )

        # Prepare enhanced response
        enhanced_response = {
            "original_query": query.query,
            "interpretation": interpretation.dict(),
            "ecosystem_context": {
                "detected_services": detected_services,
                "detected_capabilities": detected_capabilities,
                "available_workflows": await langgraph_discovery.get_workflow_suggestions(
                    query.query, interpretation.intent
                )
            },
            "langgraph_workflows": {
                "best_match": langgraph_match,
                "available_count": len(langgraph_discovery.discovered_workflows)
            },
            "processing_metadata": {
                "ecosystem_aware": True,
                "langgraph_enabled": True,
                "prompt_engineered": True
            }
        }

        return create_success_response(
            "Natural language query processed with full ecosystem context",
            enhanced_response
        )

    except Exception as e:
        return create_error_response(
            "Failed to process natural language query",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e), "query": query.query}
        )


@app.post("/execute-natural-workflow")
async def execute_natural_workflow(query: UserQuery):
    """Execute natural language query as a complete workflow.

    This endpoint:
    1. Interprets the natural language query
    2. Maps it to appropriate ecosystem workflows
    3. Executes the workflow through the orchestrator
    4. Returns comprehensive execution results

    Supports both traditional workflows and advanced LangGraph orchestrations.
    """
    try:
        # First, get enhanced interpretation
        interpretation_result = await process_natural_query(query)
        if not interpretation_result["success"]:
            return interpretation_result

        data = interpretation_result["data"]
        interpretation = data["interpretation"]

        # Determine execution strategy
        execution_result = None

        # Try LangGraph workflow first
        langgraph_match = data["langgraph_workflows"]["best_match"]
        if langgraph_match and langgraph_match["match_score"] > 0.7:
            # Execute LangGraph workflow
            workflow_name = langgraph_match["workflow_name"]
            parameters = interpretation.get("entities", {})

            # Validate and execute
            validation = await langgraph_discovery.validate_langgraph_workflow(workflow_name, parameters)
            if validation["valid"]:
                execution_result = await langgraph_discovery.execute_langgraph_workflow(
                    workflow_name, parameters, query.user_id
                )
            else:
                execution_result = {
                    "status": "validation_failed",
                    "validation_errors": validation,
                    "workflow_name": workflow_name
                }
        else:
            # Fallback to traditional workflow execution
            execution_result = await query_handlers.handle_execute_workflow(query)

        # Prepare comprehensive response
        enhanced_result = {
            "query": query.query,
            "interpretation": interpretation,
            "execution_strategy": "langgraph" if langgraph_match else "traditional",
            "execution_result": execution_result,
            "ecosystem_context": data["ecosystem_context"],
            "processing_summary": {
                "total_services_involved": len(data["ecosystem_context"]["detected_services"]),
                "workflows_available": len(data["ecosystem_context"]["available_workflows"]),
                "execution_success": execution_result.get("status") == "success" if execution_result else False
            }
        }

        return create_success_response(
            "Natural workflow execution completed",
            enhanced_result
        )

    except Exception as e:
        return create_error_response(
            "Failed to execute natural workflow",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e), "query": query.query}
        )


@app.get("/ecosystem/capabilities")
async def get_ecosystem_capabilities():
    """Get comprehensive ecosystem capabilities for natural language processing.

    Returns detailed information about:
    - Available services and their capabilities
    - Supported workflows (traditional and LangGraph)
    - Service aliases and terminology
    - Current system status
    """
    try:
        # Get service capabilities
        services = await ecosystem_context.get_service_capabilities()

        # Get available workflows
        traditional_workflows = ecosystem_context.workflow_templates
        langgraph_workflows = await langgraph_discovery.discover_langgraph_workflows()

        # Get orchestrator tools
        orchestrator_tools = await orchestrator_integration.get_orchestrator_tools()

        capabilities_response = {
            "services": services,
            "workflows": {
                "traditional": traditional_workflows,
                "langgraph": langgraph_workflows.get("workflows", {}) if langgraph_workflows.get("status") == "success" else {}
            },
            "tools": orchestrator_tools,
            "terminology": ecosystem_context.project_context.get("terminology", {}),
            "domains": ecosystem_context.project_context.get("domains", []),
            "technologies": ecosystem_context.project_context.get("technologies", []),
            "metadata": {
                "total_services": len(services),
                "traditional_workflows": len(traditional_workflows),
                "langgraph_workflows": langgraph_workflows.get("count", 0) if langgraph_workflows.get("status") == "success" else 0,
                "available_tools": len(orchestrator_tools) if orchestrator_tools else 0,
                "last_updated": "2024-01-01T00:00:00Z"  # Would be dynamic in real implementation
            }
        }

        return create_success_response(
            "Ecosystem capabilities retrieved successfully",
            capabilities_response
        )

    except Exception as e:
        return create_error_response(
            "Failed to retrieve ecosystem capabilities",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )


@app.post("/workflows/discover")
async def discover_workflows():
    """Discover all available workflows in the ecosystem.

    Returns comprehensive information about:
    - Traditional workflows (rule-based)
    - LangGraph workflows (AI-orchestrated)
    - Custom workflows (user-defined)
    - Workflow capabilities and requirements
    """
    try:
        # Discover LangGraph workflows
        langgraph_result = await langgraph_discovery.discover_langgraph_workflows()

        # Get traditional workflows
        traditional_workflows = ecosystem_context.workflow_templates

        # Combine results
        discovery_response = {
            "langgraph_workflows": langgraph_result,
            "traditional_workflows": {
                "workflows": traditional_workflows,
                "count": len(traditional_workflows),
                "status": "success"
            },
            "summary": {
                "total_langgraph_workflows": langgraph_result.get("count", 0) if langgraph_result.get("status") == "success" else 0,
                "total_traditional_workflows": len(traditional_workflows),
                "total_workflows": (langgraph_result.get("count", 0) if langgraph_result.get("status") == "success" else 0) + len(traditional_workflows),
                "discovery_status": "completed"
            }
        }

        return create_success_response(
            "Workflow discovery completed successfully",
            discovery_response
        )

    except Exception as e:
        return create_error_response(
            "Failed to discover workflows",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e)}
        )


@app.post("/prompt/translate")
async def translate_prompt(query: UserQuery):
    """Translate natural language query into structured workflow prompt.

    Uses advanced prompt engineering to:
    1. Understand the natural language query
    2. Map it to ecosystem capabilities
    3. Generate optimized workflow prompts
    4. Provide execution recommendations
    """
    try:
        # Get interpretation
        interpretation = await query_handlers.handle_interpret_query(query)

        # Get ecosystem context
        ecosystem_data = await ecosystem_context.get_service_capabilities()

        # Use prompt engineering to translate
        translation = await prompt_engineer.translate_query_to_workflow(
            query.query,
            interpretation.intent,
            interpretation.entities,
            ecosystem_data
        )

        # Prepare response
        prompt_response = {
            "original_query": query.query,
            "interpretation": interpretation.dict(),
            "translation": translation,
            "execution_recommendations": {
                "suggested_workflow": translation.get("workflow_type"),
                "confidence": translation.get("confidence", 0),
                "services_needed": translation.get("services", []),
                "estimated_complexity": "high" if len(translation.get("services", [])) > 2 else "medium"
            },
            "prompt_metadata": {
                "translation_method": translation.get("translation_method", "unknown"),
                "ecosystem_awareness": True,
                "optimization_applied": True
            }
        }

        return create_success_response(
            "Query translated to workflow prompt successfully",
            prompt_response
        )

    except Exception as e:
        return create_error_response(
            "Failed to translate query to workflow prompt",
            error_code=ErrorCodes.INTERNAL_ERROR,
            details={"error": str(e), "query": query.query}
        )

if __name__ == "__main__":
    """Run the Interpreter service directly."""
    import uvicorn
    print("🚀 Starting Interpreter Service...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
