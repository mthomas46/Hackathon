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
# ENHANCED CAPABILITIES - Ecosystem-aware modules with orchestrator integration
# ============================================================================
try:
    from .modules.ecosystem_context import ecosystem_context
    from .modules.orchestrator_integration import orchestrator_integration
    from .modules.workflow_dispatcher import workflow_dispatcher
    from .modules.conversation_memory import conversation_memory
    from .modules.query_preprocessor import query_preprocessor
    from .modules.workflow_execution_engine import workflow_execution_engine
    from .modules.output_generator import output_generator
except ImportError:
    # Enhanced modules for ecosystem integration
    from modules.ecosystem_context import ecosystem_context
    from modules.orchestrator_integration import orchestrator_integration
    from modules.workflow_dispatcher import workflow_dispatcher
    from modules.conversation_memory import conversation_memory
    from modules.query_preprocessor import query_preprocessor
    from modules.workflow_execution_engine import workflow_execution_engine
    from modules.output_generator import output_generator
    from modules.prompt_engineering import prompt_engineer
    from modules.langgraph_discovery import langgraph_discovery

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


# ============================================================================
# ENHANCED ECOSYSTEM INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/natural-query")
async def process_natural_query(query_data: UserQuery):
    """Enhanced natural language query processing with ecosystem context.
    
    This endpoint provides comprehensive natural language processing with:
    - Advanced query preprocessing and normalization
    - Ecosystem-aware intent recognition  
    - Intelligent workflow dispatch
    - Conversation memory integration
    - Real-time workflow execution
    """
    try:
        # Preprocess query for enhanced understanding
        preprocessing_result = await query_preprocessor.preprocess_query(
            query_data.query, query_data.user_id, query_data.context
        )
        
        # Enhanced intent recognition with ecosystem context
        intent_result = await query_handlers.handle_query_interpretation(query_data)
        
        # Dispatch to appropriate workflow with orchestrator integration
        dispatch_result = await workflow_dispatcher.dispatch_query(
            preprocessing_result["processed_query"],
            intent_result.intent,
            intent_result.entities,
            query_data.user_id,
            query_data.context
        )
        
        return create_success_response({
            "original_query": query_data.query,
            "preprocessing": preprocessing_result,
            "interpretation": {
                "intent": intent_result.intent,
                "confidence": intent_result.confidence,
                "entities": intent_result.entities
            },
            "workflow_dispatch": dispatch_result,
            "ecosystem_context": await ecosystem_context.get_service_capabilities(),
            "processing_timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        return create_success_response({
            "error": str(e),
            "fallback_response": "I encountered an issue processing your query. Please try rephrasing or contact support.",
            "suggestions": [
                "Try using simpler language",
                "Be more specific about what you want to accomplish",
                "Mention which service you'd like to use"
            ]
        })


@app.post("/execute-workflow")
async def execute_workflow_endpoint(execution_request: dict):
    """Execute a workflow through the enhanced execution engine."""
    try:
        user_id = execution_request.get("user_id")
        execution_plan = execution_request.get("execution_plan", {})
        priority = execution_request.get("priority", "normal")
        
        # Execute workflow through enhanced execution engine
        execution_result = await workflow_execution_engine.execute_workflow(
            execution_plan, user_id, None, priority
        )
        
        return create_success_response({
            "execution_result": execution_result,
            "execution_metadata": {
                "engine_version": "2.0",
                "orchestrator_integrated": True,
                "monitoring_enabled": True
            }
        })
        
    except Exception as e:
        return create_success_response({
            "error": str(e),
            "execution_status": "failed",
            "recovery_suggestions": [
                "Check that all required parameters are provided",
                "Verify service availability",
                "Try again with simplified parameters"
            ]
        })


@app.get("/ecosystem/capabilities")
async def get_ecosystem_capabilities():
    """Get comprehensive ecosystem capabilities and service information."""
    try:
        capabilities = await ecosystem_context.get_service_capabilities()
        workflows = workflow_dispatcher.get_all_workflows()
        
        return create_success_response({
            "services": capabilities,
            "workflows": workflows,
            "total_services": len(capabilities),
            "total_workflows": workflows["total_count"],
            "workflow_categories": workflows["categories"],
            "ecosystem_status": "active",
            "last_updated": datetime.utcnow().isoformat(),
            "metadata": {
                "discovery_agent_integrated": True,
                "orchestrator_connected": True,
                "conversation_memory_enabled": True,
                "langgraph_workflows_available": True
            }
        })
        
    except Exception as e:
        return create_success_response({
            "error": str(e),
            "fallback_capabilities": {
                "basic_interpretation": True,
                "workflow_execution": True,
                "error_handling": True
            }
        })


