"""Package export/import functionality for MCP Store.

Enables packaging MCPs into portable .mcp files and importing them back.
"""

import logging
import json
import tarfile
import io
from typing import Dict, Any, Optional
from datetime import datetime

from services.mcp_store.domain.entities.mcp_package import MCPPackage
from services.mcp_store.domain.entities.mcp_version import MCPVersion
from services.mcp_store.domain.repositories.package_repository import (
    PackageRepository,
    EntityNotFoundError,
)
from services.mcp_store.domain.repositories.storage_repository import StorageRepository
from services.mcp_store.domain.services.compression_service import CompressionService

logger = logging.getLogger(__name__)


class ExportImportError(Exception):
    """Base exception for export/import errors."""
    pass


class PackageExportImportUseCase:
    """
    Use case for exporting and importing MCP packages.
    
    Export format (.mcp file):
    - TAR archive containing:
      - metadata.json (package + version metadata)
      - package.bin (compressed package data)
    """
    
    def __init__(
        self,
        package_repo: PackageRepository,
        storage_repo: StorageRepository,
        compression_service: CompressionService,
    ):
        self.package_repo = package_repo
        self.storage_repo = storage_repo
        self.compression_service = compression_service
        logger.info("PackageExportImportUseCase initialized")
    
    async def export_package(
        self,
        package_id: str,
        version_id: Optional[str] = None,
        include_all_versions: bool = False
    ) -> bytes:
        """
        Export a package (and optionally its versions) to a .mcp file.
        
        Args:
            package_id: Package ID to export
            version_id: Specific version ID (optional)
            include_all_versions: Export all versions (default: False)
            
        Returns:
            Bytes of the .mcp file (TAR archive)
            
        Raises:
            ExportImportError: If export fails
        """
        try:
            # Get package metadata
            package = await self.package_repo.get_package_by_id(package_id)
            if not package:
                raise ExportImportError(f"Package {package_id} not found")
            
            logger.info(f"Exporting package '{package.name}' (ID: {package_id})")
            
            # Get versions to export
            if include_all_versions:
                versions = await self.package_repo.get_versions_for_package(package_id)
            elif version_id:
                version = await self.package_repo.get_version_by_id(version_id)
                versions = [version] if version else []
            elif package.latest_version_id:
                version = await self.package_repo.get_version_by_id(package.latest_version_id)
                versions = [version] if version else []
            else:
                versions = []
            
            if not versions:
                raise ExportImportError(f"No versions found for package {package_id}")
            
            # Create export metadata
            export_metadata = {
                "format_version": "1.0.0",
                "exported_at": datetime.now().isoformat(),
                "package": self._package_to_dict(package),
                "versions": [self._version_to_dict(v) for v in versions],
                "version_count": len(versions),
            }
            
            # Create TAR archive in memory
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
                # Add metadata.json
                metadata_json = json.dumps(export_metadata, indent=2).encode('utf-8')
                metadata_info = tarfile.TarInfo(name='metadata.json')
                metadata_info.size = len(metadata_json)
                metadata_info.mtime = int(datetime.now().timestamp())
                tar.addfile(metadata_info, io.BytesIO(metadata_json))
                
                # Add each version's binary data
                for version in versions:
                    try:
                        # Download binary from storage
                        binary_data = await self.storage_repo.download(version.storage_path)
                        
                        # Add to TAR
                        binary_info = tarfile.TarInfo(name=f'versions/{version.version_id}.bin')
                        binary_info.size = len(binary_data)
                        binary_info.mtime = int(version.created_at.timestamp())
                        tar.addfile(binary_info, io.BytesIO(binary_data))
                        
                        logger.info(f"Added version {version.version_string} to export")
                    except Exception as e:
                        logger.warning(f"Failed to add version {version.version_id}: {e}")
                        # Continue with other versions
            
            tar_buffer.seek(0)
            export_data = tar_buffer.read()
            
            logger.info(f"Export complete: {len(export_data):,} bytes")
            return export_data
            
        except ExportImportError:
            raise
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            raise ExportImportError(f"Failed to export package: {e}") from e
    
    async def import_package(
        self,
        mcp_file_data: bytes,
        owner_id: str,
        overwrite_existing: bool = False,
        preserve_ids: bool = False
    ) -> Dict[str, Any]:
        """
        Import a package from a .mcp file.
        
        Args:
            mcp_file_data: Bytes of the .mcp file
            owner_id: Owner ID for the imported package
            overwrite_existing: Overwrite existing package with same name
            preserve_ids: Preserve original package/version IDs
            
        Returns:
            Dictionary with import results
            
        Raises:
            ExportImportError: If import fails
        """
        try:
            logger.info(f"Importing package (size: {len(mcp_file_data):,} bytes)")
            
            # Parse TAR archive
            tar_buffer = io.BytesIO(mcp_file_data)
            metadata = None
            version_binaries = {}
            
            with tarfile.open(fileobj=tar_buffer, mode='r:gz') as tar:
                # Extract metadata
                try:
                    metadata_file = tar.extractfile('metadata.json')
                    metadata = json.loads(metadata_file.read().decode('utf-8'))
                except KeyError:
                    raise ExportImportError("Invalid .mcp file: missing metadata.json")
                
                # Extract version binaries
                for member in tar.getmembers():
                    if member.name.startswith('versions/') and member.name.endswith('.bin'):
                        version_id = member.name.split('/')[1].replace('.bin', '')
                        binary_file = tar.extractfile(member)
                        version_binaries[version_id] = binary_file.read()
            
            if not metadata:
                raise ExportImportError("Failed to parse metadata from .mcp file")
            
            # Validate format version
            format_version = metadata.get('format_version', '1.0.0')
            if not format_version.startswith('1.'):
                raise ExportImportError(f"Unsupported format version: {format_version}")
            
            # Check if package exists
            package_data = metadata['package']
            existing_package = await self.package_repo.get_package_by_name(package_data['name'])
            
            if existing_package and not overwrite_existing:
                raise ExportImportError(
                    f"Package '{package_data['name']}' already exists. "
                    "Set overwrite_existing=True to replace."
                )
            
            # Create/update package
            if existing_package and overwrite_existing:
                # Update existing package
                package = existing_package
                package.description = package_data['description']
                package.tags = package_data['tags']
                package.categories = package_data['categories']
                package.metadata = package_data.get('metadata', {})
                package.owner_id = owner_id  # Use new owner
                await self.package_repo.update_package(package)
                logger.info(f"Updated existing package: {package.name}")
            else:
                # Create new package
                package = MCPPackage(
                    package_id=package_data['package_id'] if preserve_ids else None,
                    name=package_data['name'],
                    description=package_data['description'],
                    owner_id=owner_id,  # Use new owner
                    tags=package_data['tags'],
                    categories=package_data['categories'],
                    is_public=package_data.get('is_public', False),
                    metadata=package_data.get('metadata', {}),
                )
                await self.package_repo.save_package(package)
                logger.info(f"Created new package: {package.name}")
            
            # Import versions
            imported_versions = []
            for version_data in metadata['versions']:
                version_id = version_data['version_id']
                
                if version_id not in version_binaries:
                    logger.warning(f"Binary not found for version {version_id}, skipping")
                    continue
                
                # Upload binary to storage
                storage_path = f"packages/{package.package_id}/{version_data['version_string']}.mcp"
                await self.storage_repo.upload(
                    storage_path,
                    version_binaries[version_id],
                    "application/octet-stream"
                )
                
                # Create version
                version = MCPVersion(
                    version_id=version_data['version_id'] if preserve_ids else None,
                    package_id=package.package_id,
                    version_string=version_data['version_string'],
                    storage_path=storage_path,
                    checksum=version_data['checksum'],
                    size_bytes=version_data['size_bytes'],
                    release_notes=version_data.get('release_notes'),
                    is_active=version_data.get('is_active', True),
                    metadata=version_data.get('metadata', {}),
                )
                
                await self.package_repo.save_version(version)
                imported_versions.append(version)
                logger.info(f"Imported version {version.version_string}")
            
            # Update latest version
            if imported_versions:
                latest_version = max(imported_versions, key=lambda v: v.created_at)
                package.update_latest_version(latest_version.version_id)
                await self.package_repo.update_package(package)
            
            result = {
                "status": "success",
                "package_id": package.package_id,
                "package_name": package.name,
                "versions_imported": len(imported_versions),
                "version_ids": [v.version_id for v in imported_versions],
                "overwritten": existing_package is not None,
            }
            
            logger.info(f"Import complete: {result}")
            return result
            
        except ExportImportError:
            raise
        except Exception as e:
            logger.error(f"Import failed: {e}", exc_info=True)
            raise ExportImportError(f"Failed to import package: {e}") from e
    
    async def validate_mcp_file(self, mcp_file_data: bytes) -> Dict[str, Any]:
        """
        Validate a .mcp file without importing it.
        
        Args:
            mcp_file_data: Bytes of the .mcp file
            
        Returns:
            Validation results with metadata
            
        Raises:
            ExportImportError: If validation fails
        """
        try:
            logger.info("Validating .mcp file")
            
            # Parse TAR archive
            tar_buffer = io.BytesIO(mcp_file_data)
            
            with tarfile.open(fileobj=tar_buffer, mode='r:gz') as tar:
                # Check for required files
                members = tar.getmembers()
                member_names = [m.name for m in members]
                
                if 'metadata.json' not in member_names:
                    raise ExportImportError("Invalid .mcp file: missing metadata.json")
                
                # Extract and validate metadata
                metadata_file = tar.extractfile('metadata.json')
                metadata = json.loads(metadata_file.read().decode('utf-8'))
                
                # Count version binaries
                version_binaries = [m for m in members if m.name.startswith('versions/')]
                
                return {
                    "valid": True,
                    "format_version": metadata.get('format_version'),
                    "package_name": metadata['package']['name'],
                    "package_description": metadata['package']['description'],
                    "version_count": metadata.get('version_count', 0),
                    "binaries_found": len(version_binaries),
                    "exported_at": metadata.get('exported_at'),
                    "file_size_bytes": len(mcp_file_data),
                }
        except ExportImportError:
            raise
        except Exception as e:
            logger.error(f"Validation failed: {e}", exc_info=True)
            return {
                "valid": False,
                "error": str(e)
            }
    
    def _package_to_dict(self, package: MCPPackage) -> Dict[str, Any]:
        """Convert package to dictionary for export."""
        return {
            "package_id": package.package_id,
            "name": package.name,
            "description": package.description,
            "owner_id": package.owner_id,
            "status": package.status.value,
            "tags": package.tags,
            "categories": package.categories,
            "is_public": package.is_public,
            "download_count": package.download_count,
            "star_count": package.star_count,
            "metadata": package.metadata,
            "created_at": package.created_at.isoformat(),
        }
    
    def _version_to_dict(self, version: MCPVersion) -> Dict[str, Any]:
        """Convert version to dictionary for export."""
        return {
            "version_id": version.version_id,
            "version_string": version.version_string,
            "checksum": version.checksum,
            "size_bytes": version.size_bytes,
            "release_notes": version.release_notes,
            "is_active": version.is_active,
            "metadata": version.metadata,
            "created_at": version.created_at.isoformat(),
        }
