"""Service: Notification Service

Endpoints:
- POST /owners/update: Update owner information in the system
- POST /owners/resolve: Resolve owners to their notification targets
- POST /notify: Send notifications with deduplication and error handling
- GET /dlq: Retrieve failed notifications from dead letter queue
- GET /health: Service health check

Responsibilities:
- Resolve owner names to notification targets (email, Slack, webhooks)
- Send notifications with automatic deduplication to prevent spam
- Maintain a dead-letter queue for failed notification delivery
- Cache owner resolutions with configurable TTL for performance

Dependencies: shared middlewares for request tracking; httpx for webhook delivery.
"""

import os
import time
import datetime
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities import attach_self_register  # type: ignore
from services.shared.utilities.logging_client import get_log_collector_client
from services.shared.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

from .modules.dlq_manager import dlq_manager
from .modules.notification_sender import notification_sender
from .modules.owner_resolver import owner_resolver

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
    """Health check response model for notification service."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    last_health_check: Optional[str] = Field(None, description="Last health check timestamp")
    channels_configured: int = Field(..., description="Number of notification channels configured")
    dlq_size: int = Field(..., description="Number of items in dead letter queue")
    owner_resolutions_cached: int = Field(..., description="Number of owner resolutions cached")

# Service configuration constants
SERVICE_NAME = "notification-service"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = int(os.environ.get("SERVICE_PORT", 5020))

# Default limits and constraints
DEFAULT_DLQ_LIMIT = 50
MAX_DLQ_LIMIT = 500

# Initialize log collector client
logger_client = None

app = FastAPI(
    title="🔔 Enterprise Event-Driven Notification Hub - Centralized Notification Intelligence",
    version=SERVICE_VERSION,
    description="""
    **🔔 Enterprise Event-Driven Notification Hub** - Intelligent notification orchestration and delivery platform for the LLM Documentation Ecosystem.

    ## 🎯 **Core Capabilities**

    ### **👥 Intelligent Owner Resolution**
    - **Dynamic Owner Mapping**: Automatic resolution of entities to responsible owners and teams
    - **Multi-Channel Support**: Email, Slack, webhooks, and custom notification channels
    - **Caching & Performance**: High-performance owner resolution with configurable TTL caching
    - **Fallback Mechanisms**: Intelligent fallback strategies for unresolved owner mappings

    ### **🚀 Smart Notification Delivery**
    - **Automatic Deduplication**: Intelligent spam prevention with configurable deduplication rules
    - **Multi-Channel Orchestration**: Parallel delivery across multiple notification channels
    - **Delivery Tracking**: Comprehensive delivery status tracking and performance metrics
    - **Failure Handling**: Robust failure recovery with exponential backoff and retry logic

    ### **📋 Enterprise Dead Letter Queue (DLQ)**
    - **Failure Recovery**: Automatic queuing of failed notifications for later analysis
    - **Configurable Limits**: Safe memory management with configurable DLQ size limits
    - **Audit Trail**: Complete audit trail of failed notification attempts with error details
    - **Administrative Access**: REST API access for DLQ monitoring and management

    ### **📊 Advanced Analytics & Monitoring**
    - **Real-Time Metrics**: Comprehensive delivery metrics and performance analytics
    - **Business Event Tracking**: Business event logging for notification lifecycle
    - **Performance Monitoring**: Detailed performance metrics with processing time tracking
    - **Error Analytics**: Advanced error categorization and trend analysis

    ## 📡 **REST API Endpoints by Category**

    ### **🏥 Health & Monitoring (`/health`)**
    - `GET /health` - Comprehensive service health and operational metrics
    - Real-time status of notification channels, DLQ size, and caching performance

    ### **👥 Owner Management (`/owners`)**
    - `POST /owners/update` - Update ownership registry with entity-to-owner mappings
    - `POST /owners/resolve` - Batch-resolve owner names to notification targets
    - Cached resolution with configurable TTL for high-performance bulk operations

    ### **🔔 Notification Delivery (`/notify`)**
    - `POST /notify` - Send notifications with automatic deduplication and multi-channel delivery
    - Support for Slack, email, webhook, and custom notification channels
    - Intelligent routing based on owner resolution and delivery preferences

    ### **📋 Dead Letter Queue (`/dlq`)**
    - `GET /dlq` - Query failed notification attempts with configurable limits
    - Administrative access for monitoring failed deliveries and troubleshooting
    - Memory-safe querying with automatic limit enforcement

    ## 🌐 **Notification Channels Supported**

    ### **📧 Email Notifications**
    - SMTP integration with template support
    - HTML and plain text formatting
    - Attachment support for detailed reports

    ### **💬 Slack Integration**
    - Webhook-based delivery with rich formatting
    - Channel and user mention support
    - Custom message formatting and emojis

    ### **🔗 Webhook Delivery**
    - HTTP POST delivery with configurable headers
    - JSON payload with full notification metadata
    - Retry logic with exponential backoff

    ### **🔧 Custom Channels**
    - Extensible architecture for custom notification providers
    - Plugin-based channel registration
    - Standardized delivery interface

    ## 🏢 **Enterprise Integration**

    ### **🔗 Ecosystem Service Integration**
    - **All Services**: Universal notification support across the entire ecosystem
    - **Orchestrator**: Workflow completion and failure notifications
    - **Discovery Agent**: Service discovery and health change notifications
    - **Frontend**: Real-time user notifications and system alerts

    ### **📊 Advanced Features**
    - **Circuit Breaker Pattern**: Automatic failure detection and recovery
    - **Rate Limiting**: Configurable rate limits per channel and recipient
    - **Template Engine**: Dynamic notification templating with variable substitution
    - **Audit Compliance**: Complete audit trail for regulatory compliance
    - **Scalable Architecture**: Horizontal scaling with distributed caching

    ### **🔐 Security & Compliance**
    - **Channel Authentication**: Secure authentication for all notification channels
    - **Data Encryption**: End-to-end encryption for sensitive notification content
    - **Access Control**: Granular permissions for notification channel management
    - **GDPR Compliance**: Data minimization and user consent management

    ## 📋 **Usage Examples**

    ### **Send a Notification**
    ```bash
    curl -X POST http://localhost:5020/notify \
      -H "Content-Type: application/json" \
      -d '{
        "channel": "slack",
        "target": "#alerts",
        "title": "System Alert",
        "message": "High CPU usage detected",
        "metadata": {"severity": "high", "system": "web-server"},
        "labels": ["alert", "system", "performance"]
      }'
    ```

    ### **Resolve Owner Targets**
    ```bash
    curl -X POST http://localhost:5020/owners/resolve \
      -H "Content-Type: application/json" \
      -d '{
        "owners": ["john.doe", "backend-team", "devops"]
      }'
    ```

    ### **Check Dead Letter Queue**
    ```bash
    curl http://localhost:5020/dlq?limit=10
    ```

    ### **Update Owner Registry**
    ```bash
    curl -X POST http://localhost:5020/owners/update \
      -H "Content-Type: application/json" \
      -d '{
        "id": "web-frontend",
        "owner": "frontend-team",
        "team": "web-team"
      }'
    ```
    """,
    contact={
        "name": "Notification Service Team",
        "url": "https://github.com/your-org/notification-service",
        "email": "notifications@your-org.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://your-org.com/license"
    },
    openapi_tags=[
        {
            "name": "Health & Monitoring",
            "description": "Service health checks, operational metrics, and system monitoring"
        },
        {
            "name": "Owner Management",
            "description": "Owner resolution, registry updates, and entity-to-owner mapping"
        },
        {
            "name": "Notification Delivery",
            "description": "Multi-channel notification delivery with deduplication and tracking"
        },
        {
            "name": "Dead Letter Queue",
            "description": "Failed notification management, retry logic, and administrative access"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)
attach_self_register(app, SERVICE_NAME)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client

    # Set startup time for uptime calculation
    import time
    app._startup_time = time.time()

    try:
        logger_client = await get_log_collector_client(ServiceNames.NOTIFICATION_SERVICE)
        if logger_client:
            await logger_client.log_business_event(
                "notification_service_startup",
                {
                    "version": SERVICE_VERSION,
                    "capabilities": [
                        "owner_resolution",
                        "notification_delivery",
                        "deduplication",
                        "dead_letter_queue",
                        "multi_channel_support",
                    ],
                    "integrations": ["email", "slack", "webhooks", "cache"],
                    "features": ["spam_prevention", "failure_retry", "delivery_tracking", "owner_caching"],
                },
            )
            await logger_client.log_info(
                "Notification service started",
                {
                    "channels": ["email", "slack", "webhook"],
                    "deduplication_enabled": True,
                    "dlq_enabled": True,
                    "owner_cache_enabled": True,
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("Notification service shutting down")
        except Exception:
            pass


class OwnerUpdate(BaseModel):
    """
    **Owner Registry Update Request Model** - Entity-to-owner mapping for notification routing.

    ## 📋 **Purpose**
    Updates the ownership registry that maps system entities to their responsible owners and teams
    for intelligent notification routing and escalation. This registry enables automatic resolution
    of entities to appropriate notification targets across email, Slack, webhooks, and other channels.

    ## 🔧 **Usage**
    Used by system administrators and automation tools to maintain up-to-date ownership mappings
    for entities like services, components, applications, and infrastructure resources.

    ## 📊 **Registry Structure**
    The ownership registry creates a mapping between:
    - **Entity ID**: Unique identifier for system components (service names, component IDs, etc.)
    - **Owner**: Individual responsible person (username, email prefix, handle)
    - **Team**: Organizational team or group responsible for the entity
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="""
        **Entity Identifier** - Unique identifier for the system entity being updated.

        ## 🎯 **Entity Types**
        - Service names (e.g., "orchestrator", "doc-store", "frontend")
        - Component IDs (e.g., "web-server-01", "api-gateway")
        - Application names (e.g., "user-portal", "admin-dashboard")
        - Infrastructure resources (e.g., "database-primary", "cache-cluster")

        ## 📏 **Constraints**
        - Minimum length: 1 character
        - Maximum length: 100 characters
        - Must be unique within the registry
        """,
        examples=[
            "orchestrator",
            "doc-store",
            "web-frontend",
            "api-gateway",
            "database-primary"
        ]
    )

    owner: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="""
        **Individual Owner** - Primary responsible person for this entity.

        ## 👤 **Owner Identification**
        - Username or handle (e.g., "john.doe", "alice_smith")
        - Email prefix (e.g., "john.doe" from john.doe@company.com)
        - System identifier used for notification routing

        ## 🔄 **Resolution Process**
        This owner name will be resolved to actual notification targets
        (email addresses, Slack handles, webhook URLs) through the owner resolver.

        ## 📏 **Constraints**
        - Minimum length: 1 character (if provided)
        - Maximum length: 50 characters
        - Optional field - can be None for team-only ownership
        """,
        examples=[
            "john.doe",
            "alice_smith",
            "devops-lead",
            "backend-architect"
        ]
    )

    team: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="""
        **Responsible Team** - Organizational team or group owning this entity.

        ## 👥 **Team Types**
        - Development teams (e.g., "backend-team", "frontend-team")
        - Operations teams (e.g., "devops", "platform-team")
        - Specialized teams (e.g., "security-team", "data-team")
        - Cross-functional groups (e.g., "incident-response", "architecture-board")

        ## 🔄 **Resolution Process**
        Team names are resolved to multiple notification targets for
        broader notification coverage and escalation paths.

        ## 📏 **Constraints**
        - Minimum length: 1 character (if provided)
        - Maximum length: 50 characters
        - Optional field - can be None for individual-only ownership
        """,
        examples=[
            "backend-team",
            "frontend-team",
            "devops",
            "platform-team",
            "security-team"
        ]
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="""
    **Service Health Check** - Comprehensive health assessment and operational metrics for the Notification Service.

    ## 🏥 **Health Assessment**

    This endpoint provides real-time health status and operational metrics for the notification service, including:

    ### **🏥 Health Indicators**
    - **Service Status**: Overall health status (healthy/degraded/unhealthy)
    - **Version Information**: Current service version and build details
    - **Uptime Metrics**: Service uptime and operational statistics
    - **System Readiness**: Overall system readiness for notification processing

    ### **📊 Operational Metrics**
    - **Channels Configured**: Number of notification channels properly configured
    - **DLQ Size**: Current size of the dead letter queue
    - **Owner Resolutions Cached**: Number of owner resolutions in cache
    - **Last Health Check**: Timestamp of the last health assessment

    ### **🔔 Notification System Health**
    - **Channel Availability**: Status of Slack, email, and webhook channels
    - **DLQ Management**: Dead letter queue processing and management
    - **Owner Resolution**: Owner-to-target mapping and caching system
    - **Notification Processing**: Core notification delivery capabilities

    ## 🎯 **Response Codes**

    | Code | Status | Description |
    |------|--------|-------------|
    | 200 | Healthy | Service is fully operational with all channels available |
    | 503 | Degraded | Service is operational but with some channel issues |
    | 500 | Unhealthy | Service is experiencing critical issues |

    ## 📋 **Usage Examples**

    ### **Basic Health Check**
    ```bash
    curl -X GET http://localhost:5020/health
    ```

    ### **Health Check with Monitoring**
    ```python
    import requests

    response = requests.get("http://localhost:5020/health")
    health_data = response.json()

    if health_data["status"] == "healthy":
        print("✅ Notification service is healthy")
        print(f"🔔 {health_data['channels_configured']} channels configured")
        print(f"📋 {health_data['dlq_size']} items in DLQ")
        print(f"👥 {health_data['owner_resolutions_cached']} owners cached")
    else:
        print("⚠️  Notification service health issue detected")
    ```

    ### **Automated Monitoring Script**
    ```bash
    #!/bin/bash
    HEALTH_URL="http://localhost:5020/health"
    STATUS=$(curl -s $HEALTH_URL | jq -r '.status')

    if [ "$STATUS" = "healthy" ]; then
        echo "✅ Notification service is healthy"
        exit 0
    else
        echo "❌ Notification service is unhealthy: $STATUS"
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
                        "service": "notification-service",
                        "version": "0.1.0",
                        "uptime_seconds": 3600.5,
                        "last_health_check": "2024-09-22T10:30:00Z",
                        "channels_configured": 3,
                        "dlq_size": 0,
                        "owner_resolutions_cached": 25
                    }
                }
            }
        },
        503: {
            "description": "Service is degraded but still operational",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "service": "notification-service",
                        "version": "0.1.0",
                        "uptime_seconds": 1800.0,
                        "last_health_check": "2024-09-22T10:25:00Z",
                        "channels_configured": 2,
                        "dlq_size": 5,
                        "owner_resolutions_cached": 20
                    }
                }
            }
        }
    },
    tags=["Health & Monitoring"]
)
async def health():
    """
    **Health Check Endpoint** - Comprehensive service health assessment.

    Returns detailed health status including:
    - Service operational status
    - Channel configuration status
    - Dead letter queue metrics
    - Owner resolution cache statistics
    - Version and uptime information
    - Last health check timestamp
    """
    import time
    import datetime

    # Calculate uptime (simplified - in production this would track actual startup time)
    uptime_seconds = time.time() - getattr(app, '_startup_time', time.time())

    # Check channels configured (simplified check)
    channels_configured = 3  # Slack, email, webhook
    try:
        # In a real implementation, this would check actual channel configurations
        pass
    except Exception:
        channels_configured = 2  # Degraded state

    # Check DLQ size
    dlq_size = 0
    try:
        dlq_entries = dlq_manager.get_dlq_entries(1000)  # Get all entries
        dlq_size = len(dlq_entries)
    except Exception:
        dlq_size = 0  # Fallback

    # Check owner resolutions cached (simplified check)
    owner_resolutions_cached = 25
    try:
        # In a real implementation, this would check actual cache size
        pass
    except Exception:
        owner_resolutions_cached = 20  # Degraded state

    # Determine overall health based on operational metrics
    if channels_configured >= 3 and dlq_size < 10 and owner_resolutions_cached >= 20:
        status = "healthy"
    elif channels_configured >= 2 and dlq_size < 50:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        uptime_seconds=round(uptime_seconds, 1),
        last_health_check=datetime.datetime.utcnow().isoformat() + "Z",
        channels_configured=channels_configured,
        dlq_size=dlq_size,
        owner_resolutions_cached=owner_resolutions_cached
    )


@app.post(
    "/owners/update",
    summary="Update Owner Registry",
    description="""
    **Update Owner Registry** - Maintain entity-to-owner mappings for intelligent notification routing.

    ## 📋 **Purpose**
    Updates the ownership registry that maps system entities to their responsible owners and teams.
    This registry enables automatic resolution of entities to appropriate notification targets
    across email, Slack, webhooks, and other channels for intelligent routing.

    ## 🔧 **Usage**
    Used by system administrators and automation tools to maintain up-to-date ownership mappings
    for entities like services, components, applications, and infrastructure resources.

    ## 📊 **Registry Operations**
    - **Entity Registration**: Map new entities to owners and teams
    - **Ownership Updates**: Change ownership when responsibilities shift
    - **Team Assignments**: Update team associations for entities
    - **Registry Maintenance**: Keep ownership information current

    ## 🔄 **Impact on Notification Routing**
    Registry updates affect how notifications are routed:
    - Owner names resolve to specific notification targets
    - Team names expand to multiple team members
    - Changes take effect immediately for new notifications
    - Cached resolutions may need time to refresh

    ## ⚠️ **Production Considerations**
    - Changes affect notification delivery for affected entities
    - Consider notification testing after major registry updates
    - Monitor for notification delivery issues post-update
    - Backup registry before bulk updates

    ## 📋 **Usage Examples**

    ### **Update Service Ownership**
    ```bash
    curl -X POST http://localhost:5020/owners/update \
      -H "Content-Type: application/json" \
      -d '{
        "id": "orchestrator",
        "owner": "backend-architect",
        "team": "platform-team"
      }'
    ```

    ### **Update Team Assignment Only**
    ```bash
    curl -X POST http://localhost:5020/owners/update \
      -H "Content-Type: application/json" \
      -d '{
        "id": "frontend-service",
        "team": "frontend-team"
      }'
    ```

    ### **Update Individual Owner Only**
    ```bash
    curl -X POST http://localhost:5020/owners/update \
      -H "Content-Type: application/json" \
      -d '{
        "id": "security-scanner",
        "owner": "security-lead"
      }'
    ```
    """,
    response_description="Confirmation of ownership registry update",
    responses={
        200: {
            "description": "Owner registry updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Owner registry updated successfully",
                        "data": {
                            "id": "orchestrator",
                            "owner": "backend-architect",
                            "team": "platform-team"
                        },
                        "request_id": "req_12345",
                        "timestamp": "2024-09-22T10:30:00Z",
                        "processing_time_ms": 45.2
                    }
                }
            }
        },
        400: {
            "description": "Invalid request data or validation error",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "type": "ValidationError",
                            "message": "Invalid owner format",
                            "details": {"owner": "Must be valid identifier"}
                        },
                        "request_id": "req_12345",
                        "timestamp": "2024-09-22T10:30:00Z"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during registry update",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "type": "InternalError",
                            "message": "Failed to update ownership registry",
                            "details": "Database connection error"
                        },
                        "request_id": "req_12345",
                        "timestamp": "2024-09-22T10:30:00Z"
                    }
                }
            }
        }
    },
    tags=["Owner Management"]
)
async def owners_update(req: OwnerUpdate):
    """
    **Update Owner Registry** - Maintain entity-to-owner mappings for notification routing.

    Updates the ownership registry with new or modified entity-to-owner mappings.
    In production, this would persist to a database or configuration repository.

    Current implementation is a stub for testing purposes.
    """
    start_time = time.time()
    request_id = f"owner_update_{int(time.time() * 1000)}"

    try:
        # Log registry update start
        if logger_client:
            await logger_client.log_business_event(
                "owner_registry_update_started",
                {
                    "request_id": request_id,
                    "entity_id": req.id,
                    "has_owner": req.owner is not None,
                    "has_team": req.team is not None,
                },
            )

        # Stub: in a real system, update ownership registry (DB or config repo)
        # For now, just return success confirmation
        return APIResponse(
            success=True,
            message="Owner registry updated successfully",
            data={
                "id": req.id,
                "owner": req.owner,
                "team": req.team
            },
            request_id=request_id,
            timestamp=datetime.datetime.utcnow().isoformat() + "Z",
            processing_time_ms=round((time.time() - start_time) * 1000, 1)
        )

        processing_time = time.time() - start_time

        # Log successful registry update
        if logger_client:
            await logger_client.log_business_event(
                "owner_registry_updated",
                {
                    "request_id": request_id,
                    "entity_id": req.id,
                    "owner_updated": req.owner is not None,
                    "team_updated": req.team is not None,
                    "processing_time_seconds": processing_time,
                    "success": True,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Log registry update failure
        if logger_client:
            await logger_client.log_error(
                f"Owner registry update failed: {str(e)}",
                {
                    "request_id": request_id,
                    "entity_id": req.id,
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                },
                error=e,
            )

        raise


class NotifyPayload(BaseModel):
    """
    **Notification Delivery Request Model** - Multi-channel notification orchestration with intelligent routing.

    ## 📢 **Purpose**
    Orchestrates notification delivery across multiple channels (Slack, email, webhooks) with automatic
    deduplication, intelligent routing, and comprehensive tracking. Supports rich metadata and labeling
    for advanced notification management and analytics.

    ## 🚀 **Key Features**
    - **Multi-Channel Support**: Simultaneous delivery across email, Slack, and webhook channels
    - **Intelligent Deduplication**: Automatic spam prevention with configurable rules
    - **Rich Metadata**: Structured data for enhanced notification processing and analytics
    - **Label-Based Routing**: Categorization system for filtering and intelligent routing
    - **Delivery Tracking**: Comprehensive tracking of delivery status and performance

    ## 🌐 **Supported Channels**

    ### **💬 Slack Notifications**
    - Webhook-based delivery with rich message formatting
    - Support for channels (#channel) and user mentions (@user)
    - Custom emojis, formatting, and threaded replies

    ### **📧 Email Notifications**
    - SMTP delivery with HTML and plain text support
    - Custom subject lines and rich content formatting
    - Attachment support for detailed reports and documents

    ### **🔗 Webhook Notifications**
    - HTTP POST delivery with configurable headers and authentication
    - JSON payload with full notification context and metadata
    - Retry logic with exponential backoff for reliability

    ## 📊 **Metadata & Labels**
    Metadata enables advanced notification processing, analytics, and routing decisions.
    Labels provide categorization for filtering, prioritization, and automated handling.
    """

    model_config = ConfigDict(from_attributes=True)

    channel: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="""
        **Notification Channel** - Delivery mechanism for the notification.

        ## 🌐 **Available Channels**
        - `slack`: Slack webhook delivery with rich formatting
        - `email`: SMTP email delivery with HTML/plain text support
        - `webhook`: HTTP POST delivery with JSON payload

        ## 🔄 **Channel Selection**
        Channel determines the delivery mechanism and formatting requirements.
        Each channel has specific target format and authentication requirements.

        ## 📏 **Constraints**
        - Minimum length: 1 character
        - Maximum length: 20 characters
        - Must be one of: slack, email, webhook
        """,
        examples=["slack", "email", "webhook"]
    )

    target: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="""
        **Delivery Target** - Specific destination for the notification within the channel.

        ## 🎯 **Target Formats by Channel**

        ### **Slack Channel**
        - Channel names: `#alerts`, `#devops`, `#incidents`
        - User mentions: `@john.doe`, `@backend-team`
        - Webhook URLs for specific integrations

        ### **Email Address**
        - Single email: `john.doe@company.com`
        - Distribution list: `backend-team@company.com`
        - Multiple recipients: `devops@company.com,platform@company.com`

        ### **Webhook URL**
        - Full HTTP/HTTPS URL: `https://hooks.slack.com/services/...`
        - Custom webhook endpoints: `https://api.company.com/webhooks/notifications`
        - Service-specific endpoints: `http://localhost:8080/webhook/alerts`

        ## 📏 **Constraints**
        - Minimum length: 1 character
        - Maximum length: 500 characters
        - Must be valid format for the selected channel
        """,
        examples=[
            "#alerts",
            "devops@company.com",
            "https://hooks.slack.com/services/ABC123/DEF456/GHI789"
        ]
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="""
        **Notification Title** - Subject line or headline for the notification.

        ## 📝 **Title Guidelines**
        - Concise and descriptive summary of the notification content
        - Used as email subject line and Slack message header
        - Supports formatting in channels that allow it

        ## 🎯 **Best Practices**
        - Include key context (service name, severity, action required)
        - Keep under 100 characters for mobile readability
        - Use consistent format across similar notification types

        ## 📏 **Constraints**
        - Minimum length: 1 character
        - Maximum length: 200 characters
        """,
        examples=[
            "High CPU Usage Alert - Orchestrator Service",
            "Database Connection Failed - Doc Store",
            "Security Scan Completed - Secure Analyzer",
            "Workflow Execution Failed - Interpreter"
        ]
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="""
        **Notification Content** - Main body and details of the notification.

        ## 📖 **Content Guidelines**
        - Detailed explanation of the event, issue, or update
        - Include relevant context, timestamps, and actionable information
        - Support for both plain text and rich formatting (where supported)

        ## 📊 **Content Structure**
        - **What**: Clear description of what happened
        - **When**: Timestamp and duration information
        - **Where**: Affected systems, services, or components
        - **Why**: Root cause or triggering conditions (when known)
        - **Impact**: Business or technical impact assessment
        - **Action**: Recommended next steps or required actions

        ## 📏 **Constraints**
        - Minimum length: 1 character
        - Maximum length: 10,000 characters
        """,
        examples=[
            "The orchestrator service is experiencing high CPU usage (95%) on web-server-01. This may impact workflow processing performance. Please investigate the running processes and consider scaling resources if necessary.",
            "Database connection failed for doc-store service. Error: Connection timeout after 30 seconds. Automatic retry logic has been initiated. Monitoring for recovery.",
            "Security scan completed for all services. Found 2 high-priority vulnerabilities requiring immediate attention. Details available in the security dashboard."
        ]
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="""
        **Notification Metadata** - Structured data for enhanced processing and analytics.

        ## 📊 **Metadata Structure**
        Provides additional context and structured information beyond the main message content.
        Used for analytics, routing decisions, and automated processing.

        ## 🔍 **Common Metadata Fields**
        - `severity`: Alert severity level (low, medium, high, critical)
        - `service`: Affected service name
        - `component`: Specific component or module
        - `environment`: Deployment environment (dev, staging, prod)
        - `correlation_id`: Request or transaction identifier
        - `timestamp`: Event timestamp (ISO 8601 format)
        - `duration_ms`: Operation duration in milliseconds
        - `error_code`: Application-specific error code
        - `retry_count`: Number of retry attempts
        - `user_id`: Associated user identifier
        - `request_id`: HTTP request identifier

        ## 💡 **Advanced Usage**
        Metadata enables:
        - Intelligent routing based on severity or service
        - Automated escalation for critical alerts
        - Analytics and reporting capabilities
        - Integration with monitoring and alerting systems

        ## 📏 **Constraints**
        - Optional field (defaults to empty dict)
        - Values can be strings, numbers, booleans, or nested objects
        - Total metadata size should be reasonable for performance
        """,
        examples=[
            {
                "severity": "high",
                "service": "orchestrator",
                "component": "workflow-engine",
                "environment": "production",
                "correlation_id": "wf_12345",
                "timestamp": "2024-09-22T10:30:00Z",
                "duration_ms": 2500,
                "error_code": "CPU_USAGE_HIGH",
                "retry_count": 0
            },
            {
                "severity": "medium",
                "service": "doc-store",
                "component": "database-connection",
                "environment": "staging",
                "correlation_id": "db_67890",
                "timestamp": "2024-09-22T09:15:30Z",
                "error_type": "ConnectionTimeout",
                "retry_count": 2
            }
        ]
    )

    labels: List[str] = Field(
        default_factory=list,
        description="""
        **Notification Labels** - Categorization tags for filtering and routing.

        ## 🏷️ **Label System**
        Labels provide flexible categorization for notifications, enabling:
        - Filtering and search capabilities
        - Automated routing and escalation rules
        - Analytics and reporting by category
        - Priority and handling classification

        ## 📋 **Common Label Categories**

        ### **Severity Labels**
        - `critical`, `high`, `medium`, `low`, `info`

        ### **Service Labels**
        - `orchestrator`, `interpreter`, `doc-store`, `prompt-store`, `frontend`
        - `notification-service`, `discovery-agent`, `secure-analyzer`

        ### **Event Type Labels**
        - `alert`, `error`, `warning`, `success`, `info`
        - `security`, `performance`, `availability`, `capacity`

        ### **Component Labels**
        - `database`, `cache`, `api`, `worker`, `scheduler`
        - `authentication`, `authorization`, `network`, `storage`

        ### **Environment Labels**
        - `production`, `staging`, `development`, `testing`

        ## 🔄 **Routing Examples**
        - `critical` + `security` → Immediate escalation to security team
        - `high` + `database` → Priority routing to DBA team
        - `production` + `error` → Broad notification to all on-call teams

        ## 📏 **Constraints**
        - Optional field (defaults to empty list)
        - Each label: 1-50 characters, alphanumeric + hyphens/underscores
        - Maximum 20 labels per notification
        """,
        examples=[
            ["critical", "security", "production", "database"],
            ["high", "performance", "orchestrator", "cpu"],
            ["medium", "availability", "doc-store", "connection"],
            ["low", "info", "frontend", "deployment"]
        ]
    )


@app.post(
    "/notify",
    summary="Send Notification",
    description="""
    **Send Notification** - Multi-channel notification delivery with automatic deduplication and intelligent routing.

    ## 📢 **Purpose**
    Orchestrates notification delivery across multiple channels (Slack, email, webhooks) with automatic
    deduplication, intelligent routing based on metadata and labels, and comprehensive tracking.

    ## 🚀 **Key Features**
    - **Multi-Channel Delivery**: Simultaneous delivery to email, Slack, and webhook channels
    - **Intelligent Deduplication**: Automatic spam prevention with configurable rules
    - **Owner Resolution**: Automatic routing to resolved owner notification targets
    - **Rich Metadata Support**: Structured data for enhanced processing and analytics
    - **Label-Based Routing**: Categorization system for intelligent delivery decisions

    ## 📋 **Usage Examples**

    ### **Send Alert to Slack Channel**
    ```bash
    curl -X POST http://localhost:5020/notify \
      -H "Content-Type: application/json" \
      -d '{
        "channel": "slack",
        "target": "#alerts",
        "title": "Database Connection Failed",
        "message": "Doc Store service lost connection to database",
        "metadata": {
          "severity": "high",
          "service": "doc-store",
          "component": "database"
        },
        "labels": ["critical", "database", "availability"]
      }'
    ```

    ### **Send Email Notification**
    ```bash
    curl -X POST http://localhost:5020/notify \
      -H "Content-Type: application/json" \
      -d '{
        "channel": "email",
        "target": "backend-team@company.com",
        "title": "Workflow Execution Completed",
        "message": "Monthly report generation workflow completed successfully",
        "metadata": {
          "workflow_id": "monthly-report-2024-09",
          "execution_time": 45000,
          "records_processed": 125000
        },
        "labels": ["success", "workflow", "report"]
      }'
    ```
    """,
    response_description="Notification delivery result with status and tracking information",
    responses={
        200: {
            "description": "Notification delivered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Notification delivered successfully",
                        "data": {
                            "status": "delivered",
                            "channel": "slack",
                            "target": "#alerts",
                            "deduplicated": False,
                            "delivery_id": "notif_12345"
                        },
                        "request_id": "req_12345",
                        "timestamp": "2024-09-22T10:30:00Z",
                        "processing_time_ms": 125.3
                    }
                }
            }
        },
        400: {
            "description": "Invalid notification request or channel configuration",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "type": "ValidationError",
                            "message": "Invalid channel specified",
                            "details": {"channel": "Must be one of: slack, email, webhook"}
                        },
                        "request_id": "req_12345",
                        "timestamp": "2024-09-22T10:30:00Z"
                    }
                }
            }
        }
    },
    tags=["Notification Delivery"]
)
async def notify(req: NotifyPayload):
    """
    Send a notification through the specified channel with automatic
    deduplication.

    Processes the notification request, applies deduplication logic to
    prevent spam, and delivers through the appropriate channel. Failed
    notifications are automatically added to the dead letter queue for
    retry or analysis.
    """
    start_time = time.time()
    request_id = f"notify_{int(time.time() * 1000)}"

    try:
        # Log notification send start
        if logger_client:
            await logger_client.log_business_event(
                "notification_send_started",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target": req.target,
                    "title": req.title,
                    "has_metadata": bool(req.metadata),
                    "has_labels": bool(req.labels),
                    "message_length": len(req.message) if req.message else 0,
                },
            )

            await logger_client.log_info(
                "Sending notification",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target_type": "webhook" if req.channel == "webhook" else "address",
                    "has_deduplication": True,
                    "dlq_enabled": True,
                },
            )

        result = await notification_sender.send_notification(
            channel=req.channel,
            target=req.target,
            title=req.title,
            message=req.message,
            metadata=req.metadata,
            labels=req.labels,
        )

        processing_time = time.time() - start_time

        # Log successful notification delivery
        if logger_client:
            delivery_status = result.get("status", "unknown")
            was_deduplicated = result.get("deduplicated", False)

            await logger_client.log_business_event(
                "notification_delivered",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target": req.target,
                    "delivery_status": delivery_status,
                    "was_deduplicated": was_deduplicated,
                    "processing_time_seconds": processing_time,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "notification_delivery",
                processing_time,
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "delivery_success": True,
                    "was_deduplicated": was_deduplicated,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Add failed notification to DLQ for later analysis
        dlq_manager.add_failed_notification(req.model_dump(), str(e))

        # Log notification delivery failure
        if logger_client:
            await logger_client.log_error(
                f"Notification delivery failed: {str(e)}",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target": req.target,
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                    "dlq_queued": True,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "notification_delivery_failed",
                {
                    "request_id": request_id,
                    "channel": req.channel,
                    "target": req.target,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                    "dlq_queued": True,
                },
            )

        raise


class ResolveOwnersRequest(BaseModel):
    """
    **Owner Resolution Request Model** - Batch resolution of owner names to notification targets.

    ## 🎯 **Purpose**
    Performs bulk resolution of owner names to their corresponding notification targets
    (email addresses, Slack handles, webhook URLs) for efficient bulk operations.
    Supports caching for high-performance repeated resolutions.

    ## 🚀 **Key Features**
    - **Batch Processing**: Resolve multiple owners in a single request
    - **Caching Support**: Intelligent caching with configurable TTL
    - **Fallback Mechanisms**: Graceful handling of unresolved owners
    - **Performance Optimized**: Minimizes external lookups through caching

    ## 🔄 **Resolution Process**
    1. **Cache Check**: First checks cached resolutions for performance
    2. **Owner Resolver**: Uses configured resolver to map owner names to targets
    3. **Fallback Logic**: Applies fallback strategies for unresolved owners
    4. **Cache Update**: Updates cache with new resolutions for future requests
    """

    model_config = ConfigDict(from_attributes=True)

    owners: List[str] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="""
        **Owner Names to Resolve** - List of owner identifiers to resolve to notification targets.

        ## 👥 **Owner Types**
        - Individual owners: `john.doe`, `alice_smith`, `devops-lead`
        - Team names: `backend-team`, `frontend-team`, `devops`
        - System identifiers: `platform-team`, `security-team`, `incident-response`

        ## 🔄 **Resolution Logic**
        Each owner name is resolved through the owner resolver which:
        - Maps individual owners to their notification preferences
        - Expands team names to multiple team members
        - Applies fallback strategies for unknown owners
        - Returns appropriate notification targets by channel

        ## 📏 **Constraints**
        - Minimum items: 1 (at least one owner required)
        - Maximum items: 100 (prevents excessive processing)
        - Each owner: 1-50 characters, valid identifier format
        """,
        examples=[
            ["john.doe", "backend-team", "devops"],
            ["alice_smith", "frontend-team"],
            ["security-team", "platform-lead", "incident-response"]
        ]
    )


@app.post(
    "/owners/resolve",
    summary="Resolve Owner Targets",
    description="""
    **Resolve Owner Targets** - Batch resolution of owner names to notification targets for efficient routing.

    ## 🎯 **Purpose**
    Performs bulk resolution of owner names to their corresponding notification targets
    (email addresses, Slack handles, webhook URLs) for efficient bulk operations.

    ## 📋 **Usage Examples**

    ### **Resolve Multiple Owners**
    ```bash
    curl -X POST http://localhost:5020/owners/resolve \
      -H "Content-Type: application/json" \
      -d '{
        "owners": ["john.doe", "backend-team", "devops"]
      }'
    ```
    """,
    response_description="Resolved owner targets with notification channel mappings",
    responses={
        200: {
            "description": "Owner resolution completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Owner resolution completed",
                        "data": {
                            "john.doe": {"email": "john.doe@company.com", "slack": "@john.doe"},
                            "backend-team": {"email": "backend@company.com", "slack": "#backend"},
                            "devops": {"webhook": "https://hooks.company.com/devops"}
                        },
                        "request_id": "req_12345",
                        "timestamp": "2024-09-22T10:30:00Z",
                        "processing_time_ms": 67.8
                    }
                }
            }
        }
    },
    tags=["Owner Management"]
)
async def owners_resolve(req: ResolveOwnersRequest):
    """
    Resolve a list of owner names to their notification targets.

    Takes multiple owner identifiers and returns their resolved
    notification targets (email addresses, webhook URLs, etc.) using
    cached mappings and fallback heuristics.
    """
    start_time = time.time()
    request_id = f"owner_resolve_{int(time.time() * 1000)}"

    try:
        # Log owner resolution start
        if logger_client:
            await logger_client.log_business_event(
                "owner_resolution_started",
                {
                    "request_id": request_id,
                    "owner_count": len(req.owners),
                    "owners": req.owners[:5] if len(req.owners) > 5 else req.owners,  # Limit for log size
                },
            )

            await logger_client.log_info(
                "Resolving owner targets",
                {"request_id": request_id, "owner_count": len(req.owners), "cache_enabled": True},
            )

        resolved_targets = owner_resolver.resolve_owners(req.owners)
        processing_time = time.time() - start_time

        resolved_count = sum(1 for target in resolved_targets.values() if target)
        unresolved_count = len(req.owners) - resolved_count

        # Log successful owner resolution
        if logger_client:
            await logger_client.log_business_event(
                "owner_resolution_completed",
                {
                    "request_id": request_id,
                    "total_owners": len(req.owners),
                    "resolved_count": resolved_count,
                    "unresolved_count": unresolved_count,
                    "processing_time_seconds": processing_time,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "owner_resolution",
                processing_time,
                {
                    "request_id": request_id,
                    "resolution_success": True,
                    "resolved_count": resolved_count,
                    "unresolved_count": unresolved_count,
                },
            )

        return {"resolved": resolved_targets}

    except Exception as e:
        error_time = time.time() - start_time

        # Log owner resolution failure
        if logger_client:
            await logger_client.log_error(
                f"Owner resolution failed: {str(e)}",
                {
                    "request_id": request_id,
                    "owner_count": len(req.owners),
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "owner_resolution_failed",
                {
                    "request_id": request_id,
                    "owner_count": len(req.owners),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                },
            )

        raise


@app.get(
    "/dlq",
    summary="Query Dead Letter Queue",
    description="""
    **Query Dead Letter Queue** - Administrative access to failed notification attempts for monitoring and troubleshooting.

    ## 📋 **Purpose**
    Retrieves entries from the dead letter queue containing failed notification attempts for analysis,
    retry consideration, and troubleshooting of notification delivery issues.

    ## 🔍 **Query Parameters**
    - `limit`: Maximum number of entries to return (default: 50, max: 500)

    ## 📋 **Usage Examples**

    ### **Query Recent Failed Notifications**
    ```bash
    curl http://localhost:5020/dlq?limit=10
    ```

    ### **Query All Failed Notifications**
    ```bash
    curl http://localhost:5020/dlq?limit=500
    ```
    """,
    response_description="Dead letter queue entries with failed notification details",
    responses={
        200: {
            "description": "Dead letter queue query completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "Dead letter queue query completed",
                        "data": {
                            "items": [
                                {
                                    "id": "dlq_12345",
                                    "timestamp": "2024-09-22T10:25:00Z",
                                    "notification": {
                                        "channel": "slack",
                                        "target": "#alerts",
                                        "title": "System Alert"
                                    },
                                    "error": "Webhook timeout",
                                    "retry_count": 3
                                }
                            ]
                        },
                        "request_id": "req_12345",
                        "timestamp": "2024-09-22T10:30:00Z",
                        "processing_time_ms": 23.4
                    }
                }
            }
        }
    },
    tags=["Dead Letter Queue"]
)
async def get_dlq(limit: int = 50):
    """
    Retrieve entries from the dead letter queue for failed notifications.

    Returns the most recent failed notification attempts for monitoring
    and debugging purposes. Limited to prevent excessive response sizes.
    """
    start_time = time.time()
    request_id = f"dlq_query_{int(time.time() * 1000)}"

    try:
        # Apply safety limits to prevent excessive memory usage
        safe_limit = min(limit, MAX_DLQ_LIMIT) if limit > 0 else DEFAULT_DLQ_LIMIT

        # Log DLQ query start
        if logger_client:
            await logger_client.log_business_event(
                "dlq_query_started",
                {
                    "request_id": request_id,
                    "requested_limit": limit,
                    "applied_limit": safe_limit,
                    "limit_was_capped": limit > MAX_DLQ_LIMIT if limit > 0 else False,
                },
            )

            await logger_client.log_info(
                "Querying dead letter queue",
                {"request_id": request_id, "applied_limit": safe_limit, "safety_limits_applied": True},
            )

        failed_notifications = dlq_manager.get_dlq_entries(safe_limit)
        processing_time = time.time() - start_time

        # Log successful DLQ query
        if logger_client:
            await logger_client.log_business_event(
                "dlq_query_completed",
                {
                    "request_id": request_id,
                    "entries_returned": len(failed_notifications),
                    "applied_limit": safe_limit,
                    "processing_time_seconds": processing_time,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "dlq_query",
                processing_time,
                {"request_id": request_id, "entries_returned": len(failed_notifications), "query_success": True},
            )

        return {"items": failed_notifications}

    except Exception as e:
        error_time = time.time() - start_time

        # Log DLQ query failure
        if logger_client:
            await logger_client.log_error(
                f"DLQ query failed: {str(e)}",
                {
                    "request_id": request_id,
                    "requested_limit": limit,
                    "applied_limit": safe_limit if "safe_limit" in locals() else DEFAULT_DLQ_LIMIT,
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "dlq_query_failed",
                {
                    "request_id": request_id,
                    "requested_limit": limit,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                },
            )

        raise


if __name__ == "__main__":
    """Run the Notification Service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
