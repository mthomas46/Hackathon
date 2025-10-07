"""Unit tests for MCP Store domain entities."""

import pytest
from datetime import datetime

from services.mcp_store.domain.entities.mcp_package import MCPPackage
from services.mcp_store.domain.entities.mcp_version import MCPVersion
from services.mcp_store.domain.value_objects.package_status import PackageStatus


class TestMCPPackage:
    """Tests for MCPPackage entity."""
    
    def test_create_package_with_defaults(self):
        """Test creating a package with default values."""
        pkg = MCPPackage(
            name="test-package",
            description="Test description",
            owner_id="user-123"
        )
        
        assert pkg.name == "test-package"
        assert pkg.description == "Test description"
        assert pkg.owner_id == "user-123"
        assert pkg.status == PackageStatus.DRAFT
        assert pkg.is_public is False
        assert pkg.download_count == 0
        assert pkg.star_count == 0
        assert pkg.tags == []
        assert pkg.categories == []
        assert pkg.package_id is not None  # UUID generated
    
    def test_create_package_with_custom_values(self):
        """Test creating a package with custom values."""
        pkg = MCPPackage(
            package_id="custom-id",
            name="custom-package",
            description="Custom description",
            owner_id="user-456",
            status=PackageStatus.PUBLISHED,
            tags=["AI", "ML"],
            categories=["Training"],
            is_public=True,
            download_count=100,
            star_count=50
        )
        
        assert pkg.package_id == "custom-id"
        assert pkg.status == PackageStatus.PUBLISHED
        assert pkg.tags == ["ai", "ml"]  # Tags lowercased
        assert pkg.categories == ["training"]  # Categories lowercased
        assert pkg.is_public is True
        assert pkg.download_count == 100
        assert pkg.star_count == 50
    
    def test_package_name_required(self):
        """Test that package name is required."""
        with pytest.raises(ValueError, match="Package name cannot be empty"):
            MCPPackage(
                name="",
                description="Test",
                owner_id="user-123"
            )
    
    def test_owner_id_required(self):
        """Test that owner_id is required."""
        with pytest.raises(ValueError, match="Owner ID cannot be empty"):
            MCPPackage(
                name="test",
                description="Test",
                owner_id=""
            )
    
    def test_publish_package(self, sample_package):
        """Test publishing a package."""
        assert sample_package.status == PackageStatus.DRAFT
        
        sample_package.publish()
        
        assert sample_package.status == PackageStatus.PENDING_REVIEW
    
    def test_approve_package(self, sample_package):
        """Test approving a package."""
        sample_package.publish()
        assert sample_package.status == PackageStatus.PENDING_REVIEW
        
        sample_package.approve()
        
        assert sample_package.status == PackageStatus.PUBLISHED
    
    def test_deprecate_package(self, sample_package):
        """Test deprecating a package."""
        sample_package.deprecate()
        
        assert sample_package.status == PackageStatus.DEPRECATED
    
    def test_archive_package(self, sample_package):
        """Test archiving a package."""
        sample_package.archive()
        
        assert sample_package.status == PackageStatus.ARCHIVED
    
    def test_increment_download_count(self, sample_package):
        """Test incrementing download count."""
        initial_count = sample_package.download_count
        
        sample_package.increment_download_count()
        
        assert sample_package.download_count == initial_count + 1
    
    def test_increment_star_count(self, sample_package):
        """Test incrementing star count."""
        initial_count = sample_package.star_count
        
        sample_package.increment_star_count()
        
        assert sample_package.star_count == initial_count + 1
    
    def test_decrement_star_count(self, sample_package):
        """Test decrementing star count."""
        sample_package.star_count = 10
        
        sample_package.decrement_star_count()
        
        assert sample_package.star_count == 9
    
    def test_decrement_star_count_at_zero(self, sample_package):
        """Test that star count doesn't go below zero."""
        sample_package.star_count = 0
        
        sample_package.decrement_star_count()
        
        assert sample_package.star_count == 0
    
    def test_update_latest_version(self, sample_package):
        """Test updating latest version ID."""
        version_id = "new-version-123"
        
        sample_package.update_latest_version(version_id)
        
        assert sample_package.latest_version_id == version_id
    
    def test_tags_are_lowercased(self):
        """Test that tags are automatically lowercased."""
        pkg = MCPPackage(
            name="test",
            description="test",
            owner_id="user",
            tags=["PRODUCTION", "Ml", "TeSt"]
        )
        
        assert pkg.tags == ["production", "ml", "test"]
    
    def test_categories_are_lowercased(self):
        """Test that categories are automatically lowercased."""
        pkg = MCPPackage(
            name="test",
            description="test",
            owner_id="user",
            categories=["KNOWLEDGE-BASE", "Training"]
        )
        
        assert pkg.categories == ["knowledge-base", "training"]


