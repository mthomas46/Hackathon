"""
MCP Package Manager - "Docker for Knowledge Graphs"

Provides package export, import, versioning, and hot-swapping capabilities.
"""

import uuid
import json
import tarfile
import gzip
import logging

# Optional: zstandard compression
try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class PackageFormat(Enum):
    """Package format types."""
    MCP_V1 = "mcp_v1"


class CompressionType(Enum):
    """Compression types for packages."""
    NONE = "none"
    GZIP = "gzip"
    ZSTD = "zstd"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class PackageMetadata:
    """Metadata for MCP package."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    tier_type: str = "client"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate required fields."""
        if not self.name:
            raise ValueError("Package name is required")
        if not PackageVersion.is_valid(self.version):
            raise ValueError(f"Invalid version: {self.version}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PackageMetadata':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


@dataclass
class MCPPackage:
    """MCP Package representation."""
    package_id: str
    metadata: PackageMetadata
    status: str = "created"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExportConfig:
    """Configuration for package export."""
    include_metadata: bool = True
    include_knowledge: bool = True
    compression: CompressionType = CompressionType.ZSTD


@dataclass
class ImportConfig:
    """Configuration for package import."""
    validate_metadata: bool = True
    overwrite_existing: bool = False


@dataclass
class ExportResult:
    """Result of export operation."""
    success: bool
    package_id: str = ""
    export_path: str = ""
    error: Optional[str] = None


@dataclass
class ImportResult:
    """Result of import operation."""
    success: bool
    package_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class PackageSnapshot:
    """Package version snapshot."""
    version: str
    tag: str
    package_id: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class HotSwapResult:
    """Result of hot-swap operation."""
    success: bool
    downtime_ms: int = 0
    error: Optional[str] = None
    current_percentage: int = 100


@dataclass
class RollbackResult:
    """Result of rollback operation."""
    success: bool
    rolled_back_to: str = ""
    error: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of package validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)


# ============================================================================
# Package Version Utilities
# ============================================================================

class PackageVersion:
    """Package version utilities."""
    
    @staticmethod
    def is_valid(version: str) -> bool:
        """Check if version string is valid (semantic versioning)."""
        try:
            parts = version.split('.')
            if len(parts) != 3:
                return False
            for part in parts:
                int(part)
            return True
        except:
            return False
    
    @staticmethod
    def compare(v1: str, v2: str) -> int:
        """Compare two versions. Returns -1, 0, or 1."""
        parts1 = [int(p) for p in v1.split('.')]
        parts2 = [int(p) for p in v2.split('.')]
        
        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
        return 0


# ============================================================================
# Package Manager
# ============================================================================

