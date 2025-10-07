"""Package Export Application Service."""

import json
import tarfile
import gzip
from typing import Optional
from pathlib import Path

from ...domain.entities.package import MCPPackage
from ...domain.value_objects.export_config import ExportConfig
from ...domain.value_objects.compression_type import CompressionType
from ...domain.repositories.package_repository import PackageRepository


class ExportService:
    """
    Application service for package export.
    
    Handles exporting MCP packages to portable `.mcp` files.
    """
    
    def __init__(self, package_repo: PackageRepository):
        """
        Initialize export service.
        
        Args:
            package_repo: Package repository
        """
        self.package_repo = package_repo
    
    async def export_package(
        self,
        package_id: str,
        output_path: str,
        config: Optional[ExportConfig] = None,
    ) -> str:
        """
        Export package to file.
        
        Args:
            package_id: Package ID to export
            output_path: Output file path
            config: Export configuration
            
        Returns:
            Path to exported file
            
        Raises:
            ValueError: If package not found or invalid
        """
        # Get package
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        # Use default config if not provided
        if config is None:
            config = ExportConfig()
        
        # Validate if configured
        if config.validate_before_export:
            if not package.validate():
                raise ValueError(f"Package validation failed: {package.validation_errors}")
        
        # Create export data
        export_data = self._create_export_data(package, config)
        
        # Write to file based on format
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        if config.compression == CompressionType.GZIP:
            self._export_compressed(export_data, str(output_file))
        elif config.compression == CompressionType.NONE:
            self._export_uncompressed(export_data, str(output_file))
        else:
            # Fallback to GZIP
            self._export_compressed(export_data, str(output_file))
        
        return str(output_file)
    
    def _create_export_data(
        self,
        package: MCPPackage,
        config: ExportConfig,
    ) -> dict:
        """
        Create export data structure.
        
        Args:
            package: Package to export
            config: Export configuration
            
        Returns:
            Export data dictionary
        """
        data = {
            "format_version": "1.0.0",
            "package": package.to_dict(),
        }
        
        if not config.include_metadata:
            # Remove non-essential metadata
            data["package"].pop("created_at", None)
            data["package"].pop("updated_at", None)
            data["package"].pop("published_at", None)
            data["package"].pop("deployed_count", None)
        
        if not config.include_dependencies:
            data["package"]["dependencies"] = []
        
        return data
    
    def _export_compressed(self, data: dict, output_path: str) -> None:
        """
        Export with GZIP compression.
        
        Args:
            data: Export data
            output_path: Output file path
        """
        json_data = json.dumps(data, indent=2)
        
        with gzip.open(output_path, "wt", encoding="utf-8") as f:
            f.write(json_data)
    
    def _export_uncompressed(self, data: dict, output_path: str) -> None:
        """
        Export without compression.
        
        Args:
            data: Export data
            output_path: Output file path
        """
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    
    async def export_to_tar(
        self,
        package_id: str,
        output_path: str,
    ) -> str:
        """
        Export package to TAR archive.
        
        Args:
            package_id: Package ID
            output_path: Output TAR file path
            
        Returns:
            Path to TAR file
        """
        package = await self.package_repo.get_by_id(package_id)
        if not package:
            raise ValueError(f"Package not found: {package_id}")
        
        # Create TAR archive
        with tarfile.open(output_path, "w:gz") as tar:
            # Add manifest
            manifest = json.dumps(package.to_dict(), indent=2)
            
            # Create temp file for manifest
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as tmp:
                tmp.write(manifest)
                tmp_path = tmp.name
            
            tar.add(tmp_path, arcname="manifest.json")
            
            # Clean up temp file
            Path(tmp_path).unlink()
        
        return output_path

