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
    BulkOperationCreate, PromptRelationshipCreate, WebhookCreate,
    PromptLifecycleUpdate, BulkLifecycleUpdate
)
from services.prompt_store.domain.prompts.handlers import PromptHandlers
from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers
from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers
from services.prompt_store.domain.bulk.handlers import BulkOperationHandlers
from services.prompt_store.domain.refinement.handlers import PromptRefinementHandlers
from services.prompt_store.domain.lifecycle.handlers import LifecycleHandlers
from services.prompt_store.domain.relationships.handlers import RelationshipsHandlers
from services.prompt_store.domain.notifications.handlers import NotificationsHandlers
from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers
from services.prompt_store.domain.optimization.handlers import OptimizationHandlers
from services.prompt_store.domain.validation.handlers import ValidationHandlers
from services.prompt_store.domain.orchestration.handlers import OrchestrationHandlers
from services.prompt_store.domain.intelligence.handlers import IntelligenceHandlers
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
optimization_handlers = OptimizationHandlers()
validation_handlers = ValidationHandlers()
orchestration_handlers = OrchestrationHandlers()
intelligence_handlers = IntelligenceHandlers()
bulk_handlers = BulkOperationHandlers()
refinement_handlers = PromptRefinementHandlers()
lifecycle_handlers = LifecycleHandlers()
relationships_handlers = RelationshipsHandlers()
notifications_handlers = NotificationsHandlers()

# ============================================================================
# PROMPT MANAGEMENT ENDPOINTS
# ============================================================================

@app.post("/api/v1/prompts", response_model=Dict[str, Any], status_code=201)
async def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt with validation and business rules."""
    return await prompt_handlers.handle_create_prompt(prompt_data)

@app.get("/api/v1/prompts/{prompt_id}", response_model=Dict[str, Any])
async def get_prompt(prompt_id: str):
    """Get a single prompt by ID."""
    return await prompt_handlers.handle_get_prompt(prompt_id)

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

@app.get("/api/v1/prompts/{prompt_id}/versions/{version}/refinement", response_model=Dict[str, Any])
async def get_version_refinement_details(prompt_id: str, version: int):
    """Get detailed refinement information for a specific version."""
    return await refinement_handlers.handle_get_version_refinement_details(prompt_id, version)

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
async def add_prompt_relationship(prompt_id: str, relationship: PromptRelationshipCreate,
                                user_id: str = "api_user"):
    """Add a relationship between prompts."""
    return await relationships_handlers.handle_create_relationship(prompt_id, relationship, user_id)

@app.get("/api/v1/prompts/{prompt_id}/relationships", response_model=Dict[str, Any])
async def get_prompt_relationships(prompt_id: str, direction: str = "both"):
    """Get relationships for a prompt."""
    return relationships_handlers.handle_get_relationships(prompt_id, direction)

@app.put("/api/v1/relationships/{relationship_id}/strength", response_model=Dict[str, Any])
async def update_relationship_strength(relationship_id: str, strength: float, user_id: str = "api_user"):
    """Update the strength of a relationship."""
    return relationships_handlers.handle_update_relationship_strength(relationship_id, strength, user_id)

@app.delete("/api/v1/relationships/{relationship_id}", response_model=Dict[str, Any])
async def delete_relationship(relationship_id: str, user_id: str = "api_user"):
    """Delete a relationship."""
    return relationships_handlers.handle_delete_relationship(relationship_id, user_id)

@app.get("/api/v1/prompts/{prompt_id}/relationships/graph", response_model=Dict[str, Any])
async def get_relationship_graph(prompt_id: str, depth: int = 2):
    """Get relationship graph for a prompt."""
    return relationships_handlers.handle_get_relationship_graph(prompt_id, depth)

@app.get("/api/v1/relationships/stats", response_model=Dict[str, Any])
async def get_relationship_stats():
    """Get relationship statistics."""
    return relationships_handlers.handle_get_relationship_stats()

@app.get("/api/v1/prompts/{prompt_id}/related", response_model=Dict[str, Any])
async def find_related_prompts(prompt_id: str, relationship_types: Optional[List[str]] = None,
                             min_strength: float = 0.0):
    """Find prompts related to the given prompt."""
    return relationships_handlers.handle_find_related_prompts(prompt_id, relationship_types, min_strength)

@app.post("/api/v1/relationships/validate", response_model=Dict[str, Any])
async def validate_relationship(source_prompt_id: str, target_prompt_id: str, relationship_type: str):
    """Validate if a relationship can be created."""
    return relationships_handlers.handle_validate_relationship(source_prompt_id, target_prompt_id, relationship_type)

@app.get("/api/v1/prompts/{prompt_id}/versions", response_model=Dict[str, Any])
async def get_prompt_versions(prompt_id: str, limit: int = 50, offset: int = 0):
    """Get version history for a prompt."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

