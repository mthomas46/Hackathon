"""
DRY Principles Analyzer

Analyzes code for adherence to the Don't Repeat Yourself principle.
Identifies code duplication, repetitive patterns, and opportunities for refactoring.
"""

import logging
from typing import Dict, Any, List
from pathlib import Path

from .base_analyzer import BaseAnalyzer
from ..file_system.file_system_service import FileSystemService
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DRYPrinciplesAnalysisResult:
    """Results from DRY principles analysis."""
    score: float
    duplication_score: float
    pattern_score: float
    utility_score: float
    recommendations: list
    issues: list


class DRYPrinciplesAnalyzer(BaseAnalyzer):
    """Analyzer for Don't Repeat Yourself principles."""

    def __init__(self, file_system: FileSystemService):
        """Initialize the DRY principles analyzer."""
        self.file_system = file_system

    async def analyze(self, service_info, full_audit: bool = False) -> Dict[str, Any]:
        """Analyze service for DRY principles compliance."""
        logger.info(f"🔄 Analyzing DRY principles for {service_info.name}")

        try:
            # Get all Python files
            logger.debug(f"🔍 Getting Python files for {service_info.name}")
            python_files = self.file_system.get_service_files(service_info.path, ['.py'])
            logger.debug(f"📁 Found {len(python_files)} Python files")

            # Analyze code duplication
            logger.debug("🔍 Analyzing code duplication...")
            duplication_score = self._analyze_code_duplication(python_files)
            logger.debug(f"✅ Code duplication score: {duplication_score}")

            # Analyze repetitive patterns
            logger.debug("🔍 Analyzing repetitive patterns...")
            pattern_score = self._analyze_repetitive_patterns(python_files)
            logger.debug(f"✅ Pattern score: {pattern_score}")

            # Analyze utility function usage
            logger.debug("🔍 Analyzing utility usage...")
            utility_score = self._analyze_utility_usage(python_files)
            logger.debug(f"✅ Utility score: {utility_score}")

            # Calculate overall DRY score
            overall_score = (duplication_score + pattern_score + utility_score) / 3

            recommendations = []
            if duplication_score < 70:
                recommendations.append("🔄 Extract duplicated code into shared utilities or base classes")
            if pattern_score < 70:
                recommendations.append("📋 Create helper functions for repetitive code patterns")
            if utility_score < 70:
                recommendations.append("🛠️ Consolidate utility functions into dedicated modules")

            return DRYPrinciplesAnalysisResult(
                score=round(overall_score, 2),
                duplication_score=duplication_score,
                pattern_score=pattern_score,
                utility_score=utility_score,
                recommendations=recommendations,
                issues=[]
            )

        except Exception as e:
            logger.error(f"DRY principles analysis failed: {e}")
            return DRYPrinciplesAnalysisResult(
                score=50.0,
                duplication_score=50.0,
                pattern_score=50.0,
                utility_score=50.0,
                recommendations=["Unable to analyze DRY principles due to technical issues"],
                issues=[str(e)]
            )

    def _analyze_code_duplication(self, python_files: List[Path]) -> float:
        """Analyze code for duplication patterns."""
        if not python_files:
            return 100.0

        logger.debug(f"🔍 Processing {min(len(python_files), 20)} files for duplication analysis")
        total_lines = 0
        duplicate_lines = 0

        # Simple line-based duplication detection
        line_counts = {}

        for i, file_path in enumerate(python_files[:20]):  # Limit to first 20 files for performance
            try:
                logger.debug(f"📄 Processing file {i+1}/20: {file_path.name}")

                # Skip files that are too large (>1MB)
                if file_path.stat().st_size > 1024 * 1024:
                    logger.debug(f"⏭️ Skipping large file: {file_path.name} ({file_path.stat().st_size} bytes)")
                    continue

                content = file_path.read_text()
                lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('#')]

                for line in lines:
                    if len(line) > 20:  # Only consider substantial lines
                        line_counts[line] = line_counts.get(line, 0) + 1
                        total_lines += 1

            except Exception as e:
                logger.debug(f"⚠️ Error processing {file_path.name}: {e}")
                continue

        logger.debug(f"📊 Processed {total_lines} lines, found {len(line_counts)} unique substantial lines")

        # Count duplicated lines (appearing more than once)
        for line, count in line_counts.items():
            if count > 1:
                duplicate_lines += count

        if total_lines == 0:
            return 100.0

        duplication_ratio = duplicate_lines / total_lines
        # Lower duplication is better, so invert the score
        return max(0, 100 - (duplication_ratio * 200))  # Penalize heavily for duplication

    def _analyze_repetitive_patterns(self, python_files: List[Path]) -> float:
        """Analyze for repetitive coding patterns."""
        if not python_files:
            return 100.0

        pattern_score = 100.0
        issues_found = 0

        for file_path in python_files[:10]:  # Limit for performance
            try:
                # Skip files that are too large (>1MB)
                if file_path.stat().st_size > 1024 * 1024:
                    continue

                content = file_path.read_text()

                # Check for repetitive patterns using simple string counts
                pattern_checks = [
                    ('if ', 'Conditional statements'),
                    ('for ', 'Loop statements'),
                    ('try:', 'Exception handling'),
                    ('return ', 'Return statements'),
                ]

                for pattern, description in pattern_checks:
                    count = content.count(pattern)
                    if count > 20:  # Too many similar patterns
                        issues_found += 1
                        pattern_score -= 5

            except Exception:
                continue

        return max(0, pattern_score - (issues_found * 10))

    def _analyze_utility_usage(self, python_files: List[Path]) -> float:
        """Analyze usage of utility functions vs inline code."""
        if not python_files:
            return 100.0

        utility_indicators = 0
        total_files = 0

        for file_path in python_files[:15]:  # Limit for performance
            try:
                # Skip files that are too large (>1MB)
                if file_path.stat().st_size > 1024 * 1024:
                    continue

                content = file_path.read_text()
                total_files += 1

                # Look for utility function usage indicators using simple string checks
                indicators = [
                    'from utils import',
                    'from helpers import',
                    'from common import',
                    'import utils',
                    'import helpers',
                    'import common',
                ]

                for indicator in indicators:
                    if indicator in content:
                        utility_indicators += 1
                        break

            except Exception:
                continue

        if total_files == 0:
            return 100.0

        utility_ratio = utility_indicators / total_files
        return min(100, utility_ratio * 150)  # Bonus for utility usage
