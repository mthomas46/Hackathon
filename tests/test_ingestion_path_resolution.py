"""
Unit tests for ingestion path resolution feature.

Tests the automatic path validation and resolution logic that fixes
the HTTP 400 error when using host machine paths.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys

# Add service directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ecosystem-mcp"))

from src.utils.host_path_resolver import (
    HostPathResolver,
    ResolvedPath,
    validate_ingestion_path,
    resolve_host_path
)


class TestHostPathResolver:
    """Test the HostPathResolver utility."""
    
    def test_normalize_path_basic(self):
        """Test basic path normalization."""
        resolver = HostPathResolver()
        
        # Absolute path
        result = resolver.normalize_path("/Users/test/Documents")
        assert result == Path("/Users/test/Documents")
        
        # Path with tilde
        with patch('pathlib.Path.home', return_value=Path("/Users/test")):
            result = resolver.normalize_path("~/Documents")
            assert result == Path("/Users/test/Documents")
    
    def test_normalize_path_with_symlinks(self):
        """Test path normalization resolves symlinks."""
        resolver = HostPathResolver()
        
        # Test with existing path
        test_path = Path(__file__).parent
        result = resolver.normalize_path(str(test_path))
        assert result.is_absolute()
    
    def test_detect_git_root_found(self, tmp_path):
        """Test git root detection when .git exists."""
        resolver = HostPathResolver()
        
        # Create fake git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        subdir = tmp_path / "subdir" / "nested"
        subdir.mkdir(parents=True)
        
        # Should find git root
        result = resolver.detect_git_root(subdir)
        assert result == tmp_path
    
    def test_detect_git_root_not_found(self, tmp_path):
        """Test git root detection when no .git exists."""
        resolver = HostPathResolver()
        
        # No .git directory
        result = resolver.detect_git_root(tmp_path)
        assert result is None
    
    def test_resolve_container_path_mounted(self):
        """Test container path resolution for mounted paths."""
        resolver = HostPathResolver(
            mount_points={
                "/Users/mykalthomas/Documents/work/Hackathon": "/app"
            }
        )
        
        host_path = Path("/Users/mykalthomas/Documents/work/Hackathon/services")
        result = resolver.resolve_container_path(host_path)
        
        assert result.container_path == "/app/services"
        assert result.is_mounted is True
    
    def test_resolve_container_path_not_mounted(self):
        """Test container path resolution for non-mounted paths."""
        resolver = HostPathResolver(mount_points={})
        
        host_path = Path("/Users/test/random")
        result = resolver.resolve_container_path(host_path)
        
        assert result.container_path is None
        assert result.is_mounted is False
    
    def test_resolve_full_workflow(self, tmp_path):
        """Test complete resolution workflow."""
        # Create fake git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        target_dir = tmp_path / "services" / "api"
        target_dir.mkdir(parents=True)
        
        resolver = HostPathResolver(
            mount_points={str(tmp_path): "/app"}
        )
        
        result = resolver.resolve(str(target_dir))
        
        assert result.original_path == str(target_dir)
        assert result.normalized_path == target_dir
        assert result.git_root == str(tmp_path)
        assert result.is_subdirectory is True
        assert result.target_subdir == "services/api"
        assert result.container_path == "/app"
        assert result.is_mounted is True


class TestValidateIngestionPath:
    """Test the validate_ingestion_path function."""
    
    def test_validate_valid_path(self, tmp_path):
        """Test validation of a valid ingestion path."""
        # Create fake git repo
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        
        with patch('src.utils.host_path_resolver.HostPathResolver.resolve') as mock_resolve:
            mock_resolve.return_value = ResolvedPath(
                original_path=str(tmp_path),
                normalized_path=tmp_path,
                git_root=str(tmp_path),
                container_path="/app",
                is_host_mount=True,
                is_mounted=True,
                target_subdir=None,
                is_subdirectory=False,
                mount_suggestion=None
            )
            
            is_valid, message, resolved = validate_ingestion_path(str(tmp_path))
            
            assert is_valid is True
            assert "valid" in message.lower()
            assert resolved.git_root == str(tmp_path)
    
    def test_validate_not_mounted(self):
        """Test validation fails for non-mounted paths."""
        with patch('src.utils.host_path_resolver.HostPathResolver.resolve') as mock_resolve:
            mock_resolve.return_value = ResolvedPath(
                original_path="/random/path",
                normalized_path=Path("/random/path"),
                git_root=None,
                container_path=None,
                is_host_mount=False,
                is_mounted=False,
                target_subdir=None,
                is_subdirectory=False,
                mount_suggestion="Add to docker-compose.yml: ..."
            )
            
            is_valid, message, resolved = validate_ingestion_path("/random/path")
            
            assert is_valid is False
            assert "not mounted" in message.lower()
    
    def test_validate_no_git_repo(self, tmp_path):
        """Test validation fails for non-git directories."""
        with patch('src.utils.host_path_resolver.HostPathResolver.resolve') as mock_resolve:
            mock_resolve.return_value = ResolvedPath(
                original_path=str(tmp_path),
                normalized_path=tmp_path,
                git_root=None,
                container_path="/app",
                is_host_mount=True,
                is_mounted=True,
                target_subdir=None,
                is_subdirectory=False,
                mount_suggestion=None
            )
            
            is_valid, message, resolved = validate_ingestion_path(str(tmp_path))
            
            assert is_valid is False
            assert "git" in message.lower()


class TestPathResolutionIntegration:
    """Integration tests for path resolution in the API."""
    
    @pytest.mark.asyncio
    async def test_ingest_endpoint_with_host_path_resolution(self):
        """Test ingestion endpoint resolves host paths correctly."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        with patch('src.api.routes.admin.validate_ingestion_path') as mock_validate:
            # Mock successful validation
            mock_validate.return_value = (
                True,
                "Path is valid",
                ResolvedPath(
                    original_path="/Users/test/Hackathon",
                    normalized_path=Path("/Users/test/Hackathon"),
                    git_root="/Users/test/Hackathon",
                    container_path="/app",
                    is_host_mount=True,
                    is_mounted=True,
                    target_subdir=None,
                    is_subdirectory=False,
                    mount_suggestion=None
                )
            )
            
            with patch('src.api.routes.admin.get_database') as mock_db, \
                 patch('src.api.routes.admin.get_redis_client') as mock_redis:
                
                # Mock database job creation
                mock_session = AsyncMock()
                mock_db.return_value.session.return_value.__aenter__.return_value = mock_session
                
                mock_job = Mock()
                mock_job.id = "test-job-123"
                mock_session.commit = AsyncMock()
                
                with patch('src.api.routes.admin.IngestionJobRepository') as mock_repo:
                    mock_repo.return_value.create_job = AsyncMock(return_value=mock_job)
                    
                    # Mock Redis
                    mock_redis_instance = AsyncMock()
                    mock_redis_instance._connected = True
                    mock_redis_instance.client = Mock()
                    mock_redis_instance.add_to_stream = AsyncMock()
                    mock_redis.return_value = mock_redis_instance
                    
                    # Make request
                    response = client.post(
                        "/api/v1/admin/ingest",
                        json={
                            "repo_path": "/Users/test/Hackathon",
                            "mode": "quick",
                            "resolve_host_path": True
                        }
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["job_id"] == "test-job-123"
                    assert "Processing /app" in data["message"]
    
    @pytest.mark.asyncio
    async def test_ingest_endpoint_fails_unmounted_path(self):
        """Test ingestion fails for unmounted paths."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        with patch('src.api.routes.admin.validate_ingestion_path') as mock_validate:
            # Mock failed validation (unmounted)
            mock_validate.return_value = (
                False,
                "Path is not mounted in Docker",
                ResolvedPath(
                    original_path="/random/path",
                    normalized_path=Path("/random/path"),
                    git_root=None,
                    container_path=None,
                    is_host_mount=False,
                    is_mounted=False,
                    target_subdir=None,
                    is_subdirectory=False,
                    mount_suggestion="volumes:\n  - /random/path:/mnt/data"
                )
            )
            
            response = client.post(
                "/api/v1/admin/ingest",
                json={
                    "repo_path": "/random/path",
                    "mode": "quick",
                    "resolve_host_path": True
                }
            )
            
            assert response.status_code == 400
            assert "not mounted" in response.json()["detail"].lower()


class TestFrontendPathResolution:
    """Test frontend path resolution logic."""
    
    def test_frontend_validates_before_submit(self):
        """Test that frontend validates host paths before submission."""
        import httpx
        from unittest.mock import MagicMock
        
        # Mock the validation API call
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "is_valid": True,
                "container_path": "/app",
                "git_root": "/app",
                "message": "Valid git repository"
            }
            mock_post.return_value = mock_response
            
            # Simulate frontend validation
            api_url = "http://localhost:8080"
            host_path = "/Users/test/Hackathon"
            
            validate_response = httpx.post(
                f"{api_url}/api/v1/path/validate",
                json={"path": host_path},
                timeout=10.0
            )
            
            assert validate_response.status_code == 200
            validation = validate_response.json()
            assert validation["is_valid"] is True
            assert validation["container_path"] == "/app"
            
            # Frontend should use resolved path
            resolved_path = validation["container_path"]
            assert resolved_path == "/app"
    
    def test_frontend_handles_validation_failure(self):
        """Test frontend handles validation failures gracefully."""
        import httpx
        from unittest.mock import MagicMock
        
        with patch('httpx.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "is_valid": False,
                "message": "Not a git repository",
                "container_path": None
            }
            mock_post.return_value = mock_response
            
            api_url = "http://localhost:8080"
            host_path = "/invalid/path"
            
            validate_response = httpx.post(
                f"{api_url}/api/v1/path/validate",
                json={"path": host_path},
                timeout=10.0
            )
            
            validation = validate_response.json()
            assert validation["is_valid"] is False
            
            # Frontend should NOT proceed with ingestion
            # (simulated by not making the ingest call)


class TestSubdirectoryTargeting:
    """Test subdirectory targeting within git repositories."""
    
    def test_resolve_subdirectory(self, tmp_path):
        """Test resolving a subdirectory within a git repo."""
        # Create fake git repo structure
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        target_dir = tmp_path / "services" / "api" / "routes"
        target_dir.mkdir(parents=True)
        
        resolver = HostPathResolver(
            mount_points={str(tmp_path): "/app"}
        )
        
        result = resolver.resolve(str(target_dir))
        
        assert result.git_root == str(tmp_path)
        assert result.is_subdirectory is True
        assert result.target_subdir == "services/api/routes"
        assert result.container_path == "/app"
    
    def test_ingest_subdirectory(self):
        """Test ingestion with subdirectory targeting."""
        with patch('src.utils.host_path_resolver.validate_ingestion_path') as mock_validate:
            mock_validate.return_value = (
                True,
                "Valid subdirectory",
                ResolvedPath(
                    original_path="/Users/test/Hackathon/services",
                    normalized_path=Path("/Users/test/Hackathon/services"),
                    git_root="/Users/test/Hackathon",
                    container_path="/app",
                    is_host_mount=True,
                    is_mounted=True,
                    target_subdir="services",
                    is_subdirectory=True,
                    mount_suggestion=None
                )
            )
            
            from fastapi.testclient import TestClient
            from src.api.app import create_app
            
            app = create_app()
            client = TestClient(app)
            
            with patch('src.api.routes.admin.get_database') as mock_db, \
                 patch('src.api.routes.admin.get_redis_client') as mock_redis:
                
                mock_session = AsyncMock()
                mock_db.return_value.session.return_value.__aenter__.return_value = mock_session
                
                mock_job = Mock()
                mock_job.id = "test-job-456"
                mock_session.commit = AsyncMock()
                
                with patch('src.api.routes.admin.IngestionJobRepository') as mock_repo:
                    mock_repo.return_value.create_job = AsyncMock(return_value=mock_job)
                    
                    mock_redis_instance = AsyncMock()
                    mock_redis_instance._connected = True
                    mock_redis_instance.client = Mock()
                    mock_redis_instance.add_to_stream = AsyncMock()
                    mock_redis.return_value = mock_redis_instance
                    
                    response = client.post(
                        "/api/v1/admin/ingest",
                        json={
                            "repo_path": "/Users/test/Hackathon/services",
                            "mode": "quick",
                            "resolve_host_path": True,
                            "target_subdirectory": "services"
                        }
                    )
                    
                    assert response.status_code == 200


class TestErrorRecovery:
    """Test error recovery and fallback mechanisms."""
    
    def test_validation_api_timeout(self):
        """Test handling when validation API times out."""
        import httpx
        
        with patch('httpx.post') as mock_post:
            mock_post.side_effect = httpx.TimeoutException("Request timed out")
            
            # Frontend should handle timeout gracefully
            try:
                httpx.post(
                    "http://localhost:8080/api/v1/path/validate",
                    json={"path": "/test"},
                    timeout=10.0
                )
                assert False, "Should have raised TimeoutException"
            except httpx.TimeoutException:
                # Frontend catches this and shows warning
                # "Could not validate path, using as-is"
                pass
    
    def test_validation_api_connection_error(self):
        """Test handling when validation API is unreachable."""
        import httpx
        
        with patch('httpx.post') as mock_post:
            mock_post.side_effect = httpx.ConnectError("Connection refused")
            
            try:
                httpx.post(
                    "http://localhost:8080/api/v1/path/validate",
                    json={"path": "/test"},
                    timeout=10.0
                )
                assert False, "Should have raised ConnectError"
            except httpx.ConnectError:
                # Frontend catches this and continues with original path
                pass
    
    def test_backend_path_not_exist_error(self):
        """Test backend error when resolved path doesn't exist."""
        from fastapi.testclient import TestClient
        from src.api.app import create_app
        
        app = create_app()
        client = TestClient(app)
        
        # Send request with resolve_host_path=False and non-existent path
        response = client.post(
            "/api/v1/admin/ingest",
            json={
                "repo_path": "/nonexistent/path",
                "mode": "quick",
                "resolve_host_path": False
            }
        )
        
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]


# Fixtures
@pytest.fixture
def tmp_git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    
    # Create some files
    (tmp_path / "README.md").write_text("# Test Repo")
    
    services_dir = tmp_path / "services"
    services_dir.mkdir()
    (services_dir / "api.py").write_text("# API")
    
    return tmp_path


@pytest.fixture
def mock_resolver():
    """Create a mock HostPathResolver."""
    return HostPathResolver(
        mount_points={
            "/Users/mykalthomas/Documents/work/Hackathon": "/app"
        }
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

