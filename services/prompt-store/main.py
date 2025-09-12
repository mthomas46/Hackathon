"""Prompt Store Service

Advanced prompt management system with versioning, A/B testing, and analytics
for the LLM Documentation Ecosystem.

This service provides centralized storage, management, and optimization of LLM prompts,
enabling teams to collaboratively create, test, and improve prompts for various use cases.

Key Features:
- Centralized prompt storage and retrieval
- Version control with full history tracking
- A/B testing framework for prompt optimization
- Usage analytics and performance monitoring
- Collaborative prompt management
- Template-based prompt generation
- Integration with all ecosystem services

Architecture:
- SQLite database for reliable data persistence
- FastAPI for high-performance REST API
- Template variable substitution system
- Comprehensive logging and monitoring
- Health checks and service discovery

Core Components:
- Prompt CRUD Operations: Create, read, update, delete prompts
- Version Management: Track prompt evolution over time
- A/B Testing Engine: Test prompt variations against metrics
- Analytics System: Monitor prompt usage and performance
- Template Engine: Support for dynamic prompt generation
- Migration System: Import prompts from external sources

Endpoints:
- GET  /health - Service health check
- POST /prompts - Create new prompt
- GET  /prompts - List prompts with filtering
- GET  /prompts/{id} - Get specific prompt
- PUT  /prompts/{id} - Update existing prompt
- DELETE /prompts/{id} - Delete prompt
- POST /ab-tests - Create A/B test
- GET  /analytics - Get usage analytics
- POST /migrate - Import prompts from YAML

Data Models:
- Prompt: Core prompt entity with metadata
- PromptVersion: Version history tracking
- ABTest: A/B testing configuration
- PromptUsage: Usage logging and analytics
- PromptAnalytics: Aggregated performance metrics

Integration Points:
- Orchestrator: Prompt retrieval for workflows
- Analysis Service: Prompts for document analysis
- Interpreter: Prompts for natural language processing
- CLI: Prompt management interface
- All Services: Usage logging and analytics

Environment Variables:
- PROMPT_STORE_DB: SQLite database file path
- PROMPT_STORE_PORT: Service port (default: 5110)
- Various service URLs for integration

Database Schema:
- prompts: Core prompt data with versioning
- prompt_versions: Historical versions of prompts
- ab_tests: A/B testing configurations and results
- prompt_usage: Detailed usage logging
- prompt_analytics: Aggregated analytics data
- user_sessions: User session tracking for A/B tests

Usage:
    python services/prompt-store/main.py

Or with Docker:
    docker-compose up prompt-store

Dependencies:
- fastapi: Web framework
- sqlite3: Database storage
- pydantic: Data validation
- httpx: HTTP client for integrations

Security Considerations:
- Input validation on all endpoints
- SQL injection prevention
- Rate limiting for API access
- Audit logging for sensitive operations

Performance:
- Connection pooling for database access
- Caching for frequently accessed prompts
- Asynchronous operations for I/O intensive tasks
- Optimized queries with proper indexing

Monitoring:
- Health check endpoints
- Usage metrics and analytics
- Error logging and alerting
- Performance monitoring
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

# Local imports
from .database import PromptStoreDatabase
from .models import Prompt, PromptCreate, PromptUpdate, ABTest, ABTestCreate

# ============================================================================
# SHARED UTILITIES - Leveraging centralized functionality across modules
# ============================================================================
from .modules.shared_utils import (
    get_prompt_store_client,
    handle_prompt_error,
    create_prompt_success_response,
    build_prompt_context,
    validate_prompt_data
)

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
    try:
        db = get_prompt_store_client()  # Using shared client

        # Check if prompt already exists
        existing = db.get_prompt_by_name(prompt_data.category, prompt_data.name)
        if existing:
            return handle_prompt_error(
                Exception(f"Prompt '{prompt_data.name}' already exists in category '{prompt_data.category}'"),
                ErrorCodes.VALIDATION_ERROR,
                category=prompt_data.category,
                name=prompt_data.name
            )

        # Validate prompt data
        validated_data = validate_prompt_data(prompt_data.dict())

        prompt = Prompt(
            name=validated_data['name'],
            category=validated_data['category'],
            description=validated_data.get('description', ""),
            content=validated_data['content'],
            variables=validated_data['variables'],
            tags=validated_data['tags'],
            created_by="api_user"
        )

        created = db.create_prompt(prompt)
        context = {"prompt_id": created.id, "category": created.category}
        return create_prompt_success_response("created", {"prompt_id": created.id}, **context)

    except Exception as e:
        context = {"category": getattr(prompt_data, 'category', None)}
        return handle_prompt_error("create", e, **context)

@app.get("/prompts")
async def list_prompts(category: Optional[str] = None, limit: int = 50):
    """List prompts."""
    try:
        db = get_prompt_store_client()  # Using shared client
        filters = {"category": category} if category else {}
        prompts, total = db.list_prompts(filters, limit)

        result = {
            "prompts": [
                {
                    "id": p.id,
                    "name": p.name,
                    "category": p.category,
                    "description": p.description,
                    "tags": p.tags,
                    "version": p.version
                } for p in prompts
            ],
            "total": total
        }

        context = build_prompt_context("list", category=category, limit=limit, total=total)
        return create_prompt_success_response("retrieved", result, **context)

    except Exception as e:
        context = build_prompt_context("list", category=category)
        return handle_prompt_error("retrieve", e, **context)

@app.get("/prompts/search/{category}/{name}")
async def get_prompt_by_name(category: str, name: str, **variables):
    """Get prompt by category/name and fill variables."""
    try:
        db = get_prompt_store_client()  # Using shared client
        prompt = db.get_prompt_by_name(category, name)

        if not prompt:
            return handle_prompt_error(
                "find",
                Exception(f"Prompt '{name}' not found in category '{category}'"),
                ErrorCodes.PROMPT_NOT_FOUND,
                category=category,
                name=name
            )

        # Fill template variables
        content = prompt.content
        for var_name, var_value in variables.items():
            content = content.replace(f"{{{var_name}}}", str(var_value))

        result = {
            "prompt": content,
            "id": prompt.id,
            "name": prompt.name,
            "version": prompt.version
        }

        context = build_prompt_context("retrieve", prompt_id=prompt.id, category=category, variables_count=len(variables))
        return create_prompt_success_response("retrieved", result, **context)

    except Exception as e:
        context = build_prompt_context("retrieve", category=category, name=name)
        return handle_prompt_error("retrieve", e, **context)

@app.put("/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, updates: PromptUpdate):
    """Update a prompt."""
    try:
        db = get_prompt_store_client()  # Using shared client
        update_dict = updates.dict(exclude_unset=True)
        updated = db.update_prompt(prompt_id, update_dict, "api_user")

        if not updated:
            return handle_prompt_error(
                "find",
                Exception(f"Prompt '{prompt_id}' not found for update"),
                ErrorCodes.PROMPT_NOT_FOUND,
                prompt_id=prompt_id
            )

        context = build_prompt_context("update", prompt_id=prompt_id)
        return create_prompt_success_response("updated", {"prompt_id": prompt_id}, **context)

    except Exception as e:
        context = build_prompt_context("update", prompt_id=prompt_id)
        return handle_prompt_error("update", e, **context)

@app.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str):
    """Delete a prompt."""
    try:
        db = get_prompt_store_client()  # Using shared client
        if db.delete_prompt(prompt_id, "api_user"):
            context = build_prompt_context("delete", prompt_id=prompt_id)
            return create_prompt_success_response("deleted", {"prompt_id": prompt_id}, **context)

        return handle_prompt_error(
            "find",
            Exception(f"Prompt '{prompt_id}' not found for deletion"),
            ErrorCodes.PROMPT_NOT_FOUND,
            prompt_id=prompt_id
        )

    except Exception as e:
        context = build_prompt_context("delete", prompt_id=prompt_id)
        return handle_prompt_error("delete", e, **context)

@app.post("/migrate")
async def migrate_from_yaml():
    """Migrate from YAML config."""
    try:
        db = get_prompt_store_client()  # Using shared client
        yaml_path = "services/shared/prompts.yaml"
        count = db.migrate_from_yaml(yaml_path)

        result = {"migrated": count, "status": "completed"}
        context = {"migrated_count": count}
        # Filter out keys that might conflict with function parameters
        filtered_context = {k: v for k, v in context.items() if k not in ['operation', 'operation_name']}
        return create_prompt_success_response("migrated", result, **filtered_context)

    except Exception as e:
        context = {}
        return handle_prompt_error("migrate", e, **context)

# ============================================================================
# MODULE IMPORTS - Split functionality into focused modules
# ============================================================================

from .modules.ab_testing import (
    create_ab_test as create_ab_test_logic,
    select_prompt_for_test as select_prompt_for_test_logic,
    get_usage_analytics
)

# ============================================================================
# A/B TESTING ENDPOINTS
# ============================================================================

@app.post("/ab-tests")
async def create_ab_test(test_data: ABTestCreate):
    """Create A/B test."""
    try:
        db = get_prompt_store_client()  # Using shared client
        result = create_ab_test_logic(test_data, db)

        context = build_prompt_context("ab_test_create", test_name=test_data.name)
        return create_prompt_success_response("A/B test created", result, **context)

    except Exception as e:
        context = build_prompt_context("ab_test_create")
        return handle_prompt_error("create A/B test", e, **context)

@app.get("/ab-tests/{test_id}/select")
async def select_prompt_for_test(test_id: str):
    """Select prompt for A/B testing."""
    try:
        db = get_prompt_store_client()  # Using shared client
        prompt_id = select_prompt_for_test_logic(test_id, db)

        if not prompt_id:
            return handle_prompt_error(
                "find",
                Exception(f"A/B test '{test_id}' not found"),
                ErrorCodes.AB_TEST_NOT_FOUND,
                test_id=test_id
            )

        result = {"prompt_id": prompt_id}
        context = build_prompt_context("ab_test_select", test_id=test_id, prompt_id=prompt_id)
        return create_prompt_success_response("selected for A/B testing", result, **context)

    except Exception as e:
        context = build_prompt_context("ab_test_select", test_id=test_id)
        return handle_prompt_error("select for A/B testing", e, **context)

# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@app.get("/analytics")
async def get_analytics():
    """Get usage analytics and performance metrics."""
    try:
        db = get_prompt_store_client()  # Using shared client
        analytics_data = get_usage_analytics(db)

        context = build_prompt_context("analytics_retrieval", total_prompts=len(analytics_data.get('popular_categories', [])))
        return create_prompt_success_response("analytics retrieved", analytics_data, **context)

    except Exception as e:
        context = build_prompt_context("analytics_retrieval")
        return handle_prompt_error("retrieve analytics", e, **context)

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Prompt Store Service...")
    uvicorn.run(app, host="0.0.0.0", port=5110)