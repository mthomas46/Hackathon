"""
Unit tests for MCP Package Manager.

Tests the "Docker for Knowledge Graphs" functionality:
- Package format (.mcp files)
- Export/import
- Versioning
- Hot-swapping
- Validation
"""

import pytest
import sys
from pathlib import Path
import tempfile
import os
import json
from datetime import datetime

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_package_manager.src.package_manager import (
    MCPPackage,
    PackageMetadata,
    PackageVersion,
    ExportConfig,
    ImportConfig,
    PackageManager,
    PackageFormat,
    CompressionType
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_metadata():
    """Create sample package metadata."""
    return PackageMetadata(
        name="test_package",
        version="1.0.0",
        description="Test MCP package",
        author="test_author",
        created_at=datetime.now(),
        tier_type="client",
        tags=["test", "sample"]
    )


@pytest.fixture
def package_manager(temp_dir):
    """Create package manager instance."""
    return PackageManager(storage_dir=str(temp_dir))


# ============================================================================
# Package Metadata Tests
# ============================================================================

class TestPackageMetadata:
    """Test package metadata operations."""
    
    def test_create_metadata(self, sample_metadata):
        """Test creating package metadata."""
        assert sample_metadata.name == "test_package"
        assert sample_metadata.version == "1.0.0"
        assert sample_metadata.tier_type == "client"
        assert len(sample_metadata.tags) == 2
    
    def test_metadata_to_dict(self, sample_metadata):
        """Test converting metadata to dictionary."""
        metadata_dict = sample_metadata.to_dict()
        
        assert metadata_dict["name"] == "test_package"
        assert metadata_dict["version"] == "1.0.0"
        assert "created_at" in metadata_dict
    
    def test_metadata_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "name": "test_pkg",
            "version": "2.0.0",
            "description": "Test",
            "author": "author",
            "created_at": datetime.now().isoformat(),
            "tier_type": "project",
            "tags": ["test"]
        }
        
        metadata = PackageMetadata.from_dict(data)
        
        assert metadata.name == "test_pkg"
        assert metadata.version == "2.0.0"
    
    def test_version_validation(self):
        """Test version string validation."""
        # Valid versions
        assert PackageVersion.is_valid("1.0.0")
        assert PackageVersion.is_valid("2.3.4")
        assert PackageVersion.is_valid("0.0.1")
        
        # Invalid versions
        assert not PackageVersion.is_valid("1.0")
        assert not PackageVersion.is_valid("v1.0.0")
        assert not PackageVersion.is_valid("1.0.0-beta")


# ============================================================================
# Package Export Tests
# ============================================================================

