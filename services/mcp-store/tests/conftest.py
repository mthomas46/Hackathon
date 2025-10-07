"""Pytest configuration and fixtures for MCP Store tests."""

import pytest
import asyncio
from typing import AsyncGenerator
from datetime import datetime
import uuid

from services.mcp_store.domain.entities.mcp_package import MCPPackage
from services.mcp_store.domain.entities.mcp_version import MCPVersion
from services.mcp_store.domain.value_objects.package_status import PackageStatus


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_package():
    """Create a sample MCPPackage for testing."""
    return MCPPackage(
        package_id="test-pkg-001",
        name="test-package",
        description="A test package for unit testing",
        owner_id="test-user-123",
        status=PackageStatus.DRAFT,
        tags=["test", "sample"],
        categories=["testing"],
        is_public=False,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def sample_version():
    """Create a sample MCPVersion for testing."""
    return MCPVersion(
        version_id="test-ver-001",
        package_id="test-pkg-001",
        version_string="1.0.0",
        storage_path="packages/test-pkg-001/1.0.0.mcp",
        checksum="abc123def456",
        size_bytes=1024,
        release_notes="Initial release",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def published_package():
    """Create a published MCPPackage for testing."""
    return MCPPackage(
        package_id="test-pkg-pub-001",
        name="published-package",
        description="A published test package",
        owner_id="test-user-123",
        status=PackageStatus.PUBLISHED,
        tags=["production", "ml"],
        categories=["knowledge-base"],
        is_public=True,
        download_count=42,
        star_count=15,
        latest_version_id="test-ver-pub-001",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def multiple_packages():
    """Create multiple packages for testing list/search functionality."""
    packages = []
    for i in range(5):
        pkg = MCPPackage(
            package_id=f"test-pkg-{i:03d}",
            name=f"package-{i}",
            description=f"Test package number {i}",
            owner_id="test-user-123" if i % 2 == 0 else "test-user-456",
            status=PackageStatus.PUBLISHED if i % 3 == 0 else PackageStatus.DRAFT,
            tags=["test", f"tag-{i}"],
            categories=["testing"],
            is_public=i % 2 == 0,
            download_count=i * 10,
            star_count=i * 5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        packages.append(pkg)
    return packages


@pytest.fixture
def sample_mcp_file_content():
    """Create sample .mcp file content for export/import testing."""
    import tarfile
    import io
    import json
    
    # Create metadata
    metadata = {
        "format_version": "1.0.0",
        "exported_at": datetime.now().isoformat(),
        "package": {
            "package_id": "test-pkg-001",
            "name": "test-package",
            "description": "Test package",
            "owner_id": "test-user",
            "status": "published",
            "tags": ["test"],
            "categories": ["testing"],
            "is_public": True,
        },
        "versions": [
            {
                "version_id": "test-ver-001",
                "version_string": "1.0.0",
                "checksum": "abc123",
                "size_bytes": 100,
                "release_notes": "Test version",
                "is_active": True,
                "created_at": datetime.now().isoformat(),
            }
        ],
        "version_count": 1,
    }
    
    # Create TAR archive
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode='w:gz') as tar:
        # Add metadata
        metadata_json = json.dumps(metadata, indent=2).encode('utf-8')
        metadata_info = tarfile.TarInfo(name='metadata.json')
        metadata_info.size = len(metadata_json)
        tar.addfile(metadata_info, io.BytesIO(metadata_json))
        
        # Add version binary
        binary_data = b"test binary data"
        binary_info = tarfile.TarInfo(name='versions/test-ver-001.bin')
        binary_info.size = len(binary_data)
        tar.addfile(binary_info, io.BytesIO(binary_data))
    
    tar_buffer.seek(0)
    return tar_buffer.read()