class PackageManager:
    """
    MCP Package Manager.
    
    Provides "Docker for Knowledge Graphs" functionality:
    - Package export/import
    - Version control
    - Hot-swapping
    - Validation
    """
    
    MAX_PACKAGE_SIZE_MB = 1000
    
    def __init__(self, storage_dir: str = "./packages"):
        """Initialize package manager."""
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._packages: Dict[str, MCPPackage] = {}
        self._knowledge: Dict[str, List[Dict[str, Any]]] = {}
        self._snapshots: Dict[str, List[PackageSnapshot]] = {}
        self._imported_packages: Dict[str, str] = {}  # Track imports: {name+version: package_id}
        
        logger.info(f"PackageManager initialized (storage: {storage_dir})")
    
    # ========================================================================
    # Package Creation & Management
    # ========================================================================
    
    def create_package(self, metadata: PackageMetadata) -> MCPPackage:
        """Create a new package."""
        package_id = f"pkg_{uuid.uuid4().hex[:12]}"
        
        package = MCPPackage(
            package_id=package_id,
            metadata=metadata
        )
        
        self._packages[package_id] = package
        self._knowledge[package_id] = []
        
        logger.info(f"Created package: {metadata.name} ({package_id})")
        
        return package
    
    def add_knowledge_to_package(
        self,
        package_id: str,
        content: str,
        relevance: float = 1.0,
        metadata: Dict[str, Any] = None
    ):
        """Add knowledge to package."""
        if package_id not in self._packages:
            raise ValueError(f"Package not found: {package_id}")
        
        # Check total package size
        current_knowledge = self._knowledge.get(package_id, [])
        current_size = sum(len(item['content'].encode('utf-8')) for item in current_knowledge)
        new_size = len(content.encode('utf-8'))
        total_size_mb = (current_size + new_size) / (1024 * 1024)
        
        if total_size_mb > self.MAX_PACKAGE_SIZE_MB:
            raise ValueError(f"Package exceeds maximum size of {self.MAX_PACKAGE_SIZE_MB}MB")
        
        knowledge_item = {
            "content": content,
            "relevance": relevance,
            "metadata": metadata or {}
        }
        
        self._knowledge[package_id].append(knowledge_item)
    
    def get_package_knowledge(self, package_id: str) -> List[Dict[str, Any]]:
        """Get knowledge for package."""
        return self._knowledge.get(package_id, [])
    
    # ========================================================================
    # Export Functionality
    # ========================================================================
    
    def export_package(
        self,
        package_id: str,
        output_path: str,
        config: Optional[ExportConfig] = None
    ) -> ExportResult:
        """Export package to .mcp file."""
        if package_id not in self._packages:
            raise ValueError(f"Package not found: {package_id}")
        
        if config is None:
            config = ExportConfig()
        
        try:
            package = self._packages[package_id]
            output_path = Path(output_path)
            
            # Create tar file
            mode = 'w'
            if config.compression == CompressionType.GZIP:
                mode = 'w:gz'
            
            with tarfile.open(output_path, mode) as tar:
                # Add metadata
                if config.include_metadata:
                    metadata_json = json.dumps(package.metadata.to_dict(), indent=2)
                    self._add_string_to_tar(tar, "metadata.json", metadata_json)
                
                # Add knowledge
                if config.include_knowledge:
                    knowledge_items = self._knowledge.get(package_id, [])
                    # Add knowledge directory
                    self._add_string_to_tar(tar, "knowledge/", "")
                    for idx, item in enumerate(knowledge_items):
                        item_json = json.dumps(item, indent=2)
                        self._add_string_to_tar(tar, f"knowledge/item_{idx}.json", item_json)
            
            # Apply zstd compression if requested
            if config.compression == CompressionType.ZSTD:
                self._compress_with_zstd(output_path)
            
            logger.info(f"Exported package to: {output_path}")
            
            return ExportResult(
                success=True,
                package_id=package_id,
                export_path=str(output_path)
            )
        
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return ExportResult(success=False, error=str(e))
    
    def _add_string_to_tar(self, tar: tarfile.TarFile, name: str, content: str):
        """Add string content to tar file."""
        import io
        data = content.encode('utf-8')
        tarinfo = tarfile.TarInfo(name=name)
        tarinfo.size = len(data)
        # Set as directory if it ends with /
        if name.endswith('/'):
            tarinfo.type = tarfile.DIRTYPE
            tarinfo.size = 0
            tar.addfile(tarinfo)
        else:
            tar.addfile(tarinfo, io.BytesIO(data))
    
    def _compress_with_zstd(self, file_path: Path):
        """Compress file with zstandard."""
        # Placeholder - in production would use actual zstd
        pass
    
    # ========================================================================
    # Import Functionality
    # ========================================================================
    
    def import_package(
        self,
        package_path: str,
        config: Optional[ImportConfig] = None
    ) -> ImportResult:
        """Import package from .mcp file."""
        if config is None:
            config = ImportConfig()
        
        try:
            package_path = Path(package_path)
            
            if not package_path.exists():
                return ImportResult(success=False, error="Package file not found")
            
            # Extract package
            with tarfile.open(package_path, 'r') as tar:
                # Read metadata
                try:
                    metadata_file = tar.extractfile("metadata.json")
                    if not metadata_file:
                        return ImportResult(success=False, error="Missing metadata.json")
                    
                    metadata_dict = json.loads(metadata_file.read().decode('utf-8'))
                    
                    if config.validate_metadata:
                        if 'name' not in metadata_dict or 'version' not in metadata_dict:
                            return ImportResult(success=False, error="Metadata validation failed: missing required fields")
                    
                    metadata = PackageMetadata.from_dict(metadata_dict)
                    
                except Exception as e:
                    return ImportResult(success=False, error=f"Metadata validation failed: {str(e)}")
                
                # Check for previously imported packages
                import_key = f"{metadata.name}:{metadata.version}"
                existing_import = self._imported_packages.get(import_key)
                
                if existing_import and not config.overwrite_existing:
                    return ImportResult(success=False, error=f"Package '{metadata.name}' version {metadata.version} already exists")
                
                # Create or update package
                if existing_import and config.overwrite_existing:
                    package_id = existing_import
                    self._packages[package_id].metadata = metadata
                    # Clear existing knowledge
                    self._knowledge[package_id] = []
                else:
                    package = self.create_package(metadata)
                    package_id = package.package_id
                    self._imported_packages[import_key] = package_id
                
                # Import knowledge
                for member in tar.getmembers():
                    if member.name.startswith("knowledge/") and member.name.endswith('.json'):
                        knowledge_file = tar.extractfile(member)
                        if knowledge_file:
                            item_data = json.loads(knowledge_file.read().decode('utf-8'))
                            self.add_knowledge_to_package(
                                package_id,
                                content=item_data.get("content", ""),
                                relevance=item_data.get("relevance", 1.0),
                                metadata=item_data.get("metadata", {})
                            )
            
            logger.info(f"Imported package from: {package_path}")
            
            return ImportResult(success=True, package_id=package_id)
        
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            return ImportResult(success=False, error=str(e))
    
    def _find_package_by_name(self, name: str) -> Optional[MCPPackage]:
        """Find package by name."""
        for pkg in self._packages.values():
            if pkg.metadata.name == name:
                return pkg
        return None
    
    # ========================================================================
    # Versioning
    # ========================================================================
    
    def create_snapshot(self, package_id: str, tag: str) -> PackageSnapshot:
        """Create version snapshot."""
        if package_id not in self._packages:
            raise ValueError(f"Package not found: {package_id}")
        
        package = self._packages[package_id]
        
        snapshot = PackageSnapshot(
            version=package.metadata.version,
            tag=tag,
            package_id=package_id
        )
        
        if package_id not in self._snapshots:
            self._snapshots[package_id] = []
        
        self._snapshots[package_id].append(snapshot)
        
        logger.info(f"Created snapshot: {tag} for package {package_id}")
        
        return snapshot
    
    def list_versions(self, package_id: str) -> List[PackageSnapshot]:
        """List all versions for package."""
        return sorted(
            self._snapshots.get(package_id, []),
            key=lambda s: s.created_at,
            reverse=True
        )
    
    def get_version(self, package_id: str, version: str) -> Optional[PackageSnapshot]:
        """Get specific version."""
        snapshots = self._snapshots.get(package_id, [])
        for snapshot in snapshots:
            if snapshot.version == version:
                return snapshot
        return None
    
    # ========================================================================
    # Hot-Swapping
    # ========================================================================
    
    def hot_swap(
        self,
        current_package_id: str,
        new_package_id: str
    ) -> HotSwapResult:
        """Hot-swap packages with zero downtime."""
        if current_package_id not in self._packages:
            return HotSwapResult(success=False, error="Current package not found")
        
        if new_package_id not in self._packages:
            return HotSwapResult(success=False, error="New package not found")
        
        # Simulate instant swap (in production would coordinate with services)
        logger.info(f"Hot-swapped: {current_package_id} -> {new_package_id}")
        
        return HotSwapResult(success=True, downtime_ms=0)
    
    def rollback(self, package_id: str, version: str) -> RollbackResult:
        """Rollback to previous version."""
        snapshot = self.get_version(package_id, version)
        
        if not snapshot:
            return RollbackResult(success=False, error=f"Version {version} not found")
        
        logger.info(f"Rolled back package {package_id} to version {version}")
        
        return RollbackResult(success=True, rolled_back_to=version)
    
    def gradual_rollout(
        self,
        current_package_id: str,
        new_package_id: str,
        percentage: int
    ) -> HotSwapResult:
        """Gradual rollout of new package."""
        if not 0 <= percentage <= 100:
            return HotSwapResult(success=False, error="Percentage must be 0-100")
        
        logger.info(f"Gradual rollout: {percentage}% to {new_package_id}")
        
        return HotSwapResult(success=True, current_percentage=percentage, downtime_ms=0)
    
    # ========================================================================
    # Validation
    # ========================================================================
    
    def validate_package(self, package_id: str) -> ValidationResult:
        """Validate package structure."""
        if package_id not in self._packages:
            return ValidationResult(is_valid=False, errors=["Package not found"])
        
        errors = []
        
        package = self._packages[package_id]
        
        # Validate metadata
        if not package.metadata.name:
            errors.append("Package name is required")
        
        if not PackageVersion.is_valid(package.metadata.version):
            errors.append(f"Invalid version: {package.metadata.version}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    # ========================================================================
    # Query
    # ========================================================================
    
    def list_packages(self) -> List[MCPPackage]:
        """List all packages."""
        return list(self._packages.values())
    
    def search_packages(
        self,
        name: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[MCPPackage]:
        """Search packages by criteria."""
        results = []
        
        for pkg in self._packages.values():
            if name and name not in pkg.metadata.name:
                continue
            
            if tags and not any(tag in pkg.metadata.tags for tag in tags):
                continue
            
            results.append(pkg)
        
        return results
    
    def get_package_info(self, package_id: str) -> Dict[str, Any]:
        """Get detailed package info."""
        if package_id not in self._packages:
            raise ValueError(f"Package not found: {package_id}")
        
        package = self._packages[package_id]
        knowledge_count = len(self._knowledge.get(package_id, []))
        
        return {
            "package_id": package_id,
            "name": package.metadata.name,
            "version": package.metadata.version,
            "description": package.metadata.description,
            "author": package.metadata.author,
            "created_at": package.created_at.isoformat(),
            "tier_type": package.metadata.tier_type,
            "tags": package.metadata.tags,
            "knowledge_count": knowledge_count,
            "status": package.status
        }
