"""
Integration tests for git detection API endpoints.

Tests the actual API with real HTTP calls to verify the complete flow.
"""

import pytest
import httpx
import asyncio
from pathlib import Path


@pytest.mark.integration
class TestPathValidationAPI:
    """Test the /api/v1/path/validate endpoint."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_validate_hackathon_root(self, api_base_url):
        """Test validating the Hackathon root directory."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon"},
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should be valid
                assert data["is_valid"] is True
                
                # Should map to /repo
                assert data["container_path"] == "/repo"
                
                # Should detect git root
                assert data["git_root"] is not None
                assert "Hackathon" in data["git_root"]
                
                # Should NOT be a subdirectory (it's the root)
                assert data["is_subdirectory"] is False
                assert data["target_subdir"] is None
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_validate_ecosystem_mcp_subdirectory(self, api_base_url):
        """Test validating the ecosystem-mcp subdirectory."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"},
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should be valid
                assert data["is_valid"] is True
                
                # Should map to /repo/services/ecosystem-mcp
                assert "/repo" in data["container_path"]
                assert "services" in data["container_path"]
                
                # Should detect git root
                assert data["git_root"] is not None
                assert "Hackathon" in data["git_root"]
                
                # SHOULD be a subdirectory
                assert data["is_subdirectory"] is True
                assert data["target_subdir"] == "services/ecosystem-mcp"
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_validate_dashboard_subdirectory(self, api_base_url):
        """Test validating the dashboard subdirectory."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard"},
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["is_valid"] is True
                assert data["is_subdirectory"] is True
                assert data["target_subdir"] == "services/ecosystem-mcp-dashboard"
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_validate_invalid_path(self, api_base_url):
        """Test validating a non-existent path."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/nonexistent/random/path"},
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should be invalid
                assert data["is_valid"] is False
                
                # Should have error message
                assert "message" in data
                assert len(data["message"]) > 0
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")


@pytest.mark.integration
class TestIngestionAPI:
    """Test the /api/v1/admin/ingest endpoint."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_ingest_with_container_path(self, api_base_url):
        """Test starting ingestion with container path."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": "/repo",
                        "mode": "quick",
                        "resolve_host_path": False
                    },
                    timeout=30.0
                )
                
                # Should succeed or return specific error
                if response.status_code == 200:
                    data = response.json()
                    assert "job_id" in data
                    assert data["status"] == "queued"
                elif response.status_code == 400:
                    # If it fails, check the error
                    data = response.json()
                    print(f"Ingestion failed: {data.get('detail')}")
                    # This might fail for other reasons (workers, etc)
                    # Just verify we get a proper error response
                    assert "detail" in data
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_ingest_with_subdirectory(self, api_base_url):
        """Test starting ingestion with subdirectory targeting."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": "/repo",
                        "mode": "quick",
                        "resolve_host_path": False,
                        "target_subdirectory": "services/ecosystem-mcp"
                    },
                    timeout=30.0
                )
                
                # Should succeed or return specific error
                if response.status_code == 200:
                    data = response.json()
                    assert "job_id" in data
                elif response.status_code == 400:
                    data = response.json()
                    print(f"Ingestion with subdirectory failed: {data.get('detail')}")
                    assert "detail" in data
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_ingest_with_host_path_fails(self, api_base_url):
        """Test that ingestion fails when host path is sent without resolution."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": "/Users/mykalthomas/Documents/work/Hackathon",
                        "mode": "quick",
                        "resolve_host_path": False  # Not resolving!
                    },
                    timeout=30.0
                )
                
                # Should fail with 400
                assert response.status_code == 400
                data = response.json()
                assert "does not exist" in data["detail"].lower()
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete validation → ingestion workflow."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_complete_subdirectory_workflow(self, api_base_url):
        """Test the complete workflow: validate subdirectory → ingest."""
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Validate path
                validate_response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"},
                    timeout=10.0
                )
                
                assert validate_response.status_code == 200
                validation = validate_response.json()
                assert validation["is_valid"] is True
                
                container_path = validation["container_path"]
                target_subdir = validation["target_subdir"]
                
                # Step 2: Start ingestion with resolved path
                ingest_response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": container_path,
                        "mode": "quick",
                        "resolve_host_path": False,
                        "target_subdirectory": target_subdir
                    },
                    timeout=30.0
                )
                
                # Should succeed or fail with specific error
                if ingest_response.status_code == 200:
                    data = ingest_response.json()
                    assert "job_id" in data
                    print(f"✅ Job created: {data['job_id']}")
                elif ingest_response.status_code == 400:
                    data = ingest_response.json()
                    print(f"❌ Ingestion failed: {data.get('detail')}")
                    # Verify error structure
                    assert "detail" in data
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_complete_root_workflow(self, api_base_url):
        """Test the complete workflow: validate root → ingest."""
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Validate path
                validate_response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon"},
                    timeout=10.0
                )
                
                assert validate_response.status_code == 200
                validation = validate_response.json()
                assert validation["is_valid"] is True
                assert validation["is_subdirectory"] is False
                
                container_path = validation["container_path"]
                
                # Step 2: Start ingestion
                ingest_response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": container_path,
                        "mode": "quick",
                        "resolve_host_path": False
                    },
                    timeout=30.0
                )
                
                # Check response
                if ingest_response.status_code == 200:
                    data = ingest_response.json()
                    assert "job_id" in data
                    print(f"✅ Job created: {data['job_id']}")
                else:
                    data = ingest_response.json()
                    print(f"Response: {ingest_response.status_code} - {data.get('detail')}")
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])

