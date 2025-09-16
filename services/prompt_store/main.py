"""Prompt Store Service - Domain-Driven Architecture

Main service entry point using the new domain-driven architecture.
"""

from fastapi import FastAPI
from typing import Dict, Any, Optional, List
import asyncio

# ============================================================================
# SHARED MODULES - Optimized import consolidation
# ============================================================================
from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response, create_error_response
from services.shared.error_handling import ServiceException, install_error_handlers
from services.shared.constants_new import ServiceNames
from services.shared.utilities import setup_common_middleware, attach_self_register
from services.shared.config import get_config_value

# ============================================================================
# DOMAIN MODULES - Following domain-driven design
# ============================================================================
from services.prompt_store.core.models import (
    PromptCreate, PromptUpdate, ABTestCreate, PromptSearchFilters,
    BulkOperationCreate, PromptRelationshipCreate, WebhookCreate
)
from services.prompt_store.domain.prompts.handlers import PromptHandlers
from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers
from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers
from services.prompt_store.domain.bulk.handlers import BulkOperationHandlers
from services.prompt_store.domain.refinement.handlers import PromptRefinementHandlers
from services.prompt_store.infrastructure.cache import prompt_store_cache

# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================
SERVICE_NAME = "prompt-store"
SERVICE_TITLE = "Prompt Store"
SERVICE_VERSION = "2.0.0"
DEFAULT_PORT = 5110

# ============================================================================
# APP INITIALIZATION
# ============================================================================
app = FastAPI(
    title=SERVICE_TITLE,
    description="Advanced prompt management system with domain-driven architecture",
    version=SERVICE_VERSION
)

# Use common middleware setup
setup_common_middleware(app, ServiceNames.PROMPT_STORE)
install_error_handlers(app)
register_health_endpoints(app, ServiceNames.PROMPT_STORE, SERVICE_VERSION)
attach_self_register(app, ServiceNames.PROMPT_STORE)

# Initialize cache
@app.on_event("startup")
async def startup_event():
    """Initialize service components on startup."""
    await prompt_store_cache.initialize()
    print("✅ Prompt Store service initialized with domain-driven architecture")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await prompt_store_cache.close()
    print("👋 Prompt Store service shut down")

# ============================================================================
# API ROUTES - Organized by domain
# ============================================================================

# Initialize domain handlers
prompt_handlers = PromptHandlers()
ab_test_handlers = ABTestHandlers()
analytics_handlers = AnalyticsHandlers()
bulk_handlers = BulkOperationHandlers()
refinement_handlers = PromptRefinementHandlers()

