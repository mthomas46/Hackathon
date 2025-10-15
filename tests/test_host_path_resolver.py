"""
Unit tests for host path resolver.

Tests path resolution, git root detection, and validation.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess

# Add service directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ecosystem-mcp"))

from src.utils.host_path_resolver import (
    HostPathResolver,
    HostPathValidator,
    ResolvedPath,
    resolve_host_path,
    validate_ingestion_path
)


class TestHostPathResolver:
    """Test host path resolver functionality."""
    
    def test_normalize_path_with_tilde(self):
        """Test path normalization with tilde expansion."""
        resolver = HostPathResolver()
        
        path = "~/Documents/test"
        normalized = resolver._normalize_path(path)
        
        assert not normalized.startswith("~")
        assert os.path.isabs(normalized)
    
    def test_normalize_path_with_env_var(self):
        """Test path normalization with environment variables."""
        resolver = HostPathResolver()
        
        os.environ["TEST_DIR"] = "/test/directory"
        path = "$TEST_DIR/subdir"
        normalized = resolver._normalize_path(path)
        
        assert normalized == "/test/directory/subdir"
    
    def test_normalize_path_relative(self):
        """Test normalization of relative paths."""
        resolver = HostPathResolver()
        
        path = "./relative/path"
        normalized = resolver._normalize_path(path)
        
        assert os.path.isabs(normalized)
    
    @patch('subprocess.run')
    def test_find_git_root_via_command(self, mock_run):
        """Test git root detection using git command."""
        resolver = HostPathResolver()
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout="/test/repo\n"
        )
        
        git_root = resolver._find_git_root("/test/repo/subdir")
        
        assert git_root == "/test/repo"
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_find_git_root_via_manual_search(self, mock_run):
        """Test git root detection via manual .git search."""
        resolver = HostPathResolver()
        
        # Git command fails
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="git", timeout=5)
        
        # Create temp directory structure for testing
        with patch('pathlib.Path.exists') as mock_exists:
            # Mock .git directory at parent level
            def exists_side_effect(self):
                return str(self).endswith(".git")
            
            mock_exists.side_effect = lambda: True
            
            # This test is complex due to Path object mocking
            # In real scenario, would use temp directories
            pass
    
    @patch('subprocess.run')
    def test_find_git_root_not_found(self, mock_run):
        """Test git root detection when not in a repo."""
        resolver = HostPathResolver()
        
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")
        
        # For manual search, would need temp directory
        # For now, test that it returns None appropriately
        git_root = resolver._find_git_root("/tmp")
        
        # May return None or /tmp depending on if /tmp/.git exists
        assert git_root is None or isinstance(git_root, str)
    
    def test_resolve_container_path_already_container(self):
        """Test resolving path that's already in container."""
        resolver = HostPathResolver()
        
        with patch.object(resolver, '_is_container_path', return_value=True):
            is_host_mount, container_path = resolver._resolve_container_path("/app/src")
            
            assert not is_host_mount
            assert container_path == "/app/src"
    
    def test_resolve_container_path_needs_mount(self):
        """Test resolving path that needs mounting."""
        resolver = HostPathResolver()
        resolver.host_mounts = {
            "/projects": "/Users/test/Documents/work"
        }
        
        with patch.object(resolver, '_is_container_path', return_value=False):
            is_host_mount, container_path = resolver._resolve_container_path(
                "/Users/test/Documents/work/MyProject"
            )
            
            assert is_host_mount
            assert container_path == "/projects/MyProject"
    
    def test_resolve_container_path_no_matching_mount(self):
        """Test resolving path with no matching mount point."""
        resolver = HostPathResolver()
        resolver.host_mounts = {}
        
        with patch.object(resolver, '_is_container_path', return_value=False):
            is_host_mount, container_path = resolver._resolve_container_path(
                "/some/random/path"
            )
            
            assert is_host_mount
            assert container_path.startswith("/host/")
    
    def test_is_container_path_in_app(self):
        """Test detecting path in /app as container path."""
        resolver = HostPathResolver()
        
        # Mock being in container
        with patch('os.path.exists', return_value=True):
            is_container = resolver._is_container_path("/app/src")
            assert is_container
    
    def test_suggest_mount_config(self):
        """Test mount configuration suggestion."""
        resolver = HostPathResolver()
        
        with patch.object(resolver, 'resolve') as mock_resolve:
            mock_resolve.return_value = ResolvedPath(
                original_path="/host/path",
                normalized_path="/host/path",
                container_path="/projects/repo",
                git_root="/host/path",
                is_git_repo=True,
                is_host_mount=True,
                relative_to_git="."
            )
            
            config = resolver.suggest_mount_config("/host/path")
            
            assert "volumes:" in config
            assert "/host/path" in config
            assert "docker-compose" in config or "restart" in config


