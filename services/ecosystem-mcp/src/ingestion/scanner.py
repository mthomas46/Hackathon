"""
Document scanner for discovering files in the repository.

Supports multiple modes of scanning with filtering.
"""

import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)


class DocumentScanner:
    """
    Scans repository for documents to ingest.
    
    Supports filtering by extension, path patterns, and .gitignore rules.
    """
    
    # File extensions to scan
    DEFAULT_EXTENSIONS = {
        ".md",
        ".py",
        ".yaml",
        ".yml",
        ".json",
        ".txt",
        ".rst",
        ".toml",
    }
    
    # Directories to ignore
    IGNORE_DIRS = {
        ".git",
        "__pycache__",
        "venv",
        "venv_*",
        "node_modules",
        ".pytest_cache",
        "htmlcov",
        ".mypy_cache",
        "build",
        "dist",
        "*.egg-info",
    }
    
    def __init__(self, repo_path: str | Path):
        """
        Initialize scanner.
        
        Args:
            repo_path: Path to repository root
        """
        self.repo_path = Path(repo_path)
        
        if not self.repo_path.exists():
            from ..utils.exceptions import IngestionError
            raise IngestionError(f"Repository path does not exist: {self.repo_path}")
        
        logger.info(f"Document scanner initialized: {self.repo_path}")
    
    def scan_markdown_only(self) -> List[Path]:
        """
        Scan for .md files only (Mode 1: Quick).
        
        Returns:
            List of markdown file paths
        """
        logger.info("Scanning for markdown files only")
        return self._scan_by_extensions({".md"})
    
    def scan_all_supported(self) -> List[Path]:
        """
        Scan for all supported file types (Mode 2: Standard).
        
        Returns:
            List of file paths
        """
        logger.info("Scanning for all supported file types")
        return self._scan_by_extensions(self.DEFAULT_EXTENSIONS)
    
    def scan_by_extensions(self, extensions: Set[str]) -> List[Path]:
        """
        Scan for files with specific extensions.
        
        Args:
            extensions: Set of file extensions (e.g., {".md", ".py"})
        
        Returns:
            List of matching file paths
        """
        return self._scan_by_extensions(extensions)
    
    def _scan_by_extensions(self, extensions: Set[str]) -> List[Path]:
        """
        Internal method to scan for files.
        
        Args:
            extensions: Set of file extensions
        
        Returns:
            List of file paths
        """
        files: List[Path] = []
        
        for path in self.repo_path.rglob("*"):
            # Skip directories
            if path.is_dir():
                continue
            
            # Skip ignored directories
            if self._should_ignore_path(path):
                continue
            
            # Check extension
            if path.suffix.lower() in extensions:
                files.append(path)
        
        logger.info(f"Found {len(files)} files")
        return sorted(files)
    
    def _should_ignore_path(self, path: Path) -> bool:
        """
        Check if path should be ignored.
        
        Args:
            path: File path
        
        Returns:
            True if should be ignored
        """
        # Check if any parent directory matches ignore patterns
        for parent in path.parents:
            for ignore_pattern in self.IGNORE_DIRS:
                if parent.name == ignore_pattern or parent.match(ignore_pattern):
                    return True
        
        return False
    
    def get_relative_path(self, file_path: Path) -> str:
        """
        Get path relative to repository root.
        
        Args:
            file_path: Absolute or relative file path
        
        Returns:
            Relative path string
        """
        try:
            return str(file_path.relative_to(self.repo_path))
        except ValueError:
            # If path is not relative to repo, return as-is
            return str(file_path)
    
    def extract_service_name(self, file_path: Path) -> str:
        """
        Extract service name from file path.
        
        Assumes structure: services/{service-name}/...
        
        Args:
            file_path: File path
        
        Returns:
            Service name or "unknown"
        """
        relative = self.get_relative_path(file_path)
        parts = Path(relative).parts
        
        # Check if in services directory
        if len(parts) >= 2 and parts[0] == "services":
            return parts[1]
        
        # Default
        return "unknown"