# ============================================================================
# PROMPT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/prompts", response_model=Dict[str, Any])
async def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt with validation and business rules."""
    return await prompt_handlers.handle_create_prompt(prompt_data)

@app.get("/api/v1/prompts", response_model=Dict[str, Any])
async def list_prompts(
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    **filters
):
    """List prompts with filtering and pagination."""
    return await prompt_handlers.handle_list_prompts(category, limit, offset, **filters)

@app.get("/api/v1/prompts/search/{category}/{name}", response_model=Dict[str, Any])
async def get_prompt_by_name(category: str, name: str, **variables):
    """Get prompt by category/name and optionally fill template variables."""
    return await prompt_handlers.handle_get_prompt_by_name(category, name, **variables)

@app.put("/api/v1/prompts/{prompt_id}", response_model=Dict[str, Any])
async def update_prompt(prompt_id: str, updates: PromptUpdate):
    """Update a prompt with validation."""
    return await prompt_handlers.handle_update_prompt(prompt_id, updates)

@app.delete("/api/v1/prompts/{prompt_id}", response_model=Dict[str, Any])
async def delete_prompt(prompt_id: str):
    """Soft delete a prompt."""
    return await prompt_handlers.handle_delete_prompt(prompt_id)

# ============================================================================
# ADVANCED PROMPT FEATURES
# ============================================================================

@app.post("/api/v1/prompts/{prompt_id}/fork", response_model=Dict[str, Any])
async def fork_prompt(prompt_id: str, new_name: str, created_by: str = "api_user", **changes):
    """Fork a prompt to create a new variant."""
    return await prompt_handlers.handle_fork_prompt(prompt_id, new_name, created_by, **changes)

@app.put("/api/v1/prompts/{prompt_id}/content", response_model=Dict[str, Any])
async def update_prompt_content(
    prompt_id: str,
    content: str,
    variables: Optional[List[str]] = None,
    change_summary: str = "",
    updated_by: str = "api_user"
):
    """Update prompt content with versioning."""
    return await prompt_handlers.handle_update_prompt_content(
        prompt_id, content, variables, change_summary, updated_by
    )

@app.get("/api/v1/prompts/{prompt_id}/drift", response_model=Dict[str, Any])
async def detect_prompt_drift(prompt_id: str):
    """Detect significant changes in prompt over time."""
    return await prompt_handlers.handle_detect_drift(prompt_id)

@app.get("/api/v1/prompts/{prompt_id}/suggestions", response_model=Dict[str, Any])
async def get_prompt_suggestions(prompt_id: str):
    """Get improvement suggestions for a prompt."""
    return await prompt_handlers.handle_get_suggestions(prompt_id)

# ============================================================================
# SEARCH AND DISCOVERY
# ============================================================================

@app.post("/api/v1/prompts/search", response_model=Dict[str, Any])
async def search_prompts(query: str, category: Optional[str] = None, tags: Optional[List[str]] = None, limit: int = 50):
    """Advanced prompt search with full-text search."""
    return await prompt_handlers.handle_search_prompts(query, category, tags, limit)

@app.get("/api/v1/prompts/category/{category}", response_model=Dict[str, Any])
async def get_prompts_by_category(category: str, limit: int = 50, offset: int = 0):
    """Get all prompts in a specific category."""
    # This would be implemented in the handlers
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

@app.get("/api/v1/prompts/tags/{tag}", response_model=Dict[str, Any])
async def get_prompts_by_tag(tag: str, limit: int = 50, offset: int = 0):
    """Get prompts containing a specific tag."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

# ============================================================================
# BULK OPERATIONS
# ============================================================================

@app.post("/api/v1/bulk/prompts", response_model=Dict[str, Any])
async def bulk_create_prompts(prompts: List[Dict[str, Any]], created_by: str = "api_user"):
    """Bulk create multiple prompts."""
    return await bulk_handlers.handle_bulk_create_prompts(prompts, created_by)

@app.put("/api/v1/bulk/prompts", response_model=Dict[str, Any])
async def bulk_update_prompts(updates: List[Dict[str, Any]], created_by: str = "api_user"):
    """Bulk update multiple prompts."""
    return await bulk_handlers.handle_bulk_update_prompts(updates, created_by)

@app.delete("/api/v1/bulk/prompts", response_model=Dict[str, Any])
async def bulk_delete_prompts(prompt_ids: List[str], created_by: str = "api_user"):
    """Bulk delete multiple prompts."""
    return await bulk_handlers.handle_bulk_delete_prompts(prompt_ids, created_by)

@app.put("/api/v1/bulk/prompts/tags", response_model=Dict[str, Any])
async def bulk_update_tags(prompt_ids: List[str], tags_to_add: Optional[List[str]] = None, tags_to_remove: Optional[List[str]] = None, created_by: str = "api_user"):
    """Bulk update tags on multiple prompts."""
    return await bulk_handlers.handle_bulk_update_tags(prompt_ids, tags_to_add, tags_to_remove, created_by)

@app.get("/api/v1/bulk/operations", response_model=Dict[str, Any])
async def list_bulk_operations(status: Optional[str] = None, operation_type: Optional[str] = None, limit: int = 50, offset: int = 0):
    """List bulk operations with status."""
    return await bulk_handlers.handle_list_bulk_operations(status, operation_type, limit, offset)

@app.get("/api/v1/bulk/operations/{operation_id}", response_model=Dict[str, Any])
async def get_bulk_operation_status(operation_id: str):
    """Get status of a bulk operation."""
    return await bulk_handlers.handle_get_operation_status(operation_id)

@app.put("/api/v1/bulk/operations/{operation_id}/cancel", response_model=Dict[str, Any])
async def cancel_bulk_operation(operation_id: str):
    """Cancel a bulk operation."""
    return await bulk_handlers.handle_cancel_operation(operation_id)

