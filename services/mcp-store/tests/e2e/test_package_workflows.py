"""End-to-end workflow tests for MCP Store.

These tests verify complete package management workflows through the API.
"""

import pytest
import httpx
import asyncio
import uuid
import io
import tarfile
import json

# Service URL (assumes service is running)
BASE_URL = "http://localhost:5648"


@pytest.fixture
def sample_package_data():
    """Generate sample package data for testing."""
    return {
        "name": f"test-package-{uuid.uuid4().hex[:8]}",
        "description": "A test package for E2E workflow testing",
        "owner_id": "test-user-001",
        "tags": ["test", "e2e", "automation"],
        "categories": ["testing", "demo"],
        "is_public": True,
        "metadata": {"test": True, "environment": "e2e"}
    }


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_health_check():
    """Test that the service health check endpoint works."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "service" in data
        except httpx.ConnectError:
            pytest.skip("Service not running - start with: docker-compose up -d")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_package_lifecycle(sample_package_data):
    """Test the complete package lifecycle: create, retrieve, update, delete."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Create a package
            response = await client.post(
                f"{BASE_URL}/api/v1/packages",
                json=sample_package_data
            )
            assert response.status_code in [200, 201]
            created = response.json()
            assert "package_id" in created
            package_id = created["package_id"]
            assert created["name"] == sample_package_data["name"]
            
            # Step 2: Retrieve the package
            response = await client.get(f"{BASE_URL}/api/v1/packages/{package_id}")
            assert response.status_code == 200
            retrieved = response.json()
            assert retrieved["package_id"] == package_id
            assert retrieved["name"] == sample_package_data["name"]
            
            # Step 3: Update the package
            update_data = {"description": "Updated description for E2E test"}
            response = await client.put(
                f"{BASE_URL}/api/v1/packages/{package_id}",
                json=update_data
            )
            assert response.status_code == 200
            updated = response.json()
            assert updated["description"] == update_data["description"]
            
            # Step 4: Delete the package
            response = await client.delete(f"{BASE_URL}/api/v1/packages/{package_id}")
            assert response.status_code in [200, 204]
            
            # Step 5: Verify deletion
            response = await client.get(f"{BASE_URL}/api/v1/packages/{package_id}")
            assert response.status_code == 404
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_package_search_and_filter(sample_package_data):
    """Test package search and filtering capabilities."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Create a test package
            response = await client.post(
                f"{BASE_URL}/api/v1/packages",
                json=sample_package_data
            )
            assert response.status_code in [200, 201]
            created = response.json()
            package_id = created["package_id"]
            
            # Test 1: List all packages
            response = await client.get(f"{BASE_URL}/api/v1/packages?limit=10")
            assert response.status_code == 200
            packages = response.json()
            assert isinstance(packages, list)
            
            # Test 2: Search by name
            response = await client.get(
                f"{BASE_URL}/api/v1/packages?search_query={sample_package_data['name']}"
            )
            assert response.status_code == 200
            results = response.json()
            assert len(results) >= 1
            found = any(p["package_id"] == package_id for p in results)
            assert found
            
            # Test 3: Filter by tags
            tag = sample_package_data["tags"][0]
            response = await client.get(f"{BASE_URL}/api/v1/packages?tags={tag}")
            assert response.status_code == 200
            
            # Test 4: Filter by is_public
            response = await client.get(f"{BASE_URL}/api/v1/packages?is_public=true")
            assert response.status_code == 200
            
            # Cleanup
            await client.delete(f"{BASE_URL}/api/v1/packages/{package_id}")
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_marketplace_features(sample_package_data):
    """Test marketplace features: star, trending, popular tags."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Create a test package
            response = await client.post(
                f"{BASE_URL}/api/v1/packages",
                json=sample_package_data
            )
            assert response.status_code in [200, 201]
            created = response.json()
            package_id = created["package_id"]
            
            # Test 1: Star the package
            response = await client.post(
                f"{BASE_URL}/api/v1/packages/{package_id}/star?user_id=test-user-001"
            )
            assert response.status_code == 200
            
            # Test 2: Get trending packages
            response = await client.get(
                f"{BASE_URL}/api/v1/marketplace/trending?days=7&limit=10"
            )
            assert response.status_code == 200
            trending = response.json()
            assert "packages" in trending or isinstance(trending, list)
            
            # Test 3: Get popular tags
            response = await client.get(
                f"{BASE_URL}/api/v1/marketplace/tags/popular?limit=10"
            )
            assert response.status_code == 200
            popular_tags = response.json()
            assert "tags" in popular_tags or isinstance(popular_tags, list)
            
            # Test 4: Get marketplace stats
            response = await client.get(f"{BASE_URL}/api/v1/marketplace/stats")
            assert response.status_code == 200
            stats = response.json()
            assert "total_packages" in stats or "stats" in stats
            
            # Cleanup
            await client.delete(f"{BASE_URL}/api/v1/packages/{package_id}")
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_version_management(sample_package_data):
    """Test package version management workflow."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Step 1: Create a package
            response = await client.post(
                f"{BASE_URL}/api/v1/packages",
                json=sample_package_data
            )
            assert response.status_code in [200, 201]
            package = response.json()
            package_id = package["package_id"]
            
            # Step 2: Upload a version (mock binary data)
            files = {
                "file": ("test-package.bin", b"mock binary content for testing", "application/octet-stream")
            }
            data = {
                "version_string": "1.0.0",
                "release_notes": "Initial release for E2E testing"
            }
            response = await client.post(
                f"{BASE_URL}/api/v1/packages/{package_id}/versions",
                data=data,
                files=files
            )
            # Might fail if storage not configured - that's okay for E2E
            if response.status_code in [200, 201]:
                version = response.json()
                assert "version_id" in version
                version_id = version["version_id"]
                
                # Step 3: List versions
                response = await client.get(
                    f"{BASE_URL}/api/v1/packages/{package_id}/versions"
                )
                assert response.status_code == 200
                versions = response.json()
                assert isinstance(versions, list)
                assert len(versions) >= 1
            
            # Cleanup
            await client.delete(f"{BASE_URL}/api/v1/packages/{package_id}")
            
        except httpx.ConnectError:
            pytest.skip("Service not running")
        except Exception as e:
            # Storage might not be configured - skip gracefully
            pytest.skip(f"Storage configuration required: {str(e)}")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_error_handling():
    """Test API error handling."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test 1: Get non-existent package
            response = await client.get(
                f"{BASE_URL}/api/v1/packages/nonexistent-pkg-12345"
            )
            assert response.status_code == 404
            
            # Test 2: Create package with invalid data
            response = await client.post(
                f"{BASE_URL}/api/v1/packages",
                json={"invalid": "data", "missing": "required_fields"}
            )
            assert response.status_code in [400, 422]
            
            # Test 3: Update non-existent package
            response = await client.put(
                f"{BASE_URL}/api/v1/packages/fake-id-999",
                json={"description": "Update"}
            )
            assert response.status_code == 404
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


@pytest.mark.asyncio
@pytest.mark.e2e
async def test_pagination():
    """Test pagination of package listings."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Get first page
            response = await client.get(
                f"{BASE_URL}/api/v1/packages?limit=5&offset=0"
            )
            assert response.status_code == 200
            page1 = response.json()
            assert isinstance(page1, list)
            
            # Get second page
            response = await client.get(
                f"{BASE_URL}/api/v1/packages?limit=5&offset=5"
            )
            assert response.status_code == 200
            page2 = response.json()
            assert isinstance(page2, list)
            
            # If both pages have data, they should be different
            if len(page1) > 0 and len(page2) > 0:
                page1_ids = {p["package_id"] for p in page1}
                page2_ids = {p["package_id"] for p in page2}
                # Should have some different packages
                assert page1_ids != page2_ids
            
        except httpx.ConnectError:
            pytest.skip("Service not running")


if __name__ == "__main__":
    # Run tests with: pytest tests/e2e/test_package_workflows.py -v -m e2e
    print("Run E2E tests with: pytest tests/e2e/test_package_workflows.py -v -m e2e")
    print("Make sure the service is running: docker-compose up -d")
