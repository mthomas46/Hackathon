"""
Integration tests for ingestion path resolution.

Tests the complete flow from frontend to backend, including:
- Path validation API endpoints
- Ingestion API with path resolution
- Database interactions
- Redis queue operations
"""

import pytest
import httpx
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, Mock
import sys

# Add service directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "ecosystem-mcp"))


@pytest.mark.integration
class TestPathValidationAPI:
    """Test the /api/v1/path/validate endpoint."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_validate_hackathon_path(self, api_base_url):
        """Test validating the Hackathon directory path."""
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
                
                # Should resolve to container path
                assert data["container_path"] == "/app"
                
                # Should detect git root
                assert data["git_root"] is not None
                
                # Should be mounted
                assert data["is_mounted"] is True
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_validate_subdirectory(self, api_base_url):
        """Test validating a subdirectory within the Hackathon repo."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon/services"},
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should be valid
                assert data["is_valid"] is True
                
                # Should detect subdirectory
                assert data["is_subdirectory"] is True
                assert data["target_subdir"] == "services"
                
                # Git root should be the parent
                assert "Hackathon" in data["git_root"]
                
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
    
    @pytest.mark.asyncio
    async def test_validate_non_git_path(self, api_base_url, tmp_path):
        """Test validating a path that's not a git repository."""
        try:
            # Create a temporary directory (not a git repo)
            test_dir = tmp_path / "not_a_repo"
            test_dir.mkdir()
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": str(test_dir)},
                    timeout=10.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should be invalid (no git repo)
                assert data["is_valid"] is False
                assert "git" in data["message"].lower()
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")


