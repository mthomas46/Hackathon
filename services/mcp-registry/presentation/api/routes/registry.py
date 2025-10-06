"""Registry API routes."""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File

from services.mcp_registry.application.dto.export_mcp_request import ExportMCPRequest
from services.mcp_registry.application.dto.import_mcp_request import ImportMCPRequest
from services.mcp_registry.application.dto.package_info_response import PackageInfoResponse
from services.mcp_registry.application.dto.registry_entry_response import RegistryEntryResponse
from services.mcp_registry.application.use_cases.export_mcp_use_case import ExportMCPUseCase
from services.mcp_registry.application.use_cases.import_mcp_use_case import ImportMCPUseCase
from services.mcp_registry.application.use_cases.get_registry_entry_use_case import GetRegistryEntryUseCase
from services.mcp_registry.application.use_cases.search_registry_use_case import SearchRegistryUseCase
from services.mcp_registry.presentation.api.models.requests import (
    ExportMCPRequestModel,
    ImportMCPRequestModel,
    SearchRequestModel,
)
from services.mcp_registry.presentation.dependencies import (
    get_export_use_case,
    get_import_use_case,
    get_get_entry_use_case,
    get_search_use_case,
)
from services.mcp_registry.domain.value_objects.export_format import ExportFormat
from services.mcp_registry.domain.value_objects.storage_backend import StorageBackend

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registry", tags=["Registry"])


@router.post(
    "/export",
    response_model=PackageInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Export MCP",
    description="Export an MCP to a portable package"
)
async def export_mcp(
    request: ExportMCPRequestModel,
    use_case: ExportMCPUseCase = Depends(get_export_use_case)
) -> PackageInfoResponse:
    """Export an MCP to a package."""
    try:
        dto = ExportMCPRequest(
            mcp_id=request.mcp_id,
            version=request.version,
            export_format=ExportFormat(request.export_format),
            storage_backend=StorageBackend(request.storage_backend),
            compress=request.compress,
            include_dependencies=request.include_dependencies,
            exported_by=request.exported_by,
        )
        
        return await use_case.execute(dto)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Export failed")


@router.post(
    "/import",
    response_model=RegistryEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import MCP",
    description="Import an MCP from a package"
)
async def import_mcp(
    file: UploadFile = File(..., description="MCP package file"),
    request: ImportMCPRequestModel = Depends(),
    use_case: ImportMCPUseCase = Depends(get_import_use_case)
) -> RegistryEntryResponse:
    """Import an MCP from a package file."""
    try:
        # Read package data
        package_data = await file.read()
        
        dto = ImportMCPRequest(
            package_data=package_data,
            export_format=ExportFormat(request.export_format),
            imported_by=request.imported_by,
            verify_integrity=request.verify_integrity,
            run_security_scan=request.run_security_scan,
            auto_register=request.auto_register,
            make_public=request.make_public,
            override_mcp_id=request.override_mcp_id,
            override_owner_id=request.override_owner_id,
        )
        
        return await use_case.execute(dto)
        
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Import failed")


@router.get(
    "/entries/{entry_id}",
    response_model=RegistryEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Registry Entry",
    description="Get registry entry by ID"
)
async def get_entry(
    entry_id: str,
    use_case: GetRegistryEntryUseCase = Depends(get_get_entry_use_case)
) -> RegistryEntryResponse:
    """Get registry entry by ID."""
    entry = await use_case.get_by_id(entry_id)
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    
    return entry


@router.get(
    "/mcps/{mcp_id}",
    response_model=RegistryEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get MCP",
    description="Get MCP by ID and optional version"
)
async def get_mcp(
    mcp_id: str,
    version: Optional[str] = None,
    use_case: GetRegistryEntryUseCase = Depends(get_get_entry_use_case)
) -> RegistryEntryResponse:
    """Get MCP by ID and version."""
    entry = await use_case.get_by_mcp_id(mcp_id, version)
    
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP not found")
    
    return entry


@router.get(
    "/mcps/{mcp_id}/versions",
    response_model=List[RegistryEntryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Versions",
    description="List all versions of an MCP"
)
async def list_versions(
    mcp_id: str,
    use_case: GetRegistryEntryUseCase = Depends(get_get_entry_use_case)
) -> List[RegistryEntryResponse]:
    """List all versions of an MCP."""
    return await use_case.list_versions(mcp_id)


@router.get(
    "/public",
    response_model=List[RegistryEntryResponse],
    status_code=status.HTTP_200_OK,
    summary="List Public MCPs",
    description="List all public MCPs"
)
async def list_public(
    limit: Optional[int] = 100,
    use_case: GetRegistryEntryUseCase = Depends(get_get_entry_use_case)
) -> List[RegistryEntryResponse]:
    """List public MCPs."""
    return await use_case.list_public(limit)


@router.post(
    "/search",
    response_model=List[RegistryEntryResponse],
    status_code=status.HTTP_200_OK,
    summary="Search Registry",
    description="Search the registry with filters"
)
async def search_registry(
    request: SearchRequestModel,
    use_case: SearchRegistryUseCase = Depends(get_search_use_case)
) -> List[RegistryEntryResponse]:
    """Search the registry."""
    return await use_case.search(
        query=request.query,
        tier=request.tier,
        tags=request.tags,
        limit=request.limit
    )