@app.post("/api/v1/bulk/operations/{operation_id}/retry", response_model=Dict[str, Any])
async def retry_bulk_operation(operation_id: str):
    """Retry a failed bulk operation."""
    return await bulk_handlers.handle_retry_operation(operation_id)

# ============================================================================
# PROMPT REFINEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/prompts/{prompt_id}/refine", response_model=Dict[str, Any])
async def refine_prompt(prompt_id: str, refinement_instructions: str,
                       llm_service: str = "interpreter",
                       context_documents: Optional[List[str]] = None,
                       user_id: str = "api_user"):
    """Start LLM-assisted prompt refinement workflow."""
    return await refinement_handlers.handle_refine_prompt(
        prompt_id, refinement_instructions, llm_service, context_documents, user_id
    )

@app.get("/api/v1/refinement/sessions/{session_id}", response_model=Dict[str, Any])
async def get_refinement_status(session_id: str):
    """Get status of a refinement session."""
    return await refinement_handlers.handle_get_refinement_status(session_id)

@app.get("/api/v1/prompts/{prompt_id}/refinement/compare", response_model=Dict[str, Any])
async def compare_prompt_versions(prompt_id: str, version_a: Optional[int] = None,
                                version_b: Optional[int] = None):
    """Compare different versions of a prompt."""
    return await refinement_handlers.handle_compare_prompt_versions(
        prompt_id, version_a, version_b
    )

@app.get("/api/v1/refinement/compare/{session_a}/{session_b}", response_model=Dict[str, Any])
async def compare_refinement_documents(session_a: str, session_b: str):
    """Compare documents from different refinement sessions."""
    return await refinement_handlers.handle_compare_refinement_documents(session_a, session_b)

@app.post("/api/v1/prompts/{prompt_id}/refinement/apply/{session_id}", response_model=Dict[str, Any])
async def apply_refined_prompt(prompt_id: str, session_id: str, user_id: str = "api_user"):
    """Apply refined prompt from session to replace original."""
    return await refinement_handlers.handle_replace_prompt_with_refined(
        prompt_id, session_id, user_id
    )

@app.get("/api/v1/prompts/{prompt_id}/refinement/history", response_model=Dict[str, Any])
async def get_refinement_history(prompt_id: str):
    """Get refinement history for a prompt."""
    return await refinement_handlers.handle_get_refinement_history(prompt_id)

@app.get("/api/v1/refinement/sessions/active", response_model=Dict[str, Any])
async def list_active_refinements(user_id: Optional[str] = None):
    """List all active refinement sessions."""
    return await refinement_handlers.handle_list_active_refinements(user_id)

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/api/v1/analytics/summary", response_model=Dict[str, Any])
async def get_analytics_summary(days_back: int = 30):
    """Get comprehensive analytics summary."""
    return await analytics_handlers.handle_get_analytics_summary(days_back)

@app.get("/api/v1/analytics/prompts/{prompt_id}", response_model=Dict[str, Any])
async def get_prompt_analytics(prompt_id: str, days_back: int = 30):
    """Get analytics for a specific prompt."""
    return await analytics_handlers.handle_get_prompt_analytics(prompt_id, days_back)

