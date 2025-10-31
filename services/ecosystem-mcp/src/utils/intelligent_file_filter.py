"""
Intelligent File Filtering System

Automatically filters and prioritizes files for ingestion based on:
- File type and extension
- Directory patterns
- Content value (documentation vs code vs config)
- Size and complexity
- Business rules

Goals:
- Skip low-value files (logs, configs, binaries)
- Prioritize high-value files (docs, READMEs, code)
- Reduce noise in RAG
- Maximize unique content value
"""

import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class FilePriority(Enum):
    """File priority levels for ingestion."""
    CRITICAL = 100    # README, main docs, architecture
    HIGH = 75         # Documentation, guides
    MEDIUM = 50       # Source code, scripts
    LOW = 25          # Tests, examples
    SKIP = 0          # Logs, configs, temp files


class FileCategory(Enum):
    """File categories for classification."""
    DOCUMENTATION = "documentation"
    SOURCE_CODE = "source_code"
    CONFIGURATION = "configuration"
    DATA = "data"
    BUILD_ARTIFACT = "build_artifact"
    TEST = "test"
    EXAMPLE = "example"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


@dataclass
class FileFilterRule:
    """A rule for filtering/prioritizing files."""
    pattern: str              # Glob pattern or directory name
    priority: FilePriority
    category: FileCategory
    reason: str              # Human-readable reason
    
    def matches(self, path: Path) -> bool:
        """Check if path matches this rule."""
        path_str = str(path).lower()
        pattern_lower = self.pattern.lower()
        
        # Directory pattern (e.g., "docs/")
        if self.pattern.endswith('/'):
            return pattern_lower.rstrip('/') in path_str
        
        # File extension (e.g., ".log")
        if self.pattern.startswith('.'):
            return path.suffix.lower() == pattern_lower
        
        # Filename pattern (e.g., "README")
        if '/' not in self.pattern:
            return pattern_lower in path.name.lower()
        
        # Full path pattern
        return pattern_lower in path_str


