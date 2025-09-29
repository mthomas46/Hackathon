"""Code analysis service for Source Agent.

Provides code analysis capabilities for API endpoint detection and patterns.
"""

import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes code for API endpoints and architectural patterns."""

    @staticmethod
    def analyze_code(source: str, code: str, language: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze code for API endpoints and patterns.

        Args:
            source: Source of the code
            code: Code content to analyze
            language: Programming language
            context: Additional context

        Returns:
            Analysis results
        """
        try:
            analysis = {
                "source": source,
                "language": language or "unknown",
                "endpoints": [],
                "patterns": [],
                "complexity": "low"
            }

            # Basic endpoint detection using regex
            endpoints = CodeAnalyzer._extract_endpoints(code)
            analysis["endpoints"] = endpoints

            # Basic pattern detection
            patterns = CodeAnalyzer._detect_patterns(code)
            analysis["patterns"] = patterns

            # Simple complexity assessment
            analysis["complexity"] = CodeAnalyzer._assess_complexity(code)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "source": source,
                "language": language
            }

    @staticmethod
    def _extract_endpoints(code: str) -> List[Dict[str, Any]]:
        """Extract API endpoints from code using regex patterns."""
        endpoints = []

        # FastAPI route patterns
        fastapi_patterns = [
            r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        ]

        # Flask route patterns
        flask_patterns = [
            r'@app\.route\s*\(\s*["\']([^"\']+)["\']',
        ]

        # Express.js route patterns
        express_patterns = [
            r'app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        ]

        all_patterns = fastapi_patterns + flask_patterns + express_patterns

        for pattern in all_patterns:
            matches = re.findall(pattern, code, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    method, path = match
                else:
                    method = "route"  # For Flask-style routes
                    path = match

                endpoints.append({
                    "method": method.upper(),
                    "path": path,
                    "framework": CodeAnalyzer._detect_framework(path, code)
                })

        return endpoints

    @staticmethod
    def _detect_patterns(code: str) -> List[str]:
        """Detect common architectural patterns in code."""
        patterns = []

        # MVC pattern indicators
        if re.search(r'class.*Controller', code, re.IGNORECASE):
            patterns.append("MVC Controller")

        if re.search(r'class.*Model', code, re.IGNORECASE):
            patterns.append("MVC Model")

        if re.search(r'class.*View', code, re.IGNORECASE):
            patterns.append("MVC View")

        # Repository pattern
        if re.search(r'class.*Repository', code, re.IGNORECASE):
            patterns.append("Repository Pattern")

        # Service layer
        if re.search(r'class.*Service', code, re.IGNORECASE):
            patterns.append("Service Layer")

        # Dependency injection
        if re.search(r'@inject|@Inject|injector|Injector', code):
            patterns.append("Dependency Injection")

        # Observer pattern
        if re.search(r'addEventListener|on\(|emit\(', code):
            patterns.append("Observer Pattern")

        return patterns

    @staticmethod
    def _assess_complexity(code: str) -> str:
        """Assess code complexity."""
        lines = len(code.split('\n'))
        functions = len(re.findall(r'def\s+', code))
        classes = len(re.findall(r'class\s+', code))
        nesting = len(re.findall(r'\s{8,}', code))  # Deep indentation

        score = lines + (functions * 10) + (classes * 20) + (nesting * 5)

        if score > 1000:
            return "very_high"
        elif score > 500:
            return "high"
        elif score > 200:
            return "medium"
        else:
            return "low"

    @staticmethod
    def _detect_framework(path: str, code: str) -> str:
        """Detect the web framework being used."""
        if "@app." in code or "@router." in code:
            return "FastAPI"
        elif "@app.route" in code:
            return "Flask"
        elif "app.get(" in code or "app.post(" in code:
            return "Express.js"
        elif "router." in code:
            return "Express.js Router"
        else:
            return "Unknown"
