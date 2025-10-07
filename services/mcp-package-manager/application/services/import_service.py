"""Package Import Application Service."""

import json
import gzip
import tarfile
from typing import Optional
from pathlib import Path

from ...domain.entities.package import MCPPackage
from ...domain.entities.package_version import PackageVersion
from ...domain.repositories.package_repository import PackageRepository
from ...domain.repositories.version_repository import VersionRepository


class ImportService:
    """
    Application service for package import.
    
    Handles importing MCP packages from `.mcp` files.
    """
    
    def __init__(
        self,
        package_repo: PackageRepository,
        version_repo: VersionRepository,
    ):
        """
        Initialize import service.
        
        Args:
            package_repo: Package repository
            version_repo: Version repository
        """
        self.package_repo = package_repo
        self.version_repo = version_repo
    
    async def import_package(
        self,
        file_path: str,
        override_existing: bool = False,
    ) -> MCPPackage:
        """
        Import package from file.
        
        Args:
            file_path: Path to package file
            override_existing: Whether to override existing packages
            
        Returns:
            Imported package
            
        Raises:
            ValueError: If file invalid or package already exists
        """
        # Read file
        data = self._read_package_file(file_path)
        
        # Extract package data
        package_data = data.get("package")
        if not package_data:
            raise ValueError("Invalid package file: missing package data")
        
        # Check if package already exists
        existing = await self.package_repo.get_by_name_and_version(
            package_data["name"],
            package_data["version"],
        )
        
        if existing and not override_existing:
            raise ValueError(
                f"Package {package_data['name']}@{package_data['version']} already exists"
            )
        
        # Create package from data
        package = self._create_package_from_data(package_data)
        
        # Validate
        if not package.validate():
            raise ValueError(f"Package validation failed: {package.validation_errors}")
        
        # Save package
        if existing and override_existing:
            package.package_id = existing.package_id
            await self.package_repo.update(package)
        else:
            await self.package_repo.add(package)
        
        # Create version record
        version = PackageVersion(
            package_id=package.package_id,
            version=package.version,
            changelog="Imported from file",
        )
        await self.version_repo.add(version)
        
        return package
    
    def _read_package_file(self, file_path: str) -> dict:
        """
        Read package file.
        
        Args:
            file_path: File path
            
        Returns:
            Package data dictionary
        """
        path = Path(file_path)
        
        if not path.exists():
            raise ValueError(f"File not found: {file_path}")
        
        # Detect file type
        if file_path.endswith(".gz") or file_path.endswith(".mcp"):
            # Compressed file
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                return json.load(f)
        elif file_path.endswith(".json"):
            # Uncompressed JSON
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        elif file_path.endswith(".tar") or file_path.endswith(".tar.gz"):
            # TAR archive
            return self._read_tar_package(file_path)
        else:
            # Try as JSON
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
    
    def _read_tar_package(self, file_path: str) -> dict:
        """
        Read package from TAR archive.
        
        Args:
            file_path: TAR file path
            
        Returns:
            Package data
        """
        with tarfile.open(file_path, "r:*") as tar:
            # Extract manifest
            manifest_member = tar.getmember("manifest.json")
            manifest_file = tar.extractfile(manifest_member)
            
            if manifest_file:
                return json.load(manifest_file)
        
        raise ValueError("Invalid TAR package: missing manifest.json")
    
    def _create_package_from_data(self, data: dict) -> MCPPackage:
        """
        Create package entity from data.
        
        Args:
            data: Package data dictionary
            
        Returns:
            MCPPackage instance
        """
        from datetime import datetime
        
        # Convert ISO strings to datetime
        for field in ("created_at", "updated_at", "published_at", "last_deployed_at"):
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        return MCPPackage(**data)
    
    async def batch_import(
        self,
        file_paths: list[str],
        override_existing: bool = False,
    ) -> list[MCPPackage]:
        """
        Import multiple packages.
        
        Args:
            file_paths: List of package file paths
            override_existing: Whether to override existing packages
            
        Returns:
            List of imported packages
        """
        packages = []
        
        for file_path in file_paths:
            try:
                package = await self.import_package(file_path, override_existing)
                packages.append(package)
            except Exception as e:
                # Log error and continue
                print(f"Failed to import {file_path}: {e}")
        
        return packages

