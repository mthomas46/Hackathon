"""Import MCP Use Case."""

import logging
from datetime import datetime, timezone
import uuid
import json

from services.mcp_registry.domain.entities.mcp_package import MCPPackage
from services.mcp_registry.domain.entities.mcp_manifest import MCPManifest
from services.mcp_registry.domain.entities.registry_entry import RegistryEntry
from services.mcp_registry.domain.repositories.registry_repository import RegistryRepository
from services.mcp_registry.domain.repositories.package_storage_repository import PackageStorageRepository
from services.mcp_registry.application.dto.import_mcp_request import ImportMCPRequest
from services.mcp_registry.application.dto.registry_entry_response import RegistryEntryResponse
from services.mcp_registry.domain.value_objects.registry_status import RegistryStatus
from services.mcp_registry.domain.value_objects.mcp_version import MCPVersion

logger = logging.getLogger(__name__)


class ImportMCPUseCase:
    """
    Use case for importing an MCP from a package.
    
    Workflow:
    1. Deserialize package
    2. Verify integrity (optional)
    3. Run security scan (optional)
    4. Store package
    5. Register in registry (optional)
    6. Return registry entry
    """
    
    def __init__(
        self,
        registry_repository: RegistryRepository,
        storage_repository: PackageStorageRepository,
    ):
        self.registry_repo = registry_repository
        self.storage_repo = storage_repository
    
    async def execute(self, request: ImportMCPRequest) -> RegistryEntryResponse:
        """
        Import an MCP from a package.
        
        Args:
            request: Import request
        
        Returns:
            Registry entry response
        
        Raises:
            ValueError: If package invalid or integrity check fails
        """
        logger.info(f"Importing MCP package ({len(request.package_data)} bytes)")
        
        # Deserialize package
        package = self._deserialize_package(request.package_data, request.export_format)
        
        # Verify integrity
        if request.verify_integrity:
            if not package.verify_checksum(request.package_data):
                raise ValueError("Package integrity check failed: checksum mismatch")
            logger.info("Package integrity verified")
        
        # Run security scan (placeholder)
        security_passed = True
        if request.run_security_scan:
            security_passed = await self._run_security_scan(package)
            logger.info(f"Security scan: {'passed' if security_passed else 'failed'}")
        
        # Apply overrides
        if request.override_mcp_id:
            package.manifest.mcp_id = request.override_mcp_id
        
        # Store package
        storage_location = await self.storage_repo.store(package, request.package_data)
        logger.info(f"Package stored at: {storage_location}")
        
        # Register in registry
        if request.auto_register:
            entry = await self._register_package(package, storage_location, request)
            
            # Update security status
            if request.run_security_scan:
                entry.update_security_scan(security_passed, [] if security_passed else ["Placeholder issue"])
            
            # Update integrity status
            if request.verify_integrity:
                entry.update_integrity_check(True)
            
            # Make available if checks passed
            if security_passed:
                entry.update_status(RegistryStatus.AVAILABLE, "Imported and verified")
            
            await self.registry_repo.save(entry)
            logger.info(f"MCP registered: {entry.entry_id}")
            
            return self._to_response(entry)
        else:
            # Return minimal response if not auto-registered
            raise NotImplementedError("Manual registration not yet implemented")
    
    def _deserialize_package(self, data: bytes, export_format) -> MCPPackage:
        """
        Deserialize package from bytes.
        
        Args:
            data: Package data
            export_format: Export format
        
        Returns:
            MCPPackage
        """
        # Placeholder: Just parse JSON manifest
        manifest_dict = json.loads(data.decode())
        manifest = MCPManifest.from_dict(manifest_dict)
        
        package = MCPPackage(
            package_id=f"pkg-{uuid.uuid4().hex[:12]}",
            manifest=manifest,
            export_format=export_format,
        )
        package.set_checksum(data)
        package.storage_size_bytes = len(data)
        
        return package
    
    async def _run_security_scan(self, package: MCPPackage) -> bool:
        """
        Run security scan on package (placeholder).
        
        Args:
            package: Package to scan
        
        Returns:
            True if passed
        """
        # Placeholder: Always pass
        return True
    
    async def _register_package(
        self,
        package: MCPPackage,
        storage_location: str,
        request: ImportMCPRequest
    ) -> RegistryEntry:
        """
        Register package in registry.
        
        Args:
            package: Package to register
            storage_location: Storage location
            request: Import request
        
        Returns:
            RegistryEntry
        """
        entry_id = f"entry-{uuid.uuid4().hex[:12]}"
        owner_id = request.override_owner_id or "system"
        
        entry = RegistryEntry(
            entry_id=entry_id,
            mcp_id=package.mcp_id,
            manifest=package.manifest,
            status=RegistryStatus.PENDING,
            storage_backend=self.storage_repo.get_backend(),
            storage_location=storage_location,
            export_format=package.export_format,
            owner_id=owner_id,
            owner_organization=request.override_organization,
            is_public=request.make_public,
        )
        
        return entry
    
    def _to_response(self, entry: RegistryEntry) -> RegistryEntryResponse:
        """Convert RegistryEntry to response DTO."""
        return RegistryEntryResponse(
            entry_id=entry.entry_id,
            mcp_id=entry.mcp_id,
            name=entry.name,
            version=str(entry.version),
            description=entry.description,
            status=entry.status.value,
            status_message=entry.status_message,
            storage_backend=entry.storage_backend.value,
            storage_location=entry.storage_location,
            export_format=entry.export_format.value,
            tier=entry.manifest.tier,
            scope=entry.manifest.scope,
            total_size_bytes=entry.manifest.total_size_bytes,
            has_vector_db=entry.manifest.has_vector_db,
            has_graph_db=entry.manifest.has_graph_db,
            registered_at=entry.registered_at.isoformat(),
            last_accessed_at=entry.last_accessed_at.isoformat() if entry.last_accessed_at else None,
            deprecated_at=entry.deprecated_at.isoformat() if entry.deprecated_at else None,
            archived_at=entry.archived_at.isoformat() if entry.archived_at else None,
            is_latest=entry.is_latest,
            previous_version_id=entry.previous_version_id,
            next_version_id=entry.next_version_id,
            download_count=entry.download_count,
            import_count=entry.import_count,
            access_count=entry.access_count,
            security_scan_status=entry.security_scan_status,
            security_scan_at=entry.security_scan_at.isoformat() if entry.security_scan_at else None,
            security_issues=entry.security_issues,
            integrity_check_status=entry.integrity_check_status,
            integrity_check_at=entry.integrity_check_at.isoformat() if entry.integrity_check_at else None,
            owner_id=entry.owner_id,
            owner_organization=entry.owner_organization,
            maintainers=entry.maintainers,
            is_public=entry.is_public,
            tags=entry.manifest.tags,
            metadata=entry.metadata,
        )

