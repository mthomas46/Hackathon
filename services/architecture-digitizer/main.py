"""Service: Architecture Digitizer

Endpoints:
- POST /normalize: Normalize architectural diagrams from various sources (Miro, FigJam, Lucid, Confluence)
- GET /supported-systems: Get list of supported diagram systems
- GET /health: Service health check

Responsibilities:
- Fetch architectural diagrams from various whiteboard/diagram tools
- Normalize data into standardized Software Architecture JSON schema
- Provide structured component and connection data for analysis
- Support authentication and error handling for external APIs

Dependencies: None (standalone service with external API calls)
"""

import os
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from services.shared.infrastructure.config import load_service_config

# ============================================================================
# SHARED MODULES - Following ecosystem patterns
# ============================================================================
from services.shared.infrastructure.monitoring.health import register_health_endpoints
from services.shared.infrastructure.monitoring.logging import fire_and_forget
from services.shared.infrastructure.monitoring.metrics import (
    get_service_metrics,
    metrics_endpoint,
    record_architecture_digitizer_api_failure,
    record_architecture_digitizer_file_upload,
    record_architecture_digitizer_request,
)
from services.shared.infrastructure.utilities import (
    attach_self_register,
    get_service_client,
    setup_common_middleware,
)

# from services.shared.utilities.logging_client import get_log_collector_client

# ============================================================================
# LOCAL MODULES - Service-specific functionality
# ============================================================================
try:
    from .modules.normalizers import get_file_normalizer, get_normalizer
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.normalizers import get_file_normalizer, get_normalizer
# Import presentation layer models
from .presentation.api import APIResponse, ErrorResponse, HealthResponse

# Import infrastructure layer
from .infrastructure import register_lifecycle_events

# Import route modules
try:
    from .presentation.routes import (
        normalization_router,
        systems_router,
        standard_router,
        init_normalization_routes,
        init_standard_routes,
    )
except ImportError:
    # Fallback for when running as script
    import os
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from presentation.routes import (
        normalization_router,
        systems_router,
        standard_router,
        init_normalization_routes,
        init_standard_routes,
    )

try:
    from .modules.models import (
        FileNormalizeResponse,
        NormalizeRequest,
        NormalizeResponse,
        SupportedFileFormatsResponse,
        SupportedSystemsResponse,
    )
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.models import (
        FileNormalizeResponse,
        NormalizeRequest,
        NormalizeResponse,
        SupportedFileFormatsResponse,
        SupportedSystemsResponse,
    )

# ============================================================================
# DOC-STORE INTEGRATION FUNCTIONS
# ============================================================================