@app.get("/api/v1/prompts/{prompt_id}/documents", response_model=Dict[str, Any])
async def get_prompt_documents(prompt_id: str):
    """Get all documents generated by a prompt through refinement."""
    try:
        summary = prompt_handlers.service.get_prompt_document_summary(prompt_id)
        return create_success_response(
            message="Prompt documents retrieved successfully",
            data=summary
        ).model_dump()
    except ValueError as e:
        return create_error_response(str(e), "VALIDATION_ERROR").model_dump()
    except Exception as e:
        return create_error_response(f"Failed to retrieve prompt documents: {str(e)}", "INTERNAL_ERROR").model_dump()

@app.get("/api/v1/documents/prompts", response_model=Dict[str, Any])
async def get_prompts_with_documents():
    """Get all prompts that have generated documents."""
    try:
        from services.doc_store.domain.documents.service import DocumentService
        doc_service = DocumentService()
        prompt_docs = doc_service.get_prompts_with_documents()

        # Convert to response format
        result = {}
        for prompt_id, documents in prompt_docs.items():
            result[prompt_id] = {
                "document_count": len(documents),
                "documents": [doc.to_dict() for doc in documents],
                "latest_document": documents[0].to_dict() if documents else None
            }

        return create_success_response(
            message="Prompts with documents retrieved successfully",
            data=result
        ).model_dump()
    except ImportError:
        return create_error_response("Document store service not available", "SERVICE_UNAVAILABLE").model_dump()
    except Exception as e:
        return create_error_response(f"Failed to retrieve prompts with documents: {str(e)}", "INTERNAL_ERROR").model_dump()

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.post("/api/v1/analytics/usage", response_model=Dict[str, Any])
async def record_usage_metrics(prompt_id: str, version: int, usage_data: Dict[str, Any]):
    """Record usage metrics for analytics."""
    return await analytics_handlers.handle_record_usage_metrics(prompt_id, version, usage_data)

@app.post("/api/v1/analytics/satisfaction", response_model=Dict[str, Any])
async def record_user_satisfaction(satisfaction_data: Dict[str, Any]):
    """Record user satisfaction feedback."""
    return await analytics_handlers.handle_record_satisfaction(satisfaction_data)

@app.get("/api/v1/analytics/dashboard", response_model=Dict[str, Any])
async def get_analytics_dashboard(time_range_days: int = 30):
    """Get comprehensive analytics dashboard."""
    return await analytics_handlers.handle_get_analytics_dashboard(time_range_days)

@app.get("/api/v1/analytics/performance", response_model=Dict[str, Any])
async def get_performance_overview(time_range_days: int = 30):
    """Get performance overview across all prompts."""
    return await analytics_handlers.handle_get_performance_overview(time_range_days)

@app.get("/api/v1/analytics/usage", response_model=Dict[str, Any])
async def get_usage_analytics(time_range_days: int = 30):
    """Get usage analytics and trends."""
    return await analytics_handlers.handle_get_usage_analytics(time_range_days)

@app.get("/api/v1/analytics/prompts/{prompt_id}", response_model=Dict[str, Any])
async def get_prompt_metrics(prompt_id: str, version: Optional[int] = None):
    """Get analytics metrics for a specific prompt."""
    return await analytics_handlers.handle_get_prompt_metrics(prompt_id, version)

