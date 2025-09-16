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

from typing import Dict, Any, Optional, List
import httpx
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, field_validator

# ============================================================================
# SHARED MODULES - Following ecosystem patterns
# ============================================================================
from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response, create_error_response
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import setup_common_middleware, attach_self_register, get_service_client
from services.shared.logging import fire_and_forget
from services.shared.metrics import (
    get_service_metrics,
    metrics_endpoint,
    record_architecture_digitizer_request,
    record_architecture_digitizer_api_failure,
    record_architecture_digitizer_file_upload
)

# ============================================================================
# LOCAL MODULES - Service-specific functionality
# ============================================================================
from .modules.normalizers import get_normalizer, get_file_normalizer
from .modules.models import (
    NormalizeRequest,
    NormalizeResponse,
    FileNormalizeRequest,
    FileNormalizeResponse,
    SupportedSystemsResponse,
    SupportedFileFormatsResponse
)

# ============================================================================
# DOC-STORE INTEGRATION FUNCTIONS
# ============================================================================

async def store_architecture_in_docstore(
    system: str,
    board_id: str,
    normalized_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
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
            "component_count": len(normalized_data.get('components', [])),
            "connection_count": len(normalized_data.get('connections', [])),
            "processed_at": normalized_data.get('processed_at'),
        }

        # Add any additional metadata
        if metadata:
            doc_metadata.update(metadata)

        # Store in doc_store
        result = await client.store_document({
            "content": content,
            "metadata": doc_metadata,
            "id": f"architecture:{system}:{board_id}"
        })

        return result

    except Exception as e:
        # Log error but don't fail the request
        fire_and_forget("architecture_digitizer_docstore_error", {
            "system": system,
            "board_id": board_id,
            "error": str(e)
        })
        return {"status": "error", "error": f"Failed to store in doc_store: {e}"}

# Service configuration constants
SERVICE_NAME = "architecture-digitizer"
SERVICE_TITLE = "Architecture Digitizer"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5105

# Initialize metrics
metrics = get_service_metrics(SERVICE_NAME)

# Create FastAPI app following ecosystem patterns
app = FastAPI(
    title=SERVICE_TITLE,
    description="Architecture diagram digitizer and normalizer service for the LLM Documentation Ecosystem",
    version=SERVICE_VERSION
)

# Use common middleware setup and error handlers
setup_common_middleware(app, ServiceNames.ARCHITECTURE_DIGITIZER if hasattr(ServiceNames, "ARCHITECTURE_DIGITIZER") else SERVICE_NAME)

# Register health endpoints and auto-register with orchestrator
register_health_endpoints(app, ServiceNames.ARCHITECTURE_DIGITIZER if hasattr(ServiceNames, "ARCHITECTURE_DIGITIZER") else SERVICE_NAME, SERVICE_VERSION)
attach_self_register(app, ServiceNames.ARCHITECTURE_DIGITIZER if hasattr(ServiceNames, "ARCHITECTURE_DIGITIZER") else SERVICE_NAME)

# Add metrics endpoint
app.add_route("/metrics", metrics_endpoint(SERVICE_NAME))

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.post("/normalize", response_model=NormalizeResponse)
async def normalize_architecture(request: NormalizeRequest):
    """Normalize architectural diagrams from various sources into standardized format.

    Fetches diagram data from supported systems (Miro, FigJam, Lucid, Confluence)
    and normalizes it into the common Software Architecture JSON schema with
    components and connections for downstream analysis and documentation.
    """
    import time
    start_time = time.time()

    try:
        # Get the appropriate normalizer for the system
        normalizer = get_normalizer(request.system)
        if not normalizer:
            record_architecture_digitizer_request(metrics, request.system, "error")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported system: {request.system}"
            )

        # Fetch and normalize the data
        result = await normalizer.normalize(request.board_id, request.token)

        # Record successful metrics
        duration = time.time() - start_time
        record_architecture_digitizer_request(metrics, request.system, "success", duration)

        # Store normalized data in doc_store (fire and forget)
        fire_and_forget(
            store_architecture_in_docstore,
            request.system,
            request.board_id,
            result,
            {"request_duration": duration}
        )

        # Log successful normalization
        fire_and_forget(
            "info",
            f"Successfully normalized {request.system} diagram {request.board_id}",
            SERVICE_NAME,
            {"system": request.system, "board_id": request.board_id, "duration": duration}
        )

        return NormalizeResponse(
            success=True,
            system=request.system,
            board_id=request.board_id,
            data=result,
            message="Architecture diagram normalized successfully"
        )

    except Exception as e:
        # Record failure metrics
        duration = time.time() - start_time
        record_architecture_digitizer_request(metrics, request.system, "error", duration)
        record_architecture_digitizer_api_failure(metrics, request.system, type(e).__name__)

        error_msg = f"Failed to normalize {request.system} diagram {request.board_id}: {str(e)}"

        # Log the error
        fire_and_forget(
            "error",
            error_msg,
            SERVICE_NAME,
            {"system": request.system, "board_id": request.board_id, "error": str(e), "duration": duration}
        )

        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.post("/normalize-file", response_model=FileNormalizeResponse)
