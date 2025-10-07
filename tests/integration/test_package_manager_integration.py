"""
Integration tests for MCP Package Manager.

Tests real-world workflows and end-to-end package management scenarios.
"""

import pytest
import sys
import tempfile
import asyncio
from pathlib import Path

# Add services to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_package_manager.src.package_manager import (
    PackageManager,
    PackageMetadata,
    ExportConfig,
    ImportConfig,
    CompressionType
)


# ============================================================================
# Integration Tests
# ============================================================================

class TestPackageManagerIntegration:
    """Integration tests for package manager workflows."""
    
    def test_complete_package_lifecycle(self):
        """Test complete package lifecycle: create → export → import → hot-swap."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PackageManager(storage_dir=tmpdir)
            
            # 1. Create package v1.0.0
            metadata = PackageMetadata(
                name="lifecycle_test",
                version="1.0.0",
                description="Test package",
                author="integration_test"
            )
            
            pkg_v1 = manager.create_package(metadata)
            
            # Add knowledge
            for i in range(10):
                manager.add_knowledge_to_package(
                    pkg_v1.package_id,
                    content=f"Knowledge item {i} for v1.0.0",
                    relevance=0.8 + i * 0.02
                )
            
            # 2. Export v1.0.0
            export_path_v1 = Path(tmpdir) / "package_v1.mcp"
            export_result = manager.export_package(
                pkg_v1.package_id,
                str(export_path_v1),
                ExportConfig(compression=CompressionType.GZIP)
            )
            
            assert export_result.success
            assert export_path_v1.exists()
            
            # 3. Create v2.0.0
            metadata_v2 = PackageMetadata(
                name="lifecycle_test",
                version="2.0.0",
                description="Test package v2",
                author="integration_test"
            )
            pkg_v2 = manager.create_package(metadata_v2)
            
            for i in range(15):
                manager.add_knowledge_to_package(
                    pkg_v2.package_id,
                    content=f"Knowledge item {i} for v2.0.0",
                    relevance=0.9 + i * 0.005
                )
            
            # 4. Create snapshot before hot-swap
            manager.create_snapshot(pkg_v1.package_id, tag="v1.0.0")
            
            # 5. Hot-swap to v2.0.0
            swap_result = manager.hot_swap(pkg_v1.package_id, pkg_v2.package_id)
            assert swap_result.success
            assert swap_result.downtime_ms == 0
            
            # 6. Rollback to v1.0.0
            rollback_result = manager.rollback(pkg_v1.package_id, "1.0.0")
            assert rollback_result.success
            
            # 7. Import package from file
            import_result = manager.import_package(str(export_path_v1))
            assert import_result.success
            
            # Verify imported knowledge
            imported_knowledge = manager.get_package_knowledge(import_result.package_id)
            assert len(imported_knowledge) == 10
    
    def test_multi_version_management(self):
        """Test managing multiple versions of same package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PackageManager(storage_dir=tmpdir)
            
            versions = ["1.0.0", "1.1.0", "1.2.0", "2.0.0", "2.1.0"]
            packages = {}
            
            for version in versions:
                metadata = PackageMetadata(
                    name="versioned_package",
                    version=version,
                    description=f"Version {version}"
                )
                
                pkg = manager.create_package(metadata)
                packages[version] = pkg
                
                # Add version-specific knowledge
                manager.add_knowledge_to_package(
                    pkg.package_id,
                    content=f"This is version {version}",
                    relevance=1.0
                )
                
                # Create snapshot
                manager.create_snapshot(pkg.package_id, tag=f"v{version}")
            
            # Verify all versions exist
            assert len(packages) == 5
            
            # Check version history for one package
            v1_package = packages["1.0.0"]
            versions_list = manager.list_versions(v1_package.package_id)
            assert len(versions_list) >= 1
    
    def test_package_distribution_workflow(self):
        """Test package distribution: export → transfer → import on different system."""
        with tempfile.TemporaryDirectory() as export_dir:
            with tempfile.TemporaryDirectory() as import_dir:
                # System 1: Create and export
                manager1 = PackageManager(storage_dir=export_dir)
                
                metadata = PackageMetadata(
                    name="distributed_package",
                    version="1.0.0",
                    description="Package for distribution",
                    tags=["distributed", "production"]
                )
                
                pkg = manager1.create_package(metadata)
                
                # Add comprehensive knowledge
                knowledge_items = [
                    {"content": "API documentation", "relevance": 1.0},
                    {"content": "Code examples", "relevance": 0.9},
                    {"content": "Best practices", "relevance": 0.95},
                    {"content": "Troubleshooting guide", "relevance": 0.85}
                ]
                
                for item in knowledge_items:
                    manager1.add_knowledge_to_package(
                        pkg.package_id,
                        content=item["content"],
                        relevance=item["relevance"]
                    )
                
                # Export
                export_path = Path(export_dir) / "distributed.mcp"
                export_result = manager1.export_package(pkg.package_id, str(export_path))
                assert export_result.success
                
                # System 2: Import
                manager2 = PackageManager(storage_dir=import_dir)
                
                import_result = manager2.import_package(str(export_path))
                assert import_result.success
                
                # Verify imported package
                imported_pkg_info = manager2.get_package_info(import_result.package_id)
                assert imported_pkg_info["name"] == "distributed_package"
                assert imported_pkg_info["version"] == "1.0.0"
                assert imported_pkg_info["knowledge_count"] == 4
                
                # Verify tags
                assert "distributed" in imported_pkg_info["tags"]
                assert "production" in imported_pkg_info["tags"]
    
    def test_gradual_rollout_workflow(self):
        """Test gradual rollout strategy for package updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PackageManager(storage_dir=tmpdir)
            
            # Create stable version
            metadata_stable = PackageMetadata(
                name="production_app",
                version="1.0.0",
                description="Stable production version"
            )
            pkg_stable = manager.create_package(metadata_stable)
            
            # Create new version
            metadata_new = PackageMetadata(
                name="production_app",
                version="2.0.0",
                description="New version with features"
            )
            pkg_new = manager.create_package(metadata_new)
            
            # Gradual rollout: 10% → 50% → 100%
            percentages = [10, 25, 50, 75, 100]
            
            for percentage in percentages:
                result = manager.gradual_rollout(
                    current_package_id=pkg_stable.package_id,
                    new_package_id=pkg_new.package_id,
                    percentage=percentage
                )
                
                assert result.success
                assert result.current_percentage == percentage
                assert result.downtime_ms == 0  # Zero downtime
    
    def test_package_search_and_discovery(self):
        """Test package search and discovery capabilities."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PackageManager(storage_dir=tmpdir)
            
            # Create packages with different tags
            packages_data = [
                {"name": "ml_models", "version": "1.0.0", "tags": ["machine-learning", "production"]},
                {"name": "api_docs", "version": "1.0.0", "tags": ["documentation", "api"]},
                {"name": "ml_training", "version": "2.0.0", "tags": ["machine-learning", "training"]},
                {"name": "ui_components", "version": "1.5.0", "tags": ["frontend", "react"]},
            ]
            
            for pkg_data in packages_data:
                metadata = PackageMetadata(
                    name=pkg_data["name"],
                    version=pkg_data["version"],
                    tags=pkg_data["tags"]
                )
                manager.create_package(metadata)
            
            # Search by tag
            ml_packages = manager.search_packages(tags=["machine-learning"])
            assert len(ml_packages) >= 2
            
            # List all packages
            all_packages = manager.list_packages()
            assert len(all_packages) >= 4
    
    def test_package_validation_workflow(self):
        """Test package validation in real workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PackageManager(storage_dir=tmpdir)
            
            # Create valid package
            metadata = PackageMetadata(
                name="validated_package",
                version="1.0.0",
                description="Package with validation"
            )
            
            pkg = manager.create_package(metadata)
            
            # Validate
            validation = manager.validate_package(pkg.package_id)
            assert validation.is_valid
            assert len(validation.errors) == 0
            
            # Add knowledge
            manager.add_knowledge_to_package(
                pkg.package_id,
                content="Valid knowledge content"
            )
            
            # Export
            export_path = Path(tmpdir) / "validated.mcp"
            result = manager.export_package(pkg.package_id, str(export_path))
            assert result.success
            
            # Import and validate
            import_result = manager.import_package(str(export_path))
            assert import_result.success
            
            imported_validation = manager.validate_package(import_result.package_id)
            assert imported_validation.is_valid
    
    def test_concurrent_package_operations(self):
        """Test concurrent package operations (thread-safe)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PackageManager(storage_dir=tmpdir)
            
            # Create multiple packages concurrently
            packages = []
            for i in range(10):
                metadata = PackageMetadata(
                    name=f"concurrent_pkg_{i}",
                    version="1.0.0",
                    description=f"Package {i}"
                )
                pkg = manager.create_package(metadata)
                packages.append(pkg)
            
            # Add knowledge to all packages
            for pkg in packages:
                for j in range(5):
                    manager.add_knowledge_to_package(
                        pkg.package_id,
                        content=f"Knowledge {j} for {pkg.metadata.name}"
                    )
            
            # Verify all packages exist
            all_pkgs = manager.list_packages()
            assert len(all_pkgs) >= 10
            
            # Verify knowledge counts
            for pkg in packages:
                knowledge = manager.get_package_knowledge(pkg.package_id)
                assert len(knowledge) == 5
    
    def test_error_recovery_workflow(self):
        """Test error recovery in package operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PackageManager(storage_dir=tmpdir)
            
            # Attempt to export non-existent package
            with pytest.raises(ValueError, match="Package not found"):
                manager.export_package("nonexistent_id", str(Path(tmpdir) / "out.mcp"))
            
            # Attempt to import corrupted file
            corrupted_path = Path(tmpdir) / "corrupted.mcp"
            corrupted_path.write_text("not a valid tar file")
            
            result = manager.import_package(str(corrupted_path))
            assert not result.success
            assert result.error is not None
            
            # Attempt to hot-swap with invalid package
            metadata = PackageMetadata(name="test", version="1.0.0")
            pkg = manager.create_package(metadata)
            
            result = manager.hot_swap(pkg.package_id, "nonexistent_id")
            assert not result.success
            
            # Verify manager still functional after errors
            all_pkgs = manager.list_packages()
            assert len(all_pkgs) >= 1


# ============================================================================
# Performance Tests
# ============================================================================

class TestPackageManagerPerformance:
    """Performance tests for package manager."""
    
    def test_large_package_export_import(self):
        """Test exporting and importing large packages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PackageManager(storage_dir=tmpdir)
            
            metadata = PackageMetadata(
                name="large_package",
                version="1.0.0",
                description="Large package with lots of knowledge"
            )
            
            pkg = manager.create_package(metadata)
            
            # Add 100 knowledge items
            for i in range(100):
                manager.add_knowledge_to_package(
                    pkg.package_id,
                    content=f"Knowledge item {i}: " + ("x" * 1000),  # 1KB each
                    relevance=0.5 + (i % 50) * 0.01
                )
            
            # Export
            export_path = Path(tmpdir) / "large.mcp"
            export_result = manager.export_package(pkg.package_id, str(export_path))
            assert export_result.success
            
            # Import
            import_result = manager.import_package(str(export_path))
            assert import_result.success
            
            # Verify
            imported_knowledge = manager.get_package_knowledge(import_result.package_id)
            assert len(imported_knowledge) == 100
    
    def test_many_packages_management(self):
        """Test managing many packages simultaneously."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PackageManager(storage_dir=tmpdir)
            
            # Create 50 packages
            package_count = 50
            packages = []
            
            for i in range(package_count):
                metadata = PackageMetadata(
                    name=f"package_{i}",
                    version="1.0.0",
                    description=f"Package number {i}",
                    tags=[f"category_{i % 5}"]
                )
                pkg = manager.create_package(metadata)
                packages.append(pkg)
            
            # Verify count
            all_pkgs = manager.list_packages()
            assert len(all_pkgs) == package_count
            
            # Search should be fast
            results = manager.search_packages(tags=["category_0"])
            assert len(results) >= 10  # Should find ~10 packages

