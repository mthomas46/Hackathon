"""
Repository Scanner

Scans repository structure and builds file inventory.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Set
from dataclasses import dataclass, asdict
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """File information."""
    path: Path
    relative_path: str
    size_bytes: int
    extension: str
    language: str
    is_code: bool
    is_test: bool
    is_doc: bool
    is_config: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['path'] = str(self.path)
        return data


@dataclass
class RepositoryInventory:
    """Repository inventory."""
    total_files: int
    total_size_bytes: int
    files: List[FileInfo]
    languages: Dict[str, int]  # language -> count
    frameworks: List[str]
    file_types: Dict[str, int]  # extension -> count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'total_files': self.total_files,
            'total_size_bytes': self.total_size_bytes,
            'languages': self.languages,
            'frameworks': self.frameworks,
            'file_types': self.file_types,
            'files': [f.to_dict() for f in self.files]
        }


class RepositoryScanner:
    """
    Scans repository and builds comprehensive inventory.
    
    Integrates with existing GitService for git-based repos.
    """
    
    def __init__(self):
        self.ignore_patterns = {
            # Existing patterns from scanner.py
            ".git", "__pycache__", "node_modules", ".venv", "venv",
            ".pytest_cache", ".mypy_cache", "dist", "build", ".egg-info",
            "htmlcov", ".tox", ".coverage", "*.pyc", ".DS_Store",
            "venv_audit", "venv_hardening", "venv_validation", "demo_venv",
            "test_env", ".idea", ".vscode"
        }
        
        self.code_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
            ".cpp", ".c", ".h", ".hpp", ".cs", ".rb", ".php", ".scala", 
            ".kt", ".swift", ".m", ".mm", ".r", ".R", ".sql", ".sh", ".bash"
        }
        
        self.test_patterns = {"test_", "_test", ".test.", "spec.", ".spec.", "tests/", "test/"}
        
        self.doc_extensions = {".md", ".rst", ".txt", ".adoc", ".org"}
        
        self.config_extensions = {
            ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
            ".env", ".properties", ".xml"
        }
    
    async def scan(self, repo_path: Path) -> RepositoryInventory:
        """
        Scan repository and build inventory.
        
        Args:
            repo_path: Path to repository root
        
        Returns:
            Repository inventory
        """
        logger.info(f"🔍 Scanning repository: {repo_path}")
        
        # Convert to Path if string
        if isinstance(repo_path, str):
            repo_path = Path(repo_path)
        
        files = []
        total_size = 0
        languages = {}
        file_types = {}
        
        # Traverse directory tree
        for file_path in repo_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Skip ignored paths
            if self._should_ignore(file_path):
                continue
            
            try:
                # Get file info
                file_info = await self._analyze_file(file_path, repo_path)
                files.append(file_info)
                
                total_size += file_info.size_bytes
                
                # Update statistics
                languages[file_info.language] = languages.get(file_info.language, 0) + 1
                file_types[file_info.extension] = file_types.get(file_info.extension, 0) + 1
            except Exception as e:
                logger.debug(f"Skipping file {file_path}: {e}")
                continue
        
        # Detect frameworks
        frameworks = await self._detect_frameworks(files)
        
        inventory = RepositoryInventory(
            total_files=len(files),
            total_size_bytes=total_size,
            files=files,
            languages=languages,
            frameworks=frameworks,
            file_types=file_types
        )
        
        logger.info(
            f"✅ Scan complete: {len(files)} files, "
            f"{len(languages)} languages, {total_size / 1024 / 1024:.1f} MB"
        )
        
        return inventory
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        path_str = str(path)
        
        # Check against ignore patterns
        for pattern in self.ignore_patterns:
            if pattern.startswith("*"):
                # Wildcard pattern (e.g., *.pyc)
                if path_str.endswith(pattern[1:]):
                    return True
            else:
                # Exact match or contains
                if pattern in path_str:
                    return True
        
        return False
    
    async def _analyze_file(self, file_path: Path, repo_root: Path) -> FileInfo:
        """Analyze a single file."""
        try:
            relative_path = str(file_path.relative_to(repo_root))
        except ValueError:
            relative_path = str(file_path)
        
        extension = file_path.suffix.lower()
        
        # Determine language
        language = self._detect_language(extension)
        
        # Classify file type
        is_code = extension in self.code_extensions
        is_test = any(pattern in file_path.name.lower() or pattern in relative_path for pattern in self.test_patterns)
        is_doc = extension in self.doc_extensions
        is_config = extension in self.config_extensions
        
        # Get file size
        try:
            size_bytes = file_path.stat().st_size
        except (OSError, PermissionError):
            size_bytes = 0
        
        return FileInfo(
            path=file_path,
            relative_path=relative_path,
            size_bytes=size_bytes,
            extension=extension,
            language=language,
            is_code=is_code,
            is_test=is_test,
            is_doc=is_doc,
            is_config=is_config
        )
    
    def _detect_language(self, extension: str) -> str:
        """Detect programming language from extension."""
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JavaScript",
            ".tsx": "TypeScript",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C/C++",
            ".hpp": "C++",
            ".cs": "C#",
            ".rb": "Ruby",
            ".php": "PHP",
            ".scala": "Scala",
            ".kt": "Kotlin",
            ".swift": "Swift",
            ".m": "Objective-C",
            ".mm": "Objective-C++",
            ".r": "R",
            ".R": "R",
            ".sql": "SQL",
            ".sh": "Shell",
            ".bash": "Shell"
        }
        return language_map.get(extension, "Unknown")
    
    async def _detect_frameworks(self, files: List[FileInfo]) -> List[str]:
        """Detect frameworks used in repository."""
        frameworks = set()
        
        # Check for framework-specific files
        file_names = {f.path.name for f in files}
        
        if "requirements.txt" in file_names or "setup.py" in file_names or "pyproject.toml" in file_names:
            frameworks.add("Python")
        
        if "package.json" in file_names:
            frameworks.add("Node.js")
        
        if "pom.xml" in file_names or "build.gradle" in file_names or "build.gradle.kts" in file_names:
            frameworks.add("Java/Maven/Gradle")
        
        if "go.mod" in file_names:
            frameworks.add("Go Modules")
        
        if "Cargo.toml" in file_names:
            frameworks.add("Rust/Cargo")
        
        if "docker-compose.yml" in file_names or "docker-compose.yaml" in file_names:
            frameworks.add("Docker Compose")
        
        if any("Dockerfile" in name for name in file_names):
            frameworks.add("Docker")
        
        if "Makefile" in file_names:
            frameworks.add("Make")
        
        # Check for specific frameworks in Python files
        python_files = [f for f in files if f.language == "Python"]
        if python_files:
            # Check for FastAPI, Flask, Django (would need to read files)
            # For now, just mark as having Python framework
            pass
        
        return list(frameworks)


# Singleton instance
_scanner_instance = None

def get_repository_scanner() -> RepositoryScanner:
    """Get singleton repository scanner instance."""
    global _scanner_instance
    if _scanner_instance is None:
        _scanner_instance = RepositoryScanner()
    return _scanner_instance

