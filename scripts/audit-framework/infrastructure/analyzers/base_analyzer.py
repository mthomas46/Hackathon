"""
Base Analyzer Class for DDD Compliance

Provides common functionality for all analyzers to follow DRY principles.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio
import logging

from domain.entities.service_info import ServiceInfo
from domain.value_objects.audit_profile import AuditProfile
from config.thresholds import get_thresholds_for_profile

logger = logging.getLogger(__name__)

class BaseAnalyzer(ABC):
    """Base class for all analyzers providing common functionality."""
    
    def __init__(self, profile: AuditProfile):
        self.profile = profile
        self.thresholds = get_thresholds_for_profile(profile)
        self._full_audit = False
    
    @abstractmethod
    async def analyze(self, service: ServiceInfo, full_audit: bool = False) -> Any:
        """Analyze the service and return results."""
        pass
    
    def set_full_audit_mode(self, full_audit: bool):
        """Set whether this analyzer should run in full audit mode."""
        self._full_audit = full_audit
    
    async def _get_python_files(self, service: ServiceInfo, include_tests: bool = True) -> List[Path]:
        """Get all Python files in the service, with optional test filtering."""
        python_files = []
        for root, dirs, files in service.path.walk():
            for file in files:
                if file.endswith('.py'):
                    file_path = root / file
                    # Skip test files unless explicitly requested
                    if not include_tests and ('test' in file.lower() or 'tests' in str(root).lower()):
                        continue
                    # Skip common non-source files
                    if file.startswith('.') or file.startswith('__'):
                        continue
                    python_files.append(file_path)
        return python_files
    
    async def _analyze_file_safely(self, file_path: Path) -> Optional[str]:
        """Safely read a file with error handling."""
        try:
            return file_path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Could not read file {file_path}: {e}")
            return None
    
    async def _get_file_line_count(self, file_path: Path) -> int:
        """Get the line count of a file."""
        try:
            content = await self._analyze_file_safely(file_path)
            return len(content.splitlines()) if content else 0
        except Exception:
            return 0
    
    def _is_oversized_file(self, line_count: int) -> bool:
        """Check if a file is oversized based on thresholds."""
        max_lines = self.thresholds.get('file_limits', {}).get('max_lines_per_file', 800)
        return line_count > max_lines
    
    async def _analyze_test_quality_metrics(self, service: ServiceInfo) -> Dict[str, Any]:
        """Common test quality analysis across analyzers."""
        # This is duplicated across multiple analyzers - should be here
        test_files = await self._get_python_files(service, include_tests=True)
        test_files = [f for f in test_files if 'test' in f.name.lower() or 'tests' in str(f.parent).lower()]
        
        return {
            'test_files_count': len(test_files),
            'test_files': [str(f.relative_to(service.path)) for f in test_files[:10]],  # Limit for brevity
            'has_test_directory': any('tests' in str(f.parent) for f in test_files),
            'test_file_ratio': len(test_files) / max(1, len(await self._get_python_files(service, include_tests=False)))
        }
    
    async def _analyze_linting_quality(self, service: ServiceInfo) -> Dict[str, Any]:
        """Common linting quality analysis."""
        # This should be standardized across analyzers
        python_files = await self._get_python_files(service, include_tests=False)
        
        # Basic linting checks that can be done without external tools
        issues = {
            'missing_docstrings': 0,
            'long_lines': 0,
            'trailing_whitespace': 0,
            'inconsistent_imports': 0
        }
        
        for file_path in python_files[:50]:  # Limit for performance
            content = await self._analyze_file_safely(file_path)
            if not content:
                continue
                
            lines = content.split('\n')
            
            # Check for long lines
            for line in lines:
                if len(line) > 88:  # PEP8 recommended line length
                    issues['long_lines'] += 1
            
            # Check for trailing whitespace
            for line in lines:
                if line.rstrip() != line:
                    issues['trailing_whitespace'] += 1
            
            # Check for missing docstrings (basic check)
            if 'def ' in content and '"""' not in content and "'''" not in content:
                issues['missing_docstrings'] += 1
        
        return {
            'total_issues': sum(issues.values()),
            'issues_by_type': issues,
            'files_analyzed': min(len(python_files), 50),
            'recommendations': [
                "Fix long lines (>88 characters)" if issues['long_lines'] > 0 else None,
                "Remove trailing whitespace" if issues['trailing_whitespace'] > 0 else None,
                "Add docstrings to functions" if issues['missing_docstrings'] > 0 else None,
            ]
        }
    
    def _add_detailed_issue(self, issue_type: str, file_path: str, 
                           line_number: Optional[int] = None,
                           line_block: Optional[str] = None, 
                           description: str = "",
                           severity: str = "warning", 
                           dimension: str = "general"):
        """Add a detailed issue - should be implemented by subclasses."""
        # This is a placeholder - subclasses should implement their own issue tracking
        pass
