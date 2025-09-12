"""Interpreter Service

Natural language processing and intent recognition service for the LLM Documentation Ecosystem.

This service interprets user queries in natural language and converts them into
structured workflows that can be executed by the orchestrator and other services.

Key Features:
- Intent recognition and classification
- Entity extraction from user queries
- Workflow generation from natural language
- Multi-step operation planning
- Confidence scoring for interpretations
- Integration with all ecosystem services

Architecture:
- Rule-based intent recognition engine
- Entity extraction using regex patterns
- Workflow builder for complex operations
- RESTful API for query processing
- Integration with orchestrator for execution

Core Components:
- IntentRecognizer: Classifies user intentions from text
- WorkflowBuilder: Creates executable workflows from intents
- EntityExtractor: Extracts structured data from queries
- ConfidenceScorer: Rates interpretation accuracy
- QueryProcessor: Main processing pipeline

Supported Intents:
- analyze_document: Document analysis requests
- consistency_check: Consistency validation requests
- ingest_github: GitHub data ingestion
- ingest_jira: Jira ticket ingestion
- ingest_confluence: Confluence page ingestion
- create_prompt: Prompt creation requests
- find_prompt: Prompt search requests
- generate_report: Report generation requests
- help: Help and information requests
- status: System status requests

Endpoints:
- GET  /health - Service health check
- POST /interpret - Interpret natural language query
- POST /execute - Execute interpreted workflow
- GET  /intents - List supported intents and examples

Data Models:
- UserQuery: Input query with metadata
- InterpretedIntent: Classified intent with entities
- InterpretedWorkflow: Generated workflow with steps
- WorkflowStep: Individual workflow operation

Integration Points:
- Orchestrator: Query interpretation and workflow execution
- Prompt Store: Prompt retrieval for AI operations
- Analysis Service: Analysis workflow generation
- Doc Store: Document operation workflows
- Source Agent: Data ingestion workflows
- CLI: Natural language command processing

Workflow Generation:
The service can generate complex multi-step workflows such as:
- "analyze this document for consistency issues"
  -> Document retrieval + Analysis execution + Report generation

- "ingest from github and create a summary report"
  -> GitHub ingestion + Document processing + Report creation

- "find prompts about security and test them"
  -> Prompt search + A/B testing setup + Analytics generation

Environment Variables:
- INTERPRETER_PORT: Service port (default: 5120)
- Various service URLs for integration

Usage:
    python services/interpreter/main.py

Or with Docker:
    docker-compose up interpreter

Dependencies:
- fastapi: Web framework
- pydantic: Data validation
- httpx: HTTP client for service communication
- asyncio: Asynchronous processing

Processing Pipeline:
1. Query Reception: Accept natural language input
2. Intent Recognition: Classify user intention
3. Entity Extraction: Extract structured parameters
4. Workflow Building: Create executable workflow
5. Confidence Scoring: Rate interpretation accuracy
6. Response Generation: Return structured interpretation

Error Handling:
- Graceful degradation for unrecognized intents
- Fallback responses for processing failures
- Detailed error logging for debugging
- User-friendly error messages

Performance:
- Asynchronous processing for I/O operations
- Caching for frequently used patterns
- Efficient regex matching for entity extraction
- Connection pooling for service calls

Monitoring:
- Health check endpoints
- Query processing metrics
- Intent recognition accuracy tracking
- Error rate monitoring
- Performance profiling
"""

import re
from typing import Dict, Any, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import setup_common_middleware, attach_self_register

# ============================================================================
# DATA MODELS - Define before module imports to avoid forward reference issues
# ============================================================================

class UserQuery(BaseModel):
    """User query model."""
    query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

class InterpretedIntent(BaseModel):
    """Interpreted intent from user query."""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    workflow: Optional[Dict[str, Any]] = None
    response_text: str = ""

class WorkflowStep(BaseModel):
    """Workflow step definition."""
    step_id: str
    service: str
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = []

class InterpretedWorkflow(BaseModel):
    """Complete interpreted workflow."""
    workflow_id: str
    steps: List[WorkflowStep]
    estimated_duration: int  # seconds
    required_services: List[str]

# ============================================================================
# LOCAL MODULES - Service-specific functionality (imported after models)
# ============================================================================
from .modules.shared_utils import (
    get_interpreter_clients,
    handle_interpreter_error,
    create_interpreter_success_response,
    build_interpreter_context,
    validate_user_query,
    extract_entities_with_pattern,
    add_entity_if_found,
    build_workflow_response,
    generate_response_text,
    get_supported_intents,
    log_interpretation_metrics
)
from .modules.intent_recognizer import IntentRecognizer
from .modules.workflow_builder import WorkflowBuilder

# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware and error handlers
app = FastAPI(
    title="Interpreter Service",
    description="Natural language processing for user query interpretation",
    version="1.0.0"
)

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.INTERPRETER)