class TestPackageExport:
    """Test package export functionality."""
    
    def test_create_package(self, package_manager, sample_metadata):
        """Test creating a new package."""
        package = package_manager.create_package(sample_metadata)
        
        assert package.metadata.name == "test_package"
        assert package.package_id is not None
        assert package.status == "created"
    
    def test_add_knowledge_to_package(self, package_manager, sample_metadata):
        """Test adding knowledge to package."""
        package = package_manager.create_package(sample_metadata)
        
        # Add knowledge items
        package_manager.add_knowledge_to_package(
            package.package_id,
            content="Sample knowledge",
            relevance=0.9
        )
        
        knowledge = package_manager.get_package_knowledge(package.package_id)
        assert len(knowledge) == 1
        assert knowledge[0]["content"] == "Sample knowledge"
    
    def test_export_package_to_file(self, package_manager, sample_metadata, temp_dir):
        """Test exporting package to .mcp file."""
        package = package_manager.create_package(sample_metadata)
        
        # Add some knowledge
        package_manager.add_knowledge_to_package(
            package.package_id,
            content="Test knowledge"
        )
        
        # Export
        export_path = temp_dir / "test_package.mcp"
        config = ExportConfig(
            include_metadata=True,
            include_knowledge=True,
            compression=CompressionType.ZSTD
        )
        
        result = package_manager.export_package(
            package.package_id,
            str(export_path),
            config
        )
        
        assert result.success
        assert export_path.exists()
        assert export_path.stat().st_size > 0
    
    def test_export_package_structure(self, package_manager, sample_metadata, temp_dir):
        """Test exported package has correct structure."""
        package = package_manager.create_package(sample_metadata)
        export_path = temp_dir / "package.mcp"
        
        result = package_manager.export_package(
            package.package_id,
            str(export_path)
        )
        
        # Verify it's a valid tar file
        import tarfile
        assert tarfile.is_tarfile(export_path)
        
        # Check contents
        with tarfile.open(export_path, 'r') as tar:
            names = tar.getnames()
            assert "metadata.json" in names
            # Check for knowledge directory (with or without trailing slash)
            assert any(n in ["knowledge", "knowledge/"] or n.startswith("knowledge/") for n in names)
    
    def test_export_with_compression(self, package_manager, sample_metadata, temp_dir):
        """Test export with different compression types."""
        package = package_manager.create_package(sample_metadata)
        
        for compression in [CompressionType.NONE, CompressionType.GZIP, CompressionType.ZSTD]:
            export_path = temp_dir / f"package_{compression.value}.mcp"
            config = ExportConfig(compression=compression)
            
            result = package_manager.export_package(
                package.package_id,
                str(export_path),
                config
            )
            
            assert result.success
            assert export_path.exists()


# ============================================================================
# Package Import Tests
# ============================================================================

class TestPackageImport:
    """Test package import functionality."""
    
    def test_import_package(self, package_manager, sample_metadata, temp_dir):
        """Test importing a package."""
        # Create and export
        package = package_manager.create_package(sample_metadata)
        package_manager.add_knowledge_to_package(
            package.package_id,
            content="Imported knowledge"
        )
        
        export_path = temp_dir / "export.mcp"
        package_manager.export_package(package.package_id, str(export_path))
        
        # Import
        config = ImportConfig(
            validate_metadata=True,
            overwrite_existing=False
        )
        
        result = package_manager.import_package(str(export_path), config)
        
        assert result.success
        assert result.package_id is not None
    
    def test_import_validates_metadata(self, package_manager, temp_dir):
        """Test import validates metadata."""
        # Create invalid package file
        invalid_path = temp_dir / "invalid.mcp"
        
        import tarfile
        with tarfile.open(invalid_path, 'w') as tar:
            # Add invalid metadata
            import io
            info = tarfile.TarInfo(name="metadata.json")
            data = b'{"invalid": "metadata"}'
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        
        config = ImportConfig(validate_metadata=True)
        result = package_manager.import_package(str(invalid_path), config)
        
        assert not result.success
        assert "validation" in result.error.lower()
    
    def test_import_preserves_knowledge(self, package_manager, sample_metadata, temp_dir):
        """Test import preserves all knowledge."""
        # Create package with multiple knowledge items
        package = package_manager.create_package(sample_metadata)
        
        for i in range(5):
            package_manager.add_knowledge_to_package(
                package.package_id,
                content=f"Knowledge {i}",
                relevance=0.5 + i * 0.1
            )
        
        export_path = temp_dir / "export.mcp"
        package_manager.export_package(package.package_id, str(export_path))
        
        # Import
        result = package_manager.import_package(str(export_path))
        
        # Verify knowledge
        imported_knowledge = package_manager.get_package_knowledge(result.package_id)
        assert len(imported_knowledge) == 5
    
    def test_import_duplicate_handling(self, package_manager, sample_metadata, temp_dir):
        """Test handling duplicate package imports."""
        # Export package
        package = package_manager.create_package(sample_metadata)
        export_path = temp_dir / "export.mcp"
        package_manager.export_package(package.package_id, str(export_path))
        
        # Import twice
        result1 = package_manager.import_package(str(export_path))
        assert result1.success
        
        # Second import should fail without overwrite
        config = ImportConfig(overwrite_existing=False)
        result2 = package_manager.import_package(str(export_path), config)
        assert not result2.success
        
        # Should succeed with overwrite
        config = ImportConfig(overwrite_existing=True)
        result3 = package_manager.import_package(str(export_path), config)
        assert result3.success


