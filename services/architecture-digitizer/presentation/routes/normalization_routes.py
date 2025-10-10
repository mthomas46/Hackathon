"""Normalization endpoints for architecture-digitizer service.

This module handles all diagram normalization operations including:
- API-based normalization (fetching from external diagram platforms)
- File upload normalization (processing exported diagram files)
"""

import time
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

# Local imports from modules
try:
    from ...modules.models import (
        NormalizeRequest,
        NormalizeResponse,
        FileNormalizeResponse,
    )
    from ...modules.normalizers import get_normalizer, get_file_normalizer
except ImportError:
    # Fallback for different import contexts
    import sys
    from pathlib import Path
    service_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(service_root))
    from modules.models import (
        NormalizeRequest,
        NormalizeResponse,
        FileNormalizeResponse,
    )
    from modules.normalizers import get_normalizer, get_file_normalizer

# Shared imports
from services.shared.infrastructure.monitoring.logging import fire_and_forget
from services.shared.infrastructure.monitoring.metrics import (
    record_architecture_digitizer_request,
    record_architecture_digitizer_api_failure,
    record_architecture_digitizer_file_upload,
)

# Create router
router = APIRouter()

# Global variables (will be set by main.py)
metrics = None
logger_client = None
SERVICE_NAME = "architecture-digitizer"
store_architecture_in_docstore = None


def init_normalization_routes(app_metrics, app_logger_client, app_service_name, docstore_func):
    """Initialize route with dependencies from main app."""
    global metrics, logger_client, SERVICE_NAME, store_architecture_in_docstore
    metrics = app_metrics
    logger_client = app_logger_client
    SERVICE_NAME = app_service_name
    store_architecture_in_docstore = docstore_func


@router.post("/normalize", response_model=NormalizeResponse)
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
            if metrics:
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

            raise HTTPException(
                status_code=400, detail=f"Unsupported system: {request.system}"
            )

        # Fetch and normalize the data
        result = await normalizer.normalize(request.board_id, request.token)

        # Calculate metrics
        processing_time = time.time() - start_time
        components_count = len(result.get("components", []))
        connections_count = len(result.get("connections", []))
        data_size = len(str(result)) if result else 0

        # Record successful metrics
        if metrics:
            record_architecture_digitizer_request(
                metrics, request.system, "success", processing_time
            )

        # Store normalized data in doc_store (fire and forget)
        if store_architecture_in_docstore:
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
        if metrics:
            record_architecture_digitizer_request(
                metrics, getattr(request, "system", "unknown"), "error", error_time
            )
            record_architecture_digitizer_api_failure(
                metrics, getattr(request, "system", "unknown"), type(e).__name__
            )

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


@router.post("/normalize-file", response_model=FileNormalizeResponse)
async def normalize_file_upload(
    file: UploadFile = File(...),
    system: str = Form(
        ..., description="Diagram system (miro, figjam, lucid, confluence)"
    ),
    file_format: str = Form(..., description="File format (json, xml, html)"),
):
    """
    Normalize an uploaded diagram file into standardized format.

    Accepts diagram files exported from supported systems and converts
    them into the common Software Architecture JSON schema.
    """
    start_time = time.time()

    try:
        # Validate file size (10MB limit)
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=413, detail="File too large. Maximum size is 10MB."
            )

        # Reset file pointer
        await file.seek(0)

        # Get the appropriate file normalizer for the system
        file_normalizer = get_file_normalizer(system)
        if not file_normalizer:
            if metrics:
                record_architecture_digitizer_request(metrics, system, "error")
            raise HTTPException(status_code=400, detail=f"Unsupported system: {system}")

        # Check if the file format is supported for this system
        if not file_normalizer.supports_format(file_format):
            if metrics:
                record_architecture_digitizer_request(metrics, system, "error")
            raise HTTPException(
                status_code=400,
                detail=f"File format '{file_format}' not supported for system '{system}'",
            )

        # Read file content
        content = await file.read()

        # Normalize the file
        result = await file_normalizer.normalize_file(
            content, file.filename, file_format
        )

        # Record successful metrics
        duration = time.time() - start_time
        if metrics:
            record_architecture_digitizer_request(metrics, system, "success", duration)
            record_architecture_digitizer_file_upload(
                metrics, system, file_format, file_size, "success", duration
            )

        # Store normalized data in doc_store (fire and forget)
        if store_architecture_in_docstore:
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
        if metrics:
            record_architecture_digitizer_request(metrics, system, "error", duration)
            record_architecture_digitizer_api_failure(metrics, system, type(e).__name__)
            record_architecture_digitizer_file_upload(
                metrics, system, file_format, file_size, "error", duration
            )

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

