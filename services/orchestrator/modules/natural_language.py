"""Natural language processing functionality for the Orchestrator service.

This module contains all natural language query processing and execution,
extracted from the main orchestrator service to improve maintainability.
"""

from fastapi import Request
from pydantic import BaseModel
from typing import Dict, Any, Optional

from .shared_utils import (
    get_orchestrator_service_client,
    handle_service_error,
    create_service_success_response,
    build_orchestrator_context
)


class NaturalLanguageQuery(BaseModel):
    """Natural language query model."""
    query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


# Helper functions removed - using shared utilities from shared_utils.py


async def natural_language_query(req: NaturalLanguageQuery):
    """Process natural language queries through the Interpreter service with standardized patterns."""
    try:
        service_client = get_orchestrator_service_client()

        # Send query to Interpreter service
        interpretation = await service_client.interpret_query(req.query, req.user_id)

        # Create standardized response with execution capability assessment
        result = {
            "interpretation": interpretation,
            "can_execute": "workflow" in interpretation and interpretation["workflow"] is not None,
            "query": req.query,
            "user_id": req.user_id
        }

        context = build_orchestrator_context("query_processing", query=req.query, user_id=req.user_id)
        return create_service_success_response("query processing", result, **context)

    except Exception as e:
        context = build_orchestrator_context("query_processing", query=req.query, user_id=req.user_id)
        return handle_service_error("process query", e, **context)


async def execute_natural_language_query(req: NaturalLanguageQuery):
    """Execute natural language query through the Interpreter service with standardized patterns."""
    try:
        service_client = get_orchestrator_service_client()

        # Execute query through Interpreter service
        result = await service_client.execute_workflow(req.query, req.user_id)

        # Enhance result with execution metadata
        enhanced_result = result.copy()
        enhanced_result.update({
            "query": req.query,
            "user_id": req.user_id,
            "execution_timestamp": None  # Would be set by calling service
        })

        context = build_orchestrator_context("query_execution", query=req.query, user_id=req.user_id)
        return create_service_success_response("query execution", enhanced_result, **context)

    except Exception as e:
        context = build_orchestrator_context("query_execution", query=req.query, user_id=req.user_id)
        return handle_service_error("execute query", e, **context)
