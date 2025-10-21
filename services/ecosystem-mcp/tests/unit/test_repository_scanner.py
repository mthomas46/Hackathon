"""
Unit tests for Repository Scanner (Phase 1)
"""

import pytest
from pathlib import Path
import tempfile
import os

from src.services.discovery.repository_scanner import RepositoryScanner


class TestRepositoryScanner:
    """Test RepositoryScanner class."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create test files
            (repo_path / "test.py").write_text("print('hello')")
            (repo_path / "README.md").write_text("# Test")
            (repo_path / "config.json").write_text('{"test": true}')
            
            # Create subdirectory
            sub_dir = repo_path / "subdir"
            sub_dir.mkdir()
            (sub_dir / "module.py").write_text("def test(): pass")
            
            # Create ignored files
            (repo_path / ".git").mkdir()
            (repo_path / ".git" / "config").write_text("git config")
            (repo_path / "__pycache__").mkdir()
            (repo_path / "__pycache__" / "test.pyc").write_text("bytecode")
            
            yield str(repo_path)
    
    def test_scanner_initialization(self):
        """Test scanner initializes correctly."""
        scanner = RepositoryScanner("/tmp/test")
        assert scanner.repo_path == "/tmp/test"
        assert scanner.files == []
    
    def test_scan_repository(self, temp_repo):
        """Test scanning a repository."""
        scanner = RepositoryScanner(temp_repo)
        result = scanner.scan()
        
        assert result["success"] is True
        assert result["total_files"] > 0
        assert result["total_size"] > 0
        assert len(result["files"]) > 0
    
    def test_scan_ignores_patterns(self, temp_repo):
        """Test that .git and __pycache__ are ignored."""
        scanner = RepositoryScanner(temp_repo)
        result = scanner.scan()
        
        # Check that ignored patterns are not in results
        file_paths = [f["path"] for f in result["files"]]
        assert not any(".git" in p for p in file_paths)
        assert not any("__pycache__" in p for p in file_paths)
    
    def test_detect_file_type(self):
        """Test file type detection."""
        scanner = RepositoryScanner("/tmp/test")
        
        assert scanner._detect_file_type("test.py") == "python"
        assert scanner._detect_file_type("test.js") == "javascript"
        assert scanner._detect_file_type("test.md") == "markdown"
        assert scanner._detect_file_type("test.json") == "json"
        assert scanner._detect_file_type("test.unknown") == "other"
    
    def test_detect_language(self):
        """Test language detection."""
        scanner = RepositoryScanner("/tmp/test")
        
        assert scanner._detect_language("test.py") == "python"
        assert scanner._detect_language("test.js") == "javascript"
        assert scanner._detect_language("test.go") == "go"
        assert scanner._detect_language("test.rs") == "rust"
        assert scanner._detect_language("test.md") is None
    
    def test_should_ignore(self):
        """Test ignore pattern matching."""
        scanner = RepositoryScanner("/tmp/test")
        
        assert scanner._should_ignore(".git/config") is True
        assert scanner._should_ignore("__pycache__/test.pyc") is True
        assert scanner._should_ignore("node_modules/package.json") is True
        assert scanner._should_ignore("src/test.py") is False
    
    def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepositoryScanner(tmpdir)
            result = scanner.scan()
            
            assert result["success"] is True
            assert result["total_files"] == 0
            assert len(result["files"]) == 0
    
    def test_scan_nonexistent_directory(self):
        """Test scanning a nonexistent directory."""
        scanner = RepositoryScanner("/nonexistent/path")
        result = scanner.scan()
        
        assert result["success"] is False
        assert "error" in result
    
    def test_file_metadata(self, temp_repo):
        """Test that file metadata is captured correctly."""
        scanner = RepositoryScanner(temp_repo)
        result = scanner.scan()
        
        files = result["files"]
        assert len(files) > 0
        
        # Check first file has required fields
        file_info = files[0]
        assert "path" in file_info
        assert "size" in file_info
        assert "file_type" in file_info
        assert "language" in file_info or file_info["file_type"] != "code"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

