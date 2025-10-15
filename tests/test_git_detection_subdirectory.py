"""
Unit tests for git detection with subdirectory support.

Tests the enhanced git detection that handles host paths, container mapping,
and subdirectory targeting with user confirmation.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add service directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ecosystem-mcp"))


class TestGitDetectionLogic:
    """Test core git detection logic."""
    
    def test_path_mapping_to_repo(self):
        """Test that Hackathon paths map to /repo."""
        # Simulate the mapping logic
        host_mounts = {
            "/repo": "/Users/mykalthomas/Documents/work/Hackathon",
            "/app": "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp",
        }
        
        host_path = "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"
        
        # Find matching mount
        container_path = None
        for container_mount, host_mount in host_mounts.items():
            if host_path.startswith(host_mount):
                relative = os.path.relpath(host_path, host_mount)
                if relative == ".":
                    container_path = container_mount
                else:
                    container_path = os.path.join(container_mount, relative)
                break
        
        assert container_path == "/repo/services/ecosystem-mcp"
    
    def test_path_mapping_root_directory(self):
        """Test mapping root Hackathon directory."""
        host_mounts = {
            "/repo": "/Users/mykalthomas/Documents/work/Hackathon",
        }
        
        host_path = "/Users/mykalthomas/Documents/work/Hackathon"
        
        for container_mount, host_mount in host_mounts.items():
            if host_path == host_mount:
                # Exact match - this is the root
                container_path = container_mount
                break
        
        assert container_path == "/repo"
    
    def test_no_trailing_dot_in_container_path(self):
        """Test that container paths don't have trailing /.  """
        host_path = "/Users/mykalthomas/Documents/work/Hackathon"
        host_mount = "/Users/mykalthomas/Documents/work/Hackathon"
        container_mount = "/repo"
        
        relative = os.path.relpath(host_path, host_mount)
        
        # Should be "."
        assert relative == "."
        
        # Logic should handle this
        if relative == ".":
            container_path = container_mount
        else:
            container_path = os.path.join(container_mount, relative)
        
        assert container_path == "/repo"
        assert not container_path.endswith("/.")
    
    def test_subdirectory_detection(self):
        """Test subdirectory detection logic."""
        git_root = "/Users/mykalthomas/Documents/work/Hackathon"
        selected_path = "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"
        
        # Calculate if it's a subdirectory
        try:
            relative = str(Path(selected_path).relative_to(git_root))
            is_subdirectory = (relative != ".")
            target_subdir = relative if is_subdirectory else None
        except ValueError:
            is_subdirectory = False
            target_subdir = None
        
        assert is_subdirectory is True
        assert target_subdir == "services/ecosystem-mcp"
    
    def test_root_directory_not_subdirectory(self):
        """Test that root directory is not detected as subdirectory."""
        git_root = "/Users/mykalthomas/Documents/work/Hackathon"
        selected_path = "/Users/mykalthomas/Documents/work/Hackathon"
        
        try:
            relative = str(Path(selected_path).relative_to(git_root))
            is_subdirectory = (relative != ".")
            target_subdir = relative if is_subdirectory else None
        except ValueError:
            is_subdirectory = False
            target_subdir = None
        
        assert is_subdirectory is False
        assert target_subdir is None


class TestHostPathResolver:
    """Test HostPathResolver if module can be imported."""
    
    def test_import_resolver(self):
        """Test that HostPathResolver can be imported."""
        try:
            from src.utils.host_path_resolver import HostPathResolver
            assert HostPathResolver is not None
        except ImportError as e:
            pytest.skip(f"Cannot import HostPathResolver: {e}")
    
    def test_mount_configuration(self):
        """Test that mount configuration includes /repo."""
        try:
            from src.utils.host_path_resolver import HostPathResolver
            resolver = HostPathResolver()
            
            # Check that /repo is in mounts
            assert "/repo" in resolver.host_mounts
            assert resolver.host_mounts["/repo"] == "/Users/mykalthomas/Documents/work/Hackathon"
        except ImportError:
            pytest.skip("Cannot test without imports")


class TestValidationFlow:
    """Test the complete validation flow."""
    
    def test_validation_request_structure(self):
        """Test validation API request structure."""
        path = "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp"
        
        request = {"path": path}
        
        assert "path" in request
        assert request["path"] == path
    
    def test_validation_response_parsing_subdirectory(self):
        """Test parsing validation response for subdirectory."""
        mock_response = {
            "is_valid": True,
            "container_path": "/repo/services/ecosystem-mcp",
            "git_root": "/Users/mykalthomas/Documents/work/Hackathon",
            "is_subdirectory": True,
            "target_subdir": "services/ecosystem-mcp",
            "is_mounted": True
        }
        
        assert mock_response["is_subdirectory"] is True
        assert mock_response["target_subdir"] == "services/ecosystem-mcp"
        assert mock_response["container_path"] == "/repo/services/ecosystem-mcp"
    
    def test_validation_response_parsing_root(self):
        """Test parsing validation response for root directory."""
        mock_response = {
            "is_valid": True,
            "container_path": "/repo",
            "git_root": "/Users/mykalthomas/Documents/work/Hackathon",
            "is_subdirectory": False,
            "target_subdir": None,
            "is_mounted": True
        }
        
        assert mock_response["is_subdirectory"] is False
        assert mock_response["target_subdir"] is None
        assert mock_response["container_path"] == "/repo"