# ============================================================================
# Versioning Tests
# ============================================================================

class TestVersioning:
    """Test package versioning."""
    
    def test_version_comparison(self):
        """Test version comparison."""
        assert PackageVersion.compare("1.0.0", "2.0.0") < 0
        assert PackageVersion.compare("2.0.0", "1.0.0") > 0
        assert PackageVersion.compare("1.0.0", "1.0.0") == 0
        assert PackageVersion.compare("1.0.1", "1.0.0") > 0
        assert PackageVersion.compare("1.1.0", "1.0.9") > 0
    
    def test_create_package_snapshot(self, package_manager, sample_metadata):
        """Test creating package snapshot."""
        package = package_manager.create_package(sample_metadata)
        
        # Create snapshot
        snapshot = package_manager.create_snapshot(
            package.package_id,
            tag="v1.0.0"
        )
        
        assert snapshot.version == "1.0.0"
        assert snapshot.tag == "v1.0.0"
        assert snapshot.package_id == package.package_id
    
    def test_list_package_versions(self, package_manager, sample_metadata):
        """Test listing package versions."""
        package = package_manager.create_package(sample_metadata)
        
        # Create multiple versions
        package_manager.create_snapshot(package.package_id, tag="v1.0.0")
        package_manager.create_snapshot(package.package_id, tag="v1.1.0")
        package_manager.create_snapshot(package.package_id, tag="v2.0.0")
        
        versions = package_manager.list_versions(package.package_id)
        
        assert len(versions) >= 3
        # Should be sorted newest first
        assert versions[0].version >= versions[-1].version
    
    def test_get_specific_version(self, package_manager, sample_metadata):
        """Test retrieving specific version."""
        package = package_manager.create_package(sample_metadata)
        package_manager.create_snapshot(package.package_id, tag="v1.0.0")
        
        version = package_manager.get_version(package.package_id, "1.0.0")
        
        assert version is not None
        assert version.version == "1.0.0"


# ============================================================================
# Hot-Swapping Tests
# ============================================================================

class TestHotSwapping:
    """Test package hot-swapping."""
    
    def test_hot_swap_package(self, package_manager, sample_metadata):
        """Test hot-swapping packages."""
        # Create two packages
        pkg1 = package_manager.create_package(sample_metadata)
        
        metadata2 = sample_metadata
        metadata2.version = "2.0.0"
        pkg2 = package_manager.create_package(metadata2)
        
        # Hot-swap
        result = package_manager.hot_swap(
            current_package_id=pkg1.package_id,
            new_package_id=pkg2.package_id
        )
        
        assert result.success
        assert result.downtime_ms == 0  # Zero downtime
    
    def test_rollback_package(self, package_manager, sample_metadata, temp_dir):
        """Test rolling back to previous version."""
        # Create package and snapshot
        package = package_manager.create_package(sample_metadata)
        export_path = temp_dir / "v1.mcp"
        package_manager.export_package(package.package_id, str(export_path))
        package_manager.create_snapshot(package.package_id, tag="v1.0.0")
        
        # Modify package
        package_manager.add_knowledge_to_package(
            package.package_id,
            content="New knowledge"
        )
        
        # Rollback
        result = package_manager.rollback(package.package_id, "1.0.0")
        
        assert result.success
        assert result.rolled_back_to == "1.0.0"
    
    def test_gradual_rollout(self, package_manager, sample_metadata):
        """Test gradual rollout strategy."""
        pkg1 = package_manager.create_package(sample_metadata)
        
        metadata2 = sample_metadata
        metadata2.version = "2.0.0"
        pkg2 = package_manager.create_package(metadata2)
        
        # Gradual rollout: 10% -> 50% -> 100%
        for percentage in [10, 50, 100]:
            result = package_manager.gradual_rollout(
                current_package_id=pkg1.package_id,
                new_package_id=pkg2.package_id,
                percentage=percentage
            )
            
            assert result.success
            assert result.current_percentage == percentage