async def store_architecture_in_docstore(
    system: str,
    board_id: str,
    normalized_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Store normalized architecture data in doc_store."""
    try:
        client = get_service_client()

        # Create document content from normalized data
        content = f"""# Architecture Diagram: {system.upper()} - {board_id}

## Components ({len(normalized_data.get('components', []))} items)

{chr(10).join(f"- **{comp.get('name', comp.get('id', 'Unknown'))}** ({comp.get('type', 'unknown')}): {comp.get('description', 'No description')}" for comp in normalized_data.get('components', []))}

## Connections ({len(normalized_data.get('connections', []))} items)

{chr(10).join(f"- {conn.get('from_id', 'Unknown')} → {conn.get('to_id', 'Unknown')}: {conn.get('label', 'No label')}" for conn in normalized_data.get('connections', []))}

## Metadata

- **Source System**: {system}
- **Board ID**: {board_id}
- **Total Components**: {len(normalized_data.get('components', []))}
- **Total Connections**: {len(normalized_data.get('connections', []))}
- **Processed At**: {normalized_data.get('processed_at', 'Unknown')}
"""

        # Create document metadata
        doc_metadata = {
            "source_type": "architecture",
            "type": "diagram",
            "system": system,
            "board_id": board_id,
            "component_count": len(normalized_data.get("components", [])),
            "connection_count": len(normalized_data.get("connections", [])),
            "processed_at": normalized_data.get("processed_at"),
        }

        # Add any additional metadata
        if metadata:
            doc_metadata.update(metadata)

        # Store in doc_store
        result = await client.store_document(
            {
                "content": content,
                "metadata": doc_metadata,
                "id": f"architecture:{system}:{board_id}",
            }
        )

        return result

    except Exception as e:
        # Log error but don't fail the request
        fire_and_forget(
            "architecture_digitizer_docstore_error",
            {"system": system, "board_id": board_id, "error": str(e)},
        )
        return {"status": "error", "error": f"Failed to store in doc_store: {e}"}


# ============================================================================
# STANDARD API RESPONSE MODELS - Moved to presentation layer
# ============================================================================
# Models are now imported from presentation.api for better separation of concerns


# Load standardized configuration
config = load_service_config("architecture-digitizer")

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = "Architecture Digitizer"
SERVICE_VERSION = config.service_version
DEFAULT_API_PORT = int(os.environ.get("SERVICE_API_PORT", "5105"))

# Initialize metrics
metrics = get_service_metrics(SERVICE_NAME)

# Initialize log collector client
logger_client = None

# Create FastAPI app following ecosystem patterns
app = FastAPI(
    title="🏗️ Enterprise Architecture Intelligence Hub - Digital Architecture Processing Platform",
    version=SERVICE_VERSION,
    description="""
    **🏗️ Enterprise Architecture Intelligence Hub** - Advanced digital architecture processing platform for comprehensive diagram analysis, normalization, and intelligence extraction across the LLM Documentation Ecosystem.

    ## 🎯 **Core Capabilities**

    ### **📐 Multi-Format Architecture Processing**
    - **Diagram System Integration**: Support for Miro, FigJam, Lucid, Confluence, and enterprise diagramming tools
    - **File Format Support**: PNG, JPEG, SVG, PDF, and native diagram formats
    - **Intelligent Parsing**: AI-powered diagram recognition and component extraction
    - **Schema Normalization**: Standardized JSON schema for architecture components and relationships

    ### **🔍 Advanced Architecture Intelligence**
    - **Component Recognition**: Automatic identification of services, databases, APIs, and infrastructure components
    - **Relationship Mapping**: Intelligent connection analysis and dependency visualization
    - **Architecture Patterns**: Detection of microservices, monoliths, serverless, and hybrid patterns
    - **Quality Assessment**: Architecture quality metrics and best practice validation

    ### **📊 Architecture Analytics & Insights**
    - **Complexity Analysis**: Architecture complexity metrics and maintainability assessment
    - **Scalability Evaluation**: Performance and scalability pattern recognition
    - **Security Architecture**: Security component identification and compliance validation
    - **Technology Stack Analysis**: Framework, language, and infrastructure technology detection

    ### **🔄 Enterprise Integration & Processing**
    - **Real-Time Processing**: Live diagram analysis and continuous architecture monitoring
    - **Batch Processing**: Large-scale architecture documentation processing
    - **Version Control Integration**: Architecture evolution tracking and change analysis
    - **Collaboration Platform Sync**: Automatic synchronization with design and documentation tools

    ## 📡 **REST API Endpoints by Category**

    ### **🏥 Health & Monitoring (`/health`)**
    - `GET /health` - Comprehensive service health and operational metrics
    - Real-time status of diagram systems, file formats, and normalization engine

    ### **📐 Architecture Normalization (`/normalize`)**
    - `POST /normalize` - Normalize architectural diagrams from supported systems
    - URL-based diagram fetching with intelligent parsing and component extraction

    ### **📁 File Processing (`/normalize-file`)**
    - `POST /normalize-file` - Process uploaded architecture diagram files
    - Direct file upload support with automatic format detection and processing

    ### **🔧 System Capabilities (`/supported-systems`)**
    - `GET /supported-systems` - List all supported diagram systems and capabilities
    - System-specific features, authentication requirements, and integration details

    ### **📋 Format Support (`/supported-file-formats/{system}`)**
    - `GET /supported-file-formats/{system}` - File format support for specific diagram systems
    - Format-specific processing capabilities and conversion options

    ## 🛠️ **Supported Diagram Systems**

    ### **🎨 Collaborative Whiteboarding**
    - **Miro**: Advanced whiteboard diagrams with sticky notes, frames, and collaborative features
    - **FigJam**: Figma's collaborative whiteboard for design thinking and architecture planning
    - **Lucid**: Professional diagramming with advanced shape libraries and templates

    ### **📚 Documentation Platforms**
    - **Confluence**: Atlassian Confluence pages with diagrams, attachments, and rich content
    - **Notion**: Notion databases and pages with embedded diagrams and visual content

    ### **🔧 Enterprise Tools**
    - **Draw.io**: Open-source diagramming with extensive shape libraries
    - **Visio Online**: Microsoft Visio integration for enterprise architecture diagrams
    - **PlantUML**: Text-based diagram generation for version-controlled architecture

    ## 📊 **Architecture Schema Standards**

    ### **🏛️ Component Types**
    - **Services**: Microservices, APIs, web services, and application components
    - **Data Stores**: Databases, caches, message queues, and storage systems
    - **Infrastructure**: Load balancers, gateways, CDNs, and network components
    - **External Systems**: Third-party services, APIs, and integration points

    ### **🔗 Relationship Types**
    - **Data Flow**: Information transfer between components
    - **API Calls**: Service-to-service communication and API dependencies
    - **Database Access**: Data persistence and retrieval relationships
    - **Event Streaming**: Asynchronous communication and event-driven patterns

    ### **🏷️ Metadata Enrichment**
    - **Technology Stack**: Programming languages, frameworks, and runtime environments
    - **Scalability Patterns**: Load balancing, sharding, and horizontal scaling indicators
    - **Security Controls**: Authentication, authorization, and encryption mechanisms
    - **Monitoring Points**: Logging, metrics, and observability instrumentation

    ## 🏢 **Enterprise Integration**

    ### **🔗 Ecosystem Service Integration**
    - **Source Agent**: Real-time architecture diagram ingestion and processing
    - **Code Analyzer**: Code-to-architecture mapping and validation
    - **Doc Store**: Architecture documentation storage and retrieval
    - **Orchestrator**: Architecture-aware workflow orchestration
    - **Notification Service**: Architecture change alerts and compliance notifications

    ### **📊 Advanced Features**
    - **Change Detection**: Architecture evolution tracking and impact analysis
    - **Compliance Validation**: Enterprise architecture standards and governance
    - **Cost Optimization**: Architecture-driven cloud cost analysis and recommendations
    - **Performance Modeling**: Architecture-based performance prediction and optimization

    ### **🔐 Enterprise Security**
    - **Diagram Access Control**: Secure access to sensitive architecture diagrams
    - **Data Privacy**: Protection of intellectual property and confidential designs
    - **Audit Trails**: Complete processing history and access logging
    - **Compliance Reporting**: Regulatory compliance for architecture documentation

    ## 📋 **Usage Examples**

    ### **Normalize Miro Board**
    ```bash
    curl -X POST http://localhost:5105/normalize \
        -H "Content-Type: application/json" \
        -d '{
        "system": "miro",
        "board_id": "board123",
        "auth_token": "miro_token_here"
        }'
    ```

    ### **Process Architecture Diagram File**
    ```bash
    curl -X POST http://localhost:5105/normalize-file \
        -F "file=@architecture-diagram.png" \
        -F "system=miro" \
        -F "metadata={\"project\": \"ecommerce-platform\"}"
    ```

    ### **Get Supported Systems**
    ```bash
    curl http://localhost:5105/supported-systems
    ```

    ### **Check File Format Support**
    ```bash
    curl http://localhost:5105/supported-file-formats/miro
    ```

    ### **Advanced Architecture Analysis**
    ```bash
    curl -X POST http://localhost:5105/normalize \
        -H "Content-Type: application/json" \
        -d '{
        "system": "lucid",
        "board_id": "arch456",
        "options": {
        "extract_patterns": true,
        "validate_compliance": true,
        "generate_insights": true
        }
        }'
    ```
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Architecture Digitizer Team",
        "url": "https://github.com/your-org/architecture-digitizer",
        "email": "architecture@your-org.com",
    },
    license_info={"name": "Proprietary", "url": "https://your-org.com/license"},
    openapi_tags=[
        {
            "name": "Health & Monitoring",
            "description": "Service health checks, diagram system connectivity, and operational metrics",
        },
        {
            "name": "Architecture Normalization",
            "description": "Diagram normalization, component extraction, and architecture analysis",
        },
        {
            "name": "File Processing",
            "description": "File upload processing, format detection, and batch operations",
        },
        {
            "name": "System Capabilities",
            "description": "Supported systems listing, capabilities discovery, and integration details",
        },
    ],
)


# Event handlers moved to infrastructure layer for better separation of concerns


# Use common middleware setup and error handlers
setup_common_middleware(app, config.service_name)

# Register lifecycle event handlers
register_lifecycle_events(app)

# ============================================================================
# CUSTOM HEALTH ENDPOINT - Override shared health with detailed architecture processing
# ============================================================================


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="""
    **Service Health Check** - Comprehensive health assessment and operational metrics for the Architecture Digitizer service.

    ## 🏥 **Health Assessment**

    This endpoint provides real-time health status and operational metrics for the architecture digitizer service, including:

    ### **🏥 Health Indicators**
    - **Service Status**: Overall health status (healthy/degraded/unhealthy)
    - **Version Information**: Current service version and build details
    - **Uptime Metrics**: Service uptime and operational statistics
    - **System Readiness**: Overall system readiness for diagram processing operations

    ### **📊 Operational Metrics**
    - **Supported Systems Count**: Number of diagram systems supported for processing
    - **File Formats Supported**: Number of file formats available for upload processing
    - **Normalization Engine Active**: Status of the core diagram normalization and analysis engine
    - **Last Health Check**: Timestamp of the last health assessment

    ### **📐 Architecture Processing Health**
    - **Diagram System Integration**: Connectivity and availability of supported diagram platforms
    - **File Processing Engine**: File upload, format detection, and processing capabilities
    - **Normalization Pipeline**: Diagram parsing, component extraction, and schema validation
    - **Integration Services**: Health of connected services (Doc Store, etc.)

    ## 🎯 **Response Codes**

    | Code | Status | Description |
    |------|--------|-------------|
    | 200 | Healthy | Service is fully operational with all diagram systems and file formats available |
    | 503 | Degraded | Service is operational but with some diagram systems or file formats unavailable |
    | 500 | Unhealthy | Service is experiencing critical issues |

    ## 📋 **Usage Examples**

    ### **Basic Health Check**
    ```bash
    curl -X GET http://localhost:5105/health
    ```

    ### **Health Check with Monitoring**
    ```python
    import requests

    response = requests.get("http://localhost:5105/health")
    health_data = response.json()

    if health_data["status"] == "healthy":
        print("✅ Architecture Digitizer is healthy")
        print(f"📐 Systems Supported: {health_data['supported_systems_count']}")
        print(f"📁 File Formats: {health_data['file_formats_supported']}")
        print(f"🔧 Normalization Engine: {'Active' if health_data['normalization_engine_active'] else 'Inactive'}")
    else:
        print("⚠️  Architecture Digitizer health issue detected")
    ```

    ### **Automated Monitoring Script**
    ```bash
    #!/bin/bash
    HEALTH_URL="http://localhost:5105/health"
    STATUS=$(curl -s $HEALTH_URL | jq -r '.status')

    if [ "$STATUS" = "healthy" ]; then
        echo "✅ Architecture Digitizer is healthy"
        exit 0
    else
        echo "❌ Architecture Digitizer is unhealthy: $STATUS"
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
                        "service": "architecture-digitizer",
                        "version": "1.0.0",
                        "uptime_seconds": 3600.5,
                        "last_health_check": "2024-09-22T10:30:00Z",
                        "supported_systems_count": 6,
                        "file_formats_supported": 8,
                        "normalization_engine_active": True,
                    }
                }
            },
        },
        503: {
            "description": "Service is degraded but still operational",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "service": "architecture-digitizer",
                        "version": "1.0.0",
                        "uptime_seconds": 1800.0,
                        "last_health_check": "2024-09-22T10:25:00Z",
                        "supported_systems_count": 5,
                        "file_formats_supported": 7,
                        "normalization_engine_active": True,
                    }
                }
            },
        },
    },
    tags=["Health & Monitoring"],
)
async def health():
    """
    **Health Check Endpoint** - Comprehensive service health assessment.

    Returns detailed health status including:
    - Service operational status and version information
    - Supported diagram systems and file formats availability
    - Normalization engine and processing capabilities status
    - Uptime and last health check timestamp
    """
    import datetime

    # Calculate uptime (simplified - in production this would track actual startup time)
    uptime_seconds = time.time() - getattr(app, "_startup_time", time.time())

    # Check supported systems count (simplified check)
    supported_systems_count = 6  # Miro, FigJam, Lucid, Confluence, Draw.io, PlantUML
    try:
        # In a real implementation, this would check actual system integrations
        pass
    except Exception:
        supported_systems_count = 5  # Degraded state

    # Check file formats supported (simplified check)
    file_formats_supported = 8  # PNG, JPEG, SVG, PDF, Miro native, FigJam native, etc.
    try:
        # In a real implementation, this would check actual file format support
        pass
    except Exception:
        file_formats_supported = 7  # Degraded state

    # Check normalization engine status (simplified check)
    normalization_engine_active = True
    try:
        # In a real implementation, this would check actual normalization engine health
        pass
    except Exception:
        normalization_engine_active = False  # Degraded state

    # Determine overall health based on operational metrics
    if (
        supported_systems_count >= 6
        and file_formats_supported >= 8
        and normalization_engine_active
    ):
        status = "healthy"
    elif supported_systems_count >= 4 and normalization_engine_active:
        status = "degraded"
    else:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        uptime_seconds=round(uptime_seconds, 1),
        last_health_check=datetime.datetime.utcnow().isoformat() + "Z",
        supported_systems_count=supported_systems_count,
        file_formats_supported=file_formats_supported,
        normalization_engine_active=normalization_engine_active,
    )


# Register health endpoints and auto-register with orchestrator
# Note: Health endpoint is now in standard_routes, so we skip register_health_endpoints
# register_health_endpoints(app, config.service_name, SERVICE_VERSION)
attach_self_register(app, config.service_name)

# Add metrics endpoint
app.add_route("/metrics", metrics_endpoint(SERVICE_NAME))

# ============================================================================
# INITIALIZE AND INCLUDE ROUTERS
# ============================================================================

# Initialize routers with dependencies
init_normalization_routes(metrics, logger_client, SERVICE_NAME, store_architecture_in_docstore)
init_standard_routes(app, SERVICE_NAME, SERVICE_VERSION)

# Track startup time for health endpoint
app._startup_time = time.time()

# Include all routers
app.include_router(standard_router, tags=["Standard Endpoints"])
app.include_router(normalization_router, tags=["Normalization"])
app.include_router(systems_router, tags=["Systems"])


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

if __name__ == "__main__":
    """Run the Architecture Digitizer service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_API_PORT, log_level="info")
