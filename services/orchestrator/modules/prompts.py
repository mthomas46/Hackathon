"""Prompt management functionality for the Orchestrator service.

This module contains all prompt-related endpoints and operations,
extracted from the main orchestrator service to improve maintainability.
"""

from typing import Dict, Any, Optional, List

from .shared_utils import (
    get_orchestrator_service_client,
    get_service_url,
    handle_service_error,
    create_service_success_response,
    build_orchestrator_context
)


# Helper functions removed - using shared utilities from shared_utils.py


async def get_prompt(category: str, name: str, **variables) -> Dict[str, Any]:
    """Get a prompt from Prompt Store with variable substitution."""
    try:
        service_client = get_orchestrator_service_client()
        result = await service_client.get_prompt(category, name, **variables)
        context = build_orchestrator_context("prompt_retrieval", category=category, name=name, variables_count=len(variables))
        return create_service_success_response("prompt retrieval", result, **context)
    except Exception as e:
        context = build_orchestrator_context("prompt_retrieval", category=category, name=name)
        return handle_service_error("retrieve prompt", e, **context)


async def list_prompt_categories() -> Dict[str, Any]:
    """Get available prompt categories with standardized processing."""
    try:
        service_client = get_orchestrator_service_client()

        # Use centralized URL resolution and improved error handling
        prompt_store_url = get_service_url("prompt_store", "http://prompt-store:5020")
        response = await service_client.get_json(f"{prompt_store_url}/prompts?limit=100")
        prompts = response.get("prompts", [])

        # Extract and deduplicate categories with better filtering
        categories = sorted(list(set(
            p.get("category", "").strip()
            for p in prompts
            if p.get("category", "").strip()
        )))

        category_data = {
            "categories": categories,
            "count": len(categories),
            "prompts_sampled": len(prompts)
        }

        context = build_orchestrator_context("categories_listing", categories_count=len(categories), prompts_sampled=len(prompts))
        return create_service_success_response("categories listing", category_data, **context)
    except Exception as e:
        context = build_orchestrator_context("categories_listing")
        return handle_service_error("list categories", e, **context)


async def log_prompt_usage(
    prompt_id: str,
    service_name: str = "orchestrator",
    input_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    response_time_ms: Optional[float] = None,
    success: bool = True
) -> Dict[str, Any]:
    """Log prompt usage for analytics with standardized error handling."""
    try:
        service_client = get_orchestrator_service_client()

        # Enhanced logging with comprehensive usage data
        usage_data = {
            "prompt_id": prompt_id,
            "service_name": service_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "response_time_ms": response_time_ms,
            "success": success,
            "timestamp": None  # Will be set by the service
        }

        await service_client.log_prompt_usage(**usage_data)

        # Return success response with logged data summary
        context = build_orchestrator_context("usage_logging", prompt_id=prompt_id, service_name=service_name, success=success)
        return create_service_success_response(
            "usage logging",
            {"status": "logged", "usage_data": usage_data},
            **context
        )
    except Exception as e:
        context = build_orchestrator_context("usage_logging", prompt_id=prompt_id, service_name=service_name)
        return handle_service_error("log usage", e, **context)