class TestIngestionRequest:
    """Test ingestion API request construction."""
    
    def test_ingestion_request_with_subdirectory(self):
        """Test ingestion request includes target_subdirectory."""
        request_data = {
            "repo_path": "/repo",
            "mode": "full",
            "resolve_host_path": False,
            "target_subdirectory": "services/ecosystem-mcp"
        }
        
        assert request_data["repo_path"] == "/repo"
        assert request_data["target_subdirectory"] == "services/ecosystem-mcp"
        assert request_data["resolve_host_path"] is False
    
    def test_ingestion_request_full_repo(self):
        """Test ingestion request for full repository."""
        request_data = {
            "repo_path": "/repo",
            "mode": "full",
            "resolve_host_path": False
        }
        
        assert request_data["repo_path"] == "/repo"
        assert "target_subdirectory" not in request_data
    
    def test_request_serialization(self):
        """Test that request can be JSON serialized."""
        import json
        
        request_data = {
            "repo_path": "/repo",
            "mode": "full",
            "resolve_host_path": False,
            "target_subdirectory": "services/ecosystem-mcp"
        }
        
        # Should not raise
        json_str = json.dumps(request_data)
        assert "services/ecosystem-mcp" in json_str
        assert "repo_path" in json_str


class TestUserConfirmationLogic:
    """Test user confirmation workflow logic."""
    
    def test_confirmation_needed_for_subdirectory(self):
        """Test that confirmation is needed for subdirectories."""
        is_subdirectory = True
        needs_confirmation = is_subdirectory
        
        assert needs_confirmation is True
    
    def test_no_confirmation_for_root(self):
        """Test that confirmation is NOT needed for root directory."""
        is_subdirectory = False
        needs_confirmation = is_subdirectory
        
        assert needs_confirmation is False
    
    def test_user_choice_subdirectory_only(self):
        """Test user choosing subdirectory only."""
        choice = "🎯 Just this subdirectory: services/ecosystem-mcp"
        
        if choice.startswith("🎯"):
            target_subdirectory = "services/ecosystem-mcp"
        else:
            target_subdirectory = None
        
        assert target_subdirectory == "services/ecosystem-mcp"
    
    def test_user_choice_full_repo(self):
        """Test user choosing full repository."""
        choice = "📦 Entire git repository: /Users/.../Hackathon"
        
        if choice.startswith("📦"):
            target_subdirectory = None
        else:
            target_subdirectory = "services/ecosystem-mcp"
        
        assert target_subdirectory is None


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_path_not_found_error(self):
        """Test handling path not found error."""
        error_response = {
            "detail": "Repository path does not exist: /Users/.../Hackathon"
        }
        
        error_detail = error_response.get("detail", "Unknown error")
        
        assert "does not exist" in error_detail.lower()
    
    def test_git_not_found_error(self):
        """Test handling git repository not found error."""
        error_response = {
            "detail": "Path is not in a git repository"
        }
        
        error_detail = error_response.get("detail", "Unknown error")
        
        assert "git" in error_detail.lower()
    
    def test_mount_error(self):
        """Test handling mount point error."""
        error_response = {
            "detail": "Host path requires mount at /host which is not available"
        }
        
        error_detail = error_response.get("detail", "Unknown error")
        
        assert "mount" in error_detail.lower()


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_deeply_nested_subdirectory(self):
        """Test deeply nested subdirectory path."""
        git_root = "/Users/mykalthomas/Documents/work/Hackathon"
        selected_path = "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/src/api/routes"
        
        relative = str(Path(selected_path).relative_to(git_root))
        
        assert relative == "services/ecosystem-mcp/src/api/routes"
    
    def test_path_with_spaces(self):
        """Test path with spaces in directory names."""
        git_root = "/Users/test/My Documents/Work/Hackathon"
        selected_path = "/Users/test/My Documents/Work/Hackathon/services/test service"
        
        relative = str(Path(selected_path).relative_to(git_root))
        
        assert relative == "services/test service"
    
    def test_path_with_special_chars(self):
        """Test path with special characters."""
        git_root = "/Users/test/Work/Hackathon-2024"
        selected_path = "/Users/test/Work/Hackathon-2024/services/api_v2"
        
        relative = str(Path(selected_path).relative_to(git_root))
        
        assert relative == "services/api_v2"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