class TestMCPVersion:
    """Tests for MCPVersion entity."""
    
    def test_create_version(self):
        """Test creating a version."""
        version = MCPVersion(
            package_id="pkg-123",
            version_string="1.0.0",
            storage_path="packages/pkg-123/1.0.0.mcp",
            checksum="abc123",
            size_bytes=1024
        )
        
        assert version.package_id == "pkg-123"
        assert version.version_string == "1.0.0"
        assert version.storage_path == "packages/pkg-123/1.0.0.mcp"
        assert version.checksum == "abc123"
        assert version.size_bytes == 1024
        assert version.is_active is True
        assert version.version_id is not None  # UUID generated
    
    def test_version_string_required(self):
        """Test that version_string is required."""
        with pytest.raises(ValueError, match="Version string cannot be empty"):
            MCPVersion(
                package_id="pkg-123",
                version_string="",
                storage_path="path",
                checksum="abc",
                size_bytes=100
            )
    
    def test_storage_path_required(self):
        """Test that storage_path is required."""
        with pytest.raises(ValueError, match="Storage path cannot be empty"):
            MCPVersion(
                package_id="pkg-123",
                version_string="1.0.0",
                storage_path="",
                checksum="abc",
                size_bytes=100
            )
    
    def test_checksum_required(self):
        """Test that checksum is required."""
        with pytest.raises(ValueError, match="Checksum cannot be empty"):
            MCPVersion(
                package_id="pkg-123",
                version_string="1.0.0",
                storage_path="path",
                checksum="",
                size_bytes=100
            )
    
    def test_size_bytes_must_be_positive(self):
        """Test that size_bytes must be positive."""
        with pytest.raises(ValueError, match="Size bytes must be positive"):
            MCPVersion(
                package_id="pkg-123",
                version_string="1.0.0",
                storage_path="path",
                checksum="abc",
                size_bytes=0
            )
    
    def test_deactivate_version(self, sample_version):
        """Test deactivating a version."""
        assert sample_version.is_active is True
        
        sample_version.deactivate()
        
        assert sample_version.is_active is False
    
    def test_activate_version(self, sample_version):
        """Test activating a version."""
        sample_version.deactivate()
        assert sample_version.is_active is False
        
        sample_version.activate()
        
        assert sample_version.is_active is True
    
    def test_version_with_release_notes(self):
        """Test creating a version with release notes."""
        version = MCPVersion(
            package_id="pkg-123",
            version_string="2.0.0",
            storage_path="path",
            checksum="abc",
            size_bytes=2048,
            release_notes="Major update with new features"
        )
        
        assert version.release_notes == "Major update with new features"
    
    def test_version_with_metadata(self):
        """Test creating a version with custom metadata."""
        metadata = {
            "author": "test-user",
            "build_number": 42,
            "commit_hash": "abc123def456"
        }
        
        version = MCPVersion(
            package_id="pkg-123",
            version_string="1.0.1",
            storage_path="path",
            checksum="abc",
            size_bytes=1024,
            metadata=metadata
        )
        
        assert version.metadata == metadata
        assert version.metadata["author"] == "test-user"
        assert version.metadata["build_number"] == 42


class TestPackageStatus:
    """Tests for PackageStatus value object."""
    
    def test_all_statuses_defined(self):
        """Test that all expected statuses are defined."""
        assert PackageStatus.DRAFT.value == "draft"
        assert PackageStatus.PENDING_REVIEW.value == "pending_review"
        assert PackageStatus.PUBLISHED.value == "published"
        assert PackageStatus.DEPRECATED.value == "deprecated"
        assert PackageStatus.ARCHIVED.value == "archived"
        assert PackageStatus.REJECTED.value == "rejected"
    
    def test_status_can_be_compared(self):
        """Test that statuses can be compared."""
        assert PackageStatus.DRAFT == PackageStatus.DRAFT
        assert PackageStatus.DRAFT != PackageStatus.PUBLISHED
    
    def test_status_can_be_converted_to_string(self):
        """Test that status values are strings."""
        assert isinstance(PackageStatus.DRAFT.value, str)
        assert isinstance(PackageStatus.PUBLISHED.value, str)
