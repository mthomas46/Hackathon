"""Prompt Store Service

Advanced prompt management system with versioning, A/B testing, and analytics
for the LLM Documentation Ecosystem.
"""

from fastapi import FastAPI
from typing import Dict, Any, List, Optional

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response, create_error_response
from services.shared.error_handling import ServiceException, install_error_handlers
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import utc_now, generate_id, setup_common_middleware, attach_self_register

# ============================================================================
# HANDLER MODULES - Extracted business logic
# ============================================================================
from .modules.models import PromptCreate, PromptUpdate, ABTestCreate
from .modules.prompt_handlers import prompt_handlers
from .modules.ab_handlers import ab_handlers
from .modules.analytics_handlers import analytics_handlers

# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware
app = FastAPI(title="Prompt Store", version="1.0.0")

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.PROMPT_STORE)
install_error_handlers(app)
register_health_endpoints(app, ServiceNames.PROMPT_STORE, "1.0.0")
attach_self_register(app, ServiceNames.PROMPT_STORE)

@app.post("/prompts")
async def create_prompt(prompt_data: PromptCreate):
    """Create a new prompt."""
    return await prompt_handlers.handle_create_prompt(prompt_data)

@app.get("/prompts")
async def list_prompts(category: Optional[str] = None, limit: int = 50):
    """List prompts."""
    return await prompt_handlers.handle_list_prompts(category, limit)

@app.get("/prompts/search/{category}/{name}")
async def get_prompt_by_name(category: str, name: str, **variables):
    """Get prompt by category/name and fill variables."""
    return await prompt_handlers.handle_get_prompt_by_name(category, name, **variables)

@app.put("/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, updates: PromptUpdate):
    """Update a prompt."""
    return await prompt_handlers.handle_update_prompt(prompt_id, updates)

@app.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """Delete a prompt."""
    return await prompt_handlers.handle_delete_prompt(prompt_id)

@app.post("/migrate")
async def migrate_from_yaml():
    """Migrate from YAML config."""
    return await prompt_handlers.handle_migrate_from_yaml()

# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@app.post("/ab-tests")
async def create_ab_test(test_data: ABTestCreate):
    """Create A/B test."""
    return await ab_handlers.handle_create_ab_test(test_data)

@app.get("/ab-tests/{test_id}/select")
async def select_prompt_for_test(test_id: str):
    """Select prompt for A/B testing."""
    return await ab_handlers.handle_select_prompt_for_test(test_id)

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics")
async def get_analytics():
    """Get usage analytics and performance metrics."""
    return await analytics_handlers.handle_get_analytics()

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Prompt Store Service...")
    uvicorn.run(app, host="0.0.0.0", port=5110)