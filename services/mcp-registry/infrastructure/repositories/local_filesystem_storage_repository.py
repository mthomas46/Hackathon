"""Local Filesystem Storage Repository Implementation."""

import logging
import os
from pathlib import Path
from typing import Optional
import hashlib

import aiofiles

from services.mcp_registry.domain.entities.mcp_package import MCPPackage
from services.mcp_registry.domain.repositories.package_storage_repository import PackageStorageRepository
from services.mcp_registry.domain.value_objects.storage_backend import StorageBackend

logger = logging.getLogger(__name__)


class LocalFilesystemStorageRepository(PackageStorageRepository):
    """Local filesystem implementation of PackageStorageRepository."""
    
    def __init__(self, base_path: str = "./data/mcp-packages"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_package_path(self, package: MCPPackage) -> Path:
        """Get filesystem path for package."""
        # Organize by MCP ID / version
        mcp_dir = self.base_path / package.mcp_id
        mcp_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{package.package_id}{package.export_format.file_extension}"
        return mcp_dir / filename
    
    async def store(self, package: MCPPackage, data: bytes) -> str:
        """Store package data."""
        package_path = self._get_package_path(package)
        
        async with aiofiles.open(package_path, 'wb') as f:
            await f.write(data)
        
        logger.info(f"Stored package at: {package_path}")
        return str(package_path)
    
    async def retrieve(self, storage_location: str) -> bytes:
        """Retrieve package data."""
        package_path = Path(storage_location)
        
        if not package_path.exists():
            raise FileNotFoundError(f"Package not found: {storage_location}")
        
        async with aiofiles.open(package_path, 'rb') as f:
            data = await f.read()
        
        logger.debug(f"Retrieved package from: {storage_location}")
        return data
    
    async def exists(self, storage_location: str) -> bool:
        """Check if package exists."""
        return Path(storage_location).exists()
    
    async def delete(self, storage_location: str) -> bool:
        """Delete package."""
        package_path = Path(storage_location)
        
        if not package_path.exists():
            return False
        
        package_path.unlink()
        logger.info(f"Deleted package: {storage_location}")
        return True
    
    async def get_size(self, storage_location: str) -> Optional[int]:
        """Get package size."""
        package_path = Path(storage_location)
        
        if not package_path.exists():
            return None
        
        return package_path.stat().st_size
    
    async def verify_checksum(self, storage_location: str, expected_checksum: str) -> bool:
        """Verify package checksum."""
        try:
            data = await self.retrieve(storage_location)
            actual_checksum = hashlib.sha256(data).hexdigest()
            return actual_checksum == expected_checksum
        except Exception as e:
            logger.error(f"Checksum verification failed: {e}")
            return False
    
    def get_backend(self) -> StorageBackend:
        """Get storage backend type."""
        return StorageBackend.LOCAL_FILESYSTEM

