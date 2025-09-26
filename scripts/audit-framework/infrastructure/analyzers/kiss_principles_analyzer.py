"""
KISS Principles Analyzer

Analyzes code for adherence to the Keep It Simple, Stupid principle.
Identifies overly complex code, nested structures, and opportunities for simplification.
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
class KISSPrinciplesAnalysisResult:
    """Results from KISS principles analysis."""
    score: float
    complexity_score: float
    nesting_score: float
    function_score: float
    recommendations: list
    issues: list


class KISSPrinciplesAnalyzer(BaseAnalyzer):
    """Analyzer for Keep It Simple, Stupid principles."""

    def __init__(self, file_system: FileSystemService):
        """Initialize the KISS principles analyzer."""
        self.file_system = file_system

    async def analyze(self, service_info, full_audit: bool = False) -> Dict[str, Any]:
        """Analyze service for KISS principles compliance."""
        logger.info(f"🎯 Analyzing KISS principles for {service_info.name}")

        try:
            # Get all Python files
            python_files = self.file_system.get_service_files(service_info.path, ['.py'])

            # Analyze code complexity
            complexity_score = self._analyze_code_complexity(python_files)

            # Analyze nesting levels
            nesting_score = self._analyze_nesting_levels(python_files)

            # Analyze function lengths
            function_score = self._analyze_function_lengths(python_files)

            # Calculate overall KISS score
            overall_score = (complexity_score + nesting_score + function_score) / 3

            recommendations = []
            if complexity_score < 70:
                recommendations.append("🔧 Simplify complex conditional logic and nested expressions")
            if nesting_score < 70:
                recommendations.append("📦 Reduce nesting levels by extracting methods or early returns")
            if function_score < 70:
                recommendations.append("✂️ Break down long functions into smaller, focused methods")

            return KISSPrinciplesAnalysisResult(
                score=round(overall_score, 2),
                complexity_score=complexity_score,
                nesting_score=nesting_score,
                function_score=function_score,
                recommendations=recommendations,
                issues=[]
            )

        except Exception as e:
            logger.error(f"KISS principles analysis failed: {e}")
            return KISSPrinciplesAnalysisResult(
                score=50.0,
                complexity_score=50.0,
                nesting_score=50.0,
                function_score=50.0,
                recommendations=["Unable to analyze KISS principles due to technical issues"],
                issues=[str(e)]
            )

    def _analyze_code_complexity(self, python_files: List[Path]) -> float:
        """Analyze code complexity using basic metrics."""
        if not python_files:
            return 100.0

        total_complexity_score = 0
        analyzed_functions = 0

        for file_path in python_files[:15]:  # Limit for performance
            try:
                content = file_path.read_text()

                # Find function definitions
                functions = re.findall(r'def\s+\w+\s*\([^)]*\)\s*:', content)

                for func_match in functions:
                    # Extract function body (simplified, limit to reasonable size)
                    func_start = content.find(func_match)
                    if func_start == -1:
                        continue

                    # Extract reasonable function body (first 2000 chars should be enough)
                    func_body = content[func_start:func_start + 2000]

                    # Count complexity indicators (simplified to avoid regex hangs)
                    complexity_indicators = 0

                    # Simple counts - much faster and safer
                    if_count = func_body.count('if ')
                    logical_ops = func_body.count(' and ') + func_body.count(' or ')
                    loops = func_body.count('for ') + func_body.count('while ')
                    exceptions = func_body.count('except ')

                    complexity_indicators = if_count + logical_ops + loops + exceptions

                    # Score function complexity (lower is better)
                    if complexity_indicators > 10:
                        func_score = 0
                    elif complexity_indicators > 5:
                        func_score = 50
                    elif complexity_indicators > 2:
                        func_score = 75
                    else:
                        func_score = 100

                    total_complexity_score += func_score
                    analyzed_functions += 1

            except Exception:
                continue

        if analyzed_functions == 0:
            return 100.0

        return total_complexity_score / analyzed_functions

    def _analyze_nesting_levels(self, python_files: List[Path]) -> float:
        """Analyze code nesting levels."""
        if not python_files:
            return 100.0

        total_nesting_score = 0
        analyzed_files = 0

        for file_path in python_files[:10]:  # Limit for performance
            try:
                content = file_path.read_text()
                analyzed_files += 1

                # Find maximum nesting level
                max_nesting = 0
                current_nesting = 0

                for line in content.split('\n'):
                    stripped = line.strip()
                    if not stripped or stripped.startswith('#'):
                        continue

                    # Count leading spaces/tabs
                    indent = len(line) - len(line.lstrip())
                    nesting_level = indent // 4  # Assuming 4 spaces per indent

                    max_nesting = max(max_nesting, nesting_level)

                # Score based on maximum nesting
                if max_nesting > 8:
                    nesting_score = 0
                elif max_nesting > 6:
                    nesting_score = 25
                elif max_nesting > 4:
                    nesting_score = 50
                elif max_nesting > 2:
                    nesting_score = 75
                else:
                    nesting_score = 100

                total_nesting_score += nesting_score

            except Exception:
                continue

        if analyzed_files == 0:
            return 100.0

        return total_nesting_score / analyzed_files

    def _analyze_function_lengths(self, python_files: List[Path]) -> float:
        """Analyze function lengths."""
        if not python_files:
            return 100.0

        total_length_score = 0
        analyzed_functions = 0

        for file_path in python_files[:15]:  # Limit for performance
            try:
                content = file_path.read_text()

                # Find function definitions and their line counts
                functions = re.findall(r'def\s+\w+\s*\([^)]*\)\s*:', content)

                for func_match in functions:
                    func_start = content.find(func_match)
                    if func_start == -1:
                        continue

                    # Count lines in function (simplified)
                    func_body = content[func_start:func_start + 5000]  # Reasonable limit
                    next_func_pos = func_body.find('\ndef ')
                    if next_func_pos == -1:
                        next_func_pos = func_body.find('\nclass ')
                    if next_func_pos != -1:
                        func_body = func_body[:next_func_pos]

                    line_count = func_body.count('\n') + 1

                    # Score based on function length
                    if line_count > 100:
                        func_score = 0
                    elif line_count > 50:
                        func_score = 25
                    elif line_count > 25:
                        func_score = 50
                    elif line_count > 15:
                        func_score = 75
                    else:
                        func_score = 100

                    total_length_score += func_score
                    analyzed_functions += 1

            except Exception:
                continue

        if analyzed_functions == 0:
            return 100.0

        return total_length_score / analyzed_functions
