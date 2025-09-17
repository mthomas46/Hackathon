"""Service: Prompt Store

Endpoints:
- POST /prompts: Create new prompts with versioning and categorization
- GET /prompts: List prompts with filtering by category and pagination
- GET /prompts/search/{category}/{name}: Retrieve and fill prompt templates with variables
- PUT /prompts/{prompt_id}: Update existing prompts with version tracking
- DELETE /prompts/{prompt_id}: Soft delete prompts with audit trail
- POST /migrate: Migrate prompts from YAML configuration to database
- POST /ab-tests: Create A/B tests for prompt optimization
- GET /ab-tests/{test_id}/select: Select prompts for A/B testing
- GET /analytics: Retrieve usage analytics and performance metrics

Responsibilities:
- Provide comprehensive prompt management with versioning and templates
- Support A/B testing for prompt optimization and performance comparison
- Maintain prompt analytics for usage tracking and effectiveness measurement
- Enable prompt templating with variable substitution and validation
- Support prompt categorization, tagging, and search capabilities
- Provide migration utilities for legacy prompt configurations

Dependencies: SQLite database, shared utilities for ID generation and validation.
"""

from fastapi import FastAPI
from typing import Dict, Any, List, Optional

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.responses.responses import create_success_response, create_error_response
from services.shared.utilities.error_handling import ServiceException, install_error_handlers
from services.shared.core.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import utc_now, generate_id, setup_common_middleware, attach_self_register

# ============================================================================
# HANDLER MODULES - Extracted business logic
# ============================================================================
from .modules.models import PromptCreate, PromptUpdate, ABTestCreate
from .modules.prompt_handlers import prompt_handlers
from .modules.ab_handlers import ab_handlers
from .modules.analytics_handlers import analytics_handlers

# Service configuration constants
SERVICE_NAME = "prompt-store"
SERVICE_TITLE = "Prompt Store"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5110

# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware
app = FastAPI(
    title=SERVICE_TITLE,
    description="Advanced prompt management system with versioning, A/B testing, and analytics",
    version=SERVICE_VERSION
)

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.PROMPT_STORE)
install_error_handlers(app)
register_health_endpoints(app, ServiceNames.PROMPT_STORE, SERVICE_VERSION)
attach_self_register(app, ServiceNames.PROMPT_STORE)

@app.post("/prompts")
async def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt with versioning and validation.

    Creates a new prompt with automatic versioning, validation of variables,
    and categorization support. Includes duplicate name checking within categories.
    """
    return await prompt_handlers.handle_create_prompt(prompt_data)

@app.get("/prompts")
async def list_prompts(category: Optional[str] = None, limit: int = 50):
    """List prompts with optional filtering and pagination.

    Retrieves prompts filtered by category if specified, with configurable
    result limits for efficient pagination and browsing.
    """
    return await prompt_handlers.handle_list_prompts(category, limit)

@app.get("/prompts/search/{category}/{name}")
async def get_prompt_by_name(category: str, name: str, **variables):
    """Get prompt by category/name and fill variables.

    Retrieves a specific prompt by category and name, then fills in template
    variables with provided values. Supports dynamic prompt generation.
    """
    return await prompt_handlers.handle_get_prompt_by_name(category, name, **variables)

@app.put("/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, updates: PromptUpdate):
    """Update a prompt with version tracking.

    Updates existing prompt content, variables, or metadata with automatic
    version history tracking and change documentation.
    """
    return await prompt_handlers.handle_update_prompt(prompt_id, updates)

@app.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """Soft delete a prompt with audit trail.

    Marks a prompt as inactive rather than permanent deletion, maintaining
    audit trail and preventing accidental data loss.
    """
    return await prompt_handlers.handle_delete_prompt(prompt_id)

@app.post("/migrate")
async def migrate_from_yaml():
    """Migrate prompts from YAML configuration to database.

    One-time migration utility to convert legacy YAML-based prompt
    configurations to the database-backed system with full versioning support.
    """
    return await prompt_handlers.handle_migrate_from_yaml()

# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@app.post("/ab-tests")
async def create_ab_test(test_data: ABTestCreate):
    """Create A/B test for prompt optimization.

    Sets up an A/B testing configuration comparing two prompt variants
    to determine which performs better based on defined metrics.
    """
    return await ab_handlers.handle_create_ab_test(test_data)

@app.get("/ab-tests/{test_id}/select")
async def select_prompt_for_test(test_id: str):
    """Select prompt for A/B testing.

    Returns a randomly selected prompt variant based on the test configuration
    and current traffic distribution for performance comparison.
    """
    return await ab_handlers.handle_select_prompt_for_test(test_id)

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics")
async def get_analytics():
    """Get usage analytics and performance metrics.

    Retrieves comprehensive analytics including prompt usage statistics,
    A/B test performance metrics, and system performance indicators
    for monitoring and optimization insights.
    """
    return await analytics_handlers.handle_get_analytics()

if __name__ == "__main__":
    """Run the Prompt Store service directly."""
    import uvicorn
    print("🚀 Starting Prompt Store Service...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )