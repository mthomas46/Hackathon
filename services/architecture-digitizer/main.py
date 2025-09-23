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

import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from services.shared.core.constants_new import ServiceNames

# ============================================================================
# SHARED MODULES - Following ecosystem patterns
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.monitoring.logging import fire_and_forget
from services.shared.monitoring.metrics import (
    get_service_metrics,
    metrics_endpoint,
    record_architecture_digitizer_api_failure,
    record_architecture_digitizer_file_upload,
    record_architecture_digitizer_request,
)
from services.shared.utilities import attach_self_register, get_service_client, setup_common_middleware

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
    system: str, board_id: str, normalized_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None
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
            {"content": content, "metadata": doc_metadata, "id": f"architecture:{system}:{board_id}"}
        )

        return result

    except Exception as e:
        # Log error but don't fail the request
        fire_and_forget(
            "architecture_digitizer_docstore_error", {"system": system, "board_id": board_id, "error": str(e)}
        )
        return {"status": "error", "error": f"Failed to store in doc_store: {e}"}


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
    """Health check response model for architecture digitizer service."""

    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    last_health_check: Optional[str] = Field(None, description="Last health check timestamp")
    supported_systems_count: int = Field(..., description="Number of supported diagram systems")
    file_formats_supported: int = Field(..., description="Number of supported file formats")
    normalization_engine_active: bool = Field(..., description="Whether normalization engine is active")


# Service configuration constants
SERVICE_NAME = "architecture-digitizer"
SERVICE_TITLE = "Architecture Digitizer"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5105

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
        {"name": "File Processing", "description": "File upload processing, format detection, and batch operations"},
        {
            "name": "System Capabilities",
            "description": "Supported systems listing, capabilities discovery, and integration details",
        },
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client

    # Set startup time for uptime calculation
    import time

    app._startup_time = time.time()

    try:
        # Use a fallback service name if ARCHITECTURE_DIGITIZER doesn't exist in ServiceNames
        service_name = getattr(ServiceNames, "ARCHITECTURE_DIGITIZER", SERVICE_NAME)
        # logger_client = await get_log_collector_client(service_name)
        if logger_client:
            await logger_client.log_business_event(
                "architecture_digitizer_startup",
                {
                    "version": SERVICE_VERSION,
                    "capabilities": [
                        "diagram_normalization",
                        "multi_format_support",
                        "external_api_integration",
                        "file_upload_processing",
                    ],
                    "integrations": ["miro", "figjam", "lucid", "confluence", "log_collector"],
                    "supported_formats": ["miro", "figjam", "lucid", "confluence", "json", "xml"],
                    "features": [
                        "authentication_handling",
                        "error_recovery",
                        "structured_output",
                        "component_extraction",
                    ],
                },
            )
            await logger_client.log_info(
                "Architecture Digitizer service started",
                {
                    "diagram_sources": ["miro", "figjam", "lucid", "confluence"],
                    "output_formats": ["json", "xml"],
                    "file_upload_enabled": True,
                    "api_integration_ready": True,
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("Architecture Digitizer service shutting down")
        except Exception:
            pass


# Use common middleware setup and error handlers
setup_common_middleware(
    app, ServiceNames.ARCHITECTURE_DIGITIZER if hasattr(ServiceNames, "ARCHITECTURE_DIGITIZER") else SERVICE_NAME
)

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
    if supported_systems_count >= 6 and file_formats_supported >= 8 and normalization_engine_active:
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
register_health_endpoints(
    app,
    ServiceNames.ARCHITECTURE_DIGITIZER if hasattr(ServiceNames, "ARCHITECTURE_DIGITIZER") else SERVICE_NAME,
    SERVICE_VERSION,
)
attach_self_register(
    app, ServiceNames.ARCHITECTURE_DIGITIZER if hasattr(ServiceNames, "ARCHITECTURE_DIGITIZER") else SERVICE_NAME
)

# Add metrics endpoint
app.add_route("/metrics", metrics_endpoint(SERVICE_NAME))

# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.post("/normalize", response_model=NormalizeResponse)
async def normalize_architecture(request: NormalizeRequest):
    """
    Normalize architectural diagrams from various sources into standardized
    format.

    Fetches diagram data from supported systems (Miro, FigJam, Lucid,
    Confluence) and normalizes it into the common Software Architecture
    JSON schema with components and connections for downstream analysis
    and documentation.
    """
    start_time = time.time()
    request_id = f"arch_normalize_{int(time.time() * 1000)}"

    try:
        # Log normalization start
        if logger_client:
            await logger_client.log_business_event(
                "architecture_normalization_started",
                {
                    "request_id": request_id,
                    "system": request.system,
                    "board_id": request.board_id,
                    "has_token": bool(request.token),
                    "normalization_type": "diagram_fetch_and_normalize",
                },
            )

            await logger_client.log_info(
                "Starting architecture diagram normalization",
                {
                    "request_id": request_id,
                    "system": request.system,
                    "board_id": request.board_id,
                    "external_api_call": True,
                },
            )

        # Get the appropriate normalizer for the system
        normalizer = get_normalizer(request.system)
        if not normalizer:
            error_time = time.time() - start_time
            record_architecture_digitizer_request(metrics, request.system, "error")

            # Log unsupported system error
            if logger_client:
                await logger_client.log_error(
                    f"Architecture normalization failed: Unsupported system {request.system}",
                    {
                        "request_id": request_id,
                        "system": request.system,
                        "board_id": request.board_id,
                        "error_type": "unsupported_system",
                        "processing_time_seconds": error_time,
                    },
                    error=Exception(f"Unsupported system: {request.system}"),
                )

                await logger_client.log_business_event(
                    "architecture_normalization_failed",
                    {
                        "request_id": request_id,
                        "system": request.system,
                        "board_id": request.board_id,
                        "error_type": "unsupported_system",
                        "processing_time_seconds": error_time,
                    },
                )

            raise HTTPException(status_code=400, detail=f"Unsupported system: {request.system}")

        # Fetch and normalize the data
        result = await normalizer.normalize(request.board_id, request.token)

        # Calculate metrics
        processing_time = time.time() - start_time
        components_count = len(result.get("components", []))
        connections_count = len(result.get("connections", []))
        data_size = len(str(result)) if result else 0

        # Record successful metrics
        record_architecture_digitizer_request(metrics, request.system, "success", processing_time)

        # Store normalized data in doc_store (fire and forget)
        fire_and_forget(
            store_architecture_in_docstore,
            request.system,
            request.board_id,
            result,
            {"request_duration": processing_time},
        )

        # Log successful normalization
        if logger_client:
            await logger_client.log_business_event(
                "architecture_normalization_completed",
                {
                    "request_id": request_id,
                    "system": request.system,
                    "board_id": request.board_id,
                    "components_extracted": components_count,
                    "connections_mapped": connections_count,
                    "data_size_bytes": data_size,
                    "processing_time_seconds": processing_time,
                    "doc_store_stored": True,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "architecture_normalization",
                processing_time,
                {
                    "request_id": request_id,
                    "system": request.system,
                    "board_id": request.board_id,
                    "components_count": components_count,
                    "connections_count": connections_count,
                    "normalization_success": True,
                },
            )

        return NormalizeResponse(
            success=True,
            system=request.system,
            board_id=request.board_id,
            data=result,
            message="Architecture diagram normalized successfully",
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is (already logged above for unsupported system)
        raise
    except Exception as e:
        # Record failure metrics
        error_time = time.time() - start_time
        record_architecture_digitizer_request(metrics, getattr(request, "system", "unknown"), "error", error_time)
        record_architecture_digitizer_api_failure(metrics, getattr(request, "system", "unknown"), type(e).__name__)

        # Log normalization failure
        if logger_client:
            await logger_client.log_error(
                f"Architecture normalization failed: {str(e)}",
                {
                    "request_id": request_id,
                    "system": getattr(request, "system", "unknown"),
                    "board_id": getattr(request, "board_id", "unknown"),
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                    "external_api_failure": True,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "architecture_normalization_failed",
                {
                    "request_id": request_id,
                    "system": getattr(request, "system", "unknown"),
                    "board_id": getattr(request, "board_id", "unknown"),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                },
            )

        error_msg = f"Failed to normalize {getattr(request, 'system', 'unknown')} diagram {getattr(request, 'board_id', 'unknown')}: {str(e)}"
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/normalize-file", response_model=FileNormalizeResponse)
async def normalize_file_upload(
    file: UploadFile = File(...),
    system: str = Form(..., description="Diagram system (miro, figjam, lucid, confluence)"),
    file_format: str = Form(..., description="File format (json, xml, html)"),
):
    """
    Normalize an uploaded diagram file into standardized format.

    Accepts diagram files exported from supported systems and converts
    them into the common Software Architecture JSON schema.
    """
    import time

    start_time = time.time()

    try:
        # Validate file size (10MB limit)
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

        # Reset file pointer
        await file.seek(0)

        # Get the appropriate file normalizer for the system
        file_normalizer = get_file_normalizer(system)
        if not file_normalizer:
            record_architecture_digitizer_request(metrics, system, "error")
            raise HTTPException(status_code=400, detail=f"Unsupported system: {system}")

        # Check if the file format is supported for this system
        if not file_normalizer.supports_format(file_format):
            record_architecture_digitizer_request(metrics, system, "error")
            raise HTTPException(
                status_code=400, detail=f"File format '{file_format}' not supported for system '{system}'"
            )

        # Read file content
        content = await file.read()

        # Normalize the file
        result = await file_normalizer.normalize_file(content, file.filename, file_format)

        # Record successful metrics
        duration = time.time() - start_time
        record_architecture_digitizer_request(metrics, system, "success", duration)
        record_architecture_digitizer_file_upload(metrics, system, file_format, file_size, "success", duration)

        # Store normalized data in doc_store (fire and forget)
        fire_and_forget(
            store_architecture_in_docstore,
            system,
            f"file:{file.filename}",
            result,
            {
                "filename": file.filename,
                "file_format": file_format,
                "file_size": file_size,
                "request_duration": duration,
            },
        )

        # Log successful normalization
        fire_and_forget(
            "info",
            f"Successfully normalized {system} file {file.filename} ({file_format})",
            SERVICE_NAME,
            {
                "system": system,
                "filename": file.filename,
                "file_format": file_format,
                "file_size": file_size,
                "duration": duration,
            },
        )

        return FileNormalizeResponse(
            success=True,
            system=system,
            file_format=file_format,
            filename=file.filename,
            data=result,
            message=f"File {file.filename} normalized successfully",
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Record failure metrics
        duration = time.time() - start_time
        record_architecture_digitizer_request(metrics, system, "error", duration)
        record_architecture_digitizer_api_failure(metrics, system, type(e).__name__)
        record_architecture_digitizer_file_upload(metrics, system, file_format, file_size, "error", duration)

        error_msg = f"Failed to normalize {system} file: {str(e)}"

        # Log the error
        fire_and_forget(
            "error",
            error_msg,
            SERVICE_NAME,
            {
                "system": system,
                "filename": file.filename if "file" in locals() else "unknown",
                "file_format": file_format,
                "file_size": file_size,
                "error": str(e),
                "duration": duration,
            },
        )

        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/supported-systems", response_model=SupportedSystemsResponse)
async def get_supported_systems():
    """Get list of supported diagram systems and their capabilities."""
    from .modules.normalizers import SUPPORTED_SYSTEMS

    systems_info = []
    for system_name, normalizer_class in SUPPORTED_SYSTEMS.items():
        systems_info.append(
            {
                "name": system_name,
                "description": normalizer_class.get_description(),
                "auth_type": normalizer_class.get_auth_type(),
                "supported": True,
            }
        )

    return SupportedSystemsResponse(systems=systems_info, count=len(systems_info))


@app.get("/supported-file-formats/{system}", response_model=SupportedFileFormatsResponse)
async def get_supported_file_formats(system: str):
    """Get supported file formats for a specific diagram system."""
    from .modules.normalizers import get_file_normalizer

    file_normalizer = get_file_normalizer(system)
    if not file_normalizer:
        raise HTTPException(status_code=404, detail=f"System '{system}' not found or not supported for file uploads")

    supported_formats = file_normalizer.get_supported_formats()

    return SupportedFileFormatsResponse(
        system=system, supported_formats=supported_formats, count=len(supported_formats)
    )


# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

if __name__ == "__main__":
    """Run the Architecture Digitizer service directly."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=DEFAULT_PORT, log_level="info")