async def normalize_file_upload(
    file: UploadFile = File(...),
    system: str = Form(..., description="Diagram system (miro, figjam, lucid, confluence)"),
    file_format: str = Form(..., description="File format (json, xml, html)")
):
    """Normalize an uploaded diagram file into standardized format.

    Accepts diagram files exported from supported systems and converts them
    into the common Software Architecture JSON schema.
    """
    import time
    start_time = time.time()

    try:
        # Validate file size (10MB limit)
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=413,
                detail="File too large. Maximum size is 10MB."
            )

        # Reset file pointer
        await file.seek(0)

        # Get the appropriate file normalizer for the system
        file_normalizer = get_file_normalizer(system)
        if not file_normalizer:
            record_architecture_digitizer_request(metrics, system, "error")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported system: {system}"
            )

        # Check if the file format is supported for this system
        if not file_normalizer.supports_format(file_format):
            record_architecture_digitizer_request(metrics, system, "error")
            raise HTTPException(
                status_code=400,
                detail=f"File format '{file_format}' not supported for system '{system}'"
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
                "request_duration": duration
            }
        )

        # Log successful normalization
        fire_and_forget(
            "info",
            f"Successfully normalized {system} file {file.filename} ({file_format})",
            SERVICE_NAME,
            {"system": system, "filename": file.filename, "file_format": file_format, "file_size": file_size, "duration": duration}
        )

        return FileNormalizeResponse(
            success=True,
            system=system,
            file_format=file_format,
            filename=file.filename,
            data=result,
            message=f"File {file.filename} normalized successfully"
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
            {"system": system, "filename": file.filename if 'file' in locals() else "unknown", "file_format": file_format, "file_size": file_size, "error": str(e), "duration": duration}
        )

        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.get("/supported-systems", response_model=SupportedSystemsResponse)
async def get_supported_systems():
    """Get list of supported diagram systems and their capabilities."""
    from .modules.normalizers import SUPPORTED_SYSTEMS

    systems_info = []
    for system_name, normalizer_class in SUPPORTED_SYSTEMS.items():
        systems_info.append({
            "name": system_name,
            "description": normalizer_class.get_description(),
            "auth_type": normalizer_class.get_auth_type(),
            "supported": True
        })

    return SupportedSystemsResponse(
        systems=systems_info,
        count=len(systems_info)
    )

@app.get("/supported-file-formats/{system}", response_model=SupportedFileFormatsResponse)
async def get_supported_file_formats(system: str):
    """Get supported file formats for a specific diagram system."""
    from .modules.normalizers import get_file_normalizer

    file_normalizer = get_file_normalizer(system)
    if not file_normalizer:
        raise HTTPException(
            status_code=404,
            detail=f"System '{system}' not found or not supported for file uploads"
        )

    supported_formats = file_normalizer.get_supported_formats()

    return SupportedFileFormatsResponse(
        system=system,
        supported_formats=supported_formats,
        count=len(supported_formats)
    )

# ============================================================================
# LIFECYCLE MANAGEMENT
# ============================================================================

if __name__ == "__main__":
    """Run the Architecture Digitizer service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )
