"""Systems information endpoints for architecture-digitizer service.

This module provides information about supported diagram systems and file formats.
"""

from fastapi import APIRouter, HTTPException

# Local imports from modules
try:
    from ...modules.models import (
        SupportedSystemsResponse,
        SupportedFileFormatsResponse,
    )
    from ...modules.normalizers import SUPAPI_PORTED_SYSTEMS, get_file_normalizer
except ImportError:
    # Fallback for different import contexts
    import sys
    from pathlib import Path
    service_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(service_root))
    from modules.models import (
        SupportedSystemsResponse,
        SupportedFileFormatsResponse,
    )
    from modules.normalizers import SUPAPI_PORTED_SYSTEMS, get_file_normalizer

# Create router
router = APIRouter()


@router.get("/supported-systems", response_model=SupportedSystemsResponse)
async def get_supported_systems():
    """Get list of supported diagram systems and their capabilities."""
    systems_info = []
    for system_name, normalizer_class in SUPAPI_PORTED_SYSTEMS.items():
        systems_info.append(
            {
                "name": system_name,
                "description": normalizer_class.get_description(),
                "auth_type": normalizer_class.get_auth_type(),
                "supported": True,
            }
        )

    return SupportedSystemsResponse(systems=systems_info, count=len(systems_info))


@router.get(
    "/supported-file-formats/{system}", response_model=SupportedFileFormatsResponse
)
async def get_supported_file_formats(system: str):
    """Get supported file formats for a specific diagram system."""
    file_normalizer = get_file_normalizer(system)
    if not file_normalizer:
        raise HTTPException(
            status_code=404,
            detail=f"System '{system}' not found or not supported for file uploads",
        )

    supported_formats = file_normalizer.get_supported_formats()

    return SupportedFileFormatsResponse(
        system=system, supported_formats=supported_formats, count=len(supported_formats)
    )

