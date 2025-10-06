"""Export MCP Use Case."""

import logging
from datetime import datetime, timezone
from typing import Tuple
import uuid

from services.mcp_registry.domain.entities.mcp_package import MCPPackage
from services.mcp_registry.domain.repositories.registry_repository import RegistryRepository
from services.mcp_registry.domain.repositories.package_storage_repository import PackageStorageRepository
from services.mcp_registry.application.dto.export_mcp_request import ExportMCPRequest
from services.mcp_registry.application.dto.package_info_response import PackageInfoResponse
from services.mcp_registry.domain.value_objects.mcp_version import MCPVersion

logger = logging.getLogger(__name__)


class ExportMCPUseCase:
    """
    Use case for exporting an MCP to a package.
    
    Workflow:
    1. Get MCP from registry
    2. Collect MCP artifacts
    3. Create package with checksums
    4. Store package
    5. Return package info
    """
    
    def __init__(
        self,
        registry_repository: RegistryRepository,
        storage_repository: PackageStorageRepository,
    ):
        self.registry_repo = registry_repository
        self.storage_repo = storage_repository
    
    async def execute(self, request: ExportMCPRequest) -> PackageInfoResponse:
        """
        Export an MCP to a package.
        
        Args:
            request: Export request
        
        Returns:
            Package info response
        
        Raises:
            ValueError: If MCP not found or invalid
        """
        logger.info(f"Exporting MCP: {request.mcp_id}, version: {request.version}")
        
        # Get MCP from registry
        version_obj = MCPVersion.from_string(request.version) if request.version else None
        entry = await self.registry_repo.get_by_mcp_id(request.mcp_id, version_obj)
        
        if not entry:
            raise ValueError(f"MCP not found: {request.mcp_id}")
        
        if not entry.status.is_usable:
            raise ValueError(f"MCP is not usable: {entry.status}")
        
        # Create package
        package_id = f"pkg-{uuid.uuid4().hex[:12]}"
        package = MCPPackage(
            package_id=package_id,
            manifest=entry.manifest,
            export_format=request.export_format,
            exported_at=datetime.now(timezone.utc),
            exported_by=request.exported_by,
            is_compressed=request.compress,
        )
        
        # TODO: Collect actual MCP artifacts (vector DB, graph DB, etc.)
        # For now, create placeholder data
        package_data = self._create_package_data(package, request)
        
        # Set checksums
        package.set_checksum(package_data)
        package.storage_size_bytes = len(package_data)
        
        # Store package
        storage_location = await self.storage_repo.store(package, package_data)
        package.storage_path = storage_location
        
        logger.info(f"Exported MCP {request.mcp_id} to {storage_location}")
        
        # Record download
        entry.record_download()
        await self.registry_repo.save(entry)
        
        # Return response
        return PackageInfoResponse(
            package_id=package.package_id,
            mcp_id=package.mcp_id,
            name=package.name,
            version=str(package.version),
            export_format=package.export_format.value,
            exported_at=package.exported_at.isoformat(),
            exported_by=package.exported_by,
            storage_path=package.storage_path or "",
            storage_size_bytes=package.storage_size_bytes,
            storage_size_mb=package.get_storage_size_mb(),
            is_compressed=package.is_compressed,
            compression_ratio=package.compression_ratio,
            compression_savings_mb=package.get_compression_savings_mb(),
            checksum_sha256=package.checksum_sha256 or "",
            checksum_md5=package.checksum_md5 or "",
            included_artifacts=package.included_artifacts,
            artifact_count=len(package.included_artifacts),
            bundled_dependencies=package.bundled_dependencies,
            external_dependencies=package.external_dependencies,
            tier=package.manifest.tier,
            scope=package.manifest.scope,
            description=package.manifest.description,
            has_vector_db=package.manifest.has_vector_db,
            has_graph_db=package.manifest.has_graph_db,
            metadata=package.metadata,
        )
    
    def _create_package_data(self, package: MCPPackage, request: ExportMCPRequest) -> bytes:
        """
        Create package data (placeholder implementation).
        
        In production, this would:
        1. Collect vector DB data
        2. Collect graph DB data
        3. Collect artifacts
        4. Serialize to export_format
        5. Optionally compress
        
        Args:
            package: Package to create data for
            request: Export request
        
        Returns:
            Package binary data
        """
        # Placeholder: Just return manifest as JSON
        import json
        manifest_json = json.dumps(package.manifest.to_dict(), indent=2)
        return manifest_json.encode()