class IntelligentFileFilter:
    """
    Intelligent file filtering with prioritization.
    
    Features:
    - Automatic file classification
    - Priority-based ordering
    - Configurable rules
    - Smart defaults for common patterns
    """
    
    def __init__(self, custom_rules: Optional[List[FileFilterRule]] = None):
        """
        Initialize filter with default + custom rules.
        
        Args:
            custom_rules: Additional custom rules to apply
        """
        self.rules = self._build_default_rules()
        if custom_rules:
            self.rules.extend(custom_rules)
        
        logger.info(f"Intelligent file filter initialized with {len(self.rules)} rules")
    
    def _build_default_rules(self) -> List[FileFilterRule]:
        """Build comprehensive default filtering rules."""
        
        rules = []
        
        # ============================================================
        # CRITICAL PRIORITY (Process First)
        # ============================================================
        
        # READMEs
        rules.extend([
            FileFilterRule("README.md", FilePriority.CRITICAL, FileCategory.DOCUMENTATION, 
                          "Main project documentation"),
            FileFilterRule("README", FilePriority.CRITICAL, FileCategory.DOCUMENTATION,
                          "Main project documentation"),
            FileFilterRule("readme.md", FilePriority.CRITICAL, FileCategory.DOCUMENTATION,
                          "Main project documentation"),
        ])
        
        # Architecture & Design
        rules.extend([
            FileFilterRule("ARCHITECTURE", FilePriority.CRITICAL, FileCategory.DOCUMENTATION,
                          "System architecture"),
            FileFilterRule("DESIGN", FilePriority.CRITICAL, FileCategory.DOCUMENTATION,
                          "System design"),
            FileFilterRule("/architecture/", FilePriority.CRITICAL, FileCategory.DOCUMENTATION,
                          "Architecture documentation"),
        ])
        
        # ============================================================
        # HIGH PRIORITY (Documentation)
        # ============================================================
        
        # Documentation directories
        rules.extend([
            FileFilterRule("docs/", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "Documentation directory"),
            FileFilterRule("doc/", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "Documentation directory"),
            FileFilterRule("documentation/", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "Documentation directory"),
            FileFilterRule("/guides/", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "User guides"),
            FileFilterRule("/tutorials/", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "Tutorials"),
        ])
        
        # Documentation files
        rules.extend([
            FileFilterRule(".md", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "Markdown documentation"),
            FileFilterRule(".rst", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "reStructuredText documentation"),
            FileFilterRule(".adoc", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "AsciiDoc documentation"),
        ])
        
        # Changelogs & Release Notes
        rules.extend([
            FileFilterRule("CHANGELOG", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "Change history"),
            FileFilterRule("HISTORY", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "Project history"),
            FileFilterRule("RELEASE", FilePriority.HIGH, FileCategory.DOCUMENTATION,
                          "Release notes"),
        ])
        
        # ============================================================
        # MEDIUM PRIORITY (Source Code)
        # ============================================================
        
        # Source code by language
        rules.extend([
            FileFilterRule(".py", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "Python source"),
            FileFilterRule(".js", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "JavaScript source"),
            FileFilterRule(".ts", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "TypeScript source"),
            FileFilterRule(".java", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "Java source"),
            FileFilterRule(".go", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "Go source"),
            FileFilterRule(".rs", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "Rust source"),
            FileFilterRule(".cpp", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "C++ source"),
            FileFilterRule(".c", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "C source"),
            FileFilterRule(".h", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "C/C++ header"),
        ])
        
        # API definitions
        rules.extend([
            FileFilterRule(".graphql", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "GraphQL schema"),
            FileFilterRule(".proto", FilePriority.MEDIUM, FileCategory.SOURCE_CODE,
                          "Protocol buffer"),
            FileFilterRule("openapi", FilePriority.MEDIUM, FileCategory.DOCUMENTATION,
                          "OpenAPI specification"),
        ])
        
        # ============================================================
        # LOW PRIORITY (Tests, Examples, Data)
        # ============================================================
        
        # Tests
        rules.extend([
            FileFilterRule("/tests/", FilePriority.LOW, FileCategory.TEST,
                          "Test files (low priority for RAG)"),
            FileFilterRule("/test/", FilePriority.LOW, FileCategory.TEST,
                          "Test files (low priority for RAG)"),
            FileFilterRule("_test.py", FilePriority.LOW, FileCategory.TEST,
                          "Python test"),
            FileFilterRule(".test.js", FilePriority.LOW, FileCategory.TEST,
                          "JavaScript test"),
            FileFilterRule(".spec.ts", FilePriority.LOW, FileCategory.TEST,
                          "TypeScript spec"),
        ])
        
        # Examples & Demos
        rules.extend([
            FileFilterRule("/examples/", FilePriority.LOW, FileCategory.EXAMPLE,
                          "Example code"),
            FileFilterRule("/demo/", FilePriority.LOW, FileCategory.EXAMPLE,
                          "Demo code"),
            FileFilterRule("/sample/", FilePriority.LOW, FileCategory.EXAMPLE,
                          "Sample code"),
        ])
        
        # ============================================================
        # SKIP (Do Not Process)
        # ============================================================
        
        # Logs
        rules.extend([
            FileFilterRule(".log", FilePriority.SKIP, FileCategory.TEMPORARY,
                          "Log file"),
            FileFilterRule("/logs/", FilePriority.SKIP, FileCategory.TEMPORARY,
                          "Log directory"),
            FileFilterRule(".out", FilePriority.SKIP, FileCategory.TEMPORARY,
                          "Output file"),
        ])
        
        # Configuration (low value for RAG)
        rules.extend([
            FileFilterRule(".env", FilePriority.SKIP, FileCategory.CONFIGURATION,
                          "Environment config (skip for security)"),
            FileFilterRule(".ini", FilePriority.SKIP, FileCategory.CONFIGURATION,
                          "INI config (low RAG value)"),
            FileFilterRule(".cfg", FilePriority.SKIP, FileCategory.CONFIGURATION,
                          "Config file (low RAG value)"),
            FileFilterRule(".conf", FilePriority.SKIP, FileCategory.CONFIGURATION,
                          "Config file (low RAG value)"),
            FileFilterRule("config.json", FilePriority.SKIP, FileCategory.CONFIGURATION,
                          "Config file"),
            FileFilterRule("settings.json", FilePriority.SKIP, FileCategory.CONFIGURATION,
                          "Settings file"),
        ])
        
        # Build artifacts
        rules.extend([
            FileFilterRule("/dist/", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Build output"),
            FileFilterRule("/build/", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Build output"),
            FileFilterRule("/target/", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Build output"),
            FileFilterRule("/__pycache__/", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Python cache"),
            FileFilterRule("/node_modules/", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Node dependencies"),
            FileFilterRule(".pyc", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Python bytecode"),
            FileFilterRule(".class", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Java bytecode"),
        ])
        
        # Package lock files
        rules.extend([
            FileFilterRule("package-lock.json", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Package lock (auto-generated)"),
            FileFilterRule("yarn.lock", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Yarn lock (auto-generated)"),
            FileFilterRule("poetry.lock", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Poetry lock (auto-generated)"),
            FileFilterRule("Pipfile.lock", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Pipfile lock (auto-generated)"),
        ])
        
        # Virtual environments
        rules.extend([
            FileFilterRule("/venv/", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Virtual environment"),
            FileFilterRule("/.venv/", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Virtual environment"),
            FileFilterRule("/env/", FilePriority.SKIP, FileCategory.BUILD_ARTIFACT,
                          "Environment directory"),
        ])
        
        # Data files (large, low RAG value)
        rules.extend([
            FileFilterRule(".csv", FilePriority.SKIP, FileCategory.DATA,
                          "CSV data (large, low RAG value)"),
            FileFilterRule(".parquet", FilePriority.SKIP, FileCategory.DATA,
                          "Parquet data"),
            FileFilterRule(".db", FilePriority.SKIP, FileCategory.DATA,
                          "Database file"),
            FileFilterRule(".sqlite", FilePriority.SKIP, FileCategory.DATA,
                          "SQLite database"),
        ])
        
        # Git & IDE
        rules.extend([
            FileFilterRule("/.git/", FilePriority.SKIP, FileCategory.TEMPORARY,
                          "Git internal"),
            FileFilterRule("/.idea/", FilePriority.SKIP, FileCategory.TEMPORARY,
                          "IDE settings"),
            FileFilterRule("/.vscode/", FilePriority.SKIP, FileCategory.TEMPORARY,
                          "VSCode settings"),
            FileFilterRule(".DS_Store", FilePriority.SKIP, FileCategory.TEMPORARY,
                          "macOS metadata"),
        ])
        
        return rules
    
    def classify_file(self, path: Path) -> Tuple[FilePriority, FileCategory, str]:
        """
        Classify a file and determine its priority.
        
        Args:
            path: File path to classify
        
        Returns:
            Tuple of (priority, category, reason)
        """
        # Check each rule in order (first match wins)
        for rule in self.rules:
            if rule.matches(path):
                logger.debug(
                    f"File {path.name}: {rule.priority.name} "
                    f"({rule.category.value}) - {rule.reason}"
                )
                return rule.priority, rule.category, rule.reason
        
        # Default: LOW priority for unrecognized files
        return FilePriority.LOW, FileCategory.UNKNOWN, "Unrecognized file type"
    
    def should_process(self, path: Path) -> bool:
        """
        Determine if file should be processed.
        
        Args:
            path: File path
        
        Returns:
            True if file should be processed, False if should skip
        """
        priority, category, reason = self.classify_file(path)
        
        if priority == FilePriority.SKIP:
            logger.debug(f"⏭️  Skipping {path.name}: {reason}")
            return False
        
        return True
    
    def filter_and_prioritize(
        self,
        files: List[Path],
        max_files: Optional[int] = None
    ) -> List[Path]:
        """
        Filter and sort files by priority.
        
        Args:
            files: List of file paths
            max_files: Maximum files to return (None = all)
        
        Returns:
            Sorted list of files (highest priority first)
        """
        logger.info(f"Filtering {len(files)} files...")
        
        # Classify all files
        classified = []
        for path in files:
            priority, category, reason = self.classify_file(path)
            
            if priority != FilePriority.SKIP:
                classified.append((path, priority, category, reason))
        
        # Sort by priority (descending)
        classified.sort(key=lambda x: x[1].value, reverse=True)
        
        # Extract just the paths
        filtered = [item[0] for item in classified]
        
        # Log statistics
        stats = {}
        for _, priority, _, _ in classified:
            stats[priority.name] = stats.get(priority.name, 0) + 1
        
        logger.info(f"✅ Filtered to {len(filtered)} files (from {len(files)})")
        logger.info(f"   Priority breakdown: {stats}")
        
        # Apply max_files limit if specified
        if max_files and len(filtered) > max_files:
            logger.info(f"   Limiting to top {max_files} files")
            filtered = filtered[:max_files]
        
        return filtered
    
    def get_statistics(self, files: List[Path]) -> Dict[str, any]:
        """
        Get filtering statistics for a list of files.
        
        Args:
            files: List of file paths
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "total": len(files),
            "by_priority": {},
            "by_category": {},
            "would_skip": 0,
            "would_process": 0
        }
        
        for path in files:
            priority, category, _ = self.classify_file(path)
            
            # Count by priority
            stats["by_priority"][priority.name] = \
                stats["by_priority"].get(priority.name, 0) + 1
            
            # Count by category
            stats["by_category"][category.value] = \
                stats["by_category"].get(category.value, 0) + 1
            
            # Count skip vs process
            if priority == FilePriority.SKIP:
                stats["would_skip"] += 1
            else:
                stats["would_process"] += 1
        
        return stats


# ============================================================
# Convenience Functions
# ============================================================

def get_intelligent_filter(custom_rules: Optional[List[FileFilterRule]] = None) -> IntelligentFileFilter:
    """
    Get an intelligent file filter instance.
    
    Args:
        custom_rules: Optional custom rules
    
    Returns:
        IntelligentFileFilter instance
    """
    return IntelligentFileFilter(custom_rules)


def create_custom_rule(
    pattern: str,
    priority: str,
    category: str,
    reason: str
) -> FileFilterRule:
    """
    Create a custom filtering rule.
    
    Args:
        pattern: File pattern to match
        priority: Priority level ("CRITICAL", "HIGH", "MEDIUM", "LOW", "SKIP")
        category: Category name
        reason: Human-readable reason
    
    Returns:
        FileFilterRule instance
    """
    return FileFilterRule(
        pattern=pattern,
        priority=FilePriority[priority],
        category=FileCategory[category],
        reason=reason
    )