# ============================================================================
# OPTIMIZATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/optimization/ab-tests", response_model=Dict[str, Any])
async def create_ab_test(prompt_a_id: str, prompt_b_id: str, traffic_percentage: float = 50.0):
    """Create a new A/B test between two prompt variants."""
    return await optimization_handlers.handle_create_ab_test(prompt_a_id, prompt_b_id, traffic_percentage)

@app.get("/api/v1/optimization/ab-tests/{test_id}/assign", response_model=Dict[str, Any])
async def get_prompt_assignment(test_id: str, user_id: str):
    """Get prompt assignment for a user in an A/B test."""
    return await optimization_handlers.handle_get_prompt_assignment(test_id, user_id)

@app.post("/api/v1/optimization/ab-tests/{test_id}/results", response_model=Dict[str, Any])
async def record_test_result(test_id: str, prompt_id: str, success: bool, score: float = 0.0):
    """Record the result of using a prompt in an A/B test."""
    return await optimization_handlers.handle_record_test_result(test_id, prompt_id, success, score)

@app.get("/api/v1/optimization/ab-tests/{test_id}/results", response_model=Dict[str, Any])
async def get_test_results(test_id: str):
    """Get results for an A/B test."""
    return await optimization_handlers.handle_get_test_results(test_id)

@app.post("/api/v1/optimization/ab-tests/{test_id}/end", response_model=Dict[str, Any])
async def end_ab_test(test_id: str):
    """End an A/B test and declare winner."""
    return await optimization_handlers.handle_end_test(test_id)

@app.post("/api/v1/optimization/prompts/{prompt_id}/optimize", response_model=Dict[str, Any])
async def run_prompt_optimization(prompt_id: str, base_version: int):
    """Run automated optimization cycle for a prompt."""
    return await optimization_handlers.handle_run_optimization(prompt_id, base_version)

@app.post("/api/v1/optimization/variations", response_model=Dict[str, Any])
async def generate_prompt_variations(prompt_content: str, count: int = 3):
    """Generate variations of a prompt using AI."""
    return await optimization_handlers.handle_generate_variations(prompt_content, count)

# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/validation/test-suites", response_model=Dict[str, Any])
async def create_test_suite(name: str, description: str, test_cases: List[Dict[str, Any]]):
    """Create a new test suite for prompt validation."""
    return await validation_handlers.handle_create_test_suite(name, description, test_cases)

@app.get("/api/v1/validation/test-suites/standard", response_model=Dict[str, Any])
async def get_standard_test_suites():
    """Get standard test suites for common prompt types."""
    return await validation_handlers.handle_get_standard_test_suites()

@app.post("/api/v1/validation/prompts/{prompt_id}/test", response_model=Dict[str, Any])
async def run_prompt_tests(prompt_id: str, version: int, test_suite: Dict[str, Any]):
    """Run a test suite against a specific prompt version."""
    return await validation_handlers.handle_run_test_suite(prompt_id, version, test_suite)

@app.post("/api/v1/validation/lint", response_model=Dict[str, Any])
async def lint_prompt(prompt_content: str):
    """Lint a prompt for common issues and anti-patterns."""
    return await validation_handlers.handle_lint_prompt(prompt_content)

@app.post("/api/v1/validation/bias-detect", response_model=Dict[str, Any])
async def detect_bias(prompt_content: str, prompt_id: str = None, version: int = None):
    """Detect potential biases in prompt content."""
    return await validation_handlers.handle_detect_bias(prompt_content, prompt_id, version)

@app.post("/api/v1/validation/output", response_model=Dict[str, Any])
async def validate_output(prompt_output: str, expected_criteria: Dict[str, Any]):
    """Validate prompt output against expected criteria."""
    return await validation_handlers.handle_validate_output(prompt_output, expected_criteria)

# ============================================================================
# ORCHESTRATION ENDPOINTS
# ============================================================================

@app.post("/api/v1/orchestration/chains", response_model=Dict[str, Any])
async def create_conditional_chain(chain_definition: Dict[str, Any]):
    """Create a conditional prompt chain."""
    return await orchestration_handlers.handle_create_conditional_chain(chain_definition)

