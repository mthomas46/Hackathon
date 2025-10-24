"""
Unit tests for Repository Scanner (Phase 1)
"""

import pytest
from pathlib import Path
import tempfile

from src.services.discovery.repository_scanner import RepositoryScanner, RepositoryInventory


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
            
            yield repo_path
    
    def test_scanner_initialization(self):
        """Test scanner initializes correctly."""
        scanner = RepositoryScanner()
        assert scanner is not None
        assert len(scanner.ignore_patterns) > 0
        assert len(scanner.code_extensions) > 0
    
    @pytest.mark.asyncio
    async def test_scan_repository(self, temp_repo):
        """Test scanning a repository."""
        scanner = RepositoryScanner()
        inventory = await scanner.scan(temp_repo)
        
        assert isinstance(inventory, RepositoryInventory)
        assert inventory.total_files > 0
        assert inventory.total_size_bytes > 0
        assert len(inventory.files) > 0
    
    @pytest.mark.asyncio
    async def test_scan_ignores_patterns(self, temp_repo):
        """Test that .git and __pycache__ are ignored."""
        scanner = RepositoryScanner()
        inventory = await scanner.scan(temp_repo)
        
        # Check that ignored patterns are not in results
        file_paths = [str(f.relative_path) for f in inventory.files]
        assert not any(".git" in p for p in file_paths)
        assert not any("__pycache__" in p for p in file_paths)
    
    @pytest.mark.skip(reason="RepositoryScanner._classify_file is private/removed - API has changed")
    def test_classify_file(self):
        """Test file classification."""
        scanner = RepositoryScanner()
        
        # Test code file
        is_code, is_test, is_doc, is_config = scanner._classify_file(
            Path("src/main.py"), "main.py"
        )
        assert is_code is True
        assert is_test is False
        
        # Test test file
        is_code, is_test, is_doc, is_config = scanner._classify_file(
            Path("tests/test_main.py"), "test_main.py"
        )
        assert is_code is True
        assert is_test is True
        
        # Test doc file
        is_code, is_test, is_doc, is_config = scanner._classify_file(
            Path("README.md"), "README.md"
        )
        assert is_doc is True
        assert is_code is False
        
        # Test config file
        is_code, is_test, is_doc, is_config = scanner._classify_file(
            Path("config.json"), "config.json"
        )
        assert is_config is True
    
    def test_detect_language(self):
        """Test language detection."""
        scanner = RepositoryScanner()
        
        assert scanner._detect_language(".py") == "Python"
        assert scanner._detect_language(".js") == "JavaScript"
        assert scanner._detect_language(".go") == "Go"
        assert scanner._detect_language(".rs") == "Rust"
        assert scanner._detect_language(".md") == "Unknown"
    
    def test_should_ignore(self):
        """Test ignore pattern matching."""
        scanner = RepositoryScanner()
        
        assert scanner._should_ignore(Path(".git/config")) is True
        assert scanner._should_ignore(Path("__pycache__/test.pyc")) is True
        assert scanner._should_ignore(Path("node_modules/package.json")) is True
        assert scanner._should_ignore(Path("src/test.py")) is False
    
    @pytest.mark.asyncio
    async def test_scan_empty_directory(self):
        """Test scanning an empty directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = RepositoryScanner()
            inventory = await scanner.scan(Path(tmpdir))
            
            assert inventory.total_files == 0
            assert len(inventory.files) == 0
    
    @pytest.mark.asyncio
    async def test_scan_nonexistent_directory(self):
        """Test scanning a nonexistent directory."""
        scanner = RepositoryScanner()
        
        # Scanner now handles nonexistent paths gracefully
        inventory = await scanner.scan(Path("/nonexistent/path"))
        assert inventory.total_files == 0
    
    @pytest.mark.asyncio
    async def test_file_metadata(self, temp_repo):
        """Test that file metadata is captured correctly."""
        scanner = RepositoryScanner()
        inventory = await scanner.scan(temp_repo)
        
        files = inventory.files
        assert len(files) > 0
        
        # Check first file has required fields
        file_info = files[0]
        assert file_info.path is not None
        assert file_info.size_bytes >= 0
        assert file_info.extension is not None
        assert isinstance(file_info.is_code, bool)
    
    @pytest.mark.asyncio
    async def test_language_detection_in_scan(self, temp_repo):
        """Test that languages are detected during scan."""
        scanner = RepositoryScanner()
        inventory = await scanner.scan(temp_repo)
        
        # Should detect Python files (capitalized)
        assert "Python" in inventory.languages
        assert inventory.languages["Python"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
