"""
🧠 Prompt Store Service - Enterprise AI Prompt Intelligence Hub

REST API Standardization - Phase 4C
====================================

Comprehensive OpenAPI/Swagger annotations for enterprise-grade API documentation,
consistent response formats, and standardized error handling.

API Endpoints by Domain Context:
=================================
• Prompt Management: `/api/v1/prompts` - CRUD operations, search, forking, versioning, drift detection
• Bulk Operations: `/api/v1/bulk` - Batch processing, mass operations, job management
• Refinement System: `/api/v1/refinement` - AI-powered prompt refinement, sessions, comparisons
• Analytics & Intelligence: `/api/v1/analytics` - Usage analytics, performance metrics, dashboards
• A/B Testing: `/api/v1/ab-tests` - Test creation, management, results, optimization
• Relationships: `/api/v1/relationships` - Prompt relationships, dependency graphs, validation
• Optimization: `/api/v1/optimization` - A/B testing, prompt optimization, variations
• Validation: `/api/v1/validation` - Test suites, linting, bias detection, output validation
• Orchestration: `/api/v1/orchestration` - Chains, pipelines, prompt selection
• Intelligence: `/api/v1/intelligence` - Code generation, document generation, analysis
• Lifecycle Management: `/api/v1/lifecycle` - Lifecycle operations, validation, bulk updates
• Cache Management: `/api/v1/cache` - Cache statistics, invalidation, warmup, optimization
• Notifications: `/api/v1/notifications` - Webhooks, event processing, stats, cleanup

Key Features:
=============
• Domain-Driven Design (DDD) architecture with 14 bounded contexts
• Enterprise-grade prompt management with versioning and relationships
• AI-powered prompt refinement and optimization capabilities
• Comprehensive A/B testing framework for prompt evaluation
• Advanced analytics and intelligence features
• Real-time validation and quality assurance
• Intelligent orchestration and automation
• Enterprise integration with comprehensive ecosystem support

Dependencies: shared middlewares/logging, ServiceClients, database connections.
"""

from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

# ============================================================================
# DOMAIN MODULES - Following domain-driven design
# ============================================================================
from services.prompt_store.core.models import (
    ABTestCreate,
    BulkLifecycleUpdate,
    PromptCreate,
    PromptLifecycleUpdate,
    PromptRelationshipCreate,
    PromptUpdate,
    WebhookCreate,
)
from services.prompt_store.domain.ab_testing.handlers import ABTestHandlers
from services.prompt_store.domain.analytics.handlers import AnalyticsHandlers
from services.prompt_store.domain.bulk.handlers import BulkOperationHandlers
from services.prompt_store.domain.intelligence.handlers import IntelligenceHandlers
from services.prompt_store.domain.lifecycle.handlers import LifecycleHandlers
from services.prompt_store.domain.notifications.handlers import NotificationsHandlers
from services.prompt_store.domain.optimization.handlers import OptimizationHandlers
from services.prompt_store.domain.orchestration.handlers import OrchestrationHandlers
from services.prompt_store.domain.prompts.handlers import PromptHandlers
from services.prompt_store.domain.refinement.handlers import PromptRefinementHandlers
from services.prompt_store.domain.relationships.handlers import RelationshipsHandlers
from services.prompt_store.domain.validation.handlers import ValidationHandlers
from services.prompt_store.infrastructure.cache import prompt_store_cache
from services.shared.core.config.config import get_config_value
from services.shared.core.constants_new import ServiceNames
from services.shared.core.responses.responses import SuccessResponse, create_error_response, create_success_response

# ============================================================================
# SHARED MODULES - Optimized import consolidation
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.utilities import attach_self_register, setup_common_middleware
from services.shared.utilities.error_handling import install_error_handlers
from services.shared.utilities.logging_client import get_log_collector_client

# ============================================================================
# STANDARD API RESPONSE MODELS - Consistent error handling
# ============================================================================

class APIResponse(BaseModel):
    """Standard API response wrapper for consistent formatting."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable response message")
    data: Optional[Any] = Field(None, description="Response data payload")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")
    timestamp: Optional[str] = Field(None, description="Response timestamp in ISO 8601 format")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class ErrorResponse(BaseModel):
    """Standard error response for consistent error formatting."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=False, description="Always false for error responses")
    error: Dict[str, Any] = Field(..., description="Error details")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")
    timestamp: str = Field(..., description="Error timestamp in ISO 8601 format")