@app.post("/workflows/discover")
async def discover_workflows():
    """Discover available workflows from orchestrator and LangGraph integration."""
    try:
        # Discover traditional workflows
        traditional_workflows = await orchestrator_integration.discover_available_workflows()
        
        # Discover LangGraph workflows
        langgraph_workflows = await langgraph_discovery.discover_langgraph_workflows()
        
        # Get workflow dispatcher information
        dispatcher_workflows = workflow_dispatcher.get_all_workflows()
        
        return create_success_response({
            "traditional_workflows": traditional_workflows,
            "langgraph_workflows": langgraph_workflows,
            "dispatcher_workflows": dispatcher_workflows,
            "total_discovered": (
                len(traditional_workflows.get("workflows", {})) +
                len(langgraph_workflows.get("workflows", {})) +
                dispatcher_workflows["total_count"]
            ),
            "discovery_timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "orchestrator_integrated": True,
                "langgraph_enabled": True,
                "intelligent_dispatch": True
            }
        })
        
    except Exception as e:
        return create_success_response({
            "error": str(e),
            "fallback_workflows": workflow_dispatcher.get_all_workflows()
        })


@app.get("/execution/{execution_id}/status")
async def get_execution_status(execution_id: str):
    """Get real-time status of workflow execution."""
    try:
        status = await workflow_execution_engine.get_execution_status(execution_id)
        return create_success_response(status)
        
    except Exception as e:
        return create_success_response({
            "error": str(e),
            "execution_id": execution_id,
            "status": "error"
        })


@app.get("/health/ecosystem")
async def get_ecosystem_health():
    """Get comprehensive health status of the entire ecosystem."""
    try:
        # Check orchestrator health
        orchestrator_health = await orchestrator_integration.check_orchestrator_health()

        # Check service capabilities
        service_capabilities = await ecosystem_context.get_service_capabilities()

        # Get execution engine status
        execution_metrics = await workflow_execution_engine.get_execution_metrics()

        # Calculate overall health score
        health_score = 1.0
        if not orchestrator_health.get("healthy", False):
            health_score -= 0.4
        if len(service_capabilities) < 5:  # Expect at least 5 services
            health_score -= 0.3
        if execution_metrics["success_rate"] < 0.8:
            health_score -= 0.3

        health_status = "healthy" if health_score > 0.7 else "degraded" if health_score > 0.4 else "unhealthy"

        return create_success_response({
            "ecosystem_health": {
                "overall_status": health_status,
                "health_score": max(health_score, 0.0),
                "orchestrator_health": orchestrator_health,
                "services_available": len(service_capabilities),
                "execution_success_rate": execution_metrics["success_rate"],
                "active_executions": execution_metrics["active_executions"]
            },
            "component_status": {
                "interpreter": "healthy",
                "orchestrator": "connected" if orchestrator_health.get("healthy") else "disconnected",
                "workflow_dispatcher": "operational",
                "conversation_memory": "active",
                "execution_engine": "operational"
            },
            "health_check_timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        return create_success_response({
            "ecosystem_health": {
                "overall_status": "error",
                "health_score": 0.0,
                "error": str(e)
            },
            "component_status": {
                "interpreter": "healthy",
                "error_details": str(e)
            }
        })


# ============================================================================
# END-TO-END WORKFLOW EXECUTION ENDPOINTS
# ============================================================================

