"""
ThirdPartyToolService - Infrastructure Service

Handles interactions with external analysis tools like interrogate, bandit, etc.
"""

import logging
import subprocess
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ThirdPartyToolService:
    """Infrastructure service for third-party analysis tools.

    Provides abstracted access to external tools like:
    - interrogate (docstring coverage)
    - bandit (security analysis)
    - mypy (type checking)
    - pylint (code quality)
    """

    def __init__(self):
        """Initialize the third-party tool service."""
        self.tools_available = self._check_available_tools()

    def _check_available_tools(self) -> Dict[str, bool]:
        """Check which third-party tools are available."""
        tools = {
            'interrogate': self._is_tool_available('interrogate'),
            'bandit': self._is_tool_available('bandit'),
            'mypy': self._is_tool_available('mypy'),
            'pylint': self._is_tool_available('pylint'),
        }
        return tools

    def _is_tool_available(self, tool_name: str) -> bool:
        """Check if a tool is available on the system."""
        try:
            result = subprocess.run(
                [sys.executable, '-c', f'import {tool_name}'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False

    def run_interrogate(self, path: Path, timeout: int = 60) -> Optional[Dict[str, Any]]:
        """Run interrogate for docstring coverage analysis."""
        if not self.tools_available.get('interrogate', False):
            return None

        try:
            result = subprocess.run([
                sys.executable, '-m', 'interrogate',
                '--generate-badge', '/tmp/badge.svg',
                '--fail-under', '0',  # Don't fail, just report
                str(path)
            ], capture_output=True, text=True, timeout=timeout)

            # Parse the output to extract coverage information
            coverage_info = self._parse_interrogate_output(result.stdout)
            return coverage_info

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.warning(f"Interrogate analysis failed: {e}")
            return None

    def _parse_interrogate_output(self, output: str) -> Dict[str, Any]:
        """Parse interrogate output to extract coverage metrics."""
        # This is a simplified parser - in reality you'd parse the actual output format
        lines = output.split('\n')
        coverage = {
            'total_files': 0,
            'files_with_docstrings': 0,
            'docstring_coverage': 0.0,
            'detailed_breakdown': {}
        }

        for line in lines:
            if 'RESULT:' in line or 'actual:' in line:
                # Extract percentage
                import re
                match = re.search(r'(\d+\.?\d*)%', line)
                if match:
                    coverage['docstring_coverage'] = float(match.group(1))

        return coverage

    def run_bandit(self, path: Path, timeout: int = 120) -> Optional[Dict[str, Any]]:
        """Run bandit for security analysis."""
        if not self.tools_available.get('bandit', False):
            return None

        try:
            result = subprocess.run([
                sys.executable, '-m', 'bandit',
                '-r', str(path),
                '-f', 'json'
            ], capture_output=True, text=True, timeout=timeout)

            if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                import json
                security_report = json.loads(result.stdout)
                return self._parse_bandit_output(security_report)

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError) as e:
            logger.warning(f"Bandit analysis failed: {e}")

        return None

    def _parse_bandit_output(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Parse bandit JSON output."""
        return {
            'total_issues': len(report.get('results', [])),
            'severity_breakdown': self._count_severities(report.get('results', [])),
            'confidence_breakdown': self._count_confidences(report.get('results', [])),
            'issues': report.get('results', [])[:10]  # Top 10 issues
        }

    def _count_severities(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by severity."""
        counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        for issue in issues:
            severity = issue.get('issue_severity', 'UNKNOWN')
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _count_confidences(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count issues by confidence."""
        counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        for issue in issues:
            confidence = issue.get('issue_confidence', 'UNKNOWN')
            counts[confidence] = counts.get(confidence, 0) + 1
        return counts

    def get_available_tools(self) -> Dict[str, bool]:
        """Get the availability status of all supported tools."""
        return self.tools_available.copy()