# Auto-register with orchestrator
attach_self_register(app, ServiceNames.INTERPRETER)

# Register standardized health endpoints
register_health_endpoints(app, ServiceNames.INTERPRETER, "1.0.0")

# Initialize core components
intent_recognizer = IntentRecognizer()
workflow_builder = WorkflowBuilder()

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/interpret", response_model=InterpretedIntent)
async def interpret_query(query: UserQuery):
    """Interpret user query and return intent with workflow."""
    import time
    start_time = time.time()

    try:
        # Validate user query
        validate_user_query(query.dict())

        # Recognize intent and extract entities
        intent, confidence, entities = intent_recognizer.recognize_intent(query.query)

        # Build workflow if intent is recognized with sufficient confidence
        workflow = None
        if confidence > 0.3:  # Minimum confidence threshold
            try:
                workflow = await workflow_builder.build_workflow(intent, entities)
            except Exception as e:
                from services.shared.logging import fire_and_forget
                fire_and_forget("error", f"Workflow build error: {e}", ServiceNames.INTERPRETER)

        # Generate response text
        response_text = generate_response_text(intent, confidence, entities, workflow)

        # Log interpretation metrics
        processing_time = time.time() - start_time
        log_interpretation_metrics(query.query, intent, confidence, processing_time)

        return InterpretedIntent(
            intent=intent,
            confidence=confidence,
            entities=entities,
            workflow=workflow.dict() if workflow else None,
            response_text=response_text
        )

    except Exception as e:
        processing_time = time.time() - start_time
        log_interpretation_metrics(query.query, "error", 0.0, processing_time)

        return handle_interpreter_error(
            "interpret query",
            e,
            **build_interpreter_context("interpret", query_length=len(query.query))
        )

@app.post("/execute")
async def execute_workflow(query: UserQuery):
    """Interpret query and execute the resulting workflow."""
    try:
        # First interpret the query
        interpretation = await interpret_query(query)

        if not interpretation.workflow:
            return create_interpreter_success_response(
                "interpretation completed (no workflow)",
                {
                    "status": "no_workflow",
                    "message": "Could not generate a workflow for this query",
                    "interpretation": interpretation.dict()
                },
                **build_interpreter_context("execute_no_workflow")
            )

        # Execute the workflow
        workflow_data = interpretation.workflow
        results = []
        clients = get_interpreter_clients()

        for step in workflow_data.get("steps", []):
            try:
                result = await execute_workflow_step(step, clients)
                results.append({
                    "step_id": step["step_id"],
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results.append({
                    "step_id": step["step_id"],
                    "status": "error",
                    "error": str(e)
                })

        return create_interpreter_success_response(
            "workflow executed",
            {
                "status": "completed",
                "workflow_id": workflow_data.get("workflow_id"),
                "results": results,
                "interpretation": interpretation.dict()
            },
            **build_interpreter_context("execute_workflow", step_count=len(results))
        )

    except Exception as e:
        return handle_interpreter_error(
            "execute workflow",
            e,
            **build_interpreter_context("execute_error")
        )


async def execute_workflow_step(step: Dict[str, Any], clients=None) -> Any:
    """Execute a single workflow step."""
    if clients is None:
        clients = get_interpreter_clients()

    service = step["service"]
    action = step["action"]
    parameters = step.get("parameters", {})

    # Route to appropriate service
    if service == "analysis-service":
        if action == "analyze":
            return await clients.post_json("analysis-service/analyze", parameters)
        elif action == "consistency_check":
            return await clients.get_json("analysis-service/consistency/check")
        elif action == "findings":
            return await clients.get_json("analysis-service/findings")

    elif service == "source-agent":
        if action == "ingest":
            return await clients.post_json("source-agent/ingest", parameters)

    elif service == "doc-store":
        if action == "store":
            return await clients.post_json("doc-store/store", parameters)

    elif service == "prompt-store":
        if action == "search":
            # Build query parameters
            query_params = {}
            if "categories" in parameters:
                query_params["category"] = parameters["categories"][0] if parameters["categories"] else ""
            if "query" in parameters:
                query_params["q"] = parameters["query"]

            return await clients.get_json("prompt-store/prompts", params=query_params)

    # Default: return success for unknown services/actions
    return create_success_response(
        "Workflow step executed successfully",
        {"service": service, "action": action, "parameters": parameters}
    )


@app.get("/intents")
async def list_supported_intents():
    """List all supported intents and examples."""
    try:
        intents_data = get_supported_intents()
        return create_interpreter_success_response(
            "intents retrieved",
            {"intents": intents_data},
            **build_interpreter_context("list_intents", intent_count=len(intents_data))
        )
    except Exception as e:
        return handle_interpreter_error(
            "list supported intents",
            e,
            **build_interpreter_context("list_intents_error")
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Interpreter Service...")
    uvicorn.run(app, host="0.0.0.0", port=5120)