@app.post("/api/v1/orchestration/chains/{chain_id}/execute", response_model=Dict[str, Any])
async def execute_conditional_chain(chain_id: str, initial_context: Dict[str, Any]):
    """Execute a conditional prompt chain."""
    return await orchestration_handlers.handle_execute_chain(chain_id, initial_context)

@app.post("/api/v1/orchestration/pipelines", response_model=Dict[str, Any])
async def create_pipeline(pipeline_definition: Dict[str, Any]):
    """Create a prompt pipeline."""
    return await orchestration_handlers.handle_create_pipeline(pipeline_definition)

@app.post("/api/v1/orchestration/pipelines/{pipeline_id}/execute", response_model=Dict[str, Any])
async def execute_pipeline(pipeline_id: str, input_data: Dict[str, Any]):
    """Execute a prompt pipeline."""
    return await orchestration_handlers.handle_execute_pipeline(pipeline_id, input_data)

@app.post("/api/v1/orchestration/prompts/select", response_model=Dict[str, Any])
async def select_optimal_prompt(task_description: str, context: Dict[str, Any] = None):
    """Select optimal prompt for a task."""
    return await orchestration_handlers.handle_select_optimal_prompt(task_description, context)

@app.post("/api/v1/orchestration/prompts/recommend", response_model=Dict[str, Any])
async def get_prompt_recommendations(task_description: str, context: Dict[str, Any] = None):
    """Get prompt recommendations for a task."""
    return await orchestration_handlers.handle_get_recommendations(task_description, context)

# ============================================================================
# INTELLIGENCE ENDPOINTS
# ============================================================================

@app.post("/api/v1/intelligence/code/generate", response_model=Dict[str, Any])
async def generate_prompts_from_code(code_content: str, language: str = "python"):
    """Generate prompts based on code analysis."""
    return await intelligence_handlers.handle_generate_from_code(code_content, language)

@app.post("/api/v1/intelligence/document/generate", response_model=Dict[str, Any])
async def generate_prompts_from_document(document_content: str, doc_type: str = "markdown"):
    """Generate prompts based on document analysis."""
    return await intelligence_handlers.handle_generate_from_document(document_content, doc_type)

@app.post("/api/v1/intelligence/service/generate", response_model=Dict[str, Any])
async def generate_service_integration_prompts(service_name: str, service_description: str = ""):
    """Generate prompts optimized for service integration."""
    return await intelligence_handlers.handle_generate_service_prompts(service_name, service_description)

@app.post("/api/v1/intelligence/prompts/{prompt_id}/analyze", response_model=Dict[str, Any])
async def analyze_prompt_effectiveness(prompt_id: str, usage_history: Optional[List[Dict[str, Any]]] = None):
    """Analyze prompt effectiveness based on usage patterns."""
    return await intelligence_handlers.handle_analyze_effectiveness(prompt_id, usage_history)

@app.post("/api/v1/intelligence/api/generate", response_model=Dict[str, Any])
async def generate_api_documentation_prompts(service_analysis: Dict[str, Any]):
    """Generate API endpoint documentation prompts."""
    return await intelligence_handlers.handle_generate_api_endpoints(service_analysis)

@app.post("/api/v1/prompts/{prompt_id}/versions/{version_number}/rollback", response_model=Dict[str, Any])
async def rollback_prompt_version(prompt_id: str, version_number: int, reason: str = ""):
    """Rollback prompt to a specific version."""
    return create_error_response("Not implemented yet", "NOT_IMPLEMENTED")

# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

@app.put("/api/v1/prompts/{prompt_id}/lifecycle", response_model=Dict[str, Any])
async def update_prompt_lifecycle(prompt_id: str, lifecycle_update: PromptLifecycleUpdate,
                                user_id: str = "api_user"):
    """Update prompt lifecycle status (draft/published/deprecated/archived)."""
    return await lifecycle_handlers.handle_update_lifecycle_status(
        prompt_id, lifecycle_update, user_id
    )