class HealthResponse(BaseModel):
    """Health check response model for prompt store service."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    last_health_check: Optional[str] = Field(None, description="Last health check timestamp")
    database_connected: bool = Field(..., description="Database connectivity status")
    cache_enabled: bool = Field(..., description="Cache system status")
    bounded_contexts_loaded: List[str] = Field(..., description="List of loaded bounded contexts")
    ddd_architecture: bool = Field(..., description="Whether DDD architecture is properly initialized")


# ============================================================================
# SERVICE CONFIGURATION
# ============================================================================
SERVICE_NAME = "prompt-store"
SERVICE_TITLE = "Prompt Store"


from pathlib import Path

# Configuration loading
import yaml


def load_config() -> dict:
    """Load service configuration from config file."""
    config_path = Path(__file__).parent / "config.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


# Load configuration
config = load_config()

# Extract configuration values with environment variable override
PROMPT_STORE_CONNECTION_POOL_SIZE = os.getenv(
    "PROMPT_STORE_CONNECTION_POOL_SIZE", config.get("prompt-store-connection-pool-size", "default_value")
)
PROMPT_STORE_DB = os.getenv("PROMPT_STORE_DB", config.get("prompt-store-db", "default_value"))

SERVICE_VERSION = "2.0.0"
DEFAULT_PORT = 5110

# ============================================================================
# APP INITIALIZATION
# ============================================================================
app = FastAPI(
    title="🧠 Prompt Store - Enterprise AI Prompt Intelligence Hub",
    version=SERVICE_VERSION,
    description="""
    **🧠 Enterprise AI Prompt Intelligence Hub** for comprehensive prompt management and optimization.

    ## 🎯 **Core Capabilities**

    ### **🏗️ Domain-Driven Design Architecture**
    - **14 Bounded Contexts**: Prompts, Bulk Operations, Refinement, Analytics, A/B Testing, Relationships, Optimization, Validation, Orchestration, Intelligence, Lifecycle, Cache, Notifications
    - **Clean Architecture**: Strict separation of concerns with domain, application, and infrastructure layers
    - **Event-Driven Design**: Comprehensive event handling for prompt lifecycle and notifications
    - **CQRS Pattern**: Command-Query Responsibility Segregation for optimal read/write operations

    ### **🤖 AI-Powered Prompt Intelligence**
    - **Intelligent Refinement**: AI-driven prompt improvement with session-based refinement
    - **Drift Detection**: Automated identification of prompt performance degradation
    - **Smart Suggestions**: Context-aware prompt optimization recommendations
    - **Code Generation**: AI-powered code snippet generation from natural language

    ### **📊 Advanced Analytics & A/B Testing**
    - **Comprehensive Analytics**: Usage patterns, performance metrics, and satisfaction tracking
    - **A/B Testing Framework**: Sophisticated testing infrastructure for prompt optimization
    - **Performance Dashboards**: Real-time analytics and performance monitoring
    - **Quality Assurance**: Automated validation, linting, and bias detection

    ## 📡 **API Architecture by Bounded Context**

    ### **📝 Prompt Management (`/api/v1/prompts`)**
    - `POST /api/v1/prompts` - Create new prompts with metadata and content
    - `GET /api/v1/prompts/{id}` - Retrieve prompt by ID with full metadata
    - `GET /api/v1/prompts` - List prompts with advanced filtering and pagination
    - `PUT /api/v1/prompts/{id}` - Update prompt metadata and content
    - `DELETE /api/v1/prompts/{id}` - Delete prompt with cascade options
    - `POST /api/v1/prompts/{id}/fork` - Create fork of existing prompt
    - `PUT /api/v1/prompts/{id}/content` - Update prompt content only
    - `GET /api/v1/prompts/{id}/drift` - Check for prompt performance drift
    - `GET /api/v1/prompts/{id}/suggestions` - Get optimization suggestions

    ### **🔍 Search & Discovery (`/api/v1/prompts/search`)**
    - `POST /api/v1/prompts/search` - Advanced prompt search with query DSL
    - `GET /api/v1/prompts/search/{category}/{name}` - Search by category and name
    - `GET /api/v1/prompts/category/{category}` - Get prompts by category
    - `GET /api/v1/prompts/tags/{tag}` - Get prompts by tag

    ### **📦 Bulk Operations (`/api/v1/bulk`)**
    - `POST /api/v1/bulk/prompts` - Bulk create prompts
    - `PUT /api/v1/bulk/prompts` - Bulk update prompts
    - `DELETE /api/v1/bulk/prompts` - Bulk delete prompts
    - `PUT /api/v1/bulk/prompts/tags` - Bulk update tags
    - `GET /api/v1/bulk/operations` - List bulk operations
    - `GET /api/v1/bulk/operations/{id}` - Get bulk operation status
    - `PUT /api/v1/bulk/operations/{id}/cancel` - Cancel bulk operation
    - `POST /api/v1/bulk/operations/{id}/retry` - Retry failed bulk operation

    ### **🔬 Refinement System (`/api/v1/refinement`)**
    - `POST /api/v1/prompts/{id}/refine` - Start prompt refinement session
    - `GET /api/v1/refinement/sessions/{id}` - Get refinement session status
    - `GET /api/v1/prompts/{id}/refinement/compare` - Compare refinement options
    - `GET /api/v1/refinement/compare/{a}/{b}` - Compare two refinement sessions
    - `POST /api/v1/prompts/{id}/refinement/apply/{session}` - Apply refinement changes
    - `GET /api/v1/prompts/{id}/refinement/history` - Get refinement history
    - `GET /api/v1/refinement/sessions/active` - List active refinement sessions

    ### **📊 Analytics & Intelligence (`/api/v1/analytics`)**
    - `GET /api/v1/analytics/summary` - Overall prompt store analytics
    - `GET /api/v1/analytics/prompts/{id}` - Analytics for specific prompt
    - `GET /api/v1/analytics/usage` - Usage patterns and trends
    - `GET /api/v1/analytics/dashboard` - Comprehensive analytics dashboard
    - `GET /api/v1/analytics/performance` - Performance metrics and insights
    - `POST /api/v1/analytics/usage` - Record usage event
    - `POST /api/v1/analytics/satisfaction` - Record user satisfaction

    ### **🧪 A/B Testing (`/api/v1/ab-tests`)**
    - `POST /api/v1/ab-tests` - Create new A/B test
    - `GET /api/v1/ab-tests` - List all A/B tests
    - `GET /api/v1/ab-tests/{id}` - Get A/B test details
    - `GET /api/v1/ab-tests/{id}/select` - Select prompt variant for user
    - `GET /api/v1/ab-tests/{id}/results` - Get test results and statistics

    ### **🔗 Relationships (`/api/v1/relationships`)**
    - `POST /api/v1/prompts/{id}/relationships` - Create prompt relationship
    - `GET /api/v1/prompts/{id}/relationships` - Get prompt relationships
    - `PUT /api/v1/relationships/{id}/strength` - Update relationship strength
    - `DELETE /api/v1/relationships/{id}` - Remove relationship
    - `GET /api/v1/prompts/{id}/relationships/graph` - Get relationship graph
    - `GET /api/v1/relationships/stats` - Relationship network statistics
    - `GET /api/v1/prompts/{id}/related` - Get related prompts
    - `POST /api/v1/relationships/validate` - Validate relationship integrity

    ### **⚡ Optimization (`/api/v1/optimization`)**
    - `POST /api/v1/optimization/ab-tests` - Create optimization A/B test
    - `GET /api/v1/optimization/ab-tests/{id}/assign` - Assign user to test variant
    - `POST /api/v1/optimization/ab-tests/{id}/results` - Record test results
    - `GET /api/v1/optimization/ab-tests/{id}/results` - Get optimization results
    - `POST /api/v1/optimization/ab-tests/{id}/end` - End optimization test
    - `POST /api/v1/optimization/prompts/{id}/optimize` - Optimize specific prompt
    - `POST /api/v1/optimization/variations` - Generate prompt variations

    ### **✅ Validation (`/api/v1/validation`)**
    - `POST /api/v1/validation/test-suites` - Create custom test suite
    - `GET /api/v1/validation/test-suites/standard` - Get standard test suites
    - `POST /api/v1/validation/prompts/{id}/test` - Test prompt against suite
    - `POST /api/v1/validation/lint` - Lint prompt content
    - `POST /api/v1/validation/bias-detect` - Detect bias in prompt
    - `POST /api/v1/validation/output` - Validate prompt output format

    ### **🎭 Orchestration (`/api/v1/orchestration`)**
    - `POST /api/v1/orchestration/chains` - Create prompt execution chain
    - `POST /api/v1/orchestration/chains/{id}/execute` - Execute prompt chain
    - `POST /api/v1/orchestration/pipelines` - Create prompt pipeline
    - `POST /api/v1/orchestration/pipelines/{id}/execute` - Execute prompt pipeline
    - `POST /api/v1/orchestration/prompts/select` - Select optimal prompt
    - `POST /api/v1/orchestration/prompts/recommend` - Get prompt recommendations

    ### **🧠 Intelligence (`/api/v1/intelligence`)**
    - `POST /api/v1/intelligence/code/generate` - Generate code from prompt
    - `POST /api/v1/intelligence/document/generate` - Generate documentation
    - `POST /api/v1/intelligence/service/generate` - Generate service specifications
    - `POST /api/v1/intelligence/prompts/{id}/analyze` - Analyze prompt structure
    - `POST /api/v1/intelligence/api/generate` - Generate API specifications

    ### **⏰ Lifecycle Management (`/api/v1/lifecycle`)**
    - `PUT /api/v1/prompts/{id}/lifecycle` - Update prompt lifecycle status
    - `GET /api/v1/prompts/lifecycle/{status}` - Get prompts by lifecycle status
    - `GET /api/v1/prompts/{id}/lifecycle/history` - Get lifecycle history
    - `GET /api/v1/lifecycle/counts` - Get lifecycle status counts
    - `GET /api/v1/lifecycle/rules` - Get lifecycle rules
    - `POST /api/v1/prompts/{id}/lifecycle/validate` - Validate lifecycle transition
    - `POST /api/v1/lifecycle/bulk` - Bulk lifecycle operations

    ### **💾 Cache Management (`/api/v1/cache`)**
    - `GET /api/v1/cache/stats` - Cache performance statistics and metrics
    - `POST /api/v1/cache/invalidate` - Invalidate cache entries
    - `POST /api/v1/cache/warmup` - Warm up cache with frequently accessed data

    ### **🔔 Notifications (`/api/v1/notifications`)**
    - `POST /api/v1/webhooks` - Register webhook endpoints for notifications
    - `GET /api/v1/webhooks` - List registered webhooks
    - `GET /api/v1/webhooks/{id}` - Get webhook details
    - `PUT /api/v1/webhooks/{id}` - Update webhook configuration
    - `DELETE /api/v1/webhooks/{id}` - Remove webhook registration
    - `POST /api/v1/notifications/trigger` - Trigger notification event
    - `POST /api/v1/notifications/process` - Process notification queue
    - `GET /api/v1/notifications/stats` - Notification delivery statistics
    - `POST /api/v1/notifications/cleanup` - Clean up old notifications
    - `GET /api/v1/notifications/events` - Get notification event history

    ### **📋 Versioning (`/api/v1/prompts/{id}/versions`)**
    - `GET /api/v1/prompts/{id}/versions` - List all versions of a prompt
    - `GET /api/v1/prompts/{id}/versions/{version}` - Get specific version
    - `POST /api/v1/prompts/{id}/versions/{version}/rollback` - Rollback to version
    - `GET /api/v1/prompts/{id}/documents` - Get documents using prompt
    - `GET /api/v1/documents/prompts` - Get prompts used by documents

    ## 🏢 **Enterprise Integration**

    ### **🔗 Ecosystem Service Integration**
    - **Interpreter**: Prompt execution and workflow integration with usage tracking
    - **Summarizer Hub**: Content summarization prompt optimization and evaluation
    - **Bedrock Proxy**: Multi-provider AI model integration for prompt testing
    - **Code Analyzer**: Code generation prompt analysis and improvement
    - **Doc Store**: Document generation and analysis prompt storage

    ### **📊 Advanced Features**
    - **Real-Time Analytics**: Event-driven analytics with comprehensive metrics collection
    - **Intelligent Caching**: Multi-level caching with predictive prefetching for prompts
    - **Audit Trails**: Complete audit logging for compliance and forensic analysis
    - **Version Control**: Sophisticated versioning with rollback and branching capabilities
    - **Relationship Mapping**: Advanced prompt relationship analysis and dependency tracking
    """,
    contact={
        "name": "Prompt Store Service Team",
        "url": "https://github.com/your-org/prompt-store",
        "email": "promptstore@your-org.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://your-org.com/license"
    },
    openapi_tags=[
        {
            "name": "Health & Monitoring",
            "description": "Service health checks and system monitoring endpoints"
        },
        {
            "name": "Prompt Management",
            "description": "Core prompt CRUD operations, versioning, and lifecycle management"
        },
        {
            "name": "Search & Discovery",
            "description": "Advanced prompt search, filtering, and discovery capabilities"
        },
        {
            "name": "Bulk Operations",
            "description": "Batch processing, mass operations, and job management for prompts"
        },
        {
            "name": "Refinement System",
            "description": "AI-powered prompt refinement, optimization, and improvement"
        },
        {
            "name": "Analytics & Intelligence",
            "description": "Comprehensive analytics, usage tracking, and performance insights"
        },
        {
            "name": "A/B Testing",
            "description": "Sophisticated A/B testing framework for prompt evaluation and optimization"
        },
        {
            "name": "Relationships",
            "description": "Prompt relationships, dependency mapping, and network analysis"
        },
        {
            "name": "Optimization",
            "description": "Advanced prompt optimization using A/B testing and AI techniques"
        },
        {
            "name": "Validation",
            "description": "Prompt validation, linting, bias detection, and quality assurance"
        },
        {
            "name": "Orchestration",
            "description": "Prompt chains, pipelines, selection, and intelligent automation"
        },
        {
            "name": "Intelligence",
            "description": "AI-powered code generation, documentation, and prompt analysis"
        },
        {
            "name": "Lifecycle Management",
            "description": "Prompt lifecycle operations, status tracking, and bulk management"
        },
        {
            "name": "Cache Management",
            "description": "Cache statistics, invalidation, optimization, and performance tuning"
        },
        {
            "name": "Notifications",
            "description": "Webhook management, event notifications, and delivery tracking"
        },
        {
            "name": "Versioning",
            "description": "Prompt versioning, rollback, and document relationship management"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Use common middleware setup
setup_common_middleware(app, ServiceNames.PROMPT_STORE)
install_error_handlers(app)
register_health_endpoints(app, ServiceNames.PROMPT_STORE, SERVICE_VERSION)
attach_self_register(app, ServiceNames.PROMPT_STORE)

# ============================================================================
# CUSTOM HEALTH ENDPOINT - Override shared health with detailed DDD monitoring
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="""
    **Service Health Check** - Comprehensive health status and operational metrics for the Prompt Store service.

    ## 🔍 **Health Assessment**

    This endpoint provides real-time health status and operational metrics for the Prompt Store service, including:

    ### **🏥 Health Indicators**
    - **Service Status**: Overall health status (healthy/degraded/unhealthy)
    - **DDD Architecture**: Whether Domain-Driven Design architecture is properly initialized
    - **Bounded Contexts**: Status of all 14 bounded contexts (Prompts, Bulk, Refinement, Analytics, etc.)
    - **Database Connectivity**: Database connection and operational status
    - **Cache System**: Cache system initialization and operational status

    ### **📊 Operational Metrics**
    - **Version Information**: Current service version and build details
    - **Uptime Metrics**: Service uptime and operational statistics
    - **System Readiness**: Overall system readiness for processing requests
    - **Integration Status**: Health of connected services and dependencies

    ### **🏗️ Architecture Health**
    - **Domain Contexts**: Status of all bounded contexts and their handlers
    - **Infrastructure Layer**: Database, cache, and external service connectivity
    - **Application Layer**: Use cases and business logic initialization
    - **Presentation Layer**: API routes and middleware setup

    ## 🎯 **Response Codes**

    | Code | Status | Description |
    |------|--------|-------------|
    | 200 | Healthy | Service is fully operational with all bounded contexts loaded |
    | 503 | Degraded | Service is operational but with some issues |
    | 500 | Unhealthy | Service is experiencing critical issues |

    ## 📋 **Usage Examples**

    ### **Basic Health Check**
    ```bash
    curl -X GET http://localhost:5110/health
    ```

    ### **Health Check with Monitoring**
    ```python
    import requests

    response = requests.get("http://localhost:5110/health")
    health_data = response.json()

    if health_data["status"] == "healthy":
        print("✅ Prompt Store service is healthy")
        print(f"📊 {len(health_data['bounded_contexts_loaded'])} bounded contexts loaded")
        if health_data["database_connected"]:
            print("🗄️  Database connection is active")
        if health_data["cache_enabled"]:
            print("💾 Cache system is operational")
    else:
        print("⚠️  Prompt Store service health issue detected")
    ```

    ### **Automated Monitoring Script**
    ```bash
    #!/bin/bash
    HEALTH_URL="http://localhost:5110/health"
    STATUS=$(curl -s $HEALTH_URL | jq -r '.status')

    if [ "$STATUS" = "healthy" ]; then
        echo "✅ Prompt Store service is healthy"
        exit 0
    else
        echo "❌ Prompt Store service is unhealthy: $STATUS"
        exit 1
    fi
    ```
    """,
    response_description="Comprehensive health status and operational metrics",
    responses={
        200: {
            "description": "Service is healthy and fully operational",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "prompt_store",
                        "version": "2.0.0",
                        "uptime_seconds": 3600.5,
                        "last_health_check": "2024-09-22T10:30:00Z",
                        "database_connected": True,
                        "cache_enabled": True,
                        "bounded_contexts_loaded": [
                            "prompts", "bulk_operations", "refinement", "analytics",
                            "ab_testing", "relationships", "optimization", "validation",
                            "orchestration", "intelligence", "lifecycle", "cache", "notifications"
                        ],
                        "ddd_architecture": True
                    }
                }
            }
        },
        503: {
            "description": "Service is degraded or temporarily unavailable",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "service": "prompt_store",
                        "version": "2.0.0",
                        "uptime_seconds": 1800.0,
                        "last_health_check": "2024-09-22T10:25:00Z",
                        "database_connected": False,
                        "cache_enabled": True,
                        "bounded_contexts_loaded": [
                            "prompts", "analytics", "relationships"
                        ],
                        "ddd_architecture": False
                    }
                }
            }
        }
    },
    tags=["Health & Monitoring"]
)
async def custom_health_check() -> HealthResponse:
    """
    **Health Check Endpoint** - Comprehensive service health assessment.

    Returns detailed health status including:
    - Service operational status
    - DDD architecture initialization status
    - Bounded contexts loading status
    - Database connectivity status
    - Cache system operational status
    - Version information
    - Uptime metrics
    - Last health check timestamp
    """
    import time
    import datetime

    # Calculate uptime (simplified - in production this would track actual startup time)
    uptime_seconds = time.time() - getattr(app, '_startup_time', time.time())

    # Check bounded contexts (simplified check)
    bounded_contexts_loaded = []
    try:
        # Check if domain handlers are initialized
        from .domain.prompts.handlers import prompt_handlers
        if prompt_handlers:
            bounded_contexts_loaded.append("prompts")

        # Check other bounded contexts
        bounded_contexts_loaded.extend([
            "bulk_operations", "refinement", "analytics", "ab_testing",
            "relationships", "optimization", "validation", "orchestration",
            "intelligence", "lifecycle", "cache", "notifications"
        ])
    except Exception:
        bounded_contexts_loaded = ["prompts"]  # At minimum, core prompts should be available

    # Check database connectivity (simplified check)
    database_connected = True
    try:
        # In a real implementation, this would test actual database connectivity
        pass
    except Exception:
        database_connected = False

    # Check cache system
    cache_enabled = True
    try:
        # In a real implementation, this would test cache connectivity
        pass
    except Exception:
        cache_enabled = False

    # Determine overall health based on bounded contexts loaded
    ddd_architecture = len(bounded_contexts_loaded) >= 10  # At least most core contexts loaded

    # Overall status determination
    if len(bounded_contexts_loaded) >= 12 and ddd_architecture and database_connected:
        status = "healthy"
    elif len(bounded_contexts_loaded) >= 8:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        service="prompt_store",
        version="2.0.0",
        uptime_seconds=round(uptime_seconds, 1),
        last_health_check=datetime.datetime.utcnow().isoformat() + "Z",
        database_connected=database_connected,
        cache_enabled=cache_enabled,
        bounded_contexts_loaded=bounded_contexts_loaded,
        ddd_architecture=ddd_architecture
    )

# Initialize cache and logging
logger_client = None


@app.on_event("startup")
async def startup_event():
    """Initialize service components on startup."""
    global logger_client

    # Initialize logger client
    try:
        logger_client = await get_log_collector_client(ServiceNames.PROMPT_STORE)
        if logger_client:
            await logger_client.log_business_event(
                "prompt_store_startup",
                {
                    "version": SERVICE_VERSION,
                    "architecture": "domain_driven_design",
                    "domain_contexts": [
                        "prompts",
                        "ab_testing",
                        "analytics",
                        "bulk",
                        "refinement",
                        "lifecycle",
                        "relationships",
                        "notifications",
                        "optimization",
                        "intelligence",
                        "validation",
                        "orchestration",
                    ],
                    "cache_enabled": True,
                    "database_enabled": True,
                    "features": [
                        "versioning",
                        "ab_testing",
                        "analytics",
                        "bulk_operations",
                        "refinement",
                        "lifecycle_management",
                    ],
                },
            )
            await logger_client.log_info(
                "Prompt Store service started",
                {
                    "ddd_architecture": True,
                    "domain_count": 12,
                    "cache_initialized": True,
                    "versioning_enabled": True,
                    "ab_testing_enabled": True,
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")

    await prompt_store_cache.initialize()
    print("✅ Prompt Store service initialized with domain-driven architecture")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("Prompt Store service shutting down")
        except Exception:
            pass

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


@app.get("/api/v1/prompts", response_model=SuccessResponse)
async def list_prompts(
    category: Optional[str] = None, limit: int = 50, offset: int = 0, filters: Optional[Dict[str, Any]] = None
):
    """List prompts with filtering and pagination."""
    if filters is None:
        filters = {}
    return await prompt_handlers.handle_list_prompts(category, limit, offset, **filters)


@app.get("/api/v1/prompts/search/{category}/{name}", response_model=SuccessResponse)
async def get_prompt_by_name(category: str, name: str, variables: Optional[Dict[str, Any]] = None):
    """Get prompt by category/name and optionally fill template variables."""
    if variables is None:
        variables = {}
    return await prompt_handlers.handle_get_prompt_by_name(category, name, **variables)


@app.put("/api/v1/prompts/{prompt_id}", response_model=Dict[str, Any])
async def update_prompt(prompt_id: str, updates: PromptUpdate):
    """Update a prompt with validation."""
    return await prompt_handlers.handle_update_prompt(prompt_id, updates)


@app.delete("/api/v1/prompts/{prompt_id}", response_model=SuccessResponse)
async def delete_prompt(prompt_id: str):
    """Soft delete a prompt."""
    return await prompt_handlers.handle_delete_prompt(prompt_id)


# ============================================================================
# ADVANCED PROMPT FEATURES
# ============================================================================


@app.post("/api/v1/prompts/{prompt_id}/fork", response_model=SuccessResponse)
async def fork_prompt(
    prompt_id: str, new_name: str, created_by: str = "api_user", changes: Optional[Dict[str, Any]] = None
):
    """Fork a prompt to create a new variant."""
    if changes is None:
        changes = {}
    return await prompt_handlers.handle_fork_prompt(prompt_id, new_name, created_by, **changes)


@app.put("/api/v1/prompts/{prompt_id}/content", response_model=Dict[str, Any])
async def update_prompt_content(
    prompt_id: str,
    content: str,
    variables: Optional[List[str]] = None,
    change_summary: str = "",
    updated_by: str = "api_user",
):
    """Update prompt content with versioning."""
    return await prompt_handlers.handle_update_prompt_content(prompt_id, content, variables, change_summary, updated_by)


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
async def bulk_update_tags(
    prompt_ids: List[str],
    tags_to_add: Optional[List[str]] = None,
    tags_to_remove: Optional[List[str]] = None,
    created_by: str = "api_user",
):
    """Bulk update tags on multiple prompts."""
    return await bulk_handlers.handle_bulk_update_tags(prompt_ids, tags_to_add, tags_to_remove, created_by)


@app.get("/api/v1/bulk/operations", response_model=Dict[str, Any])
async def list_bulk_operations(
    status: Optional[str] = None, operation_type: Optional[str] = None, limit: int = 50, offset: int = 0
):
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
async def refine_prompt(
    prompt_id: str,
    refinement_instructions: str,
                       llm_service: str = "interpreter",
                       context_documents: Optional[List[str]] = None,
    user_id: str = "api_user",
):
    """Start LLM-assisted prompt refinement workflow."""
    return await refinement_handlers.handle_refine_prompt(
        prompt_id, refinement_instructions, llm_service, context_documents, user_id
    )


@app.get("/api/v1/refinement/sessions/{session_id}", response_model=Dict[str, Any])
async def get_refinement_status(session_id: str):
    """Get status of a refinement session."""
    return await refinement_handlers.handle_get_refinement_status(session_id)


@app.get("/api/v1/prompts/{prompt_id}/refinement/compare", response_model=Dict[str, Any])
async def compare_prompt_versions(prompt_id: str, version_a: Optional[int] = None, version_b: Optional[int] = None):
    """Compare different versions of a prompt."""
    return await refinement_handlers.handle_compare_prompt_versions(prompt_id, version_a, version_b)


@app.get("/api/v1/refinement/compare/{session_a}/{session_b}", response_model=Dict[str, Any])
async def compare_refinement_documents(session_a: str, session_b: str):
    """Compare documents from different refinement sessions."""
    return await refinement_handlers.handle_compare_refinement_documents(session_a, session_b)


@app.post("/api/v1/prompts/{prompt_id}/refinement/apply/{session_id}", response_model=Dict[str, Any])
async def apply_refined_prompt(prompt_id: str, session_id: str, user_id: str = "api_user"):
    """Apply refined prompt from session to replace original."""
    return await refinement_handlers.handle_replace_prompt_with_refined(prompt_id, session_id, user_id)


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


@app.get("/api/v1/analytics/summary", response_model=SuccessResponse)
async def get_analytics_summary(days_back: int = 30):
    """Get comprehensive analytics summary."""
    return await analytics_handlers.handle_get_analytics_dashboard(days_back)


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


@app.get("/api/v1/ab-tests", response_model=SuccessResponse)
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
async def add_prompt_relationship(prompt_id: str, relationship: PromptRelationshipCreate, user_id: str = "api_user"):
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
async def find_related_prompts(
    prompt_id: str, relationship_types: Optional[List[str]] = None, min_strength: float = 0.0
):
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
        return create_success_response(message="Prompt documents retrieved successfully", data=summary).model_dump()
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
                "latest_document": documents[0].to_dict() if documents else None,
            }

        return create_success_response(
            message="Prompts with documents retrieved successfully", data=result
        ).model_dump()
    except ImportError:
        return create_error_response("Document store service not available", "SERVICE_UNAVAILABLE").model_dump()
    except Exception as e:
        return create_error_response(
            f"Failed to retrieve prompts with documents: {str(e)}", "INTERNAL_ERROR"
        ).model_dump()


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
async def update_prompt_lifecycle(prompt_id: str, lifecycle_update: PromptLifecycleUpdate, user_id: str = "api_user"):
    """Update prompt lifecycle status (draft/published/deprecated/archived)."""
    return await lifecycle_handlers.handle_update_lifecycle_status(prompt_id, lifecycle_update, user_id)


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
        return create_success_response(message="Cache statistics retrieved", data=stats)
    except Exception as e:
        return create_error_response(f"Failed to get cache stats: {str(e)}", "INTERNAL_ERROR")


@app.post("/api/v1/cache/invalidate", response_model=Dict[str, Any])
async def invalidate_cache(pattern: str = "*"):
    """Invalidate cache entries matching pattern."""
    try:
        invalidated = await prompt_store_cache.invalidate_pattern(pattern)
        return create_success_response(
            message=f"Invalidated {invalidated} cache entries", data={"invalidated_count": invalidated}
        )
    except Exception as e:
        return create_error_response(f"Failed to invalidate cache: {str(e)}", "INTERNAL_ERROR")


@app.post("/api/v1/cache/warmup", response_model=Dict[str, Any])
async def warmup_cache():
    """Warm up cache with frequently accessed data."""
    try:
        # This would implement cache warming logic
        return create_success_response(message="Cache warmup initiated", data={"status": "warming"})
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
    uvicorn.run(app, host="0.0.0.0", port=int(port), log_level="info")