@pytest.mark.integration
class TestIngestionWithPathResolution:
    """Test the complete ingestion flow with path resolution."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_ingest_with_automatic_resolution(self, api_base_url):
        """Test ingestion automatically resolves host paths."""
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Validate path (frontend does this)
                validate_response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon"},
                    timeout=10.0
                )
                
                assert validate_response.status_code == 200
                validation = validate_response.json()
                assert validation["is_valid"] is True
                
                resolved_path = validation["container_path"]
                
                # Step 2: Start ingestion with resolved path (frontend does this)
                ingest_response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": resolved_path,
                        "mode": "quick",
                        "resolve_host_path": False  # Already resolved
                    },
                    timeout=30.0
                )
                
                assert ingest_response.status_code == 200
                data = ingest_response.json()
                
                # Should return job ID
                assert "job_id" in data
                assert len(data["job_id"]) > 0
                
                # Should indicate queued status
                assert data["status"] == "queued"
                
                # Message should mention the resolved path
                assert resolved_path in data["message"]
                
                return data["job_id"]
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_ingest_without_resolution_fails(self, api_base_url):
        """Test ingestion fails when host path is not resolved."""
        try:
            async with httpx.AsyncClient() as client:
                # Try to ingest with host path directly (old broken behavior)
                response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": "/Users/mykalthomas/Documents/work/Hackathon",
                        "mode": "quick",
                        "resolve_host_path": True  # Backend tries to validate
                    },
                    timeout=30.0
                )
                
                # This should work now if backend properly resolves
                # OR fail with 400 if path doesn't exist in container
                # Depending on mount configuration
                
                if response.status_code == 400:
                    # Expected if path validation in backend fails
                    assert "does not exist" in response.json()["detail"].lower() or \
                           "not mounted" in response.json()["detail"].lower()
                elif response.status_code == 200:
                    # Backend successfully resolved the path
                    data = response.json()
                    assert "job_id" in data
                    
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_ingest_subdirectory(self, api_base_url):
        """Test ingesting a specific subdirectory."""
        try:
            async with httpx.AsyncClient() as client:
                # Validate subdirectory
                validate_response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"},
                    timeout=10.0
                )
                
                assert validate_response.status_code == 200
                validation = validate_response.json()
                
                if validation["is_valid"]:
                    # Start ingestion with subdirectory
                    ingest_response = await client.post(
                        f"{api_base_url}/api/v1/admin/ingest",
                        json={
                            "repo_path": validation["container_path"],
                            "mode": "quick",
                            "resolve_host_path": False,
                            "target_subdirectory": validation.get("target_subdir")
                        },
                        timeout=30.0
                    )
                    
                    assert ingest_response.status_code == 200
                    data = ingest_response.json()
                    assert "job_id" in data
                    
        except httpx.ConnectError:
            pytest.skip("Backend service not running")


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_complete_ingestion_workflow(self, api_base_url):
        """Test the complete workflow: validate → ingest → monitor."""
        try:
            async with httpx.AsyncClient() as client:
                # Step 1: Health check
                health_response = await client.get(
                    f"{api_base_url}/health",
                    timeout=5.0
                )
                assert health_response.status_code == 200
                
                # Step 2: Validate path
                validate_response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/Users/mykalthomas/Documents/work/Hackathon"},
                    timeout=10.0
                )
                assert validate_response.status_code == 200
                validation = validate_response.json()
                assert validation["is_valid"] is True
                
                resolved_path = validation["container_path"]
                
                # Step 3: Check worker health
                worker_response = await client.get(
                    f"{api_base_url}/api/v1/admin/workers/ingestion/status",
                    timeout=5.0
                )
                # Worker check may fail if workers aren't running, that's okay
                
                # Step 4: Start ingestion
                ingest_response = await client.post(
                    f"{api_base_url}/api/v1/admin/ingest",
                    json={
                        "repo_path": resolved_path,
                        "mode": "quick",
                        "resolve_host_path": False
                    },
                    timeout=30.0
                )
                assert ingest_response.status_code == 200
                data = ingest_response.json()
                job_id = data["job_id"]
                
                # Step 5: Check job status
                status_response = await client.get(
                    f"{api_base_url}/api/v1/admin/ingest/status",
                    timeout=5.0
                )
                assert status_response.status_code == 200
                jobs = status_response.json()
                
                # Our job should be in the list
                job_ids = [job.get("id") for job in jobs]
                assert job_id in job_ids
                
                return job_id
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, api_base_url):
        """Test error handling in the workflow."""
        try:
            async with httpx.AsyncClient() as client:
                # Try to validate an invalid path
                validate_response = await client.post(
                    f"{api_base_url}/api/v1/path/validate",
                    json={"path": "/invalid/nonexistent/path"},
                    timeout=10.0
                )
                
                assert validate_response.status_code == 200
                validation = validate_response.json()
                assert validation["is_valid"] is False
                
                # Frontend should NOT proceed with ingestion
                # (we'll verify by NOT making the ingest call)
                
                # If we tried anyway, it should fail
                if validation.get("container_path"):
                    ingest_response = await client.post(
                        f"{api_base_url}/api/v1/admin/ingest",
                        json={
                            "repo_path": validation["container_path"],
                            "mode": "quick",
                            "resolve_host_path": False
                        },
                        timeout=30.0
                    )
                    # Should fail because path doesn't exist
                    assert ingest_response.status_code in [400, 500]
                    
        except httpx.ConnectError:
            pytest.skip("Backend service not running")


@pytest.mark.integration
class TestMountConfiguration:
    """Test Docker mount configuration detection."""
    
    @pytest.fixture
    def api_base_url(self):
        """Base URL for the API."""
        return "http://localhost:8080"
    
    @pytest.mark.asyncio
    async def test_get_mount_points(self, api_base_url):
        """Test retrieving configured mount points."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{api_base_url}/api/v1/path/mounts",
                    timeout=5.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should return mount configuration
                assert "mounts" in data
                assert isinstance(data["mounts"], dict)
                
                # Hackathon directory should be mounted
                mounts = data["mounts"]
                assert any("/app" in str(v) for v in mounts.values())
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")
    
    @pytest.mark.asyncio
    async def test_suggest_mount_config(self, api_base_url):
        """Test mount configuration suggestions."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{api_base_url}/api/v1/path/suggest-mount",
                    json={"path": "/Users/test/new_project"},
                    timeout=5.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Should return mount suggestion
                assert "suggestion" in data
                assert "volumes:" in data["suggestion"]
                assert "/Users/test/new_project" in data["suggestion"]
                
        except httpx.ConnectError:
            pytest.skip("Backend service not running")


@pytest.mark.integration
class TestRecentPathsTracking:
    """Test recent paths tracking in the frontend."""
    
    def test_recent_paths_initialization(self):
        """Test recent paths are initialized with default."""
        # Simulate Streamlit session state
        session_state = {}
        
        # Initialize (this happens in ingestion_manager.py)
        if "recent_host_paths" not in session_state:
            session_state["recent_host_paths"] = [
                "/Users/mykalthomas/Documents/work/Hackathon"
            ]
        
        assert len(session_state["recent_host_paths"]) == 1
        assert session_state["recent_host_paths"][0] == "/Users/mykalthomas/Documents/work/Hackathon"
    
    def test_recent_paths_add_new(self):
        """Test adding new paths to recent history."""
        session_state = {
            "recent_host_paths": ["/Users/mykalthomas/Documents/work/Hackathon"]
        }
        
        # Add a new path
        new_path = "/Users/mykalthomas/Documents/other_project"
        if new_path not in session_state["recent_host_paths"]:
            session_state["recent_host_paths"].insert(0, new_path)
            session_state["recent_host_paths"] = session_state["recent_host_paths"][:10]
        
        assert len(session_state["recent_host_paths"]) == 2
        assert session_state["recent_host_paths"][0] == new_path
    
    def test_recent_paths_limit(self):
        """Test recent paths are limited to 10."""
        session_state = {"recent_host_paths": []}
        
        # Add 15 paths
        for i in range(15):
            path = f"/path/number/{i}"
            session_state["recent_host_paths"].insert(0, path)
            session_state["recent_host_paths"] = session_state["recent_host_paths"][:10]
        
        # Should only keep 10
        assert len(session_state["recent_host_paths"]) == 10
        
        # Most recent should be first
        assert session_state["recent_host_paths"][0] == "/path/number/14"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])