@app.get("/api/v1/prompts/lifecycle/{status}", response_model=Dict[str, Any])
async def get_prompts_by_lifecycle_status(status: str, limit: int = 50, offset: int = 0):
    """Get prompts by lifecycle status."""
    return await lifecycle_handlers.handle_get_prompts_by_status(status, limit, offset)

@app.get("/api/v1/prompts/{prompt_id}/lifecycle/history", response_model=Dict[str, Any])
def get_prompt_lifecycle_history(prompt_id: str):
    """Get the lifecycle transition history for a prompt."""
    return lifecycle_handlers.handle_get_lifecycle_history(prompt_id)

@app.get("/api/v1/lifecycle/counts", response_model=Dict[str, Any])
def get_lifecycle_status_counts():
    """Get counts of prompts in each lifecycle status."""
    return lifecycle_handlers.handle_get_status_counts()

@app.get("/api/v1/lifecycle/rules", response_model=Dict[str, Any])
def get_lifecycle_transition_rules():
    """Get valid lifecycle transition rules."""
    return lifecycle_handlers.handle_get_transition_rules()

@app.post("/api/v1/prompts/{prompt_id}/lifecycle/validate", response_model=Dict[str, Any])
def validate_lifecycle_transition(prompt_id: str, new_status: str):
    """Validate if a lifecycle transition is allowed for a prompt."""
    return lifecycle_handlers.handle_validate_transition(prompt_id, new_status)

@app.post("/api/v1/lifecycle/bulk", response_model=Dict[str, Any])
async def bulk_lifecycle_update(update_data: BulkLifecycleUpdate, user_id: str = "api_user"):
    """Perform bulk lifecycle status updates."""
    return await lifecycle_handlers.handle_bulk_lifecycle_update(update_data, user_id)

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
async def register_webhook(webhook: WebhookCreate, user_id: str = "api_user"):
    """Register a webhook for event notifications."""
    return await notifications_handlers.handle_register_webhook(webhook, user_id)

@app.get("/api/v1/webhooks", response_model=Dict[str, Any])
async def list_webhooks(active_only: bool = False):
    """List registered webhooks."""
    return notifications_handlers.handle_list_webhooks(active_only)

@app.get("/api/v1/webhooks/{webhook_id}", response_model=Dict[str, Any])
async def get_webhook(webhook_id: str):
    """Get webhook details."""
    return notifications_handlers.handle_get_webhook(webhook_id)

@app.put("/api/v1/webhooks/{webhook_id}", response_model=Dict[str, Any])
async def update_webhook(webhook_id: str, updates: Dict[str, Any], user_id: str = "api_user"):
    """Update webhook configuration."""
    return await notifications_handlers.handle_update_webhook(webhook_id, updates, user_id)

@app.delete("/api/v1/webhooks/{webhook_id}", response_model=Dict[str, Any])
async def delete_webhook(webhook_id: str, user_id: str = "api_user"):
    """Delete a webhook."""
    return await notifications_handlers.handle_delete_webhook(webhook_id, user_id)

@app.post("/api/v1/notifications/trigger", response_model=Dict[str, Any])
async def trigger_notification(event_type: str, event_data: Dict[str, Any], user_id: str = "api_user"):
    """Manually trigger event notifications."""
    return await notifications_handlers.handle_notify_event(event_type, event_data, user_id)

@app.post("/api/v1/notifications/process", response_model=Dict[str, Any])
async def process_notifications():
    """Process pending notifications."""
    return await notifications_handlers.handle_process_notifications()

@app.get("/api/v1/notifications/stats", response_model=Dict[str, Any])
async def get_notification_stats():
    """Get notification delivery statistics."""
    return notifications_handlers.handle_get_notification_stats()

@app.post("/api/v1/notifications/cleanup", response_model=Dict[str, Any])
async def cleanup_notifications(days_old: int = 30):
    """Clean up old notification records."""
    return notifications_handlers.handle_cleanup_notifications(days_old)

@app.get("/api/v1/notifications/events", response_model=Dict[str, Any])
async def get_valid_events():
    """Get list of valid event types."""
    return notifications_handlers.handle_get_valid_events()


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
