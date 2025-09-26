"""
Documentation Quality Analyzer

Analyzes documentation quality including docstrings, README files, and inline comments.
Evaluates completeness, clarity, and maintenance of documentation.
"""

import logging
import re
from typing import Dict, Any, List
from pathlib import Path

from .base_analyzer import BaseAnalyzer
from ..file_system.file_system_service import FileSystemService
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentationAnalysisResult:
    """Results from documentation quality analysis."""
    score: float
    docstring_score: float
    readme_score: float
    comment_score: float
    recommendations: list
    issues: list


class DocumentationAnalyzer(BaseAnalyzer):
    """Analyzer for documentation quality."""

    def __init__(self, file_system: FileSystemService):
        """Initialize the documentation analyzer."""
        self.file_system = file_system

    async def analyze(self, service_info, full_audit: bool = False) -> Dict[str, Any]:
        """Analyze service for documentation quality."""
        logger.info(f"📚 Analyzing documentation quality for {service_info.name}")

        try:
            # Get all Python files
            python_files = self.file_system.get_service_files(service_info.path, ['.py'])

            # Analyze docstring coverage
            docstring_score = self._analyze_docstring_coverage(python_files)

            # Analyze README quality
            readme_score = self._analyze_readme_quality(service_info.path)

            # Analyze comment quality
            comment_score = self._analyze_comment_quality(python_files)

            # Calculate overall documentation score
            overall_score = (docstring_score + readme_score + comment_score) / 3

            recommendations = []
            if docstring_score < 70:
                recommendations.append("📝 Add comprehensive docstrings to all public functions and classes")
            if readme_score < 70:
                recommendations.append("📖 Create or improve README.md with usage examples and API documentation")
            if comment_score < 70:
                recommendations.append("💬 Add meaningful comments explaining complex logic and business rules")

            return DocumentationAnalysisResult(
                score=round(overall_score, 2),
                docstring_score=docstring_score,
                readme_score=readme_score,
                comment_score=comment_score,
                recommendations=recommendations,
                issues=[]
            )

        except Exception as e:
            logger.error(f"Documentation analysis failed: {e}")
            return DocumentationAnalysisResult(
                score=50.0,
                docstring_score=50.0,
                readme_score=50.0,
                comment_score=50.0,
                recommendations=["Unable to analyze documentation due to technical issues"],
                issues=[str(e)]
            )

    def _analyze_docstring_coverage(self, python_files: List[Path]) -> float:
        """Analyze docstring coverage in Python files."""
        if not python_files:
            return 100.0

        total_functions = 0
        documented_functions = 0

        for file_path in python_files[:20]:  # Limit for performance
            try:
                content = file_path.read_text()

                # Find function and class definitions
                functions = re.findall(r'\bdef\s+\w+\s*\(', content)
                classes = re.findall(r'\bclass\s+\w+', content)

                total_functions += len(functions) + len(classes)

                # Check for docstrings
                for func in functions:
                    func_start = content.find(func)
                    if func_start == -1:
                        continue

                    # Look for docstring after function definition
                    func_section = content[func_start:func_start + 500]  # Check next 500 chars
                    if '"""' in func_section or "'''" in func_section:
                        documented_functions += 1

                for cls in classes:
                    class_start = content.find(cls)
                    if class_start == -1:
                        continue

                    # Look for docstring after class definition
                    class_section = content[class_start:class_start + 500]
                    if '"""' in class_section or "'''" in class_section:
                        documented_functions += 1

            except Exception:
                continue

        if total_functions == 0:
            return 100.0

        coverage_ratio = documented_functions / total_functions
        return min(100, coverage_ratio * 120)  # Slight bonus for good coverage

    def _analyze_readme_quality(self, service_path: Path) -> float:
        """Analyze README quality."""
        readme_files = ['README.md', 'README.rst', 'README.txt', 'readme.md']

        readme_score = 0

        for readme_file in readme_files:
            readme_path = service_path / readme_file
            if readme_path.exists():
                try:
                    content = readme_path.read_text().lower()

                    # Check for key sections
                    sections = [
                        'description', 'install', 'usage', 'api', 'contributing',
                        'license', 'examples', 'requirements', 'documentation'
                    ]

                    section_score = 0
                    for section in sections:
                        if section in content:
                            section_score += 1

                    # Content quality indicators
                    if len(content) > 500:
                        section_score += 2  # Substantial content
                    if '#' in content:
                        section_score += 1  # Uses markdown headers
                    if '```' in content:
                        section_score += 1  # Has code examples

                    readme_score = min(100, (section_score / 12) * 100)

                except Exception:
                    readme_score = 20.0
                break

        if readme_score == 0:
            readme_score = 10.0  # Penalty for no README

        return readme_score

    def _analyze_comment_quality(self, python_files: List[Path]) -> float:
        """Analyze comment quality in Python files."""
        if not python_files:
            return 100.0

        total_lines = 0
        comment_lines = 0
        meaningful_comments = 0

        for file_path in python_files[:15]:  # Limit for performance
            try:
                content = file_path.read_text()
                lines = content.split('\n')

                for line in lines:
                    stripped = line.strip()
                    total_lines += 1

                    if stripped.startswith('#'):
                        comment_lines += 1

                        # Check for meaningful comments (not just TODO/FIXME)
                        comment_text = stripped[1:].strip().lower()
                        if len(comment_text) > 10 and not any(word in comment_text for word in ['todo', 'fixme', 'hack', 'xxx']):
                            meaningful_comments += 1

            except Exception:
                continue

        if total_lines == 0:
            return 100.0

        comment_ratio = comment_lines / total_lines
        meaningful_ratio = meaningful_comments / max(1, comment_lines)

        # Balanced score: some comments are good, but not too many
        if comment_ratio > 0.3:  # Too many comments
            comment_score = 60
        elif comment_ratio > 0.1:  # Good amount
            comment_score = 100
        elif comment_ratio > 0.05:  # Some comments
            comment_score = 80
        else:  # Too few comments
            comment_score = 40

        # Quality bonus
        quality_bonus = meaningful_ratio * 20

        return min(100, comment_score + quality_bonus)
