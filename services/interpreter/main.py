"""Interpreter Service

Natural language processing and intent recognition service for the LLM Documentation Ecosystem.
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
# HANDLER MODULES - Extracted business logic
# ============================================================================
from .modules.models import UserQuery, InterpretedIntent, InterpretedWorkflow, WorkflowStep
from .modules.query_handlers import query_handlers
from .modules.list_handlers import list_handlers

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

# Core components are now initialized in handlers

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/interpret", response_model=InterpretedIntent)
async def interpret_query(query: UserQuery):
    """Interpret user query and return intent with workflow."""
    return await query_handlers.handle_interpret_query(query)

@app.post("/execute")
async def execute_workflow(query: UserQuery):
    """Interpret query and execute the resulting workflow."""
    return await query_handlers.handle_execute_workflow(query)



@app.get("/intents")
async def list_supported_intents():
    """List all supported intents and examples."""
    return await list_handlers.handle_list_supported_intents()

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Interpreter Service...")
    uvicorn.run(app, host="0.0.0.0", port=5120)
