"""
FileSystemService - Infrastructure Service

Handles file system operations for the audit framework,
providing a clean interface for reading service files and directories.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)


class FileSystemService:
    """Infrastructure service for file system operations.

    Provides abstracted file system access for the audit framework,
    handling service directory traversal and file operations.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the file system service.

        Args:
            base_path: Base path for file operations (defaults to current directory)
        """
        self.base_path = base_path or Path.cwd()

    def get_service_files(
        self,
        service_path: Path,
        extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[Path]:
        """Get all relevant files for a service.

        Args:
            service_path: Path to the service directory
            extensions: File extensions to include (default: ['.py'])
            exclude_patterns: Patterns to exclude (default: test and cache files)

        Returns:
            List of file paths
        """
        if extensions is None:
            extensions = ['.py']

        if exclude_patterns is None:
            exclude_patterns = ['__pycache__', 'test_', '.git', 'node_modules']

        files = []

        try:
            for root, dirs, filenames in os.walk(service_path):
                # Filter directories
                dirs[:] = [
                    d for d in dirs
                    if not any(pattern in d for pattern in exclude_patterns)
                ]

                for filename in filenames:
                    # Check extension
                    if any(filename.endswith(ext) for ext in extensions):
                        # Check exclude patterns
                        if not any(pattern in filename for pattern in exclude_patterns):
                            files.append(Path(root) / filename)

        except (OSError, PermissionError) as e:
            logger.warning(f"Error accessing service path {service_path}: {e}")

        return files

    def read_file_content(self, file_path: Path) -> Optional[str]:
        """Read content from a file.

        Args:
            file_path: Path to the file

        Returns:
            File content as string, or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (IOError, OSError, UnicodeDecodeError) as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            return None

    def get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get metadata about a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file metadata
        """
        try:
            stat = file_path.stat()
            return {
                'path': str(file_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'exists': True,
                'is_file': file_path.is_file(),
                'extension': file_path.suffix,
                'name': file_path.name,
            }
        except (OSError, AttributeError) as e:
            logger.warning(f"Error getting file info for {file_path}: {e}")
            return {
                'path': str(file_path),
                'exists': False,
                'error': str(e),
            }

    def find_files_by_pattern(
        self,
        directory: Path,
        pattern: str,
        case_sensitive: bool = False
    ) -> List[Path]:
        """Find files matching a pattern.

        Args:
            directory: Directory to search in
            pattern: Pattern to match (supports wildcards)
            case_sensitive: Whether pattern matching is case sensitive

        Returns:
            List of matching file paths
        """
        import fnmatch

        matches = []

        try:
            for root, dirs, files in os.walk(directory):
                for filename in files:
                    if case_sensitive:
                        if fnmatch.fnmatch(filename, pattern):
                            matches.append(Path(root) / filename)
                    else:
                        if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                            matches.append(Path(root) / filename)

        except (OSError, PermissionError) as e:
            logger.warning(f"Error searching directory {directory}: {e}")

        return matches

    def get_directory_structure(self, directory: Path, max_depth: int = 3) -> Dict[str, Any]:
        """Get directory structure as a nested dictionary.

        Args:
            directory: Directory to analyze
            max_depth: Maximum depth to traverse

        Returns:
            Nested dictionary representing directory structure
        """
        def _build_structure(path: Path, current_depth: int) -> Dict[str, Any]:
            if current_depth > max_depth:
                return {'type': 'directory', 'truncated': True}

            try:
                structure = {'type': 'directory', 'children': {}}

                for item in path.iterdir():
                    if item.is_file():
                        structure['children'][item.name] = {
                            'type': 'file',
                            'size': item.stat().st_size,
                            'extension': item.suffix,
                        }
                    elif item.is_dir() and not item.name.startswith('.'):
                        structure['children'][item.name] = _build_structure(item, current_depth + 1)

                return structure

            except (OSError, PermissionError) as e:
                logger.warning(f"Error reading directory {path}: {e}")
                return {'type': 'directory', 'error': str(e)}

        return _build_structure(directory, 0)

    def validate_service_structure(self, service_path: Path) -> Dict[str, Any]:
        """Validate that a service has expected structure.

        Args:
            service_path: Path to the service

        Returns:
            Validation results
        """
        validation = {
            'is_valid': True,
            'issues': [],
            'structure_score': 100,
        }

        # Check for required files
        required_files = ['main.py', 'requirements.txt', 'README.md']
        for required_file in required_files:
            if not (service_path / required_file).exists():
                validation['issues'].append(f"Missing required file: {required_file}")
                validation['structure_score'] -= 10

        # Check for common structure patterns
        has_src = (service_path / 'src').exists()
        has_domain = (service_path / 'domain').exists() or (service_path / 'src' / 'domain').exists()

        if has_domain:
            validation['issues'].append("✅ Domain-driven structure detected")
        else:
            validation['issues'].append("ℹ️ Consider adopting domain-driven structure")

        if len(validation['issues']) > 2:  # More than just informational messages
            validation['is_valid'] = False

        return validation