@app.post("/execute-query")
async def execute_query_endpoint(request: dict):
    """Complete end-to-end query execution: Natural language → Workflow → Output."""
    try:
        query = request.get("query", "")
        user_id = request.get("user_id", "anonymous")
        output_format = request.get("output_format", "json")
        filename_prefix = request.get("filename_prefix")

        if not query:
            return create_success_response({
                "error": "Query is required",
                "status": "failed"
            })

        # Step 1: Process natural language query
        query_data = UserQuery(
            query=query,
            user_id=user_id,
            context=request.get("context", {})
        )

        preprocessing_result = await query_preprocessor.preprocess_query(
            query_data.query, query_data.user_id, query_data.context
        )

        intent_result = await query_handlers.handle_query_interpretation(query_data)

        # Step 2: Dispatch to appropriate workflow
        dispatch_result = await workflow_dispatcher.dispatch_query(
            preprocessing_result["processed_query"],
            intent_result.intent,
            intent_result.entities,
            query_data.user_id,
            query_data.context
        )

        # Step 3: Execute workflow through orchestrator
        if dispatch_result.get("workflow_name"):
            workflow_result = await orchestrator_integration.execute_workflow(
                dispatch_result["workflow_name"],
                dispatch_result.get("parameters", {}),
                user_id,
                output_format
            )

            # Step 4: Generate output file
            if workflow_result.get("status") == "completed":
                output_info = await output_generator.generate_output(
                    workflow_result,
                    output_format,
                    filename_prefix
                )

                # Step 5: Update conversation memory
                await conversation_memory.update_conversation(
                    user_id, query, dispatch_result["workflow_name"], workflow_result
                )

                return create_success_response({
                    "execution_id": workflow_result["execution_id"],
                    "query": query,
                    "workflow_executed": dispatch_result["workflow_name"],
                    "status": "completed",
                    "output": output_info,
                    "workflow_result": workflow_result,
                    "processing_pipeline": {
                        "preprocessing": preprocessing_result,
                        "intent_recognition": {
                            "intent": intent_result.intent,
                            "confidence": intent_result.confidence,
                            "entities": intent_result.entities
                        },
                        "workflow_dispatch": dispatch_result
                    }
                })
            else:
                return create_success_response({
                    "execution_id": workflow_result.get("execution_id"),
                    "query": query,
                    "status": "failed", 
                    "error": workflow_result.get("error", "Workflow execution failed"),
                    "workflow_attempted": dispatch_result["workflow_name"]
                })
        else:
            return create_success_response({
                "query": query,
                "status": "no_workflow",
                "message": "Could not determine appropriate workflow for query",
                "suggestions": dispatch_result.get("suggestions", [])
            })

    except Exception as e:
        return create_success_response({
            "query": request.get("query", ""),
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })


@app.post("/workflows/execute-direct")
async def execute_workflow_direct(request: dict):
    """Direct workflow execution with output generation."""
    try:
        workflow_name = request.get("workflow_name")
        parameters = request.get("parameters", {})
        user_id = request.get("user_id", "anonymous")
        output_format = request.get("output_format", "json")
        filename_prefix = request.get("filename_prefix")

        if not workflow_name:
            return create_success_response({
                "error": "workflow_name is required",
                "status": "failed"
            })

        # Execute workflow
        workflow_result = await orchestrator_integration.execute_workflow(
            workflow_name, parameters, user_id, output_format
        )

        # Generate output if successful
        if workflow_result.get("status") == "completed":
            output_info = await output_generator.generate_output(
                workflow_result, output_format, filename_prefix
            )

            return create_success_response({
                "execution_id": workflow_result["execution_id"],
                "workflow_name": workflow_name,
                "status": "completed",
                "output": output_info,
                "workflow_result": workflow_result
            })
        else:
            return create_success_response({
                "execution_id": workflow_result.get("execution_id"),
                "workflow_name": workflow_name,
                "status": "failed",
                "error": workflow_result.get("error", "Workflow execution failed")
            })

    except Exception as e:
        return create_success_response({
            "workflow_name": request.get("workflow_name"),
            "status": "error",
            "error": str(e)
        })


@app.get("/outputs/download/{file_id}")
async def download_output_file(file_id: str):
    """Download generated output file."""
    try:
        from fastapi.responses import FileResponse
        
        file_info = await output_generator.get_file_info(file_id)
        
        if not file_info:
            return create_success_response({
                "error": "File not found",
                "file_id": file_id
            })

        return FileResponse(
            path=file_info["filepath"],
            filename=file_info["filename"],
            media_type="application/octet-stream"
        )

    except Exception as e:
        return create_success_response({
            "error": str(e),
            "file_id": file_id
        })


@app.get("/outputs/formats")
async def get_supported_formats():
    """Get list of supported output formats."""
    return create_success_response({
        "supported_formats": output_generator.get_supported_formats(),
        "format_descriptions": {
            "json": "Structured JSON data with complete results",
            "pdf": "Formatted PDF report with visualizations",
            "csv": "Comma-separated values for data analysis",
            "markdown": "Markdown formatted documentation",
            "zip": "Archive containing multiple format variants",
            "txt": "Plain text summary report"
        }
    })


@app.get("/workflows/templates")
async def get_workflow_templates():
    """Get available workflow templates."""
    return create_success_response({
        "templates": orchestrator_integration.get_workflow_templates(),
        "total_templates": len(orchestrator_integration.get_workflow_templates())
    })


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
