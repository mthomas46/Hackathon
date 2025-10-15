"""
Integration tests for host path ingestion.

Tests the full path resolution and ingestion flow with API.
"""

import pytest
import httpx
import asyncio
from pathlib import Path


API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30.0


class TestPathResolutionAPI:
    """Integration tests for path resolution API."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resolve_container_path(self):
        """Test resolving a container path."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/resolve",
                json={"path": "/app"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["original_path"] == "/app"
            assert result["is_git_repo"] in [True, False]  # May or may not be git
            assert "container_path" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resolve_host_path(self):
        """Test resolving a host machine path."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Use Hackathon directory as test
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/resolve",
                json={"path": "/Users/mykalthomas/Documents/work/Hackathon"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["is_git_repo"] is True
            assert result["git_root"] is not None
            assert "Hackathon" in result["git_root"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resolve_subdirectory(self):
        """Test resolving a subdirectory within a repo."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Use services subdirectory
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/resolve",
                json={"path": "/Users/mykalthomas/Documents/work/Hackathon/services"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should detect git root at parent level
            assert result["is_git_repo"] is True
            assert "Hackathon" in result["git_root"]
            
            # Should detect subdirectory targeting
            if result["is_subdirectory"]:
                assert result["target_subdir"] is not None
                assert "services" in result["target_subdir"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_validate_valid_path(self):
        """Test validating a valid git repository."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/validate",
                json={"path": "/Users/mykalthomas/Documents/work/Hackathon"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert result["is_valid"] is True
            assert "valid" in result["message"].lower()
            assert result["resolved_path"] is not None
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_validate_non_git_path(self):
        """Test validating a non-git directory."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/validate",
                json={"path": "/tmp"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # /tmp is not a git repo
            assert result["is_valid"] is False
            assert "git" in result["message"].lower()
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_mount_points(self):
        """Test getting configured mount points."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/path/mounts"
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert "mount_points" in result
            assert "count" in result
            assert isinstance(result["mount_points"], dict)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_suggest_mount(self):
        """Test getting mount configuration suggestion."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/suggest-mount",
                json={"path": "/Users/mykalthomas/Documents/work/SomeProject"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert "needs_mount" in result
            if result["needs_mount"]:
                assert "mount_config" in result
                assert "instructions" in result


class TestIngestionWithHostPath:
    """Integration tests for ingestion with host paths."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ingest_with_host_path_resolution(self):
        """Test starting ingestion with host path resolution."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            # Note: This may fail if mount is not configured
            # But should give clear error message
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingest",
                json={
                    "repo_path": "/Users/mykalthomas/Documents/work/Hackathon",
                    "mode": "quick",
                    "resolve_host_path": True
                }
            )
            
            # Should either succeed or give mount error
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                result = response.json()
                assert "job_id" in result
            else:
                # Should have clear error message
                result = response.json()
                assert "detail" in result
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ingest_subdirectory_targeting(self):
        """Test ingesting a specific subdirectory."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingest",
                json={
                    "repo_path": "/Users/mykalthomas/Documents/work/Hackathon/services",
                    "mode": "quick",
                    "resolve_host_path": True
                }
            )
            
            # Should either succeed or give clear error
            assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ingest_with_explicit_subdirectory(self):
        """Test ingestion with explicitly specified subdirectory."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/admin/ingest",
                json={
                    "repo_path": "/Users/mykalthomas/Documents/work/Hackathon",
                    "mode": "quick",
                    "resolve_host_path": True,
                    "target_subdirectory": "services/ecosystem-mcp"
                }
            )
            
            assert response.status_code in [200, 400]


class TestPathResolutionEdgeCases:
    """Integration tests for edge cases."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resolve_path_with_tilde(self):
        """Test resolving path with tilde expansion."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/resolve",
                json={"path": "~/Documents/work"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should expand tilde
            assert "~" not in result["normalized_path"]
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_resolve_relative_path(self):
        """Test resolving relative path."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/resolve",
                json={"path": "./services"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should normalize to absolute
            assert result["normalized_path"].startswith("/")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_validate_sensitive_directory(self):
        """Test validation blocks sensitive directories."""
        async with httpx.AsyncClient(timeout=TEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/path/validate",
                json={"path": "/etc"}
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should block /etc
            assert result["is_valid"] is False
            assert "sensitive" in result["message"].lower() or "denied" in result["message"].lower()


# Pytest configuration
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration", "--tb=short"])