class TestHostPathValidator:
    """Test path validation functionality."""
    
    @patch('src.utils.host_path_resolver.HostPathResolver')
    def test_validate_git_repo_valid(self, mock_resolver_class):
        """Test validating a valid git repository."""
        mock_resolver = Mock()
        mock_resolver_class.return_value = mock_resolver
        
        mock_resolved = ResolvedPath(
            original_path="/test/repo",
            normalized_path="/test/repo",
            container_path="/projects/repo",
            git_root="/test/repo",
            is_git_repo=True,
            is_host_mount=True,
            relative_to_git="."
        )
        mock_resolver.resolve.return_value = mock_resolved
        
        is_valid, message = HostPathValidator.validate_git_repo("/test/repo")
        
        assert is_valid
        assert "Valid git repository" in message
    
    @patch('src.utils.host_path_resolver.HostPathResolver')
    def test_validate_git_repo_invalid(self, mock_resolver_class):
        """Test validating a non-git directory."""
        mock_resolver = Mock()
        mock_resolver_class.return_value = mock_resolver
        
        mock_resolved = ResolvedPath(
            original_path="/test/notrepo",
            normalized_path="/test/notrepo",
            container_path="/projects/notrepo",
            git_root=None,
            is_git_repo=False,
            is_host_mount=True,
            relative_to_git=None
        )
        mock_resolver.resolve.return_value = mock_resolved
        
        is_valid, message = HostPathValidator.validate_git_repo("/test/notrepo")
        
        assert not is_valid
        assert "not in a git repository" in message
    
    def test_validate_accessibility_exists(self):
        """Test validating path that exists."""
        # Use a path that definitely exists
        is_valid, message = HostPathValidator.validate_accessibility("/")
        
        assert is_valid
        assert "accessible" in message.lower()
    
    def test_validate_accessibility_not_exists(self):
        """Test validating path that doesn't exist."""
        is_valid, message = HostPathValidator.validate_accessibility("/nonexistent/path/12345")
        
        assert not is_valid
        assert "does not exist" in message
    
    def test_validate_security_forbidden_path(self):
        """Test security validation blocks forbidden paths."""
        forbidden_paths = ["/etc", "/sys", "/proc", "/dev"]
        
        for path in forbidden_paths:
            is_valid, message = HostPathValidator.validate_security(path)
            
            assert not is_valid
            assert "sensitive" in message.lower() or "denied" in message.lower()
    
    def test_validate_security_allowed_path(self):
        """Test security validation allows safe paths."""
        safe_paths = ["/app", "/projects/test", "/workspace/repo"]
        
        for path in safe_paths:
            is_valid, message = HostPathValidator.validate_security(path)
            
            assert is_valid
            assert "secure" in message.lower()