# ============================================================================
# Package Validation Tests
# ============================================================================

class TestPackageValidation:
    """Test package validation."""
    
    def test_validate_package_structure(self, package_manager, sample_metadata):
        """Test validating package structure."""
        package = package_manager.create_package(sample_metadata)
        
        result = package_manager.validate_package(package.package_id)
        
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_metadata_required_fields(self):
        """Test metadata validation requires fields."""
        with pytest.raises(ValueError):
            PackageMetadata(
                name="",  # Empty name should fail
                version="1.0.0",
                description="Test"
            )
    
    def test_validate_package_size(self, package_manager, sample_metadata):
        """Test package size validation."""
        package = package_manager.create_package(sample_metadata)
        
        # Add large knowledge item (exceeds 1000MB limit)
        large_content = "x" * (1001 * 1024 * 1024)  # 1001MB
        
        with pytest.raises(ValueError, match="exceeds maximum size"):
            package_manager.add_knowledge_to_package(
                package.package_id,
                content=large_content
            )


# ============================================================================
# Package Query Tests
# ============================================================================

class TestPackageQuery:
    """Test querying packages."""
    
    def test_list_packages(self, package_manager, sample_metadata):
        """Test listing all packages."""
        # Create multiple packages
        for i in range(3):
            metadata = sample_metadata
            metadata.name = f"package_{i}"
            package_manager.create_package(metadata)
        
        packages = package_manager.list_packages()
        
        assert len(packages) >= 3
    
    def test_search_packages(self, package_manager, sample_metadata):
        """Test searching packages by criteria."""
        # Create packages with different tags
        metadata1 = sample_metadata
        metadata1.tags = ["test", "development"]
        package_manager.create_package(metadata1)
        
        metadata2 = sample_metadata
        metadata2.name = "prod_package"
        metadata2.tags = ["production"]
        package_manager.create_package(metadata2)
        
        # Search by tag
        results = package_manager.search_packages(tags=["production"])
        
        assert len(results) >= 1
        assert any("production" in pkg.metadata.tags for pkg in results)
    
    def test_get_package_info(self, package_manager, sample_metadata):
        """Test getting detailed package info."""
        package = package_manager.create_package(sample_metadata)
        
        info = package_manager.get_package_info(package.package_id)
        
        assert info["name"] == "test_package"
        assert info["version"] == "1.0.0"
        assert "created_at" in info
        assert "knowledge_count" in info


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_export_nonexistent_package(self, package_manager, temp_dir):
        """Test exporting non-existent package."""
        with pytest.raises(ValueError, match="Package not found"):
            package_manager.export_package(
                "nonexistent_id",
                str(temp_dir / "out.mcp")
            )
    
    def test_import_corrupted_file(self, package_manager, temp_dir):
        """Test importing corrupted package file."""
        corrupted_path = temp_dir / "corrupted.mcp"
        corrupted_path.write_text("not a valid package")
        
        result = package_manager.import_package(str(corrupted_path))
        
        assert not result.success
        assert result.error is not None
    
    def test_version_snapshot_without_changes(self, package_manager, sample_metadata):
        """Test creating snapshot without changes."""
        package = package_manager.create_package(sample_metadata)
        
        # Create two snapshots immediately
        snap1 = package_manager.create_snapshot(package.package_id, tag="v1.0.0")
        snap2 = package_manager.create_snapshot(package.package_id, tag="v1.0.1")
        
        # Both should succeed and use the package's version
        assert snap1.version == package.metadata.version
        assert snap2.version == package.metadata.version

