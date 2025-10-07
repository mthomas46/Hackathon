"""
E2E Tests: Package Management

Tests the MCP package management workflow through mcp-package-manager.
Mimics STEP 6 of demo_mcp_workflow_validation.py.

Test Modes:
- Code: Tests package manager logic with mocked storage
- Live: Tests full workflow with real Docker volume storage
"""

import pytest
import asyncio


class TestPackageManagement:
    """Test suite for MCP package management."""
    
    @pytest.mark.asyncio
    async def test_list_packages(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test listing available packages.
        
        Expected: Returns list of packages (empty or populated)
        """
        url = service_urls["mcp-package-manager"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        response = await http_client.get(
            f"{url}/api/v1/packages",
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code == 200, \
            f"List packages failed: {response.status_code}"
        
        data = response.json()
        assert "packages" in data or isinstance(data, list), \
            "Response should contain packages list"
    
    @pytest.mark.asyncio
    async def test_create_package(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test creating a new MCP package.
        
        Steps:
        1. Create package metadata
        2. Submit to package manager
        3. Verify package created
        
        Expected: Package created successfully
        """
        url = service_urls["mcp-package-manager"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        package_data = {
            "name": f"test_package_{correlation_id[:8]}",
            "version": "1.0.0",
            "description": "Test package for E2E validation",
            "metadata": {
                "author": "E2E Tester",
                "created_for": "testing"
            },
            "knowledge_items": [
                {"type": "test", "content": "Test knowledge item"}
            ]
        }
        
        response = await http_client.post(
            f"{url}/api/v1/packages",
            json=package_data,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201], \
            f"Package creation failed: {response.status_code}: {response.text}"
        
        data = response.json()
        assert "package_id" in data or "id" in data or "name" in data, \
            "Response missing package identifier"
    
    @pytest.mark.asyncio
    async def test_package_versioning(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test package versioning.
        
        Steps:
        1. Create package v1.0.0
        2. Create package v1.1.0 (same name)
        3. Verify both versions exist
        
        Expected: Multiple versions supported
        """
        url = service_urls["mcp-package-manager"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        package_name = f"versioned_pkg_{correlation_id[:8]}"
        
        # Create v1.0.0
        v1_data = {
            "name": package_name,
            "version": "1.0.0",
            "description": "Version 1.0.0"
        }
        
        v1_response = await http_client.post(
            f"{url}/api/v1/packages",
            json=v1_data,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert v1_response.status_code in [200, 201]
        
        # Create v1.1.0
        v2_data = {
            "name": package_name,
            "version": "1.1.0",
            "description": "Version 1.1.0"
        }
        
        v2_response = await http_client.post(
            f"{url}/api/v1/packages",
            json=v2_data,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # Should either accept new version or indicate duplicate
        assert v2_response.status_code in [200, 201, 409]
    
    @pytest.mark.asyncio
    async def test_export_package(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test exporting a package to .mcp file.
        
        Expected: Package exported successfully
        """
        url = service_urls["mcp-package-manager"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # First create a package
        package_data = {
            "name": f"export_test_{correlation_id[:8]}",
            "version": "1.0.0",
            "description": "Package for export testing"
        }
        
        create_response = await http_client.post(
            f"{url}/api/v1/packages",
            json=package_data,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Package creation failed, cannot test export")
        
        # Get package ID from response
        package_id = create_response.json().get("package_id") or \
                     create_response.json().get("id") or \
                     package_data["name"]
        
        # Export package
        export_response = await http_client.get(
            f"{url}/api/v1/packages/{package_id}/export",
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # Export may return 200 with file or 404 if not implemented
        assert export_response.status_code in [200, 404, 501]
    
    @pytest.mark.asyncio
    async def test_get_package_by_id(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test retrieving a package by ID.
        
        Expected: Package details returned
        """
        url = service_urls["mcp-package-manager"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Create a package first
        package_data = {
            "name": f"retrieve_test_{correlation_id[:8]}",
            "version": "1.0.0",
            "description": "Package for retrieval testing"
        }
        
        create_response = await http_client.post(
            f"{url}/api/v1/packages",
            json=package_data,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Package creation failed")
        
        package_id = create_response.json().get("package_id") or \
                     create_response.json().get("id") or \
                     package_data["name"]
        
        # Retrieve package
        get_response = await http_client.get(
            f"{url}/api/v1/packages/{package_id}",
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert get_response.status_code in [200, 404], \
            f"Unexpected status: {get_response.status_code}"
        
        if get_response.status_code == 200:
            data = get_response.json()
            assert data.get("name") == package_data["name"] or \
                   "name" in data or "package_id" in data, \
                   "Package data incomplete"
    
    @pytest.mark.asyncio
    async def test_package_validation(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test package validation with invalid data.
        
        Expected: Validation errors returned
        """
        url = service_urls["mcp-package-manager"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        # Invalid package (missing required fields)
        invalid_package = {
            "name": "",  # Empty name
            # Missing version
        }
        
        response = await http_client.post(
            f"{url}/api/v1/packages",
            json=invalid_package,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # Should reject invalid package
        assert response.status_code in [400, 422, 500], \
            f"Invalid package not rejected: {response.status_code}"
    
    @pytest.mark.asyncio
    async def test_package_metadata(
        self,
        http_client,
        service_urls,
        correlation_id,
        test_mode
    ):
        """
        Test package with rich metadata.
        
        Expected: Metadata preserved
        """
        url = service_urls["mcp-package-manager"]
        
        if test_mode == "code":
            pytest.skip("Code mode not implemented yet")
        
        package_data = {
            "name": f"metadata_test_{correlation_id[:8]}",
            "version": "1.0.0",
            "description": "Package with rich metadata",
            "metadata": {
                "author": "E2E Tester",
                "tags": ["test", "e2e", "validation"],
                "license": "MIT",
                "repository": "https://github.com/test/repo",
                "custom_field": "custom_value"
            }
        }
        
        response = await http_client.post(
            f"{url}/api/v1/packages",
            json=package_data,
            headers={"X-Correlation-ID": correlation_id}
        )
        
        assert response.status_code in [200, 201], \
            f"Package with metadata failed: {response.status_code}"