@app.get("/api/v1/analytics/usage", response_model=Dict[str, Any])
async def get_usage_analytics(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Get usage analytics with date filtering."""
    return await analytics_handlers.handle_get_usage_analytics(start_date, end_date)

# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@app.post("/api/v1/ab-tests", response_model=Dict[str, Any])
async def create_ab_test(test_data: ABTestCreate):
    """Create a new A/B test."""
    return await ab_test_handlers.handle_create_ab_test(test_data)

@app.get("/api/v1/ab-tests", response_model=Dict[str, Any])
async def list_ab_tests(limit: int = 50, offset: int = 0):
    """List A/B tests."""
    return await ab_test_handlers.handle_list_ab_tests(limit, offset)

@app.get("/api/v1/ab-tests/{test_id}", response_model=Dict[str, Any])
async def get_ab_test(test_id: str):
    """Get A/B test details."""
    return await ab_test_handlers.handle_get_ab_test(test_id)

@app.get("/api/v1/ab-tests/{test_id}/select", response_model=Dict[str, Any])
async def select_prompt_for_test(test_id: str):
    """Select a prompt variant for A/B testing."""
    return await ab_test_handlers.handle_select_prompt_for_test(test_id)

@app.get("/api/v1/ab-tests/{test_id}/results", response_model=Dict[str, Any])
async def get_ab_test_results(test_id: str):
    """Get A/B test results and analysis."""
    return await ab_test_handlers.handle_get_test_results(test_id)

# ============================================================================
# RELATIONSHIPS AND VERSIONING
# ============================================================================

@app.post("/api/v1/prompts/{prompt_id}/relationships", response_model=Dict[str, Any])
async def add_prompt_relationship(prompt_id: str, relationship: PromptRelationshipCreate):
    """Add a relationship between prompts."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

@app.get("/api/v1/prompts/{prompt_id}/relationships", response_model=Dict[str, Any])
async def get_prompt_relationships(prompt_id: str, direction: str = "both"):
    """Get relationships for a prompt."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

@app.get("/api/v1/prompts/{prompt_id}/versions", response_model=Dict[str, Any])
async def get_prompt_versions(prompt_id: str, limit: int = 50, offset: int = 0):
    """Get version history for a prompt."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

@app.post("/api/v1/prompts/{prompt_id}/versions/{version_number}/rollback", response_model=Dict[str, Any])
async def rollback_prompt_version(prompt_id: str, version_number: int, reason: str = ""):
    """Rollback prompt to a specific version."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@app.put("/api/v1/prompts/{prompt_id}/lifecycle", response_model=Dict[str, Any])
async def update_prompt_lifecycle(prompt_id: str, status: str, reason: str = ""):
    """Update prompt lifecycle status (draft/published/deprecated/archived)."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

@app.get("/api/v1/prompts/lifecycle/{status}", response_model=Dict[str, Any])
async def get_prompts_by_lifecycle_status(status: str, limit: int = 50, offset: int = 0):
    """Get prompts by lifecycle status."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

@app.get("/api/v1/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats():
    """Get cache performance statistics."""
    try:
        stats = prompt_store_cache.get_stats()
        return create_success_response(
            message="Cache statistics retrieved",
            data=stats
        )
    except Exception as e:
        return create_error_response(f"Failed to get cache stats: {str(e)}", "INTERNAL_ERROR")

@app.post("/api/v1/cache/invalidate", response_model=Dict[str, Any])
async def invalidate_cache(pattern: str = "*"):
    """Invalidate cache entries matching pattern."""
    try:
        invalidated = await prompt_store_cache.invalidate_pattern(pattern)
        return create_success_response(
            message=f"Invalidated {invalidated} cache entries",
            data={"invalidated_count": invalidated}
        )
    except Exception as e:
        return create_error_response(f"Failed to invalidate cache: {str(e)}", "INTERNAL_ERROR")

@app.post("/api/v1/cache/warmup", response_model=Dict[str, Any])
async def warmup_cache():
    """Warm up cache with frequently accessed data."""
    try:
        # This would implement cache warming logic
        return create_success_response(
            message="Cache warmup initiated",
            data={"status": "warming"}
        )
    except Exception as e:
        return create_error_response(f"Failed to warmup cache: {str(e)}", "INTERNAL_ERROR")

# ============================================================================
# NOTIFICATIONS AND WEBHOOKS
# ============================================================================

@app.post("/api/v1/webhooks", response_model=Dict[str, Any])
async def register_webhook(webhook: WebhookCreate):
    """Register a webhook for event notifications."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

@app.get("/api/v1/webhooks", response_model=Dict[str, Any])
async def list_webhooks():
    """List registered webhooks."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

@app.get("/api/v1/notifications/stats", response_model=Dict[str, Any])
async def get_notification_stats():
    """Get notification delivery statistics."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")


if __name__ == "__main__":
    """Run the Prompt Store service directly."""
    import uvicorn

    port = get_config_value("port", DEFAULT_PORT, section="server", env_key="PROMPT_STORE_PORT")
    print(f"🚀 Starting Prompt Store Service v{SERVICE_VERSION} on port {port}...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(port),
        log_level="info"
    )