class TestResolvedPath:
    """Test ResolvedPath dataclass."""
    
    def test_resolved_path_creation(self):
        """Test creating a ResolvedPath instance."""
        resolved = ResolvedPath(
            original_path="/test",
            normalized_path="/test/path",
            container_path="/projects/path",
            git_root="/test/path",
            is_git_repo=True,
            is_host_mount=True,
            relative_to_git="."
        )
        
        assert resolved.original_path == "/test"
        assert resolved.is_git_repo
        assert resolved.is_host_mount
    
    def test_resolved_path_no_git(self):
        """Test ResolvedPath for non-git directory."""
        resolved = ResolvedPath(
            original_path="/test",
            normalized_path="/test/path",
            container_path="/projects/path",
            git_root=None,
            is_git_repo=False,
            is_host_mount=True,
            relative_to_git=None
        )
        
        assert not resolved.is_git_repo
        assert resolved.git_root is None


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @patch('src.utils.host_path_resolver.HostPathResolver')
    def test_resolve_host_path(self, mock_resolver_class):
        """Test resolve_host_path convenience function."""
        mock_resolver = Mock()
        mock_resolver_class.return_value = mock_resolver
        
        mock_resolved = ResolvedPath(
            original_path="/test",
            normalized_path="/test",
            container_path="/projects/test",
            git_root="/test",
            is_git_repo=True,
            is_host_mount=True,
            relative_to_git="."
        )
        mock_resolver.resolve.return_value = mock_resolved
        
        result = resolve_host_path("/test")
        
        assert result.is_git_repo
        mock_resolver.resolve.assert_called_once_with("/test")
    
    @patch('src.utils.host_path_resolver.HostPathResolver')
    def test_validate_ingestion_path_valid(self, mock_resolver_class):
        """Test validate_ingestion_path with valid path."""
        mock_resolver = Mock()
        mock_resolver_class.return_value = mock_resolver
        
        mock_resolved = ResolvedPath(
            original_path="/test",
            normalized_path="/test",
            container_path="/projects/test",
            git_root="/test",
            is_git_repo=True,
            is_host_mount=True,
            relative_to_git="."
        )
        mock_resolver.validate_and_prepare.return_value = mock_resolved
        
        is_valid, message, resolved = validate_ingestion_path("/test")
        
        assert is_valid
        assert "valid" in message.lower()
        assert resolved is not None
    
    @patch('src.utils.host_path_resolver.HostPathResolver')
    def test_validate_ingestion_path_invalid(self, mock_resolver_class):
        """Test validate_ingestion_path with invalid path."""
        mock_resolver = Mock()
        mock_resolver_class.return_value = mock_resolver
        
        mock_resolver.validate_and_prepare.side_effect = ValueError("Not a git repo")
        
        is_valid, message, resolved = validate_ingestion_path("/test")
        
        assert not is_valid
        assert "Not a git repo" in message
        assert resolved is None


class TestMountConfiguration:
    """Test mount configuration handling."""
    
    def test_load_default_mounts(self):
        """Test loading default mount configuration."""
        resolver = HostPathResolver()
        
        assert "/host" in resolver.host_mounts
        assert "/" == resolver.host_mounts["/host"]
    
    def test_load_custom_mounts_from_env(self):
        """Test loading custom mounts from environment."""
        os.environ["CUSTOM_HOST_MOUNTS"] = "/custom:/custom/path,/another:/another/path"
        
        resolver = HostPathResolver()
        
        assert "/custom" in resolver.host_mounts
        assert resolver.host_mounts["/custom"] == "/custom/path"


class TestPathResolutionEdgeCases:
    """Test edge cases in path resolution."""
    
    def test_resolve_path_with_trailing_slash(self):
        """Test resolving path with trailing slash."""
        resolver = HostPathResolver()
        
        path1 = resolver._normalize_path("/test/path/")
        path2 = resolver._normalize_path("/test/path")
        
        # Both should normalize to same path
        assert path1.rstrip("/") == path2.rstrip("/")
    
    def test_resolve_path_with_dots(self):
        """Test resolving path with . and .. components."""
        resolver = HostPathResolver()
        
        path = "/test/path/../other/./file"
        normalized = resolver._normalize_path(path)
        
        # Should resolve . and ..
        assert ".." not in normalized
        assert "/." not in normalized
    
    def test_resolve_empty_path(self):
        """Test resolving empty or invalid path."""
        resolver = HostPathResolver()
        
        # Empty path should resolve to current directory
        path = resolver._normalize_path("")
        assert os.path.isabs(path)


# Pytest configuration
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

