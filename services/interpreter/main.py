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
